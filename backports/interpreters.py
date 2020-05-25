import _xxsubinterpreters
from typing import List


class Interpreter:
    def __init__(self, id: int):
        self._id = id

    @property
    def id(self) -> int:
        return int(self._id)

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
    return Interpreter(_xxsubinterpreters.create())
