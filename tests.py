import pickle
import pytest

from backports import interpreters


def test_list_all():
    assert interpreters.list_all()


def test_get_main():
    main = interpreters.get_main()
    assert isinstance(main, interpreters.Interpreter)
    assert main.id == 0  # Main interpreter's id is always 0.
    assert main.whence == 'runtime init'


def test_get_current():
    current = interpreters.get_current()
    assert isinstance(current, interpreters.Interpreter)
    assert current.id == 0  # Since we are running under the main interpreter.


def test_create():
    created = interpreters.create()
    assert isinstance(created, interpreters.Interpreter)
    assert created.id > 0
    created.close()


def test_basic_fields():
    main = interpreters.get_main()
    assert main.id == 0
    assert main.is_running() is True

    other = interpreters.create()
    assert other.id > 0
    other.close()


def test_destroy():
    new = interpreters.create()
    new.close()


def test_exec_string():
    interp = interpreters.create()
    interp.exec("x = 1 + 1")
    interp.close()


def test_exec_failure():
    interp = interpreters.create()
    with pytest.raises(interpreters.ExecutionFailed):
        interp.exec("raise ValueError('boom')")
    interp.close()


def _double():
    return 21 * 2


def test_call_returns_value():
    interp = interpreters.create()
    assert interp.call(_double) == 42
    interp.close()


def _add(a, b):
    return a + b


def test_call_with_args():
    interp = interpreters.create()
    assert interp.call(_add, 3, 4) == 7
    interp.close()


def test_call_in_thread():
    interp = interpreters.create()
    t = interp.call_in_thread(_double)
    t.join()
    interp.close()


def test_prepare_main():
    interp = interpreters.create()
    interp.prepare_main(value=123)
    interp.exec("assert value == 123, value")
    interp.close()


def test_is_shareable():
    assert interpreters.is_shareable(b"abc")
    assert interpreters.is_shareable(42)


def test_queue_put_get():
    q = interpreters.create_queue()
    q.put({"a": 1, "b": [2, 3]})
    assert q.get() == {"a": 1, "b": [2, 3]}


def test_queue_nowait_empty():
    q = interpreters.create_queue()
    with pytest.raises(interpreters.QueueEmpty):
        q.get_nowait()


def test_queue_across_interpreters():
    q = interpreters.create_queue()
    interp = interpreters.create()
    interp.prepare_main(q=q)
    interp.exec("q.put('from sub')")
    assert q.get() == "from sub"
    interp.close()
