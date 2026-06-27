"""Moves pickled bytes between interpreters.

Backed by the native ``_interpqueues`` on 3.13 and by interpreter channels on
3.8 through 3.12. Channels cannot report their size, so ``SUPPORTS_COUNT`` is
False there and the queue size methods are unavailable.
"""

import sys

_PY = sys.version_info


class _Empty(Exception):
    pass


class _NotFound(Exception):
    pass


if _PY >= (3, 13):
    import _interpqueues as _q

    SUPPORTS_COUNT = True

    # fmt 0 stores our bytes as-is, unboundop 3 replaces unbound items.
    _FMT = 0
    _UNBOUNDOP = 3

    QueueError = _q.QueueError
    QueueNotFoundError = _q.QueueNotFoundError

    # Runs in a target interpreter to send a bytes payload back. Wants
    # __xi_tid and __xi_payload already in scope.
    SUBINTERP_SEND = (
        "import _interpqueues as __xi_t\n"
        "__xi_t.put(__xi_tid, __xi_payload, 0, 3)\n"
    )

    def create(maxsize=0):
        return _q.create(maxsize, _FMT, _UNBOUNDOP)

    def destroy(qid):
        try:
            _q.destroy(qid)
        except QueueNotFoundError:
            pass

    def bind(qid):
        _q.bind(qid)

    def release(qid):
        try:
            _q.release(qid)
        except QueueNotFoundError:
            pass

    def put(qid, data):
        _q.put(qid, data, _FMT, _UNBOUNDOP)

    def get(qid):
        if _q.get_count(qid) == 0:
            raise _Empty
        obj = _q.get(qid)[0]
        return obj

    def count(qid):
        return _q.get_count(qid)

    def is_full(qid):
        return _q.is_full(qid)

    def maxsize(qid):
        return _q.get_maxsize(qid)

else:
    if _PY >= (3, 12):
        import _xxinterpchannels as _c

        _create = _c.create
        _send = _c.send
        _recv = _c.recv
        _destroy = _c.destroy
        _Empty_native = _c.ChannelEmptyError
        _NotFound_native = _c.ChannelNotFoundError

        SUBINTERP_SEND = (
            "import _xxinterpchannels as __xi_t\n"
            "__xi_t.send(__xi_tid, __xi_payload)\n"
        )
    else:
        import _xxsubinterpreters as _c

        _create = _c.channel_create
        _send = _c.channel_send
        _recv = _c.channel_recv
        _destroy = _c.channel_destroy
        _Empty_native = _c.ChannelEmptyError
        _NotFound_native = _c.ChannelNotFoundError

        SUBINTERP_SEND = (
            "import _xxsubinterpreters as __xi_t\n"
            "__xi_t.channel_send(__xi_tid, __xi_payload)\n"
        )

    SUPPORTS_COUNT = False

    class QueueError(Exception):
        pass

    class QueueNotFoundError(QueueError):
        pass

    # The ChannelID owns the channel, so keep it alive like an interpreter id.
    _chan_objs = {}

    def create(maxsize=0):
        # Channels are unbounded, so maxsize is ignored here.
        obj = _create()
        cid = int(obj)
        _chan_objs[cid] = obj
        return cid

    def destroy(qid):
        try:
            _destroy(qid)
        except Exception:
            pass
        _chan_objs.pop(int(qid), None)

    def bind(qid):
        pass

    def release(qid):
        try:
            _destroy(qid)
        except Exception:
            pass
        _chan_objs.pop(int(qid), None)

    def put(qid, data):
        _send(qid, data)

    def get(qid):
        try:
            return _recv(qid)
        except _Empty_native:
            raise _Empty
        except _NotFound_native as exc:
            raise _NotFound from exc

    def count(qid):
        raise NotImplementedError(
            "queue size is not available before Python 3.13"
        )

    def is_full(qid):
        return False

    def maxsize(qid):
        return 0
