"""
Tests for the default application event loop.
"""
from threading import Event, Thread

from pyglet.app import event_loop
from tests import mock


def check_running():
    assert event_loop.is_running


def test_start_stop(performance):
    event_loop.clock.schedule_once(lambda dt: check_running(), .1)
    event_loop.clock.schedule_once(lambda dt: event_loop.exit(), .2)
    with performance.timer(1.):
        event_loop.run()
    assert not event_loop.is_running


def test_multiple_start_stop(performance):
    with performance.timer(30.):
        for _ in range(100):
            test_start_stop(performance)


def test_events():
    enter_mock = mock.MagicMock()
    exit_mock = mock.MagicMock()
    event_loop.push_handlers(on_enter=enter_mock,
                             on_exit=exit_mock)
    try:
        event_loop.clock.schedule_once(lambda dt: event_loop.exit(), .1)
        event_loop.run()
        enter_mock.assert_called_once_with()
        exit_mock.assert_called_once_with()
    finally:
        event_loop.pop_handlers()


def test_on_window_close():
    event_loop.clock.schedule_once(lambda dt: event_loop.on_window_close(None), .1)
    event_loop.run()
    assert not event_loop.is_running


def test_sleep(performance):
    def _sleep():
        event_loop.sleep(100.)
        _sleep.returned.set()
    _sleep.returned = Event()
    thread = Thread(target=_sleep)

    event_loop.clock.schedule_once(lambda dt: thread.start(), .1)
    event_loop.clock.schedule_once(lambda dt: event_loop.exit(), .2)
    with performance.timer(1.):
        event_loop.run()
    assert not event_loop.is_running
    assert _sleep.returned.wait(1.)
