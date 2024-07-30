from __future__ import annotations

import signal

from threading import Thread

from pyglet.app.base import PlatformEventLoop, EventLoop
from pyglet.libs.darwin import cocoapy, AutoReleasePool, PyObjectEncoding, send_super
from pyglet.libs.darwin import ObjCClass, ObjCSubclass, ObjCInstance, get_selector

NSApplication = cocoapy.ObjCClass('NSApplication')
NSMenu = cocoapy.ObjCClass('NSMenu')
NSMenuItem = cocoapy.ObjCClass('NSMenuItem')
NSDate = cocoapy.ObjCClass('NSDate')
NSEvent = cocoapy.ObjCClass('NSEvent')
NSUserDefaults = cocoapy.ObjCClass('NSUserDefaults')
NSTimer = cocoapy.ObjCClass('NSTimer')


def add_menu_item(menu, title, action, key):
    with AutoReleasePool():
        title = cocoapy.CFSTR(title)
        action = cocoapy.get_selector(action)
        key = cocoapy.CFSTR(key)
        menu_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, action, key)
        menu.addItem_(menu_item)

        # cleanup
        menu_item.release()


def create_menu():
    with AutoReleasePool():
        appMenu = NSMenu.alloc().init()

        # Hide still doesn't work!?
        add_menu_item(appMenu, 'Hide!', 'hide:', 'h')
        appMenu.addItem_(NSMenuItem.separatorItem())
        add_menu_item(appMenu, 'Quit!', 'terminate:', 'q')

        menubar = NSMenu.alloc().init()
        appMenuItem = NSMenuItem.alloc().init()
        appMenuItem.setSubmenu_(appMenu)
        menubar.addItem_(appMenuItem)
        NSApp = NSApplication.sharedApplication()
        NSApp.setMainMenu_(menubar)

        # cleanup
        appMenu.release()
        menubar.release()
        appMenuItem.release()


class _AppDelegate_Implementation:

    _AppDelegate = ObjCSubclass('NSObject', '_AppDelegate')

    @_AppDelegate.method(b'@' + PyObjectEncoding)
    def init(self, pyglet_platform_loop):
        objc = ObjCInstance(send_super(self, 'init'))
        self._pyglet_platform_loop = pyglet_platform_loop
        return objc  # objc is self

    @_AppDelegate.method('v')
    def updatePyglet_(self):
        self._pyglet_platform_loop.step()

    @_AppDelegate.method('v@')
    def applicationWillTerminate_(self, notification):
        self._pyglet_platform_loop.is_running = False
        self._pyglet_platform_loop.has_exit = True

    @_AppDelegate.method('v@')
    def applicationDidFinishLaunching_(self, notification):
        self._pyglet_platform_loop._finished_launching = True


_AppDelegate = ObjCClass('_AppDelegate')  # the actual class


# class CocoaAlternateEventLoop(EventLoop):
#     """This is an alternate loop developed mainly for ARM64 variants of macOS.
#     nextEventMatchingMask_untilDate_inMode_dequeue_ is very broken with ctypes calls. Events eventually stop
#     working properly after X returns. This event loop differs in that it uses the built-in NSApplication event
#     loop. We tie our schedule into it via timer.
#     """
#     def __init__(self):
#         super().__init__()
#         self.platform_event_loop = None
#
#     def run(self, interval=1/60):
#         if not interval:
#             self.clock.schedule(self._redraw_windows)
#         else:
#             self.clock.schedule_interval(self._redraw_windows, interval)
#
#         self.has_exit = False
#
#         from pyglet.window import Window
#         Window._enable_event_queue = False
#
#         # Dispatch pending events
#         for window in pyglet.app.windows:
#             window.switch_to()
#             window.dispatch_pending_events()
#
#         self.platform_event_loop = pyglet.app.platform_event_loop
#
#         self.dispatch_event('on_enter')
#         self.is_running = True
#         self.platform_event_loop.nsapp_start(interval)
#
#     def exit(self):
#         """Safely exit the event loop at the end of the current iteration.
#
#         This method is a thread-safe equivalent for setting
#         :py:attr:`has_exit` to ``True``.  All waiting threads will be
#         interrupted (see :py:meth:`sleep`).
#         """
#         self.has_exit = True
#         if self.platform_event_loop is not None:
#             self.platform_event_loop.notify()
#
#         self.is_running = False
#         self.dispatch_event('on_exit')
#
#         if self.platform_event_loop is not None:
#             self.platform_event_loop.nsapp_stop()


class CocoaPlatformEventLoop(PlatformEventLoop):

    def __init__(self):
        super().__init__()
        with AutoReleasePool():
            # Prepare the default application.
            self.NSApp = NSApplication.sharedApplication()
            if self.NSApp.isRunning():
                # Application was already started by GUI library (e.g. wxPython).
                return
            if not self.NSApp.mainMenu():
                create_menu()
            self.NSApp.setActivationPolicy_(cocoapy.NSApplicationActivationPolicyRegular)
            # Prevent Lion / Mountain Lion from automatically saving application state.
            # If we don't do this, new windows will not display on 10.8 after finishLaunching
            # has been called.
            defaults = NSUserDefaults.standardUserDefaults()
            ignore_state = cocoapy.CFSTR("ApplePersistenceIgnoreState")
            if not defaults.objectForKey_(ignore_state):
                defaults.setBool_forKey_(True, ignore_state)

            hold_enabled = cocoapy.CFSTR("ApplePressAndHoldEnabled")
            if not defaults.objectForKey_(hold_enabled):
                defaults.setBool_forKey_(False, hold_enabled)

            self._finished_launching = False

    def start(self):
        with AutoReleasePool():
            if not self.NSApp.isRunning() and not self._finished_launching:
                # finishLaunching should be called only once. However isRunning will not
                # guard this, as we are not using the normal event loop.
                self.NSApp.finishLaunching()
                self.NSApp.activateIgnoringOtherApps_(True)
                self._finished_launching = True

    def step(self, timeout=None):
        with AutoReleasePool():
            self.dispatch_posted_events()

            # Determine the timeout date.
            if timeout is None:
                # Using distantFuture as untilDate means that nextEventMatchingMask
                # will wait until the next event comes along.
                timeout_date = NSDate.distantFuture()
            elif timeout == 0.0:
                timeout_date = NSDate.distantPast()
            else:
                timeout_date = NSDate.dateWithTimeIntervalSinceNow_(timeout)

            # Retrieve the next event (if any).  We wait for an event to show up
            # and then process it, or if timeout_date expires we simply return.
            # We only process one event per call of step().
            self._is_running.set()
            event = self.NSApp.nextEventMatchingMask_untilDate_inMode_dequeue_(
                cocoapy.NSAnyEventMask, timeout_date, cocoapy.NSDefaultRunLoopMode, True)

            # Dispatch the event (if any).
            if event is not None:
                event_type = event.type()
                if event_type != cocoapy.NSApplicationDefined:
                    self.NSApp.sendEvent_(event)

                self.NSApp.updateWindows()
                did_time_out = False
            else:
                did_time_out = True

            self._is_running.clear()

            return did_time_out

    def stop(self):
        pass

    def notify(self):
        with AutoReleasePool():
            notifyEvent = NSEvent.otherEventWithType_location_modifierFlags_timestamp_windowNumber_context_subtype_data1_data2_(
                cocoapy.NSApplicationDefined, # type
                cocoapy.NSPoint(0.0, 0.0),    # location
                0,                            # modifierFlags
                0,                            # timestamp
                0,                            # windowNumber
                None,                         # graphicsContext
                0,                            # subtype
                0,                            # data1
                0,                            # data2
                )

            self.NSApp.postEvent_atStart_(notifyEvent, False)


class ArmPlatformEventLoop(PlatformEventLoop):

    _event_loop: EventLoop
    appdelegate: _AppDelegate
    timer: NSTimer

    def __init__(self, interval=1/60):
        super().__init__()
        with AutoReleasePool():
            # Prepare the default application.
            self.NSApp = NSApplication.sharedApplication()
            if self.NSApp.isRunning():
                # Application was already started by GUI library (e.g. wxPython).
                return
            if not self.NSApp.mainMenu():
                create_menu()
            self.NSApp.setActivationPolicy_(cocoapy.NSApplicationActivationPolicyRegular)
            # Prevent Lion / Mountain Lion from automatically saving application state.
            # If we don't do this, new windows will not display on 10.8 after finishLaunching
            # has been called.
            defaults = NSUserDefaults.standardUserDefaults()
            ignore_state = cocoapy.CFSTR("ApplePersistenceIgnoreState")
            if not defaults.objectForKey_(ignore_state):
                defaults.setBool_forKey_(True, ignore_state)

            hold_enabled = cocoapy.CFSTR("ApplePressAndHoldEnabled")
            if not defaults.objectForKey_(hold_enabled):
                defaults.setBool_forKey_(False, hold_enabled)

            self._finished_launching = False

        self._interval = interval
        self._timer_thread = None

    def start(self):
        self._timer_thread = Thread(target=self._start_timer, daemon=True)
        self._timer_thread.start()

    def _start_timer(self):
        from pyglet.app import event_loop
        self._event_loop = event_loop

        def _sigterm_received(*args):
            if self.timer:
                self.timer.invalidate()
                self.timer = None
            self.stop()

        # Force NSApp to close if Python receives sig events.
        signal.signal(signal.SIGINT, _sigterm_received)
        signal.signal(signal.SIGTERM, _sigterm_received)

        self.appdelegate = _AppDelegate.alloc().init(self)
        self.NSApp.setDelegate_(self.appdelegate)

        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
             self._interval,  # Clamped internally to 0.0001 (including 0)
             self.appdelegate,
             get_selector('updatePyglet:'),
             False,
             True
        )

        self.NSApp.run()

    def step(self, timeout: float | None = None) -> None:
        """Used only for CocoaAlternateEventLoop"""
        self.dispatch_posted_events()

    def stop(self):
        """Used only for CocoaAlternateEventLoop"""
        self.NSApp.terminate_(None)

    def notify(self):
        with (AutoReleasePool()):
            notify_event = \
                NSEvent.otherEventWithType_location_modifierFlags_timestamp_windowNumber_context_subtype_data1_data2_(
                    cocoapy.NSApplicationDefined,  # type
                    cocoapy.NSPoint(0.0, 0.0),     # location
                    0,                             # modifierFlags
                    0,                             # timestamp
                    0,                             # windowNumber
                    None,                          # graphicsContext
                    0,                             # subtype
                    0,                             # data1
                    0,                             # data2
                    )

            self.NSApp.postEvent_atStart_(notify_event, False)
