#!/usr/bin/env python

'''
Platform-independent windows and events.
===========================================================================

This module allows applications to create and display windows with an
OpenGL context on Windows, OS X and Linux.  Windows can be created with
a variety of border styles or set fullscreen, and these properties can
be changed while the window is visible.

You can register event handlers for keyboard, mouse and window events.
For games and kiosks you can also restrict the input to your windows,
for example disabling users from switching away from the application
with certain key combinations or capturing and hiding the mouse.

This module depends on `pyglet.gl`, `pyglet.event` and `pyglet.image`.

---------------
Getting Started
---------------

Call the Window constructor to create a new window:

    >>> from pyglet.window import Window
    >>> win = Window(width=640, height=480, fullscreen=False)
    >>> 

Windows are subclasses of EventDispatcher, so you can push event handlers
onto them::

    >>> class MyEvents:
    ...     def on_key_press(self, symbol, modifiers):
    ...         print 'Pressed key %d' % symbol
    ...
    >>> win.push_handlers(MyEvents())
    >>>

Windows automatically set an instance of WindowExitHandler, which sets a flag
has_exit if the window is closed or the ESC key is pressed.

The easiest way to find out the events that are available and their
parameters, use the WindowEventLogger, which will print out all events
received by the window to the terminal::

    >>> win.push_handler(pyglet.window.event.WindowEventLogger())
    >>>

For a complete list of events, see the `pyglet.window.event` documentation.

Each window has its own OpenGL buffer and context.  When you create a
window it will be set as the current context automatically, so you can start
using OpenGL functions straight away.  Use the window's `flip` method to
make the back-buffer visible::

    >>> from pyglet.gl import *
    >>> glClear(GL_COLOR_BUFFER_BIT)
    >>> win.flip()
    >>>

If you are using more than one window, you will need to explicitly select
which context to send OpenGL commands to using the `switch_to` method::

    >>> window1.switch_to()
    >>> gl... # Commands for window1
    >>> window1.flip()
    >>> window2.switch_to()
    >>> gl... # Commands for window2
    >>> window2.flip()
    >>>

----------------
Creating Windows
----------------

The Window constructor simplifies the multi-step process involved in
creating a window.  It accepts the following optional keyword arguments:

width, height
    The size of the window to create.  These are ignored if the window is
    fullscreen.
fullscreen
    `True` to create a fullscreen window on the default screen.  Defaults
    to False.
visible
    By default, windows are shown as soon as they are created.  To register
    events and set properties of the window first, set this to `False`.
    You can then manually show the window using the `set_visible` method.
doublebuffer
    Use double-buffering to eliminate flicker and tearing.  Enabled by
    default.
vsync
    Enables syncing double-buffered display swaps to the monitor's
    video frame.

You can also specify any other OpenGL attributes supported by the platform;
these are listed elsewhere.  (TODO: where?)

-------------------
Using WindowFactory
-------------------

For complete flexibility in creating windows, use the WindowFactory to
set up your window step by step.  Obtain a WindowFactory using the
`get_factory` function::

    >>> factory = pyglet.window.get_factory()
    >>>

Call methods on the factory to set up the initial attributes of the window.
For example::

    >>> factory.set_fullscreen(False)
    >>> factory.set_size(640, 480)
    >>>

You can get a list of the available screens (for example, on a multi-monitor
system), and then select one to use::

    >>> screens = factory.get_screens()
    >>> factory.set_screen(screens[0])      # Use the default screen
    >>>

When you have set the screen (or want to use the default screen) and GL
attributes, you can get a list of available GL configurations that
support the attributes you specified::

    >>> configs = factory.get_matching_configs()
    >>> factory.set_config(configs[0])      # Set the first matching config

If the requested attributes cannot be satisfied by the device (for example,
requesting a buffer size that's too large), no matching configs will be
returned, and you should revise the attributes and try again.  Some platforms
will return multiple matching configurations from which you can pick and
choose from (by default, the first matching config is used).

Once a config has been set, or you will use the default, you can create
a GL context::

    >>> context = factory.get_context()
    >>>

Contexts can optionally share display lists, shaders and textures with another
context.  By default the WindowFactory will try to share the context with the
most recently created context, if any.  You can override this explicitly
before calling `get_context`::

    >>> factory.set_context_share(my_context)
    >>> context = factory.get_context()
    >>>

Finally, create the window with the attributes, config and context you have
set::

    >>> window = factory.create_window()
    >>>

The `create_window` method can optionally take the base class for the window,
which defaults to `get_platform().get_window_class()`.

You can create multiple windows with the same configuration but different
contexts by repeatedly calling `create_window`.

-----------------
Modifying Windows
-----------------

You can modify an existing window (for example, to make it fullscreen or
windowed, or to change a GL attribute) by calling the `create` method
with a properly configured factory::

    >>> window.create(factory)
    >>>

Note that in some cases the context may need to be recreated, and state
and/or objects may be lost.

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import pprint
import sys

from pyglet.gl import *
from pyglet.window.event import WindowEventDispatcher, WindowExitHandler
from pyglet import projection
import pyglet.window.key

# List of contexts currently in use, so we can create new contexts that
# share objects with.  Remember to remove from this list when context is
# destroyed.
_active_contexts = []
_current_context = None

# Constants for WindowFactory.set_context_share
CONTEXT_SHARE_NONE = None           # Do not share the created context.
CONTEXT_SHARE_EXISTING = 1          # Share the context with any other 
                                    # arbitrary compatible context.

# Constants for WindowFactory.set_location
LOCATION_DEFAULT = None             # No preference for window location.

# Constants for Window.get_system_mouse_cursor
CURSOR_DEFAULT = None
CURSOR_CROSSHAIR = 'crosshair'
CURSOR_HAND = 'hand'
CURSOR_HELP = 'help'
CURSOR_NO = 'no'
CURSOR_SIZE = 'size'
CURSOR_SIZE_UP = 'size_up'
CURSOR_SIZE_UP_RIGHT = 'size_up_right'
CURSOR_SIZE_RIGHT = 'size_right'
CURSOR_SIZE_DOWN_RIGHT = 'size_down_right'
CURSOR_SIZE_DOWN = 'size_down'
CURSOR_SIZE_DOWN_LEFT = 'size_down_left'
CURSOR_SIZE_LEFT = 'size_left'
CURSOR_SIZE_UP_LEFT = 'size_up_left'
CURSOR_SIZE_UP_DOWN = 'size_up_down'
CURSOR_SIZE_LEFT_RIGHT = 'size_left_right'
CURSOR_TEXT = 'text'
CURSOR_WAIT = 'wait'
CURSOR_WAIT_ARROW = 'wait_arrow'

WINDOW_STYLE_DEFAULT = None
WINDOW_STYLE_DIALOG = 'dialog'
WINDOW_STYLE_TOOL = 'tool'
WINDOW_STYLE_BORDERLESS = 'borderless'

def get_current_context():
    return _current_context

class WindowException(Exception):
    pass

class BaseScreen(object):
    '''Virtual screen that supports windows and/or fullscreen.

    Virtual screens typically map onto a physical display such as a
    from pyglet.gl import *
    monitor, television or projector.  Selecting a screen for a window
    has no effect unless the window is made fullscreen, in which case
    the window will fill only that particular virtual screen.

    The `width` and `height` attributes of a screen give the current
    resolution of the display (which can possibly be changed).  The
    `x` and `y` attributes give the global location of the top-left
    corner of the screen.  This is useful for determining if screens
    arranged above or next to one another.  
    
    You should not rely on the origin to give the placement of moniters. 
    For example, an X server with two displays without Xinerama enabled
    will present two logically separate screens with no relation to each
    other.
    '''

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def __repr__(self):
        return '%s(x=%d, y=%d, width=%d, height=%d)' % \
            (self.__class__.__name__, self.x, self.y, self.width, self.height)

    '''
    Proposed interface for switching resolution:

    def get_modes(self):
        raise NotImplementedError()

    def set_mode(self, mode):
        raise NotImplementedError()
    '''

class BaseGLConfig(object):
    '''Graphics configuration.

    A GLConfig stores the preferences for OpenGL attributes such as the
    number of auxilliary buffers, size of the colour and depth buffers,
    double buffering, stencilling, multi- and super-sampling, and so on.

    Different platforms support a different set of attributes, so these
    are set with a string key and a value which is integer or boolean.
    '''

    def get_gl_attribute(self, name):
        '''Get the value of a GL attribute.

        If the attribute has not been specified, None will be returned,
        otherwise the result will be an integer.
        '''
        return self.get_gl_attributes().get(name, None)

    def get_gl_attributes():
        '''Get a dict of all GL attributes set.'''
        raise NotImplementedError()

    def __repr__(self):
        prefix = '%s(' % self.__class__.__name__
        return '%s%s)' % (prefix, 
                          pprint.pformat(self.get_gl_attributes(),
                                         indent=len(prefix)))

class GLSharedObjectSpace(object):
    pass

class BaseGLContext(object):
    '''OpenGL context for drawing.

    Windows in pyglet each have their own GL context.  This class boxes
    the context in a platform-independent manner.  Applications will have
    no need to deal with contexts directly.
    '''

    # Used for error checking, True if currently within a glBegin/End block.
    # Ignored if error checking is disabled.
    gl_begin = False

    def __init__(self, context_share=None):
        if context_share:
            self._shared_object_space = context_share.get_shared_object_space()
        else:
            self._shared_object_space = GLSharedObjectSpace()

    
    def __repr__(self):
        return '%s()' % self.__class__.__name__

    def set_current(self):
        global _current_context
        _current_context = self

    def destroy(self):
        '''Release the context.

        The context will not be useable after being destroyed.  Each platform
        has its own convention for releasing the context and the buffer(s)
        that depend on it in the correct order; this should never be called
        by an application.
        '''
        global _current_context
        _active_contexts.remove(self)
        _current_context = None

    def get_shared_object_space(self):
        return self._shared_object_space

class MouseCursor(object):
    drawable = True     # if True, draw method is called each frame
    def draw(self, x, y):
        raise NotImplementedError('abstract')

class DefaultMouseCursor(MouseCursor):
    drawable = False

class ImageMouseCursor(MouseCursor):
    drawable = True
    def __init__(self, image, hot_x, hot_y):
        self.texture = image.texture
        self.hot_x = hot_x
        self.hot_y = hot_y

    def draw(self, x, y):
        glPushAttrib(GL_ENABLE_BIT)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self.texture.blit(x - self.hot_x, y - self.hot_y, 0)
        glPopAttrib()

class BaseWindow(WindowEventDispatcher, WindowExitHandler):
    '''Platform-independent application window.

    A window is a "heavyweight" object occupying operating system resources.
    The "client" or "content" area of a window is filled entirely with
    an OpenGL viewport.  Applications have no access to operating system
    widgets or controls; all rendering must be done via OpenGL.

    Windows may appear as floating regions or can be set to fill an entire
    screen (fullscreen).  When floating, windows may appear borderless or
    decorated with a platform-specific frame (including, for example, the
    title bar, minimize and close buttons, resize handles, and so on).

    While it is possible to set the location of a window, it is recommended
    that applications allow the platform to place it according to local
    conventions.  This will ensure it is not obscured by other windows,
    and appears on an appropriate screen for the user.

    To render into a window, you must first call `switch_to`, to make
    it the current OpenGL context.  If you use only one window in the
    application, there is no need to do this.
    '''

    _context = None
    _config = None

    # Used to restore window size and position after fullscreen
    _windowed_size = None
    _windowed_location = None

    _resizable = False
    _style = WINDOW_STYLE_DEFAULT

    # Subclasses should update these after relevant events
    _mouse_cursor = DefaultMouseCursor()
    _mouse_x = 0
    _mouse_y = 0
    _mouse_visible = True
    _mouse_exclusive = False
    _mouse_in_window = True
 
    def __init__(self):
        WindowEventDispatcher.__init__(self)

    def create(self, factory):
        self._config = factory.get_config()
        self._context = factory.get_context()
        self._fullscreen = factory.get_fullscreen()

    def close(self):
        self._context.destroy()
        self._config = None
        self._context = None

    def switch_to(self):
        raise NotImplementedError()

    def draw_mouse_cursor(self):
        # Draw mouse cursor if set and visible.
        # XXX leaves state in modelview regardless of starting state
        if (self._mouse_cursor.drawable and 
            self._mouse_visible and 
            self._mouse_in_window):
            glMatrixMode(GL_PROJECTION)
            glPushMatrix()
            glLoadIdentity()
            glOrtho(0, self.width, 0, self.height, -1, 1)

            glMatrixMode(GL_MODELVIEW)
            glPushMatrix()
            glLoadIdentity()

            self._mouse_cursor.draw(self._mouse_x, self._mouse_y)

            glMatrixMode(GL_PROJECTION)
            glPopMatrix()

            glMatrixMode(GL_MODELVIEW)
            glPopMatrix()

    def get_context(self):
        return self._context

    def get_config(self):
        return self._config

    def set_caption(self, caption):
        self.caption = caption

    def get_caption(self):
        return self.caption

    def set_minimum_size(self, width, height):
        raise NotImplementedError()

    def set_maximum_size(self, width, height):
        raise NotImplementedError()

    def set_size(self, width, height):
        raise NotImplementedError()

    def get_size(self):
        raise NotImplementedError()

    def set_location(self, x, y):
        raise NotImplementedError()

    def get_location(self):
        raise NotImplementedError()

    def activate(self):
        raise NotImplementedError()

    def set_visible(self, visible=True):    
        raise NotImplementedError()

    def minimize(self):
        raise NotImplementedError()

    def maximize(self):
        raise NotImplementedError()
        
    def set_fullscreen(self, fullscreen=True, width=None, height=None):
        if fullscreen == self._fullscreen:
            return

        factory = get_factory()
        factory.set_gl_attributes(self.get_config().get_gl_attributes())
        if width and height:
            factory.set_size(width, height)
        elif fullscreen:
            self._windowed_size = self.get_size()
            self._windowed_location = self.get_location()
            screen = factory.get_screen()
            factory.set_size(screen.width, screen.height)
            factory.set_location(screen.x, screen.y)
        elif self._windowed_size:
            factory.set_size(*self._windowed_size)
            factory.set_location(*self._windowed_location)
        factory.set_fullscreen(fullscreen)
        factory.set_context_share(self.get_context())
        self.create(factory)
        self.switch_to()
        self.set_visible(True)

    def get_resizable(self):
        return self._resizable

    resizable = property(get_resizable)

    def get_style(self):
        return self._style
    
    style = property(get_style)

    def get_vsync(self):
        return None

    def set_vsync(self, vsync):
        pass

    def set_mouse_visible(self, visible=True):
        self._mouse_visible = visible
        self.set_mouse_platform_visible()

    def set_mouse_platform_visible(self, platform_visible=None):
        '''Set the platform-drawn mouse cursor visibility.  This is called
        automatically after changing the mouse cursor or exclusive mode.

        Applications should not normally need to call this method, see
        `set_mouse_visible` instead.

        :Parameters:
            `platform_visible` : bool or None
                If None, sets platform visibility to the required visibility
                for the current exclusive mode and cursor type.  Otherwise,
                a bool value will override and force a visibility.

        '''
        raise NotImplementedError()

    def set_mouse_cursor(self, cursor=None):
        if cursor is None:
            cursor = DefaultMouseCursor()
        self._mouse_cursor = cursor
        self.set_mouse_platform_visible()

    def get_mouse_cursor(self):
        return self._mouse_cursor

    def set_exclusive_mouse(self, exclusive=True):
        raise NotImplementedError()

    def set_exclusive_keyboard(self, exclusive=True):
        raise NotImplementedError()

    width = property(lambda self: self.get_size()[0],
                     lambda self, width: self.set_size(width, self.height))

    height = property(lambda self: self.get_size()[1],
                      lambda self, height: self.set_size(self.width, height))

    def get_system_mouse_cursor(self, name):
        '''Subclasses must override to return a mouse cursor for the
        given name.

        Valid names are
        * pyglet.window.CURSOR_DEFAULT
        * pyglet.window.CURSOR_WAIT 
        * pyglet.window.CURSOR_TEXT 
        * pyglet.window.CURSOR_CROSS

        :Parameters:
            `name` : str
                Name describing the mouse cursor to return.


        :rtype: MouseCursor
        '''
        raise NotImplementedError()

    def set_icon(self, *images):
        '''Set the window icon.

        If multiple images are provided, one with an appropriate size 
        will be selected (if the correct size is not provided, the image
        will be scaled).

        Useful sizes to provide are 16x16, 32x32, 64x64 (Mac only) and
        128x128 (Mac only).

        :Parameters:
            `images` : sequence of `pyglet.image.AbstractImage`
                List of images to use for the window icon.
        
        '''
        pass

class BasePlatform(object):
    '''Abstraction of platform-specific methods.

    The BasePlatform class is subclassed by each platform to provide
    methods for creating instances of BaseScreen, BaseGLConfig, BaseGLContext
    and BaseWindow.  In each case the constructed object will reflect
    the properties set by the user on a WindowFactory object.
    '''

    # Platform specific abstract methods.
    def get_screens(self, factory):
        '''Subclasses must override to return a list of BaseScreen.

        If multimonitor support is not implemented, return [BaseScreen()]
        (one instance).
        '''
        raise NotImplementedError()

    def create_configs(self, factory):
        '''Subclasses must override to create and return a list of BaseGLConfig.
        '''
        raise NotImplementedError()

    def create_context(self, factory):
        '''Subclasses must override to create and return a BaseGLContext.

        The created context must share with factory.get_context_share() if not
        None.  
        '''
        raise NotImplementedError()

    def get_window_class(self):
        '''Subclasses must override to create and return a subclass of 
        BaseWindow.
        '''
        raise NotImplementedError()

class WindowFactory(object):
    '''Configuration and build pattern for BaseWindow instances.

    This class fulfils two roles: firstly, applications set the desired
    configuration on this factory for later interpretation by the 
    specific Platform.  Secondly, it provides the algorithms necessary
    for constructing windows in stages.

    This is the class that applications work directly with to create
    windows by following these steps:
    
    1. Use pyglet.window.get_factory() to create a new factory
       using the appropriate BasePlatform.  
    2. Set attributes on the factory and (optionally) examine the intermediate
       Screen, GLConfig and GLContext settings.
    3. When ready, pass the factory to a BaseWindow's `create` method
       to apply the factory's settings to the new or existing window.

    '''

    _config = None
    _config_attributes = {}
    _context = None
    _context_share = CONTEXT_SHARE_EXISTING

    _screen = None
    _resizable = False
    _style = WINDOW_STYLE_DEFAULT
    _fullscreen = False
    _vsync = None
    _width = 640
    _height = 480 # Reasonable default size.
    _location = LOCATION_DEFAULT
    _x_display = None
    
    def __init__(self, platform):
        self._platform = platform

    # Window and context attributes, to be set before selecting a config.
    def set_size(self, width, height):
        self._width = width
        self._height = height

    def get_size(self):
        return self._width, self._height

    def set_location(self, x, y):
        self._location = x, y

    def get_location(self):
        return self._location

    def set_fullscreen(self, fullscreen):
        self._fullscreen = fullscreen

    def get_fullscreen(self):
        return self._fullscreen

    def set_resizable(self, resizable):
        self._resizable = resizable

    def get_resizable(self):
        return self._resizable

    def set_style(self, style):
        self._style = style

    def get_style(self):
        return self._style

    def set_vsync(self, vsync):
        self._vsync = vsync

    def get_vsync(self):
        return self._vsync

    def set_gl_attribute(self, name, value):
        '''Set the minimum value of a GL attribute for creating a context.

        Allowable `name`s depend on the platform.  The common ones supported
        on all platforms are:
        
        buffer_size
            Bits per sample, as int (typically 32).
        doublebuffer
            True to create two colour buffers and enable flip() (typically
            True).
        stereo
            True to create left and right colour buffers (typically False).
        red_size, green_size, blue_size, alpha_size
            Size of component per sample, in bits (typically 8).
        depth_size
            Size of depth sample, in bits (typically 24).
        stencil_size
            Size of stencil buffer sample, in bits (typically 8).
        accum_red_size, accum_blue_size, accum_green_size, accum_alpha_size
            Size of accumulation buffer component sizes, in bits (typically
            16).
        multisample, supersample, sample_alpha, sample_buffers, samples
            TODO
        color_float
            TODO

        Unsupported attributes are ignored (see platform-specific
        documentation for more attribute names).
        '''
        self._config_attributes[name] = value

    def set_gl_attributes(self, attributes):
        '''Identical to set_gl_attribute, but set a whole dictionary of
        attributes.
        '''
        for name, value in attributes.items():
            self._config_attributes[name] = value

    def get_gl_attributes(self):
        return self._config_attributes

    def set_context_share(self, context):
        '''Set a context to share display lists and objects with.

        By default the most recently created context will be used as
        the share.  Pass None to this function to share with no 
        existing context.
        '''
        self._context_share = context

    def get_context_share(self):
        # If sharing context objects (the default), find a context to share
        # with.
        if self._context_share is CONTEXT_SHARE_EXISTING:
            self._context_share = self.get_existing_context()

        return self._context_share

    def set_x_display(self, display):
        '''For X11, set the display.  
        
        Normally read from an environment variable or command line.  For
        example::

            set_x_display(':1.0')   # Select second X server.

        On other platforms, has no effect.
        '''
        self._x_display = display

    def get_x_display(self):
        return self._x_display

    def set_arguments(self, args):
        '''Convenience function to set common window attributes from
        the command line.

        Any unrecognized options or arguments are returned as a list.  The
        recognized options are:

         * --width=
         * --height=
         * --fullscreen
         * --no-fullscreen
         * --display=

        '''
        remaining_args = []
        for arg in args:
            if '=' in arg:
                key, value = arg.split('=', 1)
            else:
                key = arg
            if key == '--width':
                self._width = int(value)
            elif key == '--height':
                self._height = int(value)
            elif key == '--fullscreen':
                self._fullscreen = True
            elif key == '--no-fullscreen':
                self._fullscreen = False
            elif key == '--display':
                self.set_x_display(value)
            else:
                remaining_args.append(arg)

        return args
    
    # Multimonitor selection
    def get_screens(self):
        return self._platform.get_screens(self)

    def set_screen(self, screen):
        self._screen = screen

    def get_screen(self):
        # Choose primary screen by default
        if not self._screen:
            screen = self.get_screens()[0]
            self.set_screen(screen)
        return self._screen

    # Creation process.
    def get_matching_configs(self):
        return self._platform.create_configs(self)

    def set_config(self, config):
        self._config = config

    def get_config(self):
        # If no configuration has been decided yet, choose the first
        # compatible one.
        if not self._config:
            configs = self.get_matching_configs()
            if not configs:
                raise WindowException('No matching GL configuration available.')
            self.set_config(configs[0])

        return self._config

    def create_context(self):
        self._context = self._platform.create_context(self)
        _active_contexts.append(self._context)

    def get_existing_context(self):
        if _active_contexts:
            return _active_contexts[-1]
        return None

    def set_context(self, context):
        self._context = context

    def get_context(self):
        if not self._context:
            self.create_context()
        return self._context

    def create_window(self, window_class=None):
        # Create a window based on factory attributes.
        if not window_class:
            window_class = self._platform.get_window_class()
        window = window_class()
        window.create(self)
        window.switch_to()

        # We should reset now in case someone tries to use the
        # same factory to create more than one window.
        self._context = None

        return window

def get_platform():
    '''Get an instance of the BasePlatform most appropriate for this
    system.
    '''
    return _platform

def get_factory():
    '''Create a new WindowFactory which can be used to construct or
    alter windows.
    '''
    return WindowFactory(_platform)


# Try to determine which platform to use.
if sys.platform == 'darwin':
    from pyglet.window.carbon import CarbonPlatform
    _platform = CarbonPlatform()
elif sys.platform in ('win32', 'cygwin'):
    from pyglet.window.win32 import Win32Platform
    _platform = Win32Platform()
else:
    from pyglet.window.xlib import XlibPlatform
    _platform = XlibPlatform()
   

class Window(_platform.get_window_class()):
    def __init__(self, 
                 width=None,
                 height=None,
                 resizable=False,
                 style=WINDOW_STYLE_DEFAULT,
                 fullscreen=False,
                 visible=True,
                 doublebuffer=True,
                 vsync=True,
                 depth_size=24,
                 factory=None,
                 screen=None,
                 **kwargs):

        super(Window, self).__init__()

        if factory is None:
            factory = get_factory()
        if screen is not None:
            factory.set_screen(screen)
        if width or height:
            _width, _height = factory.get_size()
            if not width:
                width = _width
            if not height:
                height = _height
            factory.set_size(width, height)
        factory.set_resizable(resizable)
        factory.set_style(style)
        factory.set_fullscreen(fullscreen)
        factory.set_gl_attribute('doublebuffer', doublebuffer)
        factory.set_gl_attribute('depth_size', depth_size)
        factory.set_vsync(vsync)
        for key, value in kwargs.items():
            factory.set_gl_attribute(key, value)
        sys.argv = factory.set_arguments(sys.argv)

        if fullscreen:
            screen = factory.get_screen()
            factory.set_size(screen.width, screen.height)

        self.create(factory)
        self.set_caption(sys.argv[0])

        self.switch_to()
        self.set_viewport()
        self.set_projection()

        if visible:
            self.set_visible(True)
            self.activate()

    def set_viewport(self):
        self.viewport = projection.WindowViewport(self)

    def set_projection(self):
        self.projection = projection.OrthographicProjection(self.viewport)
        self.projection.apply()

    def on_resize(self, width, height):
        # TODO rearrange this so switch_to not magically called from
        # event handler; wait until user switches, then apply.
        self.switch_to()
        self.projection.apply()

