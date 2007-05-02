#!/usr/bin/env python

'''Events for `pyglet.window`.

See `WindowEventHandler` for a description of the window event types.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from pyglet.window import key
from pyglet.window import mouse
from pyglet.event import EventDispatcher

class WindowEventDispatcher(EventDispatcher):
    pass

# symbolic names for the window events
EVENT_KEY_PRESS = WindowEventDispatcher.register_event_type('on_key_press')
EVENT_KEY_RELEASE = WindowEventDispatcher.register_event_type('on_key_release')
EVENT_TEXT = WindowEventDispatcher.register_event_type('on_text')
EVENT_MOUSE_MOTION = \
    WindowEventDispatcher.register_event_type('on_mouse_motion')
EVENT_MOUSE_DRAG = WindowEventDispatcher.register_event_type('on_mouse_drag')
EVENT_MOUSE_PRESS = WindowEventDispatcher.register_event_type('on_mouse_press')
EVENT_MOUSE_RELEASE = \
    WindowEventDispatcher.register_event_type('on_mouse_release')
EVENT_MOUSE_SCROLL = \
    WindowEventDispatcher.register_event_type('on_mouse_scroll')
EVENT_MOUSE_ENTER = WindowEventDispatcher.register_event_type('on_mouse_enter')
EVENT_MOUSE_LEAVE = WindowEventDispatcher.register_event_type('on_mouse_leave')
EVENT_CLOSE = WindowEventDispatcher.register_event_type('on_close')
EVENT_EXPOSE = WindowEventDispatcher.register_event_type('on_expose')
EVENT_RESIZE = WindowEventDispatcher.register_event_type('on_resize')
EVENT_MOVE = WindowEventDispatcher.register_event_type('on_move')
EVENT_ACTIVATE = WindowEventDispatcher.register_event_type('on_activate')
EVENT_DEACTIVATE = WindowEventDispatcher.register_event_type('on_deactivate')
EVENT_SHOW = WindowEventDispatcher.register_event_type('on_show')
EVENT_HIDE = WindowEventDispatcher.register_event_type('on_hide')
EVENT_CONTEXT_LOST = \
    WindowEventDispatcher.register_event_type('on_context_lost')
EVENT_CONTEXT_STATE_LOST = \
    WindowEventDispatcher.register_event_type('on_context_state_lost')

class WindowEventHandler(object):
    '''The abstract window event handler.

    This class contains all method definitions for window event handlers.  The
    methods do nothing; this class merely serves as documentation for the
    arguments that each handler expects.
    '''

    def on_key_press(self, symbol, modifiers):
        '''A key on the keyboard was pressed (and held down).

        :Parameters:
            `symbol` : int
                The key symbol pressed.
            `modifiers` : int
                Bitwise combination of the key modifiers active.

        '''

    def on_key_release(self, symbol, modifiers):
        '''A key on the keyboard was released.

        :Parameters:
            `symbol` : int
                The key symbol pressed.
            `modifiers` : int
                Bitwise combination of the key modifiers active.

        '''

    def on_text(self, text):
        '''The user input some text.

        Typically this is called after `on_key_press` and before
        `on_key_release`, but may also be called multiple times if the key is
        held down (key repeating); or called without key presses if another
        input method was used (e.g., a pen input).

        You should always use this method for interpreting text, as the
        key symbols often have complex mappings to their unicode
        representation which this event takes care of.

        :Parameters:
            `text` : unicode
                The text entered by the user.

        '''


    def on_mouse_motion(self, x, y, dx, dy):
        '''The mouse was moved with no buttons held down.

        :Parameters:
            `x` : float
                Distance in pixels from the left edge of the window.
            `y`: float
                Distance in pixels from the bottom edge of the window.
            `dx` : float
                Relative X position from the previous mouse position.
            `dy` : float
                Relative Y position from the previous mouse position.

        '''

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        '''The mouse was moved with one or more mouse buttons pressed.

        This event will continue to be fired even if the mouse leaves
        the window, so long as the drag buttons are continuously held down.

        :Parameters:
            `x` : float
                Distance in pixels from the left edge of the window.
            `y`: float
                Distance in pixels from the bottom edge of the window.
            `dx` : float
                Relative X position from the previous mouse position.
            `dy` : float
                Relative Y position from the previous mouse position.
            `buttons` : int
                Bitwise combination of the mouse buttons currently pressed.
            `modifiers` : int
                Bitwise combination of any keyboard modifiers currently
                active.

        '''

    def on_mouse_press(self, button, x, y, modifiers):
        '''A mouse button was pressed (and held down).

        :Parameters:
            `button` : int
                The mouse button that was pressed.
            `x` : float
                Distance in pixels from the left edge of the window.
            `y`: float
                Distance in pixels from the bottom edge of the window.
            `modifiers` : int
                Bitwise combination of any keyboard modifiers currently
                active.
            
        '''

    def on_mouse_release(self, button, x, y, modifiers):
        '''A mouse button was released.

        :Parameters:
            `button` : int
                The mouse button that was released.
            `x` : float
                Distance in pixels from the left edge of the window.
            `y`: float
                Distance in pixels from the bottom edge of the window.
            `modifiers` : int
                Bitwise combination of any keyboard modifiers currently
                active.
        '''
            
    def on_mouse_scroll(self, dx, dy):
        '''The mouse wheel was scrolled.

        Note that most mice have only a vertical scroll wheel, so `dx` is
        usually 0.  An exception to this is the Apple Mighty Mouse, which
        has a mouse ball in place of the wheel which allows both `dx` and `dy`
        movement.

        :Parameters:
            `dx` : int
                Number of "clicks" towards the right (left if negative).
            `dy` : int
                Number of "clicks" upwards (downards if negative).

        '''

    def on_close(self):
        '''The user attempted to close the window.

        This event can be triggered by clicking on the "X" control box in
        the window title bar, or by some other platform-dependent manner.
        '''

    def on_mouse_enter(self, x, y):
        '''The mouse was moved into the window.

        This event will not be trigged if the mouse is currently being
        dragged.

        :Parameters:
            `x` : float
                Distance in pixels from the left edge of the window.
            `y`: float
                Distance in pixels from the bottom edge of the window.
        '''

    def on_mouse_leave(self, x, y):
        '''The mouse was moved outside of the window.

        This event will not be trigged if the mouse is currently being
        dragged.  Note that the coordinates of the mouse pointer will be
        outside of the window rectangle.

        :Parameters:
            `x` : float
                Distance in pixels from the left edge of the window.
            `y`: float
                Distance in pixels from the bottom edge of the window.
        '''

    def on_expose(self):
        '''A portion of the window needs to be redrawn.

        This event is triggered when the window first appears, and any time
        the contents of the window is invalidated due to another window
        obscuring it.

        There is no way to determine which portion of the window needs
        redrawing.  Note that the use of this method is becoming increasingly
        uncommon, as newer window managers composite windows automatically and
        keep a backing store of the window contents.
        '''

    def on_resize(self, width, height):
        '''The window was resized.

        :Parameters:
            `width` : int
                The new width of the window, in pixels.
            `height` : int
                The new height of the window, in pixels.

        '''

    def on_move(self, x, y):
        '''The window was moved.

        :Parameters:
            `x` : int
                Distance from the left edge of the screen to the left edge
                of the window.
            `y` : int
                Distance from the top edge of the screen to the top edge of
                the window.  Note that this is one of few methods in pyglet
                which use a Y-down coordinate system.

        '''

    def on_activate(self):
        '''The window was activated.

        This event can be triggered by clicking on the title bar, bringing
        it to the foreground; or by some platform-specific method.

        When a window is "active" it has the keyboard focus.
        '''

    def on_deactivate(self):
        '''The window was deactivated.

        This event can be triggered by clicking on another application window.
        When a window is deactivated it no longer has the keyboard focus.
        '''

    def on_show(self):
        '''The window was shown.

        This event is triggered when a window is restored after being
        minimised, or after being displayed for the first time.
        '''

    def on_hide(self):
        '''The window was hidden.

        This event is triggered when a window is minimised or (on Mac OS X)
        hidden by the user.
        '''

    def on_context_lost(self):
        '''The window's GL context was lost.
        
        When the context is lost no more GL methods can be called until it is
        recreated.  This is a rare event, triggered perhaps by the user
        switching to an incompatible video mode.  When it occurs, an
        application will need to reload all objects (display lists, texture
        objects, shaders) as well as restore the GL state.
        '''

    def on_context_state_lost(self):
        '''The state of the window's GL context was lost.

        pyglet may sometimes need to recreate the window's GL context if the
        window is moved to another video device, or between fullscreen or
        windowed mode.  In this case it will try to share the objects (display
        lists, texture objects, shaders) between the old and new contexts.  If
        this is possible, only the current state of the GL context is lost,
        and the application should simply restore state.
        '''

class WindowExitHandler(object):
    '''Determine if the window should be closed.

    This event handler watches for the ESC key or the window close event
    and sets `self.has_exit` to True when either is pressed.  An instance
    of this class is automatically attached to all new `pyglet.window.Window`
    objects.

    :Ivariables:
        `has_exit` : bool
            True if the user wants to close the window.

    '''
    has_exit = False

    def on_close(self):
        self.has_exit = True

    def on_key_press(self, symbol, modifiers):
        if symbol == key.ESCAPE:
            self.has_exit = True

class WindowEventLogger(object):
    '''Print all events to a file.

    When this event handler is added to a window it prints out all events
    and their parameters; useful for debugging or discovering which events
    you need to handle.

    Example::

        win = window.Window()
        win.push_handlers(WindowEventLogger())

    '''
    def __init__(self, logfile=None):
        '''Create a `WindowEventLogger` which writes to `logfile`.

        :Parameters:
            `logfile` : file-like object
                The file to write to.  If unspecified, stdout will be used.

        '''
        if logfile is None:
            import sys
            logfile = sys.stdout
        self.file = logfile

    def on_key_press(self, symbol, modifiers):
        print >> self.file, 'on_key_press(symbol=%s, modifiers=%s)' % (
            key.symbol_string(symbol), key.modifiers_string(modifiers))

    def on_key_release(self, symbol, modifiers):
        print >> self.file, 'on_key_release(symbol=%s, modifiers=%s)' % (
            key.symbol_string(symbol), key.modifiers_string(modifiers))

    def on_text(self, text):
        print >> self.file, 'on_text(text=%r)' % text

    def on_mouse_motion(self, x, y, dx, dy):
        print >> self.file, 'on_mouse_motion(x=%d, y=%d, dx=%d, dy=%d)' % (
            x, y, dx, dy)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        print >> self.file, 'on_mouse_drag(x=%d, y=%d, dx=%d, dy=%d, '\
                            'buttons=%s, modifiers=%s)' % (
              x, y, dx, dy, 
              mouse.buttons_string(buttons), key.modifiers_string(modifiers))

    def on_mouse_press(self, button, x, y, modifiers):
        print >> self.file, 'on_mouse_press(button=%r, x=%d, y=%d, '\
                            'modifiers=%s)' % (
            mouse.buttons_string(button), x, y, 
            key.modifiers_string(modifiers))

    def on_mouse_release(self, button, x, y, modifiers):
        print >> self.file, 'on_mouse_release(button=%r, x=%d, y=%d, '\
                            'modifiers=%s)' % (
            mouse.buttons_string(button), x, y, 
            key.modifiers_string(modifiers))

    def on_mouse_scroll(self, dx, dy):
        print >> self.file, 'on_mouse_scroll(dx=%f, dy=%f)' % (dx, dy)

    def on_close(self):
        print >> self.file, 'on_destroy()'

    def on_mouse_enter(self, x, y):
        print >> self.file, 'on_mouse_enter(x=%d, y=%d)' % (x, y)

    def on_mouse_leave(self, x, y):
        print >> self.file, 'on_mouse_leave(x=%d, y=%d)' % (x, y)

    def on_expose(self):
        print >> self.file, 'on_expose()'

    def on_resize(self, width, height):
        print >> self.file, 'on_resize(width=%d, height=%d)' % (width, height)

    def on_move(self, x, y):
        print >> self.file, 'on_move(x=%d, y=%d)' % (x, y)

    def on_activate(self):
        print >> self.file, 'on_activate()'

    def on_deactivate(self):
        print >> self.file, 'on_deactivate()'

    def on_show(self):
        print >> self.file, 'on_show()'

    def on_hide(self):
        print >> self.file, 'on_hide()'

    def on_context_lost(self):
        print >> self.file, 'on_context_lost()'

    def on_context_state_lost(self):
        print >> self.file, 'on_context_state_lost()'
