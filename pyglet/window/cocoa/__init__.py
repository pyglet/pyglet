# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions 
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright 
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from ctypes import *
import unicodedata

import pyglet
from pyglet.window import BaseWindow, WindowException
from pyglet.window import MouseCursor, DefaultMouseCursor
from pyglet.window import key, mouse
from pyglet.event import EventDispatcher

from pyglet.canvas.cocoa import CocoaCanvas

from pyglet.libs.darwin import *
from pyglet.libs.darwin.quartzkey import keymap, charmap


# This class is a wrapper around NSCursor which prevents us from
# sending too many hide or unhide messages in a row.  Apparently
# NSCursor treats them like retain/release messages, which can be
# problematic when we are e.g. switching between window & fullscreen.
class SystemCursor:
    cursor_is_hidden = False
    @classmethod
    def hide(cls):
        if not cls.cursor_is_hidden:
            NSCursor.hide()
            cls.cursor_is_hidden = True
    @classmethod
    def unhide(cls):
        if cls.cursor_is_hidden:
            NSCursor.unhide()
            cls.cursor_is_hidden = False


class CocoaMouseCursor(MouseCursor):
    drawable = False
    def __init__(self, constructor):
        # constructor is an NSCursor class method creating one of the
        # default cursors, e.g. NSCursor.pointingHandCursor.
        self.constructor = constructor
    def set(self):
        self.constructor().set()


class PygletDelegate(NSObject):

    # CocoaWindow object.
    _window = None

    def initWithWindow_(self, window):
        self = super(PygletDelegate, self).init()
        if self is not None:
            self._window = window
            window._nswindow.setDelegate_(self)
        # Register delegate for hide and unhide notifications so that we 
        # can dispatch the corresponding pyglet events.
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self, "applicationDidHide:", NSApplicationDidHideNotification, None)
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self, "applicationDidUnhide:", NSApplicationDidUnhideNotification, None)
        # Flag set when we pause exclusive mouse mode if window loses key status.
        self.did_pause_exclusive_mouse = False
        return self

    def dealloc(self):
        # Unregister delegate from notification center.
        NSNotificationCenter.defaultCenter().removeObserver_(self)
        super(PygletDelegate, self).dealloc()

    def applicationDidHide_(self, notification):
        self._window.dispatch_event("on_hide")
    
    def applicationDidUnhide_(self, notification):
        if self._window._is_mouse_exclusive and CGCursorIsVisible():
            # The cursor should be hidden, but for some reason it's not;
            # try to force the cursor to hide (without over-hiding).
            SystemCursor.unhide()
            SystemCursor.hide()
        self._window.dispatch_event("on_show")

    def windowShouldClose_(self, notification):
        # The method is not called if [NSWindow close] was used.
        self._window.dispatch_event("on_close")
        return False

    def windowDidMove_(self, notification):
        x, y = self._window.get_location()
        self._window.dispatch_event("on_move", x, y)

    def windowDidResize_(self, notification):
        # Don't need to do anything here because if we subclass PygletView
        # from NSOpenGLView, we handle everything in the reshape method.
        pass

    def windowDidBecomeKey_(self, notification):
        # Restore exclusive mouse mode if it was active before we lost key status.
        if self.did_pause_exclusive_mouse:
            self._window.set_exclusive_mouse(True)
            self.did_pause_exclusive_mouse = False
            self._window._nswindow.setMovable_(True)   # Mac OS X 10.6 
        # Restore previous mouse visibility settings.
        self._window.set_mouse_platform_visible()
        self._window.dispatch_event("on_activate")
    
    def windowDidResignKey_(self, notification):
        # Pause exclusive mouse mode if it is active.
        if self._window._is_mouse_exclusive:
            self._window.set_exclusive_mouse(False)
            self.did_pause_exclusive_mouse = True
            # We need to prevent the window from being unintentionally dragged
            # (by the call to set_mouse_position in set_exclusive_mouse) when
            # the window is reactivated by clicking on its title bar.
            self._window._nswindow.setMovable_(False)   # Mac OS X 10.6 
        # Make sure that cursor is visible.
        self._window.set_mouse_platform_visible(True)
        self._window.dispatch_event("on_deactivate")
        
    def windowDidMiniaturize_(self, notification):
        self._window.dispatch_event("on_hide")

    def windowDidDeminiaturize_(self, notification):
        if self._window._is_mouse_exclusive and CGCursorIsVisible():
            # The cursor should be hidden, but for some reason it's not;
            # try to force the cursor to hide (without over-hiding).
            SystemCursor.unhide()
            SystemCursor.hide()
        self._window.dispatch_event("on_show")

    def windowDidExpose_(self,  notification):
        self._window.dispatch_event("on_expose")

    def terminate_(self, sender):
        NSApp().terminate_(self)

    def validateMenuItem_(self, menuitem):
        # Disable quitting with command-q when in keyboard exclusive mode.
        if menuitem.action() == 'terminate:':
            return not self._window._is_keyboard_exclusive
        return True


# This custom NSTextView subclass is used for capturing all of the
# on_text, on_text_motion, and on_text_motion_select events.
class PygletTextView(NSTextView):

    def keyDown_(self, nsevent):
        self.interpretKeyEvents_( [ nsevent ] )

    def initWithCocoaWindow_(self, window):
        self = super(PygletTextView, self).init()
        if self is not None:
            self._window = window
            self.setFieldEditor_(False)  # interpret tab and return as raw characters
        return self

    def insertText_(self, text):
        self.setString_("")
        # Don't send control characters (tab, newline) as on_text events.
        if unicodedata.category(text[0]) != 'Cc':
            self._window.dispatch_event("on_text", text)

    def insertNewline_(self, sender):
        # Distinguish between carriage return (u'\r') and enter (u'\x03').
        # Only the return key press gets sent as an on_text event.
        if NSApp().currentEvent().charactersIgnoringModifiers()[0] == u'\r':
            self._window.dispatch_event("on_text", u'\r')

    def moveUp_(self, sender):
        self._window.dispatch_event("on_text_motion", key.MOTION_UP)
    def moveDown_(self, sender):
        self._window.dispatch_event("on_text_motion", key.MOTION_DOWN)
    def moveLeft_(self, sender):
        self._window.dispatch_event("on_text_motion", key.MOTION_LEFT)
    def moveRight_(self, sender):
        self._window.dispatch_event("on_text_motion", key.MOTION_RIGHT)
    def moveWordLeft_(self, sender):
        self._window.dispatch_event("on_text_motion", key.MOTION_PREVIOUS_WORD)        
    def moveWordRight_(self, sender):
        self._window.dispatch_event("on_text_motion", key.MOTION_NEXT_WORD)        
    def moveToBeginningOfLine_(self, sender):
        self._window.dispatch_event("on_text_motion", key.MOTION_BEGINNING_OF_LINE)
    def moveToEndOfLine_(self, sender):
        self._window.dispatch_event("on_text_motion", key.MOTION_END_OF_LINE)
    def scrollPageUp_(self, sender):
        self._window.dispatch_event("on_text_motion", key.MOTION_PREVIOUS_PAGE)
    def scrollPageDown_(self, sender):
        self._window.dispatch_event("on_text_motion", key.MOTION_NEXT_PAGE)
    def scrollToBeginningOfDocument_(self, sender):   # Mac OS X 10.6
        self._window.dispatch_event("on_text_motion", key.MOTION_BEGINNING_OF_FILE)
    def scrollToEndOfDocument_(self, sender):         # Mac OS X 10.6
        self._window.dispatch_event("on_text_motion", key.MOTION_END_OF_FILE)
    def deleteBackward_(self, sender):
        self._window.dispatch_event("on_text_motion", key.MOTION_BACKSPACE)
    def deleteForward_(self, sender):
        self._window.dispatch_event("on_text_motion", key.MOTION_DELETE)
    def moveUpAndModifySelection_(self, sender):
        self._window.dispatch_event("on_text_motion_select", key.MOTION_UP)
    def moveDownAndModifySelection_(self, sender):
        self._window.dispatch_event("on_text_motion_select", key.MOTION_DOWN)
    def moveLeftAndModifySelection_(self, sender):
        self._window.dispatch_event("on_text_motion_select", key.MOTION_LEFT)
    def moveRightAndModifySelection_(self, sender):
        self._window.dispatch_event("on_text_motion_select", key.MOTION_RIGHT)
    def moveWordLeftAndModifySelection_(self, sender):
        self._window.dispatch_event("on_text_motion_select", key.MOTION_PREVIOUS_WORD)        
    def moveWordRightAndModifySelection_(self, sender):
        self._window.dispatch_event("on_text_motion_select", key.MOTION_NEXT_WORD)        
    def moveToBeginningOfLineAndModifySelection_(self, sender):      # Mac OS X 10.6
        self._window.dispatch_event("on_text_motion_select", key.MOTION_BEGINNING_OF_LINE)
    def moveToEndOfLineAndModifySelection_(self, sender):            # Mac OS X 10.6
        self._window.dispatch_event("on_text_motion_select", key.MOTION_END_OF_LINE)
    def pageUpAndModifySelection_(self, sender):                     # Mac OS X 10.6
        self._window.dispatch_event("on_text_motion_select", key.MOTION_PREVIOUS_PAGE)
    def pageDownAndModifySelection_(self, sender):                   # Mac OS X 10.6
        self._window.dispatch_event("on_text_motion_select", key.MOTION_NEXT_PAGE)
    def moveToBeginningOfDocumentAndModifySelection_(self, sender):  # Mac OS X 10.6
        self._window.dispatch_event("on_text_motion_select", key.MOTION_BEGINNING_OF_FILE)
    def moveToEndOfDocumentAndModifySelection_(self, sender):        # Mac OS X 10.6
        self._window.dispatch_event("on_text_motion_select", key.MOTION_END_OF_FILE)


class PygletWindow(NSWindow):

    def canBecomeKeyWindow(self):
        return True

    # When the window is being resized, it enters into a mini event loop that
    # only looks at mouseDragged and mouseUp events, blocking everything else.
    # Among other things, this makes it impossible to run an NSTimer to call the
    # idle() function in order to update the view during the resize.  So we
    # override this method, called by the resizing event loop, and call the
    # idle() function from here.  This *almost* works.  I can't figure out what
    # is happening at the very beginning of a resize event.  The NSView's
    # viewWillStartLiveResize method is called and then nothing happens until
    # the mouse is dragged.  I think NSApplication's nextEventMatchingMask_etc
    # method is being called instead of this one.  I don't really feel like
    # subclassing NSApplication just to fix this.  Also, to prevent white flashes
    # while resizing, we must also call idle() from the view's reshape method.
    def nextEventMatchingMask_untilDate_inMode_dequeue_(self, mask, date, mode, dequeue):
        if self.inLiveResize():
            # Call the idle() method while we're stuck in a live resize event.
            from pyglet import app
            if app.event_loop is not None:
                app.event_loop.idle()
                
        return super(PygletWindow, self).nextEventMatchingMask_untilDate_inMode_dequeue_(mask, date, mode, dequeue)

    # Need this for set_size to not flash.
    def animationResizeTime_(self, newFrame):
        return 0.0

class PygletToolWindow(NSPanel):

    def nextEventMatchingMask_untilDate_inMode_dequeue_(self, mask, date, mode, dequeue):
        if self.inLiveResize():
            # Call the idle() method while we're stuck in a live resize event.
            from pyglet import app
            if app.event_loop is not None:
                app.event_loop.idle()
                
        return super(PygletToolWindow, self).nextEventMatchingMask_untilDate_inMode_dequeue_(mask, date, mode, dequeue)


class PygletView(NSView):

    # CocoaWindow object.
    _window = None

    # The tracking area is used to get mouseEntered, mouseExited, and cursorUpdate 
    # events so that we can custom set the mouse cursor within the view.
    _tracking_area = None

    def initWithFrame_cocoaWindow_(self, frame, window):
        self = super(PygletView, self).initWithFrame_(frame)
        if self is not None:
            self._window = window
            self.updateTrackingAreas()

        # Create an instance of PygletTextView to handle text events. 
        # We must do this because NSOpenGLView doesn't conform to the
        # NSTextInputClient protocol by default, and the insertText: method will
        # not do the right thing with respect to translating key sequences like
        # "Option-e", "e" if the protocol isn't implemented.  So the easiest
        # thing to do is to subclass NSTextView which *does* implement the
        # protocol and let it handle text input.
        self._textview = PygletTextView.alloc().initWithCocoaWindow_(window)
        self.addSubview_(self._textview)       # add text view to the responder chain.
        return self

    def updateTrackingAreas(self):
        # This method is called automatically whenever the tracking areas need to be
        # recreated, for example when window resizes.
        if self._tracking_area:
            self.removeTrackingArea_(self._tracking_area)
            del self._tracking_area

        tracking_options = NSTrackingMouseEnteredAndExited | NSTrackingActiveInActiveApp | NSTrackingCursorUpdate

        self._tracking_area = NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
            self.frame(),     # rect
            tracking_options, # options
            self,             # owner
            None)             # userInfo

        self.addTrackingArea_(self._tracking_area)
    
    def canBecomeKeyView(self):
        return True

    def isOpaque(self):
        return True

    # This method is called during window close.
    def destroy(self):
        # Remove tracking area.
        if self._tracking_area:
            self.removeTrackingArea_(self._tracking_area)
            self._tracking_area = None
        # Get rid of the textview, then remove self from window.
        # BUG: the textview never gets garbage collected...
        self._textview._window = None
        self._textview.removeFromSuperviewWithoutNeedingDisplay()
        self._textview = None
        self._window = None
        self.removeFromSuperviewWithoutNeedingDisplay()        

    ## Event data.

    def getMouseDelta_(self, nsevent):
        dx = nsevent.deltaX()
        # Pyglet coordinate system has positive y up, but NSWindow
        # has positive y down, so we must flip sign on dy.
        dy = -nsevent.deltaY()
        return int(dx), int(dy)

    def getMousePosition_(self, nsevent):
        in_window = nsevent.locationInWindow()
        x, y = map(int, self.convertPoint_fromView_(in_window, None))
        # Must record mouse position for BaseWindow.draw_mouse_cursor to work.
        self._window._mouse_x = x
        self._window._mouse_y = y
        return x, y

    def getModifiers_(self, nsevent):
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
        return modifiers
    
    def getSymbol_(self, nsevent):
        return keymap[nsevent.keyCode()]

    ## Event responders.

    # This method is called whenever the view changes size.
    def setFrameSize_(self, size):
        super(PygletView, self).setFrameSize_(size)
        
        # This method is called when view is first installed as the
        # contentView of window.  Don't do anything on first call.
        # This also helps ensure correct window creation event ordering.
        if not self._window.context.canvas:
            return

        width, height = map(int, size)
        self._window.switch_to()
        self._window.context.update_geometry()
        self._window.dispatch_event("on_resize", width, height)
        self._window.dispatch_event("on_expose")
        # Can't get app.event_loop.enter_blocking() working with Cocoa, because
        # when mouse clicks on the window's resize control, Cocoa enters into a
        # mini-event loop that only responds to mouseDragged and mouseUp events.
        # This means that using NSTimer to call idle() won't work.  Our kludge
        # is to override NSWindow's nextEventMatchingMask_etc method and call
        # idle() from there.
        if self.inLiveResize():
            from pyglet import app
            if app.event_loop is not None:
                app.event_loop.idle()

    def pygletKeyDown_(self, nsevent):
        symbol = self.getSymbol_(nsevent)
        modifiers = self.getModifiers_(nsevent)
        self._window.dispatch_event('on_key_press', symbol, modifiers)

    def pygletKeyUp_(self, nsevent):
        symbol = self.getSymbol_(nsevent)
        modifiers = self.getModifiers_(nsevent)
        self._window.dispatch_event('on_key_release', symbol, modifiers)

    def pygletFlagsChanged_(self, nsevent):
        # Handles on_key_press and on_key_release events for modifier keys.
        # Note that capslock is handled differently than other keys; it acts
        # as a toggle, so on_key_release is only sent when it's turned off.

        # TODO: Move these constants somewhere else.
        # Undocumented left/right modifier masks found by experimentation:
        NSLeftShiftKeyMask      = 1 << 1
        NSRightShiftKeyMask     = 1 << 2
        NSLeftControlKeyMask    = 1 << 0
        NSRightControlKeyMask   = 1 << 13
        NSLeftAlternateKeyMask  = 1 << 5
        NSRightAlternateKeyMask = 1 << 6
        NSLeftCommandKeyMask    = 1 << 3
        NSRightCommandKeyMask   = 1 << 4

        maskForKey = { key.LSHIFT : NSLeftShiftKeyMask,
                       key.RSHIFT : NSRightShiftKeyMask,
                       key.LCTRL : NSLeftControlKeyMask,
                       key.RCTRL : NSRightControlKeyMask,
                       key.LOPTION : NSLeftAlternateKeyMask,
                       key.ROPTION : NSRightAlternateKeyMask,
                       key.LCOMMAND : NSLeftCommandKeyMask,
                       key.RCOMMAND : NSRightCommandKeyMask,
                       key.CAPSLOCK : NSAlphaShiftKeyMask }

        symbol = self.getSymbol_(nsevent)

        # Ignore this event if symbol is not a modifier key.  We must check this
        # because e.g., we receive a flagsChanged message when using CMD-tab to
        # switch applications, with symbol == "a" when command key is released.
        if symbol not in maskForKey: 
            return

        modifiers = self.getModifiers_(nsevent)
        modifierFlags = nsevent.modifierFlags()

        if symbol and modifierFlags & maskForKey[symbol]:
            self._window.dispatch_event('on_key_press', symbol, modifiers)
        else:
            self._window.dispatch_event('on_key_release', symbol, modifiers)

    # Overriding this method helps prevent system beeps for unhandled events.
    def performKeyEquivalent_(self, nsevent):
        # Let arrow keys and certain function keys pass through the responder
        # chain so that the textview can handle on_text_motion events.
        modifierFlags = nsevent.modifierFlags()
        if modifierFlags & NSNumericPadKeyMask:
            return False
        if modifierFlags & NSFunctionKeyMask:
            ch = nsevent.charactersIgnoringModifiers()
            if ch in (NSHomeFunctionKey, NSEndFunctionKey, 
                      NSPageUpFunctionKey, NSPageDownFunctionKey):
                return False
        # Send the key equivalent to the main menu to perform menu items.
        NSApp().mainMenu().performKeyEquivalent_(nsevent)
        # Indicate that we've handled the event so system won't beep.
        return True

    def mouseMoved_(self, nsevent):
        if self._window._mouse_ignore_motion:
            self._window._mouse_ignore_motion = False
            return
        # Don't send on_mouse_motion events if we're not inside the content rectangle.
        if not self._window._mouse_in_window:
            return
        x, y = self.getMousePosition_(nsevent)
        dx, dy = self.getMouseDelta_(nsevent)
        self._window.dispatch_event('on_mouse_motion', x, y, dx, dy)
    
    def scrollWheel_(self, nsevent):
        x, y = self.getMousePosition_(nsevent)
        scroll_x, scroll_y = self.getMouseDelta_(nsevent)
        # Flip sign (back to original) on dy for scroll wheel.
        self._window.dispatch_event('on_mouse_scroll', x, y, scroll_x, -scroll_y)
    
    def mouseDown_(self, nsevent):
        x, y = self.getMousePosition_(nsevent)
        buttons = mouse.LEFT
        modifiers = self.getModifiers_(nsevent)
        self._window.dispatch_event('on_mouse_press', x, y, buttons, modifiers)
    
    def mouseDragged_(self, nsevent):
        x, y = self.getMousePosition_(nsevent)
        dx, dy = self.getMouseDelta_(nsevent)
        buttons = mouse.LEFT
        modifiers = self.getModifiers_(nsevent)
        self._window.dispatch_event('on_mouse_drag', x, y, dx, dy, buttons, modifiers)
    
    def mouseUp_(self, nsevent):
        x, y = self.getMousePosition_(nsevent)
        buttons = mouse.LEFT
        modifiers = self.getModifiers_(nsevent)
        self._window.dispatch_event('on_mouse_release', x, y, buttons, modifiers)
    
    def rightMouseDown_(self, nsevent):
        x, y = self.getMousePosition_(nsevent)
        buttons = mouse.RIGHT
        modifiers = self.getModifiers_(nsevent)
        self._window.dispatch_event('on_mouse_press', x, y, buttons, modifiers)
    
    def rightMouseDragged_(self, nsevent):
        x, y = self.getMousePosition_(nsevent)
        dx, dy = self.getMouseDelta_(nsevent)
        buttons = mouse.RIGHT
        modifiers = self.getModifiers_(nsevent)
        self._window.dispatch_event('on_mouse_drag', x, y, dx, dy, buttons, modifiers)
    
    def rightMouseUp_(self, nsevent):
        x, y = self.getMousePosition_(nsevent)
        buttons = mouse.RIGHT
        modifiers = self.getModifiers_(nsevent)
        self._window.dispatch_event('on_mouse_release', x, y, buttons, modifiers)
    
    def otherMouseDown_(self, nsevent):
        x, y = self.getMousePosition_(nsevent)
        buttons = mouse.MIDDLE
        modifiers = self.getModifiers_(nsevent)
        self._window.dispatch_event('on_mouse_press', x, y, buttons, modifiers)
    
    def otherMouseDragged_(self, nsevent):
        x, y = self.getMousePosition_(nsevent)
        dx, dy = self.getMouseDelta_(nsevent)
        buttons = mouse.MIDDLE
        modifiers = self.getModifiers_(nsevent)
        self._window.dispatch_event('on_mouse_drag', x, y, dx, dy, buttons, modifiers)
    
    def otherMouseUp_(self, nsevent):
        x, y = self.getMousePosition_(nsevent)
        buttons = mouse.MIDDLE
        modifiers = self.getModifiers_(nsevent)
        self._window.dispatch_event('on_mouse_release', x, y, buttons, modifiers)

    def mouseEntered_(self, nsevent):
        x, y = self.getMousePosition_(nsevent)
        self._window._mouse_in_window = True
        # Don't call self._window.set_mouse_platform_visible() from here.
        # Better to do it from cursorUpdate:
        self._window.dispatch_event('on_mouse_enter', x, y)

    def mouseExited_(self, nsevent):
        x, y = self.getMousePosition_(nsevent)
        self._window._mouse_in_window = False
        if not self._window._is_mouse_exclusive:
            self._window.set_mouse_platform_visible()
        self._window.dispatch_event('on_mouse_leave', x, y)

    def cursorUpdate_(self, nsevent):
        # Called when mouse cursor enters view.  Unlike mouseEntered:,
        # this method will be called if the view appears underneath a
        # motionless mouse cursor, as can happen during window creation,
        # or when switching into fullscreen mode.  
        # BUG: If the mouse enters the window via the resize control at the
        # the bottom right corner, the resize control will set the cursor
        # to the default arrow and screw up our cursor tracking.
        self._window._mouse_in_window = True
        if not self._window._is_mouse_exclusive:
            self._window.set_mouse_platform_visible()


class CocoaWindow(BaseWindow):

    # NSWindow instance.
    _nswindow = None

    # Delegate object.
    _delegate = None
    
    # Window properties
    _minimum_size = None
    _maximum_size = None

    _is_mouse_exclusive = False
    _mouse_platform_visible = True
    _mouse_ignore_motion = False

    _is_keyboard_exclusive = False

    # Flag set during close() method.
    _was_closed = False

    # NSWindow style masks.
    _style_masks = {
        BaseWindow.WINDOW_STYLE_DEFAULT:    NSTitledWindowMask |
                                            NSClosableWindowMask |
                                            NSMiniaturizableWindowMask,
        BaseWindow.WINDOW_STYLE_DIALOG:     NSTitledWindowMask |
                                            NSClosableWindowMask,
        BaseWindow.WINDOW_STYLE_TOOL:       NSTitledWindowMask |
                                            NSClosableWindowMask | 
                                            NSUtilityWindowMask,
        BaseWindow.WINDOW_STYLE_BORDERLESS: NSBorderlessWindowMask,
    }

    def _recreate(self, changes):
        if ('context' in changes):
            self.context.set_current()
        
        if 'fullscreen' in changes:
            if not self._fullscreen:  # leaving fullscreen
                self.screen.release_display()

        self._create()

    def _create(self):
        # Create a temporary autorelease pool for this method.
        pool = NSAutoreleasePool.alloc().init()

        if self._nswindow:
            # The window is about the be recreated so destroy everything
            # associated with the old window, then destroy the window itself.
            self.canvas = None
            self._nswindow.orderOut_(None)
            self._nswindow.close()
            self.context.detach()
            self._nswindow = None

        # Determine window parameters.
        content_rect = NSMakeRect(0, 0, self._width, self._height)
        WindowClass = PygletWindow
        if self._fullscreen:
            style_mask = NSBorderlessWindowMask
        else:
            if self._style not in self._style_masks:
                self._style = self.WINDOW_STYLE_DEFAULT
            style_mask = self._style_masks[self._style]
            if self._resizable:
                style_mask |= NSResizableWindowMask
            if self._style == BaseWindow.WINDOW_STYLE_TOOL:
                WindowClass = PygletToolWindow

        # First create an instance of our NSWindow subclass.
        self._nswindow = WindowClass.alloc().initWithContentRect_styleMask_backing_defer_(
            content_rect,           # contentRect
            style_mask,             # styleMask
            NSBackingStoreBuffered, # backing
            False)                  # defer

        if self._fullscreen:
            # BUG: I suspect that this doesn't do the right thing when using
            # multiple monitors (which would be to go fullscreen on the monitor
            # where the window is located).  However I've no way to test.
            self._nswindow.setBackgroundColor_(NSColor.blackColor())            
            self._nswindow.setOpaque_(True)
            self.screen.capture_display()
            self._nswindow.setLevel_(CGShieldingWindowLevel())
            self.context.set_full_screen()
            self._center_fullscreen_window()
        else:
            self._set_nice_window_location()

        # Then create a view and set it as our NSWindow's content view.
        nsview = PygletView.alloc().initWithFrame_cocoaWindow_(content_rect, self)
        self._nswindow.setContentView_(nsview)
        self._nswindow.makeFirstResponder_(nsview)

        # Create a canvas with the view as its drawable and attach context to it.
        self.canvas = CocoaCanvas(self.display, self.screen, nsview)
        self.context.attach(self.canvas)

        # Configure the window.
        self._nswindow.setAcceptsMouseMovedEvents_(True)
        self._nswindow.setReleasedWhenClosed_(False)
        self._nswindow.useOptimizedDrawing_(True)
        self._nswindow.setPreservesContentDuringLiveResize_(False)

        # Set the delegate.
        self._delegate = PygletDelegate.alloc().initWithWindow_(self)

        # Configure CocoaWindow.
        self.set_caption(self._caption)
        if self._minimum_size is not None:
            self.set_minimum_size(*self._minimum_size)
        if self._maximum_size is not None:
            self.set_maximum_size(*self._maximum_size)

        self.context.update_geometry()
        self.switch_to()
        self.set_vsync(self._vsync)
        self.set_visible(self._visible)

        del pool

    def _set_nice_window_location(self):
        # Construct a list of all visible windows that aren't us.
        visible_windows = [ win for win in pyglet.app.windows if
                            win is not self and 
                            win._nswindow and 
                            win._nswindow.isVisible() ]
        # If there aren't any visible windows, then center this window.
        if not visible_windows:
            self._nswindow.center()
        # Otherwise, cascade from last window in list.
        else:
            point = visible_windows[-1]._nswindow.cascadeTopLeftFromPoint_(NSZeroPoint)
            self._nswindow.cascadeTopLeftFromPoint_(point)

    def _center_fullscreen_window(self):
        # [NSWindow center] does not move the window to a true center position.
        x = int((self.screen.width - self._width)/2)
        y = int((self.screen.height - self._height)/2)
        self._nswindow.setFrameOrigin_((x, y))

    def close(self):
        # If we've already gone through this once, don't do it again.
        if self._was_closed:
            return

        # Create a temporary autorelease pool for this method.
        pool = NSAutoreleasePool.alloc().init()

        # Restore cursor visibility
        self.set_mouse_platform_visible(True)
        self.set_exclusive_mouse(False)
        self.set_exclusive_keyboard(False)

        # Remove the delegate object
        if self._delegate:
            self._nswindow.setDelegate_(None)
            self._delegate._window = None
            self._delegate = None
            
        # Remove window from display and remove its view.
        if self._nswindow:
            self._nswindow.orderOut_(None)
            self._nswindow.setContentView_(None)
            self._nswindow.close()

        # Restore screen mode. This also releases the display
        # if it was captured for fullscreen mode.
        self.screen.restore_mode()

        # Remove view from canvas and then remove canvas.
        if self.canvas:
            self.canvas.nsview.destroy()
            self.canvas.nsview = None
            self.canvas = None

        # Do this last, so that we don't see white flash 
        # when exiting application from fullscreen mode.
        super(CocoaWindow, self).close()

        self._was_closed = True
        del pool

    def switch_to(self):
        if self.context:
            self.context.set_current()

    def flip(self):
        self.draw_mouse_cursor()
        if self.context:
            self.context.flip()

    def dispatch_events(self):
        self._allow_dispatch_event = True
        # Process all pyglet events.
        self.dispatch_pending_events()
        event = True

        # Dequeue and process all of the pending Cocoa events.
        pool = NSAutoreleasePool.alloc().init()
        while event and self._nswindow and self._context:
            event = NSApp().nextEventMatchingMask_untilDate_inMode_dequeue_(
                NSAnyEventMask, None, NSEventTrackingRunLoopMode, True)

            if event is not None:
                event_type = event.type()
                # Pass on all events.
                NSApp().sendEvent_(event)
                # And resend key events to special handlers.
                if event_type == NSKeyDown and not event.isARepeat():
                    NSApp().sendAction_to_from_("pygletKeyDown:", None, event)
                elif event_type == NSKeyUp:
                    NSApp().sendAction_to_from_("pygletKeyUp:", None, event)
                elif event_type == NSFlagsChanged:
                    NSApp().sendAction_to_from_("pygletFlagsChanged:", None, event)
                NSApp().updateWindows()

        del pool

        self._allow_dispatch_event = False

    def dispatch_pending_events(self):
        while self._event_queue:
            event = self._event_queue.pop(0)
            EventDispatcher.dispatch_event(self, *event)

    def set_caption(self, caption):
        self._caption = caption
        if self._nswindow is not None:
            self._nswindow.setTitle_(caption)

    def set_icon(self, *images):
        # Only use the biggest image from the list.
        max_image = images[0]
        for img in images:
            if img.width > max_image.width and img.height > max_image.height:
                max_image = img

        # Grab image data from pyglet image.
        image = max_image.get_image_data()
        format = 'ARGB'
        bytesPerRow = len(format) * image.width
        data = image.get_data(format, -bytesPerRow)

        # Use image data to create a data provider.
        # Using CGDataProviderCreateWithData crashes PyObjC 2.2b3, so we create
        # a CFDataRef object first and use it to create the data provider.
        cfdata = CoreFoundation.CFDataCreate(None, data, len(data))
        provider = CGDataProviderCreateWithCFData(cfdata)
        
        # Then create a CGImage from the provider.
        cgimage = CGImageCreate(
            image.width, image.height, 8, 32, bytesPerRow,
            CGColorSpaceCreateDeviceRGB(),
            kCGImageAlphaFirst,
            provider,
            None,
            True,
            kCGRenderingIntentDefault)
        
        if not cgimage:
            return

        # Turn the CGImage into an NSImage.
        size = NSMakeSize(image.width, image.height)
        nsimage = NSImage.alloc().initWithCGImage_size_(cgimage, size)
        if not nsimage:
            return

        # And finally set the app icon.
        NSApp().setApplicationIconImage_(nsimage)

    def get_location(self):
        rect = self._nswindow.contentRectForFrameRect_(self._nswindow.frame())        
        screen_width, screen_height = self._nswindow.screen().frame().size
        return int(rect.origin.x), int(screen_height - rect.origin.y - rect.size.height)

    def set_location(self, x, y):
        rect = self._nswindow.contentRectForFrameRect_(self._nswindow.frame())        
        screen_width, screen_height = self._nswindow.screen().frame().size
        self._nswindow.setFrameOrigin_(NSPoint(x, screen_height - y - rect.size.height))

    def get_size(self):
        rect = self._nswindow.contentRectForFrameRect_(self._nswindow.frame())
        return int(rect.size.width), int(rect.size.height)

    def set_size(self, width, height):
        if self._fullscreen:
            raise WindowException('Cannot set size of fullscreen window.')
        self._width = max(1, int(width))
        self._height = max(1, int(height))
        # Move frame origin down so that top-left corner of window doesn't move.
        rect = self._nswindow.contentRectForFrameRect_(self._nswindow.frame())
        rect.origin.y += rect.size.height - self._height
        rect.size.width = self._width
        rect.size.height = self._height
        frame = self._nswindow.frameRectForContentRect_(rect)
        # The window background flashes when the frame size changes unless it's
        # animated, but we can set the window's animationResizeTime to zero.
        self._nswindow.setFrame_display_animate_(frame, True, self._nswindow.isVisible())

    def set_minimum_size(self, width, height):
        self._minimum_size = NSSize(width, height)
        if self._nswindow is not None:
            self._nswindow.setContentMinSize_(self._minimum_size)

    def set_maximum_size(self, width, height):
        self._maximum_size = NSSize(width, height)
        if self._nswindow is not None:
            self._nswindow.setContentMaxSize_(self._maximum_size)

    def activate(self):
        if self._nswindow is not None:
            NSApp().activateIgnoringOtherApps_(True)
            self._nswindow.makeKeyAndOrderFront_(None)

    def set_visible(self, visible=True):
        self._visible = visible
        if self._nswindow is not None:
            if visible:
                # Not really sure why on_resize needs to be here, 
                # but it's what pyglet wants.
                self.dispatch_event('on_resize', self._width, self._height)
                self.dispatch_event('on_show')
                self.dispatch_event('on_expose')
                self._nswindow.makeKeyAndOrderFront_(None)
            else:
                self._nswindow.orderOut_(None)

    def minimize(self):
        self._mouse_in_window = False
        if self._nswindow is not None:
            self._nswindow.miniaturize_(None)

    def maximize(self):
        if self._nswindow is not None:
            self._nswindow.zoom_(None)

    def set_vsync(self, vsync):
        if pyglet.options['vsync'] is not None:
            vsync = pyglet.options['vsync']
        self._vsync = vsync # _recreate depends on this
        if self.context:
            self.context.set_vsync(vsync)

    def _mouse_in_content_rect(self):
        # Returns true if mouse is inside the window's content rectangle.
        # Better to use this method to check manually rather than relying
        # on instance variables that may not be set correctly.
        point = NSEvent.mouseLocation()
        rect = self._nswindow.contentRectForFrameRect_(self._nswindow.frame())
        return NSMouseInRect(point, rect, False)

    def set_mouse_platform_visible(self, platform_visible=None):
        # When the platform_visible argument is supplied with a boolean, then this
        # method simply sets whether or not the platform mouse cursor is visible.
        if platform_visible is not None:
            if platform_visible:
                SystemCursor.unhide()
            else:
                SystemCursor.hide()
        # But if it has been called without an argument, it turns into
        # a completely different function.  Now we are trying to figure out
        # whether or not the mouse *should* be visible, and if so, what it should
        # look like.
        else:
            # If we are in mouse exclusive mode, then hide the mouse cursor.
            if self._is_mouse_exclusive:
                SystemCursor.hide()
            # If we aren't inside the window, then always show the mouse
            # and make sure that it is the default cursor.
            elif not self._mouse_in_content_rect():
                NSCursor.arrowCursor().set()
                SystemCursor.unhide()
            # If we are in the window, then what we do depends on both
            # the current pyglet-set visibility setting for the mouse and
            # the type of the mouse cursor.  If the cursor has been hidden
            # in the window with set_mouse_visible() then don't show it.
            elif not self._mouse_visible:
                SystemCursor.hide()
            # If the mouse is set as a system-defined cursor, then we
            # need to set the cursor and show the mouse.
            elif isinstance(self._mouse_cursor, CocoaMouseCursor):
                self._mouse_cursor.set()
                SystemCursor.unhide()
            # If the mouse cursor is drawable, then it we need to hide
            # the system mouse cursor, so that the cursor can draw itself.
            elif self._mouse_cursor.drawable:
                SystemCursor.hide()
            # Otherwise, show the default cursor.
            else:
                NSCursor.arrowCursor().set()
                SystemCursor.unhide()
                
    def get_system_mouse_cursor(self, name):
        # It would make a lot more sense for most of this code to be
        # inside the CocoaMouseCursor class, but all of the CURSOR_xxx
        # constants are defined as properties of BaseWindow.
        if name == self.CURSOR_DEFAULT:
            return DefaultMouseCursor()
        cursors = {
            self.CURSOR_CROSSHAIR:       NSCursor.crosshairCursor,
            self.CURSOR_HAND:            NSCursor.pointingHandCursor,
            self.CURSOR_HELP:            NSCursor.arrowCursor,
            self.CURSOR_NO:              NSCursor.operationNotAllowedCursor, # Mac OS 10.6
            self.CURSOR_SIZE:            NSCursor.arrowCursor,
            self.CURSOR_SIZE_UP:         NSCursor.resizeUpCursor,
            self.CURSOR_SIZE_UP_RIGHT:   NSCursor.arrowCursor,
            self.CURSOR_SIZE_RIGHT:      NSCursor.resizeRightCursor,
            self.CURSOR_SIZE_DOWN_RIGHT: NSCursor.arrowCursor,
            self.CURSOR_SIZE_DOWN:       NSCursor.resizeDownCursor,
            self.CURSOR_SIZE_DOWN_LEFT:  NSCursor.arrowCursor,
            self.CURSOR_SIZE_LEFT:       NSCursor.resizeLeftCursor,
            self.CURSOR_SIZE_UP_LEFT:    NSCursor.arrowCursor,
            self.CURSOR_SIZE_UP_DOWN:    NSCursor.resizeUpDownCursor,
            self.CURSOR_SIZE_LEFT_RIGHT: NSCursor.resizeLeftRightCursor,
            self.CURSOR_TEXT:            NSCursor.IBeamCursor,
            self.CURSOR_WAIT:            NSCursor.arrowCursor, # No wristwatch cursor in Cocoa
            self.CURSOR_WAIT_ARROW:      NSCursor.arrowCursor, # No wristwatch cursor in Cocoa
            }  
        if name not in cursors:
            raise RuntimeError('Unknown cursor name "%s"' % name)
        return CocoaMouseCursor(cursors[name])

    def set_mouse_position(self, x, y, absolute=False):
        if absolute:
            # If absolute, then x, y is given in global display coordinates
            # which sets (0,0) at top left corner of main display.  It is possible
            # to warp the mouse position to a point inside of another display.
            CGWarpMouseCursorPosition((x,y))
        else: 
            # Window-relative coordinates: (x, y) are given in window coords
            # with (0,0) at bottom-left corner of window and y up.  We find
            # which display the window is in and then convert x, y into local
            # display coords where (0,0) is now top-left of display and y down.
            screenInfo = self._nswindow.screen().deviceDescription()
            displayID = screenInfo.objectForKey_("NSScreenNumber") 
            displayBounds = CGDisplayBounds(displayID)
            windowOrigin = self._nswindow.frame().origin
            x += windowOrigin.x
            y = displayBounds.size.height - windowOrigin.y - y
            CGDisplayMoveCursorToPoint(displayID, (x,y))

    def set_exclusive_mouse(self, exclusive=True):
        self._is_mouse_exclusive = exclusive
        if exclusive:
            # Skip the next motion event, which would return a large delta.
            self._mouse_ignore_motion = True
            # Move mouse to center of window.
            width, height = self._nswindow.frame().size
            self.set_mouse_position(width/2, height/2)
            CGAssociateMouseAndMouseCursorPosition(False)
        else:
            CGAssociateMouseAndMouseCursorPosition(True)

        # Update visibility of mouse cursor.
        self.set_mouse_platform_visible()

    def set_exclusive_keyboard(self, exclusive=True):
        # http://developer.apple.com/mac/library/technotes/tn2002/tn2062.html
        # http://developer.apple.com/library/mac/#technotes/KioskMode/

        # BUG: System keys like F9 or command-tab are disabled, however 
        # pyglet also does not receive key press events for them.

        # Need to define these constants for PyObjC < 2.3
        NSApplicationPresentationDefault = 0
        NSApplicationPresentationHideDock = 1 << 1
        NSApplicationPresentationHideMenuBar = 1 << 3
        NSApplicationPresentationDisableProcessSwitching = 1 << 5
        NSApplicationPresentationDisableHideApplication = 1 << 8

        # This flag is queried by window delegate to determine whether 
        # the quit menu item is active.
        self._is_keyboard_exclusive = exclusive
            
        if exclusive:
            # "Be nice! Don't disable force-quit!" 
            #          -- Patrick Swayze, Road House (1989)
            options = NSApplicationPresentationHideDock | \
                      NSApplicationPresentationHideMenuBar | \
                      NSApplicationPresentationDisableProcessSwitching | \
                      NSApplicationPresentationDisableHideApplication
        else:
            options = NSApplicationPresentationDefault

        NSApp().setPresentationOptions_(options)
