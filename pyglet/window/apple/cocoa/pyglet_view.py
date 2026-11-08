from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pyglet
from pyglet.libs.darwin.cocoapy.cocoatypes import NSMakeRect, NSRect, NSRectEncoding, NSSize, NSSizeEncoding, PyObjectEncoding
from pyglet.libs.darwin.cocoapy.lib_appkit import (
    NSAlphaShiftKeyMask,
    NSAlternateKeyMask,
    NSCommandKeyMask,
    NSControlKeyMask,
    NSDragOperationGeneric,
    NSFunctionKeyMask,
    NSLeftAlternateKeyMask,
    NSLeftCommandKeyMask,
    NSLeftControlKeyMask,
    NSLeftShiftKeyMask,
    NSPasteboardURLReadingFileURLsOnlyKey,
    NSRightAlternateKeyMask,
    NSRightCommandKeyMask,
    NSRightControlKeyMask,
    NSRightShiftKeyMask,
    NSShiftKeyMask,
    NSTrackingActiveInActiveApp,
    NSTrackingCursorUpdate,
    NSTrackingInVisibleRect,
    NSTrackingMouseEnteredAndExited,
)
from pyglet.libs.darwin.cocoapy.lib_corefoundation import cfstring_to_string
from pyglet.libs.darwin.cocoapy.runtime import ObjCClass, ObjCInstance, objc_method, send_super
from pyglet.libs.darwin.quartzkey import charmap, keymap
from pyglet.window import key, mouse
from pyglet.window.pen import PenButton, PenEvent

from .pyglet_textview import PygletTextView

if TYPE_CHECKING:
    import ctypes
    from . import CocoaWindow

NSTrackingArea = ObjCClass('NSTrackingArea')
NSView = ObjCClass('NSView')
NSURL = ObjCClass('NSURL')
NSArray = ObjCClass('NSArray')
NSDictionary = ObjCClass('NSDictionary')
NSNumber = ObjCClass('NSNumber')
NSNotificationCenter = ObjCClass('NSNotificationCenter')

# Key to mask mapping.
maskForKey: dict[int, int] = {
    key.LSHIFT: NSLeftShiftKeyMask,
    key.RSHIFT: NSRightShiftKeyMask,
    key.LCTRL: NSLeftControlKeyMask,
    key.RCTRL: NSRightControlKeyMask,
    key.LOPTION: NSLeftAlternateKeyMask,
    key.ROPTION: NSRightAlternateKeyMask,
    key.LCOMMAND: NSLeftCommandKeyMask,
    key.RCOMMAND: NSRightCommandKeyMask,
    key.CAPSLOCK: NSAlphaShiftKeyMask,
    key.FUNCTION: NSFunctionKeyMask,
}


# Event data helper functions.


_mouseViewRect = NSMakeRect(0, 0, 0, 0)

def getMouseDelta(nsevent: ObjCInstance) -> tuple[int, int]:
    dx = nsevent.deltaX()
    dy = -nsevent.deltaY()
    return dx, dy


def getMousePosition(self: ObjCInstance, nsevent: ObjCInstance) \
        -> tuple[int, int]:
    in_window = nsevent.locationInWindow()
    in_window = self.convertPoint_fromView_(in_window, None)
    if pyglet.options.dpi_scaling != "stretch":
        _mouseViewRect.origin.x = in_window.x
        _mouseViewRect.origin.y = in_window.y
        converted = self.convertRectToBacking_(_mouseViewRect)
        in_window = converted.origin
    x = int(in_window.x)
    y = int(in_window.y)
    # Must record mouse position for BaseWindow.draw_mouse_cursor to work.
    self._window._mouse_x = x
    self._window._mouse_y = y
    return x, y


def getTouchPosition(self: ObjCInstance, touch: ObjCInstance) -> tuple[int, int]:
    """Convert an NSTouch normalized position to pyglet window coordinates."""
    position = touch.normalizedPosition()
    bounds = self.bounds()
    _mouseViewRect.origin.x = position.x * bounds.size.width
    _mouseViewRect.origin.y = position.y * bounds.size.height
    if pyglet.options.dpi_scaling != "stretch":
        converted = self.convertRectToBacking_(_mouseViewRect)
        return int(converted.origin.x), int(converted.origin.y)
    return int(_mouseViewRect.origin.x), int(_mouseViewRect.origin.y)


def getModifiers(nsevent: ObjCInstance) -> int:
    modifiers = 0
    modifierFlags = nsevent.modifierFlags()
    if modifierFlags & NSAlphaShiftKeyMask:
        modifiers |= key.MOD_CAPSLOCK
    if modifierFlags & NSShiftKeyMask:
        modifiers |= key.MOD_SHIFT
    if modifierFlags & NSControlKeyMask:
        modifiers |= key.MOD_CTRL
    if modifierFlags & NSAlternateKeyMask:
        modifiers |= key.MOD_ALT
        modifiers |= key.MOD_OPTION
    if modifierFlags & NSCommandKeyMask:
        modifiers |= key.MOD_COMMAND
    if modifierFlags & NSFunctionKeyMask:
        modifiers |= key.MOD_FUNCTION
    return modifiers


def getSymbol(nsevent: ObjCInstance) -> int | None:
    symbol = keymap.get(nsevent.keyCode(), None)
    if symbol is not None:
        return symbol

    chars = cfstring_to_string(nsevent.charactersIgnoringModifiers())
    if chars:
        return charmap.get(chars[0].upper(), None)

    return None


def _get_drag_position(self: ObjCInstance,
                       dragging_info: ObjCInstance) -> tuple[int, int]:
    position = dragging_info.draggingLocation()
    position = self.convertPoint_fromView_(position, None)
    if pyglet.options.dpi_scaling != "stretch":
        _mouseViewRect.origin.x = position.x
        _mouseViewRect.origin.y = position.y
        converted = self.convertRectToBacking_(_mouseViewRect)
        position = converted.origin
    return int(position.x), int(position.y)


def _get_dragging_paths(dragging_info: ObjCInstance) -> list[str]:
    pasteboard = dragging_info.draggingPasteboard()

    classes = NSArray.arrayWithObject_(NSURL)
    options = NSDictionary.dictionaryWithObject_forKey_(
        NSNumber.numberWithBool_(True), NSPasteboardURLReadingFileURLsOnlyKey,
    )

    urls = pasteboard.readObjectsForClasses_options_(classes, options)
    if not urls:
        return []

    paths = []
    for i in range(urls.count()):
        fpath = urls.objectAtIndex_(i).fileSystemRepresentation()
        paths.append(fpath.decode())
    return paths


class PygletView(NSView):  # type: ignore[valid-type, misc]
    _window: CocoaWindow | None
    _pen_erasers: dict[int, bool]

    @objc_method(b'@' + NSRectEncoding + PyObjectEncoding)
    def initWithFrame_cocoaWindow_(self: Any, frame: NSRect, window: CocoaWindow) -> ObjCInstance | None:

        # The tracking area is used to get mouseEntered, mouseExited, and cursorUpdate
        # events so that we can custom set the mouse cursor within the view.
        # self._tracking_area = None

        self = ObjCInstance(send_super(self, 'initWithFrame:', frame, argtypes=[NSRect]))

        if not self:
            return None

        # CocoaWindow object.
        self._window = window
        self._pen_erasers = {}
        self._file_drag_active = False

        self.associate("_tracking_area", None)

        self.updateTrackingAreas()

        # Create an instance of PygletTextView to handle text events.
        # We must do this because NSOpenGLView doesn't conform to the
        # NSTextInputClient protocol by default, and the insertText: method will
        # not do the right thing with respect to translating key sequences like
        # "Option-e", "e" if the protocol isn't implemented.  So the easiest
        # thing to do is to subclass NSTextView which *does* implement the
        # protocol and let it handle text input.
        textview = PygletTextView.alloc().initWithCocoaWindow_(window)
        self.associate("_textview", textview)
        # Add text view to the responder chain.
        self.addSubview_(self._textview)
        return self

    @objc_method('v')
    def dealloc(self) -> None:
        self._window = None
        self._textview.removeFromSuperviewWithoutNeedingDisplay()
        self._textview.release()
        self._tracking_area.release()
        send_super(self, 'dealloc')

    @objc_method('v')
    def updateTrackingAreas(self) -> None:
        # This method is called automatically whenever the tracking areas need to be
        # recreated, for example when window resizes.
        if self._tracking_area:
            self.removeTrackingArea_(self._tracking_area)
            self._tracking_area.release()
            self.associate("_tracking_area", None)

        tracking_options = (NSTrackingMouseEnteredAndExited | NSTrackingActiveInActiveApp |
                            NSTrackingCursorUpdate | NSTrackingInVisibleRect)
        frame = self.frame()
        tracking_area = NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
            frame,  # rect
            tracking_options,  # options
            self,  # owner
            None)  # userInfo

        self.associate("_tracking_area", tracking_area)

        self.addTrackingArea_(self._tracking_area)
        send_super(self, 'updateTrackingAreas', superclass_name='NSView')

    @objc_method('B')
    def canBecomeKeyView(self) -> bool:
        return True

    @objc_method('B')
    def isOpaque(self) -> bool:
        return True

    @objc_method('B')
    def acceptsTouchEvents(self) -> bool:
        return True

    @objc_method('v@')
    def displayLinkFired_(self, display_link: ObjCInstance) -> None:
        if self._window is not None:
            self._window._display_link_tick(display_link)

    ## Event responders.

    # This method is called whenever the view changes size.
    @objc_method(b'v' + NSSizeEncoding)
    def setFrameSize_(self, size: NSSize) -> None:
        send_super(self, 'setFrameSize:', size,
                           superclass_name='NSView',
                           argtypes=[NSSize])

        # Installing the view as the window's contentView invokes this method,
        # but that is not a user-visible resize.
        # This also helps ensure correct window creation event ordering.
        if self._window._installing_view or self._window._shadow:  # noqa: SLF001
            return

        width, height = int(size.width), int(size.height)
        self._window.switch_to()
        self._window._update_geometry()
        self._window._width, self._window._height = width, height  # noqa: SLF001
        self._window.dispatch_event('_on_internal_resize', width, height)
        self._window.dispatch_event('on_expose')
        # Can't get app.event_loop.enter_blocking() working with Cocoa, because
        # when mouse clicks on the window's resize control, Cocoa enters into a
        # mini-event loop that only responds to mouseDragged and  mouseUp events.
        # This means that using NSTimer to call idle() won't work.  Our kludge
        # is to override NSWindow's nextEventMatchingMask_etc method and call
        # idle() from there.
        if self.inLiveResize():
            from pyglet import app
            if app.event_loop is not None:
                app.event_loop.idle()

    @objc_method('v@')
    def keyDown_(self, nsevent: ObjCInstance) -> None:
        if not nsevent.isARepeat():
            symbol = getSymbol(nsevent)
            modifiers = getModifiers(nsevent)
            self._window.dispatch_event('on_key_press', symbol, modifiers)

    @objc_method('v@')
    def keyUp_(self, nsevent: ObjCInstance) -> None:
        symbol = getSymbol(nsevent)
        modifiers = getModifiers(nsevent)
        self._window.dispatch_event('on_key_release', symbol, modifiers)

    @objc_method('v@')
    def flagsChanged_(self, nsevent: ObjCInstance) -> None:
        # Handles on_key_press and on_key_release events for modifier keys.
        # Note that capslock is handled differently than other keys; it acts
        # as a toggle, so on_key_release is only sent when it's turned off.
        symbol = keymap.get(nsevent.keyCode(), None)

        # Ignore this event if symbol is not a modifier key.  We must check this
        # because e.g., we receive a flagsChanged message when using CMD-tab to
        # switch applications, with symbol == "a" when command key is released.
        if symbol is None or symbol not in maskForKey:
            return

        modifiers = getModifiers(nsevent)
        modifierFlags = nsevent.modifierFlags()

        if symbol and modifierFlags & maskForKey[symbol]:
            self._window.dispatch_event('on_key_press', symbol, modifiers)
        else:
            self._window.dispatch_event('on_key_release', symbol, modifiers)

    @objc_method('v:')
    def doCommandBySelector_(self, selector: ctypes.c_void_p) -> None:
        """Prevent system beeps when an event or key is not handled."""

    def _dispatch_pen_mouse(self, nsevent: ObjCInstance) -> bool:
        # AppKit delivers tablet points both natively and as mouse subtypes.
        # https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/EventOverview/HandlingTabletEvents/HandlingTabletEvents.html
        if nsevent.subtype() == 1:  # NSTabletPointEventSubtype
            PygletView._dispatch_pen_point(self, nsevent)
            return True
        if nsevent.subtype() == 2:  # NSTabletProximityEventSubtype
            PygletView._dispatch_pen_proximity(self, nsevent)
            return True
        return False

    @objc_method('v@')
    def tabletProximity_(self, nsevent: ObjCInstance) -> None:
        PygletView._dispatch_pen_proximity(self, nsevent)

    def _dispatch_pen_proximity(self, nsevent: ObjCInstance) -> None:
        pointer_id = int(nsevent.deviceID())
        if nsevent.isEnteringProximity():
            eraser = nsevent.pointingDeviceType() == 3  # NSEraserPointingDevice
            self._pen_erasers[pointer_id] = eraser
            x, y = getMousePosition(self, nsevent)
            if 0 <= x < self._window.width and 0 <= y < self._window.height:
                self._window._update_pen(PenEvent(pointer_id, x, y, eraser=eraser))
        else:
            self._window._leave_pen(pointer_id)
            self._pen_erasers.pop(pointer_id, None)

    @objc_method('v@')
    def tabletPoint_(self, nsevent: ObjCInstance) -> None:
        PygletView._dispatch_pen_point(self, nsevent)

    def _dispatch_pen_point(self, nsevent: ObjCInstance) -> None:
        pointer_id = int(nsevent.deviceID())
        x, y = getMousePosition(self, nsevent)
        tilt = nsevent.tilt()
        buttons = int(nsevent.buttonMask())
        if not buttons & PenButton.TIP and not (0 <= x < self._window.width and 0 <= y < self._window.height):
            self._window._leave_pen(pointer_id)
            return
        self._window._update_pen(PenEvent(
            pointer_id, x, y, nsevent.pressure(), tilt.x * 90, -tilt.y * 90,
            nsevent.rotation(), PenButton(buttons & 7), self._pen_erasers.get(pointer_id, False),
            bool(buttons & PenButton.TIP),
        ))

    @objc_method('v@')
    def mouseMoved_(self, nsevent: ObjCInstance) -> None:
        if PygletView._dispatch_pen_mouse(self, nsevent):
            return
        if self._window._mouse_ignore_motion:  # noqa: SLF001
            self._window._mouse_ignore_motion = False  # noqa: SLF001
            return
        # Don't send on_mouse_motion events if we're not inside the content rectangle.
        if not self._window._mouse_in_window:  # noqa: SLF001
            return
        x, y = getMousePosition(self, nsevent)
        dx, dy = getMouseDelta(nsevent)
        factor = self._window._nswindow.backingScaleFactor()
        self._window.dispatch_event('on_mouse_motion', x, y, dx * factor, dy * factor)

    def _dispatch_touches(self, event: ObjCInstance, phase: int, dispatch_name: str) -> None:
        touches = event.touchesMatchingPhase_inView_(phase, self)
        if not touches:
            return

        touch_array = touches.allObjects()
        for index in range(touch_array.count()):
            touch = touch_array.objectAtIndex_(index)
            x, y = getTouchPosition(self, touch)
            self._window._dispatch_touch_event(dispatch_name, int(touch.hash()), x, y, 0, 0, 0.0)

    @objc_method('v@')
    def touchesBeganWithEvent_(self, event: ObjCInstance) -> None:
        self._dispatch_touches(event, 1, 'on_touch_start')

    @objc_method('v@')
    def touchesMovedWithEvent_(self, event: ObjCInstance) -> None:
        self._dispatch_touches(event, 2, 'on_touch_move')

    @objc_method('v@')
    def touchesEndedWithEvent_(self, event: ObjCInstance) -> None:
        self._dispatch_touches(event, 4, 'on_touch_end')

    @objc_method('v@')
    def touchesCancelledWithEvent_(self, event: ObjCInstance) -> None:
        self._dispatch_touches(event, 8, 'on_touch_end')

    @objc_method('v@')
    def scrollWheel_(self, nsevent: ObjCInstance) -> None:
        x, y = getMousePosition(self, nsevent)
        scroll_x, scroll_y = getMouseDelta(nsevent)
        self._window.dispatch_event('on_mouse_scroll', x, y, scroll_x, scroll_y)

    @objc_method('v@')
    def mouseDown_(self, nsevent: ObjCInstance) -> None:
        if PygletView._dispatch_pen_mouse(self, nsevent):
            return
        x, y = getMousePosition(self, nsevent)
        buttons = mouse.LEFT
        modifiers = getModifiers(nsevent)
        self._window.dispatch_event('on_mouse_press', x, y, buttons, modifiers)

    @objc_method('v@')
    def mouseDragged_(self, nsevent: ObjCInstance) -> None:
        if PygletView._dispatch_pen_mouse(self, nsevent):
            return
        x, y = getMousePosition(self, nsevent)
        dx, dy = getMouseDelta(nsevent)
        buttons = mouse.LEFT
        modifiers = getModifiers(nsevent)
        self._window.dispatch_event('on_mouse_drag', x, y, dx, dy, buttons, modifiers)

    @objc_method('v@')
    def mouseUp_(self, nsevent: ObjCInstance) -> None:
        if PygletView._dispatch_pen_mouse(self, nsevent):
            return
        x, y = getMousePosition(self, nsevent)
        buttons = mouse.LEFT
        modifiers = getModifiers(nsevent)
        self._window.dispatch_event('on_mouse_release', x, y, buttons, modifiers)

    @objc_method('v@')
    def rightMouseDown_(self, nsevent: ObjCInstance) -> None:
        if PygletView._dispatch_pen_mouse(self, nsevent):
            return
        x, y = getMousePosition(self, nsevent)
        buttons = mouse.RIGHT
        modifiers = getModifiers(nsevent)
        self._window.dispatch_event('on_mouse_press', x, y, buttons, modifiers)

    @objc_method('v@')
    def rightMouseDragged_(self, nsevent: ObjCInstance) -> None:
        if PygletView._dispatch_pen_mouse(self, nsevent):
            return
        x, y = getMousePosition(self, nsevent)
        dx, dy = getMouseDelta(nsevent)
        buttons = mouse.RIGHT
        modifiers = getModifiers(nsevent)
        self._window.dispatch_event('on_mouse_drag', x, y, dx, dy, buttons, modifiers)

    @objc_method('v@')
    def rightMouseUp_(self, nsevent: ObjCInstance) -> None:
        if PygletView._dispatch_pen_mouse(self, nsevent):
            return
        x, y = getMousePosition(self, nsevent)
        buttons = mouse.RIGHT
        modifiers = getModifiers(nsevent)
        self._window.dispatch_event('on_mouse_release', x, y, buttons, modifiers)

    @objc_method('v@')
    def otherMouseDown_(self, nsevent: ObjCInstance) -> None:
        if PygletView._dispatch_pen_mouse(self, nsevent):
            return
        x, y = getMousePosition(self, nsevent)
        buttons = mouse.MIDDLE
        modifiers = getModifiers(nsevent)
        self._window.dispatch_event('on_mouse_press', x, y, buttons, modifiers)

    @objc_method('v@')
    def otherMouseDragged_(self, nsevent: ObjCInstance) -> None:
        if PygletView._dispatch_pen_mouse(self, nsevent):
            return
        x, y = getMousePosition(self, nsevent)
        dx, dy = getMouseDelta(nsevent)
        buttons = mouse.MIDDLE
        modifiers = getModifiers(nsevent)
        self._window.dispatch_event('on_mouse_drag', x, y, dx, dy, buttons, modifiers)

    @objc_method('v@')
    def otherMouseUp_(self, nsevent: ObjCInstance) -> None:
        if PygletView._dispatch_pen_mouse(self, nsevent):
            return
        x, y = getMousePosition(self, nsevent)
        buttons = mouse.MIDDLE
        modifiers = getModifiers(nsevent)
        self._window.dispatch_event('on_mouse_release', x, y, buttons, modifiers)

    @objc_method('v@')
    def mouseEntered_(self, nsevent: ObjCInstance) -> None:
        x, y = getMousePosition(self, nsevent)
        self._window._mouse_in_window = True  # noqa: SLF001
        # Don't call self._window.set_mouse_cursor_platform_visible() from here.
        # Better to do it from cursorUpdate:
        self._window.dispatch_event('on_mouse_enter', x, y)

    @objc_method('v@')
    def mouseExited_(self, nsevent: ObjCInstance) -> None:
        x, y = getMousePosition(self, nsevent)
        self._window._mouse_in_window = False  # noqa: SLF001
        for pointer_id, event in tuple(self._window._pen_state.pens.items()):
            if not event.in_contact:
                self._window._leave_pen(pointer_id)
        if not self._window._mouse_exclusive:  # noqa: SLF001
            self._window.set_mouse_cursor_platform_visible()
        self._window.dispatch_event('on_mouse_leave', x, y)

    @objc_method('v@')
    def cursorUpdate_(self, nsevent: ObjCInstance) -> None:
        # Called when mouse cursor enters view.  Unlike mouseEntered:,
        # this method will be called if the view appears underneath a
        # motionless mouse cursor, as can happen during window creation,
        # or when switching into fullscreen mode.
        # BUG: If the mouse enters the window via the resize control at the
        # the bottom right corner, the resize control will set the cursor
        # to the default arrow and screw up our cursor tracking.
        self._window._mouse_in_window = True  # noqa: SLF001
        if not self._window._mouse_exclusive:  # noqa: SLF001
            self._window.set_mouse_cursor_platform_visible()

    @objc_method('Q@')
    def draggingEntered_(self, draginfo: ObjCInstance) -> int:
        paths = _get_dragging_paths(draginfo)
        if paths:
            x, y = _get_drag_position(self, draginfo)
            if not self._file_drag_active:
                self._window.dispatch_event('on_file_drag_enter', x, y, paths)
                self._file_drag_active = True
            return NSDragOperationGeneric
        return 0

    @objc_method('Q@')
    def draggingUpdated_(self, draginfo: ObjCInstance) -> int:
        paths = _get_dragging_paths(draginfo)
        if paths:
            x, y = _get_drag_position(self, draginfo)
            if not self._file_drag_active:
                self._window.dispatch_event('on_file_drag_enter', x, y, paths)
                self._file_drag_active = True
            self._window.dispatch_event('on_file_drag', x, y, paths)
            return NSDragOperationGeneric
        if self._file_drag_active:
            self._window.dispatch_event('on_file_drag_exit')
            self._file_drag_active = False
        return 0

    @objc_method('v@')
    def draggingExited_(self, draginfo: ObjCInstance) -> None:
        if self._file_drag_active:
            self._window.dispatch_event('on_file_drag_exit')
            self._file_drag_active = False

    @objc_method('B@')
    def performDragOperation_(self, sender: ObjCInstance) -> bool:
        x, y = _get_drag_position(self, sender)
        paths = _get_dragging_paths(sender)
        if paths:
            self._window.dispatch_event('on_file_drop', x, y, paths)
        if self._file_drag_active:
            self._window.dispatch_event('on_file_drag_exit')
            self._file_drag_active = False
        return bool(paths)
