import _xxsubinterpreters
from typing import List, Tuple


class Interpreter:
    def __init__(self, id: int):
        self._id = id
        self._subinterpreter = None

    @property
    def id(self) -> int:
        return self._id

    @property
    def isolated(self) -> bool:
        return True

    def is_running(self) -> bool:
        return _xxsubinterpreters.is_running(self._id)

    def close(self):
        _xxsubinterpreters.destroy(self._id)

    def run(self, source_str, /, *, channels=None):
        _xxsubinterpreters.run_string(self._id, source_str)


def list_all() -> List[Interpreter]:
    return [Interpreter(x) for x in _xxsubinterpreters.list_all()]


def get_current() -> Interpreter:
    return Interpreter(_xxsubinterpreters.get_current())


def get_main() -> Interpreter:
    return Interpreter(_xxsubinterpreters.get_main())


def create(*, isolated=True) -> Interpreter:
    subinterp = _xxsubinterpreters.create()
    interp = Interpreter(int(subinterp))
    interp._subinterpreter = (
        subinterp  # Add refference to ensure that they have the same lifetime.
    )
    return interp


def is_shareable(obj) -> bool:
    return _xxsubinterpreters.is_shareable(obj)


class RecvChannel:
    def __init__(self, id: int):
        self._channel = None
        self._id = id

    @property
    def id(self) -> int:
        return int(self._id)

    def recv(self):
        return _xxsubinterpreters.channel_recv(self._id)


class SendChannel:
    def __init__(self, id: int):
        self._channel = None
        self._id = id

    @property
    def id(self) -> int:
        return int(self._id)

    def send(self, obj):
        _xxsubinterpreters.channel_send(self._id, obj)


def create_channel() -> Tuple[RecvChannel, SendChannel]:
    c = _xxsubinterpreters.channel_create()
    recv = RecvChannel(c.recv)
    recv._channel = c
    send = SendChannel(c.send)
    send._channel = c
    return (recv, send)


def list_all_channels() -> List[Tuple[RecvChannel, SendChannel]]:
    return [
        (RecvChannel(c.recv), SendChannel(c.send))
        for c in _xxsubinterpreters.channel_list_all()
    ]
