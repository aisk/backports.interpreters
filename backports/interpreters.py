import sys
import _xxsubinterpreters
from typing import List


class Interpreter:
    def __init__(self, id: int):
        self._id = id
        self._subinterpreter = None

    @property
    def id(self) -> int:
        return self._id

    def is_running(self) -> bool:
        return _xxsubinterpreters.is_running(self._id)

    def close(self):
        _xxsubinterpreters.destroy(self._id)

    def run(self, src_str, /):
        _xxsubinterpreters.run_string(self._id, src_str)


def list_all() -> List[Interpreter]:
    return [Interpreter(x) for x in _xxsubinterpreters.list_all()]


def get_current() -> Interpreter:
    return Interpreter(_xxsubinterpreters.get_current())


def get_main() -> Interpreter:
    return Interpreter(_xxsubinterpreters.get_main())


def create() -> Interpreter:
    if sys.version_info >= (3, 9):
        subinterp = _xxsubinterpreters.create(isolated=1)
    else:
        subinterp = _xxsubinterpreters.create()
    interp = Interpreter(int(subinterp))
    interp._subinterpreter = (
        subinterp  # Add refference to ensure that they have the same lifetime.
    )
    return interp
