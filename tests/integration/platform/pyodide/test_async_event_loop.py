from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
import sys

import pytest

if sys.platform != "emscripten":
    pytest.skip("requires the Emscripten/Pyodide runtime", allow_module_level=True)

from js import KeyboardEvent, Object
from pyodide.ffi import run_sync, to_js

import pyglet
from pyglet import app, clock
from pyglet.app.async_app import AsyncEventLoop, AsyncPlatformEventLoop, RequestAnimationFrameDrawSource
from pyglet.event import EventDispatcher


class _EventTarget(EventDispatcher):
    def __init__(self) -> None:
        self.received: list[int] = []

    def on_value(self, value: int) -> None:
        self.received.append(value)


_EventTarget.register_event_type("on_value")


def test_window_close_exits_synchronously(monkeypatch):
    loop = AsyncEventLoop()
    assert not loop._has_exit_event.is_set()  # noqa: SLF001
    monkeypatch.setattr(app, "windows", set())

    loop.dispatch_event("on_window_close", None)

    assert loop._has_exit_event.is_set()  # noqa: SLF001


def test_post_event_matches_platform_event_loop_contract(monkeypatch):
    loop = AsyncPlatformEventLoop()
    target = _EventTarget()

    monkeypatch.setattr(app, "platform_event_loop", loop)
    loop.start()
    target.post_event("on_value", 42)
    loop.dispatch_posted_events()
    loop.stop()

    assert target.received == [42]


def test_request_animation_frame_draw_source_uses_browser_timestamps(monkeypatch):
    loop = AsyncEventLoop()
    draws: list[float] = []
    monkeypatch.setattr(loop, "_redraw_windows", draws.append)
    source = RequestAnimationFrameDrawSource(loop)
    monkeypatch.setattr(source, "_request_next_frame", lambda: None)

    source.start(1 / 60)
    source._on_animation_frame(1000)  # noqa: SLF001
    source._on_animation_frame(1016)  # noqa: SLF001
    source.stop()

    assert draws == pytest.approx([0.0, 0.016])


@pytest.fixture(autouse=True)
def restore_default_clock(monkeypatch):
    """Restore the shared clock after AsyncEventLoop replaces it."""
    monkeypatch.setattr(clock, "_default", clock.get_default())


@pytest.fixture
def running_loop(monkeypatch):
    @asynccontextmanager
    async def run(interval=1 / 60, initial_delay=None, *, draw=False):
        loop = AsyncEventLoop()
        platform = AsyncPlatformEventLoop()
        monkeypatch.setattr(app, "event_loop", loop)
        monkeypatch.setattr(app, "platform_event_loop", platform)
        monkeypatch.setattr(app, "windows", set())
        if initial_delay is not None:
            loop.clock.schedule_once(lambda dt: None, initial_delay)
        waiting = asyncio.Event()
        timeouts = []
        original_wait = platform.wait

        async def wait(timeout):
            timeouts.append(timeout)
            waiting.set()
            await original_wait(timeout)

        monkeypatch.setattr(platform, "wait", wait)
        task = asyncio.create_task(loop._run(interval))
        try:
            await asyncio.wait_for(waiting.wait(), 2)
            if not draw and loop._window_draw_source is not None:
                # Stop the real draw source to exercise scheduling without frames.
                loop._window_draw_source.stop()
            yield loop, platform, task, timeouts
        finally:
            loop.exit()
            await asyncio.wait_for(task, 2)

    return run


@pytest.mark.parametrize("interval", [None, 1 / 60])
@pytest.mark.parametrize("initial_delay", [None, 60])
@pytest.mark.parametrize("scheduler, args", [
    ("schedule", ()),
    ("schedule_once", (0.005,)),
    ("schedule_interval", (0.005,)),
    ("schedule_interval_soft", (0.005,)),
    ("schedule_interval_fixed_delay", (0.005,)),
    ("schedule_interval_for_duration", (0.005, 60)),
])
def test_external_scheduling_runs_without_frames(running_loop, interval, initial_delay, scheduler, args):
    async def scenario():
        async with running_loop(interval, initial_delay) as (loop, platform, task, timeouts):
            assert (timeouts[0] is None) == (initial_delay is None)
            fired = asyncio.get_running_loop().create_future()

            def callback(dt, value, *, label):
                clock.unschedule(callback)
                fired.set_result((value, label))

            # This coroutine schedules work after _run() has entered its wait,
            # outside any DOM, resize, draw, or posted-event callback.
            getattr(clock, scheduler)(callback, *args, 42, label="scheduled")
            assert await asyncio.wait_for(fired, 2) == (42, "scheduled")
            assert not task.done()

    run_sync(scenario())


def test_existing_interval_keeps_running_without_frames(running_loop):
    async def scenario():
        async with running_loop() as (loop, platform, task, timeouts):
            fired = asyncio.Event()
            calls = []

            def callback(dt):
                calls.append(dt)
                if len(calls) == 3:
                    loop.clock.unschedule(callback)
                    fired.set()

            loop.clock.schedule_interval(callback, 0.005)
            await asyncio.wait_for(fired.wait(), 2)
            assert len(calls) == 3

    run_sync(scenario())


def test_later_work_does_not_interrupt_existing_wait(running_loop, monkeypatch):
    async def scenario():
        async with running_loop(initial_delay=60) as (loop, platform, task, timeouts):
            notifications = []
            original_notify = platform.notify

            def notify():
                notifications.append(True)
                original_notify()

            monkeypatch.setattr(platform, "notify", notify)
            loop.clock.schedule_once(lambda dt: None, 120)
            # Check the notification instead of counting asyncio turns
            # wait_for() needs extra turns to resume on Python 3.11 and older.
            assert notifications == []
            assert len(timeouts) == 1

    run_sync(scenario())


def test_dom_handler_can_schedule_without_frames(running_loop):
    async def scenario():
        async with running_loop(interval=None) as (loop, platform, task, timeouts):
            window = pyglet.window.Window(width=128, height=96)
            received_key = asyncio.get_running_loop().create_future()

            def on_key_press(symbol, modifiers):
                clock.schedule_once(lambda dt: received_key.set_result(symbol), 0.01)

            window.push_handlers(on_key_press=on_key_press)
            try:
                init = to_js({"key": "a", "code": "KeyA"}, dict_converter=Object.fromEntries)
                window.canvas.dispatchEvent(KeyboardEvent.new("keydown", init))
                window.canvas.dispatchEvent(KeyboardEvent.new("keyup", init))
                assert await asyncio.wait_for(received_key, 2) == pyglet.window.key.A
            finally:
                window.pop_handlers()
                window.close()

    run_sync(scenario())


def test_resize_handler_can_schedule_without_frames(running_loop):
    async def scenario():
        async with running_loop(interval=None) as (loop, platform, task, timeouts):
            window = pyglet.window.Window(width=128, height=96, resizable=True)
            received_size = asyncio.get_running_loop().create_future()

            def on_resize(width, height):
                clock.schedule_once(lambda dt: received_size.set_result((width, height)), 0.01)

            window.push_handlers(on_resize=on_resize)
            try:
                # Changing the canvas size makes the browser's ResizeObserver call on_resize.
                window.set_size(160, 120)
                expected_size = window.get_size()
                assert await asyncio.wait_for(received_size, 2) == expected_size
            finally:
                window.pop_handlers()
                window.close()

    run_sync(scenario())


def test_scheduling_inside_clock_callback_does_not_add_a_wakeup(running_loop, monkeypatch):
    async def scenario():
        async with running_loop() as (loop, platform, task, timeouts):
            fired = asyncio.Event()
            loop.clock.schedule_once(lambda dt: loop.clock.schedule_once(lambda dt: fired.set(), 0.005), 0)
            notifications = []
            original_notify = platform.notify

            def notify():
                notifications.append(True)
                original_notify()

            monkeypatch.setattr(platform, "notify", notify)
            await asyncio.wait_for(fired.wait(), 2)
            assert notifications == []

    run_sync(scenario())


def test_posted_handler_can_schedule_without_frames(running_loop):
    async def scenario():
        received_value = asyncio.get_running_loop().create_future()

        class Target(EventDispatcher):
            def on_work(self, value):
                clock.schedule_once(lambda dt: received_value.set_result(value), 0)

        Target.register_event_type("on_work")
        async with running_loop() as (loop, platform, task, timeouts):
            platform.post_event(Target(), "on_work", 42)
            assert await asyncio.wait_for(received_value, 2) == 42

    run_sync(scenario())


def test_clock_callback_can_exit_without_frames(running_loop):
    async def scenario():
        async with running_loop(interval=None) as (loop, platform, task, timeouts):
            loop.clock.schedule_once(lambda dt: loop.exit(), 0)
            await asyncio.wait_for(asyncio.shield(task), 2)
            assert not loop.is_running

    run_sync(scenario())


@pytest.mark.parametrize("timeout", [None, 60, 0])
def test_wait_preserves_pending_notification(timeout):
    async def scenario():
        platform = AsyncPlatformEventLoop()
        platform.notify()
        await asyncio.wait_for(platform.wait(timeout), 2)
        assert not platform._wake_event.is_set()

        # The notification was consumed, so a later indefinite wait must sleep.
        task = asyncio.create_task(platform.wait(None))
        await asyncio.sleep(0)
        assert not task.done()
        platform.notify()
        await asyncio.wait_for(task, 2)

    run_sync(scenario())




def test_drawing_only_wakes_clock_when_it_schedules_work(running_loop):
    async def scenario():
        async with running_loop(draw=True) as (loop, platform, task, timeouts):
            window = pyglet.window.Window(width=128, height=96)
            source = loop._window_draw_source
            frames_drawn = asyncio.Event()
            draws = []

            def on_draw():
                window.clear()
                draws.append(True)
                if len(draws) == 3:
                    source.stop()
                    frames_drawn.set()

            window.push_handlers(on_draw=on_draw)
            try:
                await asyncio.wait_for(frames_drawn.wait(), 2)
                assert len(timeouts) == 1
                window.pop_handlers()

                fired = asyncio.Event()

                def schedule_from_draw():
                    window.clear()
                    clock.schedule_once(lambda dt: fired.set(), 0.01)
                    source.stop()

                window.push_handlers(on_draw=schedule_from_draw)
                source.start(1 / 60)
                # The drawing handler stops frames, so only clock scheduling can wake the loop.
                await asyncio.wait_for(fired.wait(), 2)
            finally:
                window.pop_handlers()
                window.close()

    run_sync(scenario())
