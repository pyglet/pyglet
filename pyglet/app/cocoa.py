import signal
import time

from pyglet import app
from pyglet.app.base import PlatformEventLoop, EventLoop
from pyglet.libs.darwin import cocoapy, AutoReleasePool, ObjCSubclass, PyObjectEncoding, ObjCInstance, send_super, \
    ObjCClass, get_selector

NSApplication = cocoapy.ObjCClass('NSApplication')
NSMenu = cocoapy.ObjCClass('NSMenu')
NSMenuItem = cocoapy.ObjCClass('NSMenuItem')
NSDate = cocoapy.ObjCClass('NSDate')
NSEvent = cocoapy.ObjCClass('NSEvent')
NSUserDefaults = cocoapy.ObjCClass('NSUserDefaults')
NSTimer = cocoapy.ObjCClass('NSTimer')
NSRunningApplication = cocoapy.ObjCClass('NSRunningApplication')


def add_menu_item(menu, title, action, key):
    with AutoReleasePool():
        title = cocoapy.CFSTR(title)
        action = cocoapy.get_selector(action)
        key = cocoapy.CFSTR(key)
        menuItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            title, action, key)
        menu.addItem_(menuItem)

        # cleanup
        menuItem.release()


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
    def init(self, pyglet_loop):
        objc = ObjCInstance(send_super(self, 'init'))
        self._pyglet_loop = pyglet_loop
        return objc  # objc is self

    @_AppDelegate.method('v')
    def updatePyglet_(self):
        self._pyglet_loop.nsapp_step()

    @_AppDelegate.method('v@')
    def applicationWillTerminate_(self, notification):
        self._pyglet_loop.is_running = False
        self._pyglet_loop.has_exit = True

    @_AppDelegate.method('v@')
    def applicationDidFinishLaunching_(self, notification):
        self._pyglet_loop._finished_launching = True

        # Force App to activate to the foreground due to being an unbundled CLI program.
        # This prevents an issue where if you move the mouse when launching the program, it's focus can be stolen
        # by an app under/behind it leading to a weird state of input and the menu bar being greyed out until
        # reactivating it.
        NSApp = NSApplication.sharedApplication()

        # Activate dock to ensure all other apps are deactivated.
        dock_str = cocoapy.get_NSString("com.apple.dock")
        running_apps = NSRunningApplication.runningApplicationsWithBundleIdentifier_(dock_str)
        app_count = running_apps.count()
        for i in range(app_count):
            running_app = running_apps.objectAtIndex_(i)
            running_app.activateWithOptions_(cocoapy.NSApplicationActivateIgnoringOtherApps)
            break

        # Doesn't seem to work unless we add a small sleep for some reason...
        time.sleep(0.01)

        NSApp.activateIgnoringOtherApps_(True)

    @_AppDelegate.method('v@')
    def applicationWillFinishLaunching_(self, notification):
        pass

    @_AppDelegate.method('B')
    def applicationSupportsSecureRestorableState_(self):
        return True

_AppDelegate = ObjCClass('_AppDelegate')  # the actual class

class CocoaAlternateEventLoop(EventLoop):
    """This is an alternate loop developed mainly for ARM64 variants of macOS.
    nextEventMatchingMask_untilDate_inMode_dequeue_ is very broken with ctypes calls. Events eventually stop
    working properly after X returns. This event loop differs in that it uses the built-in NSApplication event
    loop. We tie our schedule into it via timer.
    """
    def __init__(self):
        super().__init__()
        self.platform_event_loop = None

    def run(self, interval=1/60):
        if not interval:
            self.clock.schedule(self._redraw_windows)
        else:
            self.clock.schedule_interval(self._redraw_windows, interval)

        self.has_exit = False

        from pyglet.window import Window
        Window._enable_event_queue = False

        # Dispatch pending events
        for window in app.windows:
            window.switch_to()
            window.dispatch_pending_events()

        self.platform_event_loop = app.platform_event_loop

        self.dispatch_event('on_enter')
        self.is_running = True
        self.platform_event_loop.nsapp_start(interval)

    def exit(self):
        """Safely exit the event loop at the end of the current iteration.

        This method is a thread-safe equivalent for setting
        :py:attr:`has_exit` to ``True``.  All waiting threads will be
        interrupted (see :py:meth:`sleep`).
        """
        self.has_exit = True
        if self.platform_event_loop is not None:
            self.platform_event_loop.notify()

        self.is_running = False
        self.dispatch_event('on_exit')

        if self.platform_event_loop is not None:
            self.platform_event_loop.nsapp_stop()

class CocoaPlatformEventLoop(PlatformEventLoop):

    def __init__(self):
        super().__init__()
        self._timer = None

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
            ignoreState = cocoapy.CFSTR("ApplePersistenceIgnoreState")
            if not defaults.objectForKey_(ignoreState):
                defaults.setBool_forKey_(True, ignoreState)

            holdEnabled = cocoapy.CFSTR("ApplePressAndHoldEnabled")
            if not defaults.objectForKey_(holdEnabled):
                defaults.setBool_forKey_(False, holdEnabled)

            self.appdelegate = _AppDelegate.alloc().init(self)
            self.NSApp.setDelegate_(self.appdelegate)

            self._finished_launching = False

        def term_received(*args):
            if self._timer:
                self._timer.invalidate()
                self._timer = None

            if self.NSApp:
                self.NSApp.terminate_(None)

        # Force NSApp to close if Python receives sig events.
        signal.signal(signal.SIGINT, term_received)
        signal.signal(signal.SIGTERM, term_received)

    def start(self):
        with AutoReleasePool():
            if not self.NSApp.isRunning() and not self._finished_launching:
                # finishLaunching should be called only once. However isRunning will not
                # guard this, as we are not using the normal event loop.
                self.NSApp.finishLaunching()
                self.NSApp.activateIgnoringOtherApps_(True)
                self._finished_launching = True

    def nsapp_start(self, interval):
        """Used only for CocoaAlternateEventLoop"""
        from pyglet.app import event_loop
        self._event_loop = event_loop

        assert self._timer is None

        self._timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            interval,  # Clamped internally to 0.0001 (including 0)
            self.appdelegate,
            get_selector('updatePyglet:'),
            False,
            True
        )

        self.NSApp.run()

    def nsapp_step(self):
        """Used only for CocoaAlternateEventLoop"""
        self._event_loop.idle()
        with AutoReleasePool():
            self.dispatch_posted_events()

    def nsapp_stop(self):
        """Used only for CocoaAlternateEventLoop"""
        self.NSApp.stop_(None)

        if self._timer:
            self._timer.invalidate()
            self._timer = None

    def step(self, timeout=None):
        with AutoReleasePool():
            self.dispatch_posted_events()

            # Determine the timeout date.
            if timeout is None:
                # Using distantFuture as untilDate means that nextEventMatchingMask
                # will wait until the next event comes along.
                timeout_date = NSDate.distantFuture()
            elif timeout == 0.0:
                timeout_date = None
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
