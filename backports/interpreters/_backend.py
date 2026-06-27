"""Low level interpreter primitives, normalised across Python versions.

On 3.13 the native ``_interpreters`` module is used directly, apart from
``call()`` which gains its 3.14 arguments and return value here. On 3.8 through
3.12 everything is emulated over ``_xxsubinterpreters`` by running a small
pickle/marshal bootstrap and shipping the result back over a channel.
"""

import os
import sys
import time
import types
import pickle
import marshal

from . import _qbackend

_PY = sys.version_info

WHENCE_UNKNOWN = 0
WHENCE_RUNTIME = 1
WHENCE_LEGACY_CAPI = 2
WHENCE_CAPI = 3
WHENCE_XI = 4
WHENCE_STDLIB = 5


class _ExcInfo:
    """Stands in for what _interpreters.capture_exception returns."""

    def __init__(self, formatted, typename, msg):
        self.formatted = formatted
        self.errdisplay = formatted
        self.type = types.SimpleNamespace(__name__=typename)
        self.msg = msg


# Runs in the target interpreter and ships a pickled (ok, ...) tuple back home.
_RUNNER = """
import pickle as __xi_pk, traceback as __xi_tb, marshal as __xi_ma, types as __xi_ty
try:
    if __xi_mode == 0:
        exec(compile(__xi_code.decode('utf-8'), '<string>', 'exec'), globals())
        __xi_res = None
    else:
        __xi_fn = __xi_ty.FunctionType(__xi_ma.loads(__xi_code), globals())
        __xi_a, __xi_k = __xi_pk.loads(__xi_callargs)
        __xi_res = __xi_fn(*__xi_a, **__xi_k)
    __xi_ok = True
except BaseException as __xi_e:
    __xi_ok = False
    __xi_err = (__xi_tb.format_exc(), type(__xi_e).__name__, str(__xi_e))
if __xi_ok:
    try:
        __xi_payload = __xi_pk.dumps((True, __xi_res))
    except BaseException as __xi_e:
        __xi_payload = __xi_pk.dumps(
            (False, __xi_tb.format_exc(), type(__xi_e).__name__, str(__xi_e)))
else:
    __xi_payload = __xi_pk.dumps((False,) + __xi_err)
""" + _qbackend.SUBINTERP_SEND


def _recv_oneshot(tid, timeout=30.0):
    deadline = time.time() + timeout
    while True:
        try:
            return _qbackend.get(tid)
        except _qbackend._Empty:
            if time.time() >= deadline:
                raise InterpreterError("timed out waiting for interpreter result")
            time.sleep(0.0005)


def _run_captured(id, *, mode, code, callargs):
    tid = _qbackend.create()
    _qbackend.bind(tid)
    shared = {"__xi_tid": int(tid), "__xi_mode": mode, "__xi_code": code}
    if callargs is not None:
        shared["__xi_callargs"] = callargs
    try:
        err = _run_string(id, _RUNNER, shared)
        if err is not None:
            raise InterpreterError(getattr(err, "formatted", str(err)))
        payload = _recv_oneshot(tid)
    finally:
        _qbackend.destroy(tid)
    data = pickle.loads(payload)
    if data[0]:
        return data[1], None
    return None, _ExcInfo(data[1], data[2], data[3])


def _code_payload(code):
    if isinstance(code, str):
        return 0, code.encode("utf-8")
    if isinstance(code, types.FunctionType):
        code = code.__code__
    if isinstance(code, types.CodeType):
        return 1, marshal.dumps(code)
    raise TypeError("exec() arg must be a string, function, or code object")


_PKG_PARENT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def _bind_main(id, ns):
    if not ns:
        return
    # Put our package on the worker's path so it can unpickle a Queue etc.
    shared = {"__xi_path": _PKG_PARENT}
    boot = [
        "import sys as __xi_sys, pickle as __xi_pk",
        "__xi_path in __xi_sys.path or __xi_sys.path.insert(0, __xi_path)",
    ]
    for i, (key, value) in enumerate(ns.items()):
        slot = "__xi_b%d" % i
        try:
            shared[slot] = pickle.dumps(value)
        except Exception as exc:
            raise NotShareableError(key) from exc
        boot.append("globals()[%r] = __xi_pk.loads(%s); del %s" % (key, slot, slot))
    boot.append("del __xi_pk, __xi_sys, __xi_path")
    err = _run_string(id, "\n".join(boot), shared)
    if err is not None:
        raise InterpreterError(getattr(err, "formatted", str(err)))


if _PY >= (3, 13):
    import _interpreters as _impl

    InterpreterError = _impl.InterpreterError
    InterpreterNotFoundError = _impl.InterpreterNotFoundError
    NotShareableError = _impl.NotShareableError
    is_shareable = _impl.is_shareable

    create = _impl.create
    destroy = _impl.destroy
    list_all = _impl.list_all
    get_current = _impl.get_current
    get_main = _impl.get_main
    is_running = _impl.is_running
    whence = _impl.whence
    incref = _impl.incref
    decref = _impl.decref
    exec = _impl.exec

    def _run_string(id, src, shared):
        return _impl.exec(id, src, shared, restrict=False)

    def set___main___attrs(id, ns, *, restrict=False):
        # Native set___main___attrs only takes shareables, so go through pickle
        # to also accept plain picklable objects like our Queue.
        _bind_main(id, dict(ns))

    def call(id, callable, args=None, kwargs=None, *, restrict=False):
        # Native call() here takes no args and returns nothing, so emulate it.
        if not isinstance(callable, types.FunctionType):
            raise TypeError("call() only supports plain functions")
        payload = marshal.dumps(callable.__code__)
        callargs = pickle.dumps((tuple(args or ()), dict(kwargs or {})))
        return _run_captured(id, mode=1, code=payload, callargs=callargs)


else:
    import _xxsubinterpreters as _impl

    class InterpreterError(Exception):
        """A cross-interpreter operation failed."""

    class InterpreterNotFoundError(InterpreterError):
        """An interpreter was not found."""

    class NotShareableError(ValueError):
        """An object cannot be shared between interpreters."""

    is_shareable = _impl.is_shareable

    _refcounts = {}
    # The id object owns the interpreter, so dropping it destroys the
    # interpreter. Hold onto it until we are done.
    _objs = {}

    def _cid(id):
        return int(id)

    def incref(id, *, implieslink=False):
        id = _cid(id)
        _refcounts[id] = _refcounts.get(id, 0) + 1

    def decref(id):
        id = _cid(id)
        count = _refcounts.get(id, 0) - 1
        if count <= 0:
            _refcounts.pop(id, None)
            if id in _objs:
                try:
                    _impl.destroy(id)
                except Exception:
                    pass
                _objs.pop(id, None)
        else:
            _refcounts[id] = count

    def whence(id):
        id = _cid(id)
        try:
            if id == int(_impl.get_main()):
                return WHENCE_RUNTIME
        except Exception:
            pass
        return WHENCE_STDLIB if id in _objs else WHENCE_UNKNOWN

    def create(config="isolated", *, reqrefs=False):
        if _PY >= (3, 9):
            try:
                obj = _impl.create(isolated=(config != "legacy"))
            except TypeError:
                obj = _impl.create()
        else:
            obj = _impl.create()
        id = _cid(obj)
        _objs[id] = obj
        return id

    def destroy(id, *, restrict=False):
        id = _cid(id)
        try:
            _impl.destroy(id)
        except Exception as exc:
            raise InterpreterNotFoundError(id) from exc
        _objs.pop(id, None)
        _refcounts.pop(id, None)

    def list_all(*, require_ready=False):
        return [(_cid(i), whence(i)) for i in _impl.list_all()]

    def get_current():
        id = _cid(_impl.get_current())
        return (id, whence(id))

    def get_main():
        id = _cid(_impl.get_main())
        return (id, WHENCE_RUNTIME)

    def is_running(id, *, restrict=False):
        return _impl.is_running(_cid(id))

    def _run_string(id, src, shared):
        try:
            _impl.run_string(_cid(id), src, shared=shared)
        except _impl.RunFailedError as exc:
            return _ExcInfo(str(exc), "RunFailedError", str(exc))
        return None

    def set___main___attrs(id, ns, *, restrict=False):
        _bind_main(_cid(id), dict(ns))

    def exec(id, code, shared=None, *, restrict=False):
        if shared:
            _bind_main(_cid(id), dict(shared))
        mode, payload = _code_payload(code)
        callargs = pickle.dumps(((), {})) if mode == 1 else None
        _res, excinfo = _run_captured(_cid(id), mode=mode, code=payload,
                                      callargs=callargs)
        return excinfo

    def call(id, callable, args=None, kwargs=None, *, restrict=False):
        if not isinstance(callable, types.FunctionType):
            raise TypeError("call() only supports plain functions")
        payload = marshal.dumps(callable.__code__)
        callargs = pickle.dumps((tuple(args or ()), dict(kwargs or {})))
        return _run_captured(_cid(id), mode=1, code=payload, callargs=callargs)
