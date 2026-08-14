"""
Tests for the default application event loop.
"""
from threading import Event, Thread

import pyglet
from pyglet.app import event_loop
from pyglet.event import EventDispatcher
from pyglet.window import Window
from tests import mock
from tests.annotations import Platform, skip_platform


class EventTarget(EventDispatcher):
    def __init__(self):
        self.received = False

    def on_custom_event(self):
        self.received = True


EventTarget.register_event_type("on_custom_event")


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


@skip_platform(Platform.EMSCRIPTEN)
def test_documented_custom_event_loop_pumps_events_and_draws():
    """A bounded version of the documented manual event loop works."""
    window = Window(width=64, height=64, visible=False, vsync=False)
    target = EventTarget()
    clock_called = False
    window_event_received = False
    draw_called = False

    def scheduled(_dt):
        nonlocal clock_called
        clock_called = True

    @window.event
    def on_text(text):
        nonlocal window_event_received
        window_event_received = text == "custom-loop"

    @window.event
    def on_draw():
        nonlocal draw_called
        draw_called = True

    try:
        window.dispatch_events()
        initial_frame = window.context.frame_index
        pyglet.clock.schedule_once(scheduled, 0)
        target.post_event("on_custom_event")
        window.dispatch_event("on_text", "custom-loop")

        iterations = 0
        while iterations < 5 and not all((clock_called, target.received, window_event_received, draw_called)):
            dt = pyglet.clock.tick()
            pyglet.app.platform_event_loop.step(0)

            for app_window in pyglet.app.windows:
                app_window.switch_to()
                app_window.dispatch_events()
                app_window.draw(dt)

            iterations += 1

        assert clock_called
        assert target.received
        assert window_event_received
        assert draw_called
        assert window.context.frame_index > initial_frame
    finally:
        pyglet.clock.unschedule(scheduled)
        window.close()
