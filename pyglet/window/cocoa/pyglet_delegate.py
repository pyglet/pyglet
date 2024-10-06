from __future__ import annotations

from ctypes import c_void_p
from typing import TYPE_CHECKING

import pyglet
from pyglet.libs.darwin.cocoapy import (
    NSApplicationDidHideNotification,
    NSApplicationDidUnhideNotification,
    NSMakeRect,
    ObjCClass,
    ObjCInstance,
    ObjCSubclass,
    PyObjectEncoding,
    appkit,
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

NSBackingPropertyOldScaleFactorKey = c_void_p.in_dll(appkit, 'NSBackingPropertyOldScaleFactorKey')


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

    @PygletDelegate.method('v@')
    def windowDidChangeBackingProperties_(self, notification):
        if not self._window._shadow:
            user_info = notification.userInfo()
            old_scale_value = user_info.objectForKey_(NSBackingPropertyOldScaleFactorKey)

            old_scale = old_scale_value.doubleValue()
            new_scale = self._window._nswindow.backingScaleFactor()
            if old_scale != new_scale:
                self._window.switch_to()

                currentFrame = self._window._nswindow.frame()

                if pyglet.options.dpi_scaling == "real":
                    screen_scale = new_scale
                    w, h = self._window.get_requested_size()
                    width, height = int(w / screen_scale), int(h / screen_scale)

                    # Force Window back to correct size.
                    self._window._set_frame_size(width, height)
                else:
                    # MacOS seems to cache the state of the window size, even between different DPI scales/monitors.
                    # This means that the screen will refuse to refresh until we resize the window to a different size.
                    # Force a refresh by setting a temporary frame, then forcing it back.
                    if pyglet.options.dpi_scaling == "scaled":
                        tempRect = NSMakeRect(currentFrame.origin.x, currentFrame.origin.y,
                                              currentFrame.size.width + 1, currentFrame.size.height + 1)
                        # TODO: Add variable to ignore the next two on-resize events?
                        self._window._nswindow.setFrame_display_(tempRect, True)
                        self._window._nswindow.setFrame_display_(currentFrame, True)

                self._window.context.update_geometry()
                self._window.dispatch_event("_on_internal_scale", new_scale, self._window._get_dpi_desc())



PygletDelegate = ObjCClass('PygletDelegate')
