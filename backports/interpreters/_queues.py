"""The high level Queue, version-independent.

Objects are pickled to bytes and handed to :mod:`._qbackend` to cross the
interpreter boundary.
"""

import time
import queue
import pickle
import weakref

from . import _qbackend

__all__ = [
    "create", "list_all", "Queue",
    "QueueError", "QueueNotFoundError", "QueueEmpty", "QueueFull",
]


class QueueError(Exception):
    pass


class QueueNotFoundError(QueueError):
    pass


class QueueEmpty(QueueError, queue.Empty):
    pass


class QueueFull(QueueError, queue.Full):
    pass


def create(maxsize=0):
    """Return a new cross-interpreter queue."""
    qid = _qbackend.create(maxsize)
    return Queue(qid, _maxsize=maxsize)


def list_all():
    listing = getattr(_qbackend, "list_all", None)
    if listing is None:
        raise NotImplementedError(
            "listing queues is not available before Python 3.13"
        )
    return [Queue(qid) for qid in listing()]


_known_queues = weakref.WeakValueDictionary()


class Queue:
    """A cross-interpreter FIFO queue."""

    def __new__(cls, id, /, _maxsize=0):
        if not isinstance(id, int):
            raise TypeError(f"id must be an int, got {id!r}")
        id = int(id)
        try:
            self = _known_queues[id]
        except KeyError:
            self = super().__new__(cls)
            self._id = id
            self._maxsize = _maxsize
            _known_queues[id] = self
            _qbackend.bind(id)
        return self

    def __del__(self):
        try:
            _qbackend.release(self._id)
        except Exception:
            pass

    def __repr__(self):
        return f"{type(self).__name__}({self._id})"

    def __hash__(self):
        return hash(self._id)

    def __reduce__(self):
        return (type(self), (self._id,))

    @property
    def id(self):
        return self._id

    @property
    def maxsize(self):
        return self._maxsize

    def qsize(self):
        return _qbackend.count(self._id)

    def empty(self):
        return self.qsize() == 0

    def full(self):
        if self._maxsize <= 0:
            return _qbackend.is_full(self._id)
        return self.qsize() >= self._maxsize

    def put(self, obj, block=True, timeout=None, *, _delay=10 / 1000):
        data = pickle.dumps(obj)
        if not block:
            return self.put_nowait(obj)
        deadline = None if timeout is None else time.time() + timeout
        while True:
            if self._maxsize > 0 and _qbackend.SUPPORTS_COUNT:
                if _qbackend.count(self._id) >= self._maxsize:
                    if deadline is not None and time.time() >= deadline:
                        raise QueueFull
                    time.sleep(_delay)
                    continue
            _qbackend.put(self._id, data)
            return

    def put_nowait(self, obj):
        if self._maxsize > 0 and _qbackend.SUPPORTS_COUNT:
            if _qbackend.count(self._id) >= self._maxsize:
                raise QueueFull
        _qbackend.put(self._id, pickle.dumps(obj))

    def get(self, block=True, timeout=None, *, _delay=10 / 1000):
        if not block:
            return self.get_nowait()
        deadline = None if timeout is None else time.time() + timeout
        while True:
            try:
                data = _qbackend.get(self._id)
            except _qbackend._Empty:
                if deadline is not None and time.time() >= deadline:
                    raise QueueEmpty
                time.sleep(_delay)
                continue
            except _qbackend._NotFound as exc:
                raise QueueNotFoundError(self._id) from exc
            return pickle.loads(data)

    def get_nowait(self):
        try:
            data = _qbackend.get(self._id)
        except _qbackend._Empty:
            raise QueueEmpty
        except _qbackend._NotFound as exc:
            raise QueueNotFoundError(self._id) from exc
        return pickle.loads(data)
