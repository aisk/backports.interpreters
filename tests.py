from backports import interpreters
import _xxsubinterpreters


def test_list_all():
    assert interpreters.list_all()


def test_get_main():
    main = interpreters.get_main()
    assert isinstance(main, interpreters.Interpreter)
    assert main.id == 0  # Main interpreter's id is always be 0.


def test_get_current():
    current = interpreters.get_current()
    assert isinstance(current, interpreters.Interpreter)
    assert current.id == 0  # Since we are running under main interpreter.


def test_create():
    created = interpreters.create()
    assert isinstance(created, interpreters.Interpreter)


def test_basic_fields():
    main = interpreters.get_main()
    assert main.id == 0
    assert main.is_running() == True

    other = interpreters.create()
    assert other.id > 0


def test_destroy():
    new = interpreters.create()
    new.close()


def test_run():
    interp = interpreters.create()
    interp.run("print('Hello world!')")