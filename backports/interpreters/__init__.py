"""Backport of the concurrent.interpreters module (PEP 734).

On Python 3.14+ this re-exports the standard library module. On 3.8 through
3.13 it builds the same API on the primitives in :mod:`._backend`.
"""

import sys

__all__ = [
    "get_current", "get_main", "create", "list_all", "is_shareable",
    "Interpreter",
    "InterpreterError", "InterpreterNotFoundError", "ExecutionFailed",
    "NotShareableError",
    "create_queue", "Queue", "QueueEmpty", "QueueFull",
]


if sys.version_info >= (3, 14):
    # The real thing exists in the standard library.
    from concurrent.interpreters import (  # noqa: F401
        get_current, get_main, create, list_all, is_shareable,
        Interpreter,
        InterpreterError, InterpreterNotFoundError, ExecutionFailed,
        NotShareableError,
        create_queue, Queue, QueueEmpty, QueueFull,
    )

else:
    import threading
    import weakref

    from . import _backend as _interpreters

    InterpreterError = _interpreters.InterpreterError
    InterpreterNotFoundError = _interpreters.InterpreterNotFoundError
    NotShareableError = _interpreters.NotShareableError
    is_shareable = _interpreters.is_shareable

    from ._queues import (
        create as create_queue,
        Queue, QueueEmpty, QueueFull,
    )

    _EXEC_FAILURE_STR = """
{superstr}

Uncaught in the interpreter:

{formatted}
""".strip()

    class ExecutionFailed(InterpreterError):
        """An unhandled exception happened during execution."""

        def __init__(self, excinfo):
            msg = excinfo.formatted
            if not msg:
                if excinfo.type and excinfo.msg:
                    msg = f'{excinfo.type.__name__}: {excinfo.msg}'
                else:
                    msg = excinfo.type.__name__ or excinfo.msg
            super().__init__(msg)
            self.excinfo = excinfo

        def __str__(self):
            try:
                formatted = self.excinfo.errdisplay
            except Exception:
                return super().__str__()
            else:
                return _EXEC_FAILURE_STR.format(
                    superstr=super().__str__(),
                    formatted=formatted,
                )

    def create():
        """Return a new (idle) Python interpreter."""
        id = _interpreters.create(reqrefs=True)
        return Interpreter(id, _ownsref=True)

    def list_all():
        """Return all existing interpreters."""
        return [Interpreter(id, _whence=whence)
                for id, whence in _interpreters.list_all(require_ready=True)]

    def get_current():
        """Return the currently running interpreter."""
        id, whence = _interpreters.get_current()
        return Interpreter(id, _whence=whence)

    def get_main():
        """Return the main interpreter."""
        id, whence = _interpreters.get_main()
        assert whence == _interpreters.WHENCE_RUNTIME, repr(whence)
        return Interpreter(id, _whence=whence)

    _known = weakref.WeakValueDictionary()

    class Interpreter:
        """A single Python interpreter.

        Interpreters not created by this module cannot be modified, so
        close(), prepare_main(), exec() and call() will fail on them.
        """

        _WHENCE_TO_STR = {
            _interpreters.WHENCE_UNKNOWN: 'unknown',
            _interpreters.WHENCE_RUNTIME: 'runtime init',
            _interpreters.WHENCE_LEGACY_CAPI: 'legacy C-API',
            _interpreters.WHENCE_CAPI: 'C-API',
            _interpreters.WHENCE_XI: 'cross-interpreter C-API',
            _interpreters.WHENCE_STDLIB: '_interpreters module',
        }

        def __new__(cls, id, /, _whence=None, _ownsref=None):
            # There is only one instance for any given ID.
            if not isinstance(id, int):
                raise TypeError(f'id must be an int, got {id!r}')
            id = int(id)
            if _whence is None:
                if _ownsref:
                    _whence = _interpreters.WHENCE_STDLIB
                else:
                    _whence = _interpreters.whence(id)
            assert _whence in cls._WHENCE_TO_STR, repr(_whence)
            if _ownsref is None:
                _ownsref = (_whence == _interpreters.WHENCE_STDLIB)
            try:
                self = _known[id]
                assert hasattr(self, '_ownsref')
            except KeyError:
                self = super().__new__(cls)
                _known[id] = self
                self._id = id
                self._whence = _whence
                self._ownsref = _ownsref
                if _ownsref:
                    # May raise InterpreterNotFoundError.
                    _interpreters.incref(id)
            return self

        def __repr__(self):
            return f'{type(self).__name__}({self.id})'

        def __hash__(self):
            return hash(self._id)

        def __del__(self):
            self._decref()

        def _decref(self):
            if not self._ownsref:
                return
            self._ownsref = False
            try:
                _interpreters.decref(self._id)
            except InterpreterNotFoundError:
                pass

        @property
        def id(self):
            return self._id

        @property
        def whence(self):
            return self._WHENCE_TO_STR[self._whence]

        def is_running(self):
            """Return whether the interpreter is running."""
            return _interpreters.is_running(self._id)

        def close(self):
            """Finalize and destroy the interpreter."""
            return _interpreters.destroy(self._id, restrict=True)

        def prepare_main(self, ns=None, /, **kwargs):
            """Bind the given values into the interpreter's __main__."""
            ns = dict(ns, **kwargs) if ns is not None else kwargs
            _interpreters.set___main___attrs(self._id, ns, restrict=True)

        def exec(self, code, /):
            """Run source code in the interpreter, blocking until it finishes.

            Raises ExecutionFailed if the code raises something uncaught.
            """
            excinfo = _interpreters.exec(self._id, code, restrict=True)
            if excinfo is not None:
                raise ExecutionFailed(excinfo)

        def _call(self, callable, args, kwargs):
            res, excinfo = _interpreters.call(
                self._id, callable, args, kwargs, restrict=True)
            if excinfo is not None:
                raise ExecutionFailed(excinfo)
            return res

        def call(self, callable, /, *args, **kwargs):
            """Call the function in the interpreter and return its result.

            Raises ExecutionFailed if the call raises something uncaught.
            """
            return self._call(callable, args, kwargs)

        def call_in_thread(self, callable, /, *args, **kwargs):
            """Like call(), but run it in a new thread and return the thread."""
            t = threading.Thread(
                target=self._call, args=(callable, args, kwargs))
            t.start()
            return t
