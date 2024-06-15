from __future__ import annotations

from typing import TYPE_CHECKING

from pyglet.libs.darwin.cocoapy import (
    NSApplicationDidHideNotification,
    NSApplicationDidUnhideNotification,
    ObjCClass,
    ObjCInstance,
    ObjCSubclass,
    PyObjectEncoding,
    get_selector,
    quartz,
    send_super,
)

from .systemcursor import SystemCursor

if TYPE_CHECKING:
    from . import CocoaWindow

NSNotificationCenter = ObjCClass('NSNotificationCenter')
NSApplication = ObjCClass('NSApplication')
NSNotification = ObjCClass('NSNotification')


class PygletDelegate_Implementation:
    PygletDelegate = ObjCSubclass('NSObject', 'PygletDelegate')

    @PygletDelegate.method(b'@' + PyObjectEncoding)
    def initWithWindow_(self, window: CocoaWindow) -> ObjCInstance | None:
        self = ObjCInstance(send_super(self, 'init'))

        if not self:
            return None

        # CocoaWindow object.
        self._window = window
        window._nswindow.setDelegate_(self)  # noqa: SLF001

        # Register delegate for hide and unhide notifications so that we
        # can dispatch the corresponding pyglet events.
        notificationCenter = NSNotificationCenter.defaultCenter()

        notificationCenter.addObserver_selector_name_object_(
            self, get_selector('applicationDidHide:'),
            NSApplicationDidHideNotification, None)

        notificationCenter.addObserver_selector_name_object_(
            self, get_selector('applicationDidUnhide:'),
            NSApplicationDidUnhideNotification, None)

        # Flag set when we pause exclusive mouse mode if window loses key status.
        self.did_pause_exclusive_mouse = False
        return self

    @PygletDelegate.method('v')
    def dealloc(self) -> None:
        # Unregister delegate from notification center.
        notificationCenter = NSNotificationCenter.defaultCenter()
        notificationCenter.removeObserver_(self)
        self._window = None
        send_super(self, 'dealloc')

    @PygletDelegate.method('v@')
    def applicationDidHide_(self, notification: NSNotification) -> None:
        self._window.dispatch_event('on_hide')

    @PygletDelegate.method('v@')
    def applicationDidUnhide_(self, notification: NSNotification) -> None:
        if self._window._mouse_exclusive and quartz.CGCursorIsVisible():
            # The cursor should be hidden, but for some reason it's not;
            # try to force the cursor to hide (without over-hiding).
            SystemCursor.unhide()
            SystemCursor.hide()
        self._window.dispatch_event('on_show')

    @PygletDelegate.method('B@')
    def windowShouldClose_(self, sender: ObjCInstance) -> bool:
        # The method is not called if [NSWindow close] was used.
        self._window.dispatch_event('on_close')
        return False

    @PygletDelegate.method('v@')
    def windowDidMove_(self, notification: NSNotification) -> None:
        x, y = self._window.get_location()
        self._window.dispatch_event('on_move', x, y)

    @PygletDelegate.method('v@')
    def windowDidBecomeKey_(self, notification: NSNotification) -> None:
        # Restore exclusive mouse mode if it was active before we lost key status.
        if self.did_pause_exclusive_mouse:
            self._window.set_exclusive_mouse(True)
            self.did_pause_exclusive_mouse = False
            self._window._nswindow.setMovable_(True)  # Mac OS 10.6  # noqa: SLF001
        # Restore previous mouse visibility settings.
        self._window.set_mouse_platform_visible()
        self._window.dispatch_event('on_activate')

    @PygletDelegate.method('v@')
    def windowDidResignKey_(self, notification: NSNotification) -> None:
        # Pause exclusive mouse mode if it is active.
        if self._window._mouse_exclusive:  # noqa: SLF001
            self._window.set_exclusive_mouse(False)
            self.did_pause_exclusive_mouse = True
            # We need to prevent the window from being unintentionally dragged
            # (by the call to set_mouse_position in set_exclusive_mouse) when
            # the window is reactivated by clicking on its title bar.
            self._window._nswindow.setMovable_(False)  # Mac OS X 10.6  # noqa: SLF001
        # Make sure that cursor is visible.
        self._window.set_mouse_platform_visible(True)
        self._window.dispatch_event('on_deactivate')

    @PygletDelegate.method('v@')
    def windowDidMiniaturize_(self, notification: NSNotification) -> None:
        self._window.dispatch_event('on_hide')

    @PygletDelegate.method('v@')
    def windowDidDeminiaturize_(self, notification: NSNotification) -> None:
        if self._window._mouse_exclusive and quartz.CGCursorIsVisible():  # noqa: SLF001
            # The cursor should be hidden, but for some reason it's not;
            # try to force the cursor to hide (without over-hiding).
            SystemCursor.unhide()
            SystemCursor.hide()
        self._window.dispatch_event('on_show')

    @PygletDelegate.method('v@')
    def windowDidExpose_(self, notification: NSNotification) -> None:
        self._window.dispatch_event('on_expose')

    @PygletDelegate.method('v@')
    def terminate_(self, sender: ObjCInstance) -> None:
        NSApp = NSApplication.sharedApplication()
        NSApp.terminate_(self)

    @PygletDelegate.method('B@')
    def validateMenuItem_(self, menuitem: ObjCInstance) -> bool:
        # Disable quitting with command-q when in keyboard exclusive mode.
        if menuitem.action() == get_selector('terminate:'):
            return not self._window._keyboard_exclusive  # noqa: SLF001
        return True


PygletDelegate = ObjCClass('PygletDelegate')
