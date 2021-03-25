from backports import interpreters


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
    assert main.is_running() is True

    other = interpreters.create()
    assert other.id > 0


def test_destroy():
    new = interpreters.create()
    new.close()


def test_run():
    interp = interpreters.create()
    interp.run("print('Hello world!')")


def test_is_shareable():
    assert interpreters.is_shareable(1)
    assert not interpreters.is_shareable({})


def test_create_and_list_channels():
    recv, send = interpreters.create_channel()
    assert interpreters.list_all_channels()


def test_send_and_recv_on_channel():
    recv, send = interpreters.create_channel()
    send.send(42)
    assert recv.recv() == 42


def test_send_and_recv_on_channel_between_interpreters():
    recv, send = interpreters.create_channel()
    send.send(43)
    script = f"from backports import interpreters; assert interpreters.RecvChannel({recv.id}).recv() == 43"
    interpreters.create().run(script)
