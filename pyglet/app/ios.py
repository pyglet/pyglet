"""UIKit run-loop integration for pyglet on iOS."""
from __future__ import annotations

import os
import sys

from pyglet import app
from pyglet.app.base import EventLoop, PlatformEventLoop
from pyglet.libs.darwin.cocoapy import (
    ObjCClass,
    ObjCInstance,
    ObjCSubclass,
    PyObjectEncoding,
    get_selector,
    send_super,
)

_XCTEST_ENVIRONMENT = (
    "XCTestBundlePath",
    "XCTestConfigurationFilePath",
    "XCTestSessionIdentifier",
)

def _is_xctest() -> bool:
    return any(name in os.environ for name in _XCTEST_ENVIRONMENT)

NSTimer = ObjCClass('NSTimer')


class _IOSRunLoopTargetImplementation:
    Target = ObjCSubclass('NSObject', 'PygletIOSRunLoopTarget')

    @Target.method(b'@' + PyObjectEncoding)
    def initWithEventLoop_(self, event_loop: 'IOSEventLoop') -> ObjCInstance | None:
        self = ObjCInstance(send_super(self, 'init'))
        if not self:
            return None
        self._event_loop = event_loop
        return self

    # ``NSTimer`` invokes ``tick:`` with the timer as its explicit argument.
    # ObjCSubclass.method adds the hidden ``self`` and ``_cmd`` parameters,
    # therefore the method encoding must still include the final ``@``.  If it
    # is omitted, Objective-C calls a ctypes closure with an incompatible ABI
    # on arm64 and the process eventually faults in ``ffi_closure_SYSV``.
    @Target.method('v@')
    def tick_(self, _timer: ObjCInstance) -> None:
        if not getattr(self, '_did_tick', False):
            self._did_tick = True
        self._event_loop._tick()

_IOSRunLoopTarget = ObjCClass('PygletIOSRunLoopTarget')


class IOSPlatformEventLoop(PlatformEventLoop):
    """Schedules pyglet work from UIKit's already-running main run loop."""

    def __init__(self) -> None:
        super().__init__()
        self._timer = None
        self._target = None

    def notify(self) -> None:
        # The timer polls posted events on the next UIKit run-loop turn.
        return None

    def start(self, event_loop: IOSEventLoop, interval: float | None = 1 / 60) -> None:
        if self._timer is not None:
            return
        self._target = _IOSRunLoopTarget.alloc().initWithEventLoop_(event_loop)
        self._timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            1 / 60 if interval is None else interval,
            self._target,
            get_selector('tick:'),
            None,
            True,
        )

    def step(self, timeout: float | None = None) -> None:
        self.dispatch_posted_events()

    def stop(self) -> None:
        if self._timer is not None:
            self._timer.invalidate()
            self._timer = None
        if self._target is not None:
            self._target.release()
            self._target = None


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

        Window._enable_event_queue = False
        for window in app.windows:
            window.dispatch_pending_events()

        self._interval = interval
        self.dispatch_event('on_enter')
        self.is_running = True
        app.platform_event_loop.start(self, interval)

    def _tick(self) -> None:
        if not self.is_running or self.has_exit:
            return
        self._tick_app()

    def _tick_app(self):
        app.platform_event_loop.dispatch_posted_events()
        dt = self.clock.update_time()
        self.clock.call_scheduled_functions(dt)
        if self._interval is not None:
            for window in app.windows:
                window.draw(dt)

    def exit(self) -> None:
        if not self.is_running:
            return
        self.has_exit = True
        self.is_running = False
        app.platform_event_loop.stop()
        self.dispatch_event('on_exit')
