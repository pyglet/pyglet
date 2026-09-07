"""UIKit app loop integration on iOS."""
from __future__ import annotations

import os

from pyglet import app
from pyglet.app.base import EventLoop, PlatformEventLoop, WindowDrawSource
from pyglet.libs.darwin import get_display_link_dt
from pyglet.libs.darwin.cocoapy import (
    CAFrameRateRange,
    NSRunLoopCommonModes,
    ObjCClass,
    ObjCInstance,
    PyObjectEncoding,
    get_selector,
    objc_method,
    send_super,
)

_XCTEST_ENVIRONMENT = (
    "XCTestBundlePath",
    "XCTestConfigurationFilePath",
    "XCTestSessionIdentifier",
)

def _is_xctest() -> bool:
    return any(name in os.environ for name in _XCTEST_ENVIRONMENT)

NSObject = ObjCClass('NSObject')
NSRunLoop = ObjCClass('NSRunLoop')
CADisplayLink = ObjCClass('CADisplayLink')


class _PygletIOSDisplayLinkTarget(NSObject):

    @objc_method(b'@' + PyObjectEncoding)
    def initWithDrawSource_(self, draw_source: IOSDisplayLinkDrawSource) -> ObjCInstance | None:
        self = ObjCInstance(send_super(self, 'init'))
        if not self:
            return None
        self._draw_source = draw_source
        return self

    @objc_method('v@')
    def displayLinkFired_(self, display_link: ObjCInstance) -> None:
        self._draw_source.tick(display_link)


class IOSDisplayLinkDrawSource(WindowDrawSource):
    """One UIKit display link that paces all pyglet window drawing."""

    def __init__(self, event_loop: IOSEventLoop) -> None:
        self._event_loop = event_loop
        self._display_link = None
        self._target = None
        self._last_timestamp: float | None = None

    def start(self, interval: float) -> bool:
        if self._display_link is not None:
            return True

        self._target = _PygletIOSDisplayLinkTarget.alloc().initWithDrawSource_(self)
        display_link = CADisplayLink.displayLinkWithTarget_selector_(
            self._target,
            get_selector('displayLinkFired:'),
        )
        if display_link is None:
            self._target.release()
            self._target = None
            return False

        if interval:
            frame_rate = 1 / interval
            if CADisplayLink.instancesRespondToSelector_(get_selector('setPreferredFrameRateRange:')):
                display_link.setPreferredFrameRateRange_(
                    CAFrameRateRange(frame_rate, frame_rate, frame_rate),
                )
            else:
                display_link.setPreferredFramesPerSecond_(round(frame_rate))

        self._display_link = display_link
        self._last_timestamp = None
        display_link.addToRunLoop_forMode_(NSRunLoop.mainRunLoop(), NSRunLoopCommonModes)
        return True

    def stop(self) -> None:
        if self._display_link is not None:
            self._display_link.invalidate()
            self._display_link = None
        if self._target is not None:
            self._target.release()
            self._target = None
        self._last_timestamp = None

    def tick(self, display_link: ObjCInstance) -> None:
        if self._display_link is None or not self._event_loop.is_running:
            return
        self._last_timestamp, dt = get_display_link_dt(display_link, self._last_timestamp)
        self._event_loop._tick_app(dt)  # noqa: SLF001

class IOSPlatformEventLoop(PlatformEventLoop):
    """Schedules pyglet work from UIKit's already-running main run loop."""

    def __init__(self) -> None:
        super().__init__()

    def notify(self) -> None:
        return None

    def start(self) -> None:
        self._is_running.set()

    def step(self, timeout: float | None = None) -> None:
        self.dispatch_posted_events()

    def stop(self) -> None:
        self._is_running.clear()

    def create_window_draw_source(self, event_loop: EventLoop) -> WindowDrawSource:
        return IOSDisplayLinkDrawSource(event_loop)


class IOSEventLoop(EventLoop):
    """Event loop similar to what we did for alt macos loop.."""

    def run(self, interval: float | None = 1 / 60) -> None:
        # Check for XCode environment as it owns the app lifetime and finalizes its embedded
        # interpreter after the test returns.  It must not receive native
        # callbacks from a pyglet timer after that point.
        if _is_xctest():
            # Tick app once during test to ensure at least one draw.
            self._tick_app()
            self.has_exit = True
            return

        self.has_exit = False
        from pyglet.window import Window  # noqa: PLC0415
        Window._enable_event_queue = False # noqa: SLF001
        for window in app.windows:
            window.dispatch_pending_events()

        self._interval = interval
        self.dispatch_event('on_enter')
        self.is_running = True
        app.platform_event_loop.start()
        self._schedule_display_link(interval)

    def _schedule_display_link(self, interval: float | None) -> None:
        self._window_draw_source = app.platform_event_loop.create_window_draw_source(self)
        if not self._window_draw_source.start(1 / 60 if interval is None else interval):
            raise RuntimeError("Unable to create the iOS CADisplayLink.")

    def _tick_app(self, draw_dt: float | None = None) -> None:
        app.platform_event_loop.dispatch_posted_events()
        clock_dt = self.clock.update_time()
        self.clock.call_scheduled_functions(clock_dt)
        if self._interval is not None:
            for window in app.windows:
                self._dispatch_platform_draw(window, clock_dt if draw_dt is None else draw_dt)

    def exit(self) -> None:
        if not self.is_running:
            return
        self.has_exit = True
        self.is_running = False
        self._unschedule_window_draw()
        app.platform_event_loop.stop()
        self.dispatch_event('on_exit')
