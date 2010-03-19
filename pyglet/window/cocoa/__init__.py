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
import os.path
import unicodedata
import warnings

import pyglet
from pyglet.window import WindowException, \
    BaseWindow, MouseCursor, DefaultMouseCursor, _PlatformEventHandler
from pyglet.window import key
from pyglet.window import mouse
from pyglet.window import event
from pyglet.canvas.cocoa import CocoaCanvas

from pyglet.libs.darwin import *
from pyglet.libs.darwin.quartzkey import keymap, charmap

from pyglet.gl import gl_info
from pyglet.gl import glu_info

from pyglet.event import EventDispatcher

from Cocoa import *
from Quartz import *

# Map symbol,modifiers -> motion
# Determined by experiment with TextEdit.app
_motion_map = {
    (key.UP, False):                    key.MOTION_UP,
    (key.RIGHT, False):                 key.MOTION_RIGHT,
    (key.DOWN, False):                  key.MOTION_DOWN,
    (key.LEFT, False):                  key.MOTION_LEFT,
    (key.LEFT, key.MOD_OPTION):         key.MOTION_PREVIOUS_WORD,
    (key.RIGHT, key.MOD_OPTION):        key.MOTION_NEXT_WORD,
    (key.LEFT, key.MOD_COMMAND):        key.MOTION_BEGINNING_OF_LINE,
    (key.RIGHT, key.MOD_COMMAND):       key.MOTION_END_OF_LINE,
    (key.PAGEUP, False):                key.MOTION_PREVIOUS_PAGE,
    (key.PAGEDOWN, False):              key.MOTION_NEXT_PAGE,
    (key.HOME, False):                  key.MOTION_BEGINNING_OF_FILE,
    (key.END, False):                   key.MOTION_END_OF_FILE,
    (key.UP, key.MOD_COMMAND):          key.MOTION_BEGINNING_OF_FILE,
    (key.DOWN, key.MOD_COMMAND):        key.MOTION_END_OF_FILE,
    (key.BACKSPACE, False):             key.MOTION_BACKSPACE,
    (key.DELETE, False):                key.MOTION_DELETE,
}


class CocoaMouseCursor(MouseCursor):
    drawable = False
    def __init__(self, theme):
        self.theme = theme


class PygletDelegate(NSObject):

    # CocoaWindow object.
    _window = None

    # NSWindow object.
    _nswindow = None

    # NSView object.
    _nsview = None

    def initWithWindow_(self, window):
        self = super(PygletDelegate, self).init()
        if self is not None:
            self._window = window
            self._nswindow = window._nswindow
            self._nsview = window._nsview
            self._nswindow.setDelegate_(self)
        return self

    def windowWillClose_(self, notification):
        self._window.dispatch_event("on_close")

    def windowDidMove_(self, notification):
        x, y = self._window.get_location()
        self._window.dispatch_event("on_move", x, y)

    def windowDidResize_(self, notification):
        width, height = self._window.get_size()
        self._window.dispatch_event("on_resize", width, height)

    def windowDidChangeScreen(self, notification):
        pass


class PygletWindow(NSWindow):

    def canBecomeKeyWindow(self):
        return True


class PygletView(NSView):

    # CocoaWindow object.
    _window = None

    def initWithWindow_(self, window):
        self = super(PygletView, self).init()
        if self is not None:
            self._window = window
            tracking_options = NSTrackingMouseEnteredAndExited | \
                               NSTrackingActiveAlways | \
                               NSTrackingInVisibleRect
            self.tracking_area = NSTrackingArea.alloc() \
                .initWithRect_options_owner_userInfo_(
                    self.frame(),     # rect
                    tracking_options, # options
                    self,             # owner
                    None,             # userInfo
                    )
            self.addTrackingArea_(self.tracking_area)
        return self
    
    def canBecomeKeyView(self):
        return True

    ## Event data.

    def getDelta_(self, nsevent):
        dx = nsevent.deltaX()
        dy = nsevent.deltaY()
        return int(dx), int(dy)

    def getLocation_(self, nsevent):
        in_window = nsevent.locationInWindow()
        x, y = self.convertPoint_fromView_(in_window, None)
        return int(x), int(y)

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
            modifiers |= key.MOD_OPTION
        if modifierFlags & NSCommandKeyMask:
            modifiers |= key.MOD_COMMAND
        return modifiers
    
    def getSymbol_(self, nsevent):
        return keymap[nsevent.keyCode()]

    ## Event responders.

    def keyDown_(self, nsevent):
        symbol = self.getSymbol_(nsevent)
        modifiers = self.getModifiers_(nsevent)
        self._window.dispatch_event('on_key_press', symbol, modifiers)
    
    def keyUp_(self, nsevent):
        symbol = self.getSymbol_(nsevent)
        modifiers = self.getModifiers_(nsevent)
        self._window.dispatch_event('on_key_release', symbol, modifiers)
    
    def mouseMoved_(self, nsevent):
        x, y = self.getLocation_(nsevent)
        dx, dy = self.getDelta_(nsevent)
        self._window.dispatch_event('on_mouse_motion', x, y, dx, dy)
    
    def scrollWheel_(self, nsevent):
        x, y = self.getLocation_(nsevent)
        scroll_x, scroll_y = self.getDelta_(nsevent)
        self._window.dispatch_event('on_mouse_scroll', x, y, scroll_x, scroll_y)
    
    def mouseDown_(self, nsevent):
        x, y = self.getLocation_(nsevent)
        buttons = mouse.LEFT
        modifiers = self.getModifiers_(nsevent)
        self._window.dispatch_event('on_mouse_press', x, y, buttons, modifiers)
    
    def mouseDragged_(self, nsevent):
        x, y = self.getLocation_(nsevent)
        dx, dy = self.getDelta_(nsevent)
        buttons = mouse.LEFT
        modifiers = self.getModifiers_(nsevent)
        self._window.dispatch_event('on_mouse_drag', x, y, dx, dy, buttons,
                                    modifiers)
    
    def mouseUp_(self, nsevent):
        x, y = self.getLocation_(nsevent)
        buttons = mouse.LEFT
        modifiers = self.getModifiers_(nsevent)
        self._window.dispatch_event('on_mouse_release', x, y, buttons,
                                    modifiers)
    
    def rightMouseDown_(self, nsevent):
        x, y = self.getLocation_(nsevent)
        buttons = mouse.RIGHT
        modifiers = self.getModifiers_(nsevent)
        self._window.dispatch_event('on_mouse_press', x, y, buttons, modifiers)
    
    def rightMouseDragged_(self, nsevent):
        x, y = self.getLocation_(nsevent)
        dx, dy = self.getDelta_(nsevent)
        buttons = mouse.RIGHT
        modifiers = self.getModifiers_(nsevent)
        self._window.dispatch_event('on_mouse_drag', x, y, dx, dy, buttons,
                                    modifiers)
    
    def rightMouseUp_(self, nsevent):
        x, y = self.getLocation_(nsevent)
        buttons = mouse.RIGHT
        modifiers = self.getModifiers_(nsevent)
        self._window.dispatch_event('on_mouse_release', x, y, buttons,
                                    modifiers)
    
    def otherMouseDown_(self, nsevent):
        x, y = self.getLocation_(nsevent)
        buttons = mouse.MIDDLE
        modifiers = self.getModifiers_(nsevent)
        self._window.dispatch_event('on_mouse_press', x, y, buttons, modifiers)
    
    def otherMouseDragged_(self, nsevent):
        x, y = self.getLocation_(nsevent)
        dx, dy = self.getDelta_(nsevent)
        buttons = mouse.MIDDLE
        modifiers = self.getModifiers_(nsevent)
        self._window.dispatch_event('on_mouse_drag', x, y, dx, dy, buttons,
                                    modifiers)
    
    def otherMouseUp_(self, nsevent):
        x, y = self.getLocation_(nsevent)
        buttons = mouse.MIDDLE
        modifiers = self.getModifiers_(nsevent)
        self._window.dispatch_event('on_mouse_release', x, y, buttons,
                                    modifiers)

    def mouseEntered_(self, nsevent):
        x, y = self.getLocation_(nsevent)
        self._window.dispatch_event('on_mouse_enter', x, y)

    def mouseExited_(self, nsevent):
        x, y = self.getLocation_(nsevent)
        self._window.dispatch_event('on_mouse_leave', x, y)


class CocoaWindow(BaseWindow):

    # NSWindow instance.
    _nswindow = None

    # NSView instance.
    _nsview = None

    # NSOpenGLContext instance.
    _nscontext = None

    # Delegate object.
    _delegate = None
    
    # Window properties
    _location = None
    _minimum_size = None
    _maximum_size = None
    _event_dispatcher = None
    _current_modifiers = 0
    _mapped_modifers = 0
    _track_ref = 0
    _track_region = None

    _mouse_exclusive = False
    _mouse_platform_visible = True
    _mouse_ignore_motion = False

    # NSWindow style masks.
    _style_masks = {
        BaseWindow.WINDOW_STYLE_DEFAULT:    NSTitledWindowMask |
                                            NSClosableWindowMask |
                                            NSMiniaturizableWindowMask,
        BaseWindow.WINDOW_STYLE_DIALOG:     NSTitledWindowMask |
                                            NSClosableWindowMask,
        BaseWindow.WINDOW_STYLE_TOOL:       NSTitledWindowMask |
                                            NSClosableWindowMask,
        BaseWindow.WINDOW_STYLE_BORDERLESS: NSBorderlessWindowMask,
    }

    def _recreate(self, changes):
        if ('context' in changes):
            self._nscontext.makeCurrentContext()
        
        if 'fullscreen' in changes:
            if not self._fullscreen:
                # Leaving fullscreen
                self._nscontext.clearDrawable()
                CGDisplayRelease(self.screen.cg_display_id)
        
        self._create()

    def _create(self):

        self._nscontext = self.context._ns_context

        if self._nswindow:
            self._nscontext.clearDrawable()
            self._nswindow.orderOut_(None)
            self._nswindow.close()
            self._nswindow = None

        # Determine window parameters.
        content_rect = NSMakeRect(0, 0, self._width, self._height)
        if self._fullscreen:
            style_mask = NSBorderlessWindowMask
        else:
            if self._style not in self._style_masks:
                self._style = self.WINDOW_STYLE_DEFAULT
            style_mask = self._style_masks[self._style]
            if self._resizable:
                style_mask |= NSResizableWindowMask
            
        # Create window, view and delegate.

        self._nswindow = PygletWindow.alloc() \
                .initWithContentRect_styleMask_backing_defer_(
                        content_rect,           # contentRect
                        style_mask,             # styleMask
                        NSBackingStoreBuffered, # backing
                        False,                  # defer
                        )

        self._nsview = PygletView.alloc() \
                .initWithFrame_(
                        NSMakeRect(0, 0, 0, 0), # frame
                        ) \
                .initWithWindow_(
                        self, # window
                        )

        self._delegate = PygletDelegate.alloc() \
                .initWithWindow_(
                        self, # window
                        )
            
        # Configure NSWindow and NSView.
        self._nswindow.setContentView_(self._nsview)
        self._nswindow.makeFirstResponder_(self._nsview)
        self._nswindow.setAcceptsMouseMovedEvents_(True)
        self._nswindow.setReleasedWhenClosed_(False)
        if self._fullscreen:
            self._width = self.screen.width
            self._height = self.screen.height
            CGDisplayCapture(self.screen.cg_display_id)
            self._nscontext.setFullScreen()
            self._nswindow.setLevel_(CGShieldingWindowLevel())
            self._nswindow.setBackgroundColor_(NSColor.blackColor())
        else: 
            self._nswindow.center()
        self._nscontext.setView_(self._nsview)

        # Configure CocoaWindow.
        self.set_caption(self._caption)
        self.set_visible(self._visible)
        if self._location is not None:
            self.set_location(*self._location)
        if self._minimum_size is not None:
            self.set_minimum_size(*self._minimum_size)
        if self._maximum_size is not None:
            self.set_maximum_size(*self._maximum_size)
        
        self._nscontext.update()
        self.context.attach(self.context.config.canvas)
        self.switch_to()
        self.set_vsync(self._vsync)
        self.dispatch_event("on_resize", self._width, self._height)

    def close(self):
        super(CocoaWindow, self).close()
        if not self._nscontext:
            return
        
        self._nscontext.clearDrawable()
        self._nscontext = None

        # Restore cursor visibility
        self.set_mouse_platform_visible(True)
        self.set_exclusive_mouse(False)

        if self._fullscreen:
            CGDisplayRelease( CGMainDisplayID() )
        else:
            self._nswindow.close()
            self._nswindow = None

    def switch_to(self):
        self._context.set_current()

    def flip(self):
        self.draw_mouse_cursor()
        self._nscontext.flushBuffer()

    def dispatch_events(self):
        self.dispatch_pending_events()
    
    def dispatch_pending_events(self):
        while self._event_queue:
            EventDispatcher.dispatch_event(self, *self._event_queue.pop(0))


    def set_caption(self, caption):
        self._caption = caption
        if self._nswindow is not None:
            self._nswindow.setTitle_(caption)

    def get_location(self):
        if self._nswindow is not None:
            origin = self._nswindow.frame().origin
            return int(origin.x), int(origin.y)
        return 0, 0

    def set_location(self, x, y):
        if self._nswindow is not None:
            self.window.setFrameOrigin_(self._location)

    def get_size(self):
        if self._nswindow is not None:
            size = self._nswindow.contentView().frame().size
            return int(size.width), int(size.height)
        return 0, 0

    def set_size(self, width, height):
        self._width = int(width)
        self._height = int(height)
        if self._nswindow is not None:
            if not self._fullscreen:
                frame = self._nswindow.frame()
                frame.size.width = self._width
                frame.size.height = self._height
                self._nswindow.setFrame_display_(frame, False)

    def set_minimum_size(self, width, height):
        self._minimum_size = NSSize(width, height)
        if self._nswindow is not None:
            self._nswindow.setMinSize_(self._minimum_size)

    def set_maximum_size(self, width, height):
        self._maximum_size = NSSize(width, height)
        if self._nswindow is not None:
            self._nswindow.setMaxSize_(self._maximum_size)

    def activate(self):
        if self._nswindow is not None:
            NSApp().activateIgnoringOtherApps_(True)
            self._nswindow.makeKeyAndOrderFront_(None)

    def set_visible(self, visible=True):
        self._visible = visible
        if self._nswindow is not None:
            if visible:
                self._nswindow.makeKeyAndOrderFront_(None)
            else:
                self._nswindow.orderOut_(None)

    def minimize(self):
        self._mouse_in_window = False
        self.set_mouse_platform_visible()
        if self._nswindow is not None:
            self._nswindow.minimize_(None)

    def maximize(self):
        if self._nswindow is not None:
            self._nswindow.zoom_(None)

    def set_vsync(self, vsync):
        pass

    def set_mouse_platform_visible(self, visible=None):
        if visible is None:
            visible = self._mouse_visible
        if visible:
            NSCursor.unhide()
        else:
            NSCursor.hide()

    def set_exclusive_mouse(self, exclusive=True):
        pass

    def set_exclusive_keyboard(self, exclusive=True):
        # http://developer.apple.com/mac/library/technotes/tn2002/tn2062.html
        pass
