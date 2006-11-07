#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import pprint
import sys

from pyglet.window.event import WindowEventHandler
import pyglet.window.key

# List of contexts currently in use, so we can create new contexts that
# share objects with.  Remember to remove from this list when context is
# destroyed.
_active_contexts = []

CONTEXT_SHARE_NONE = None
CONTEXT_SHARE_EXISTING = 1

LOCATION_DEFAULT = None

class WindowException(Exception):
    pass

class BaseScreen(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def __repr__(self):
        return '%s(width=%d, height=%d)' % \
            (self.__class__.__name__, self.width, self.height)

class BaseGLConfig(object):
    def get_gl_attribute(self, name):
        return self.get_gl_attributes().get(name, None)

    def get_gl_attributes():
        raise NotImplementedError()

    def __repr__(self):
        prefix = '%s(' % self.__class__.__name__
        return '%s%s)' % (prefix, 
                          pprint.pformat(self.get_gl_attributes(),
                                         indent=len(prefix)))

class BaseGLContext(object):
    def __repr__(self):
        return '%s()' % self.__class__.__name__

    def destroy(self):
        _active_contexts.remove(self)

class BaseWindow(WindowEventHandler):
    _context = None
    _config = None

    # Used to restore window size and position after fullscreen
    _windowed_size = None
    _windowed_location = None

    def __init__(self, config, context, width, height):
        WindowEventHandler.__init__(self)
        self.width = width
        self.height = height
        self._config = config
        self._context = context

    def get_context(self):
        return self._context

    def get_config(self):
        return self._config

    def set_caption(self, caption):
        self.caption = caption

    def get_caption(self):
        return self.caption

    def get_context(self):
        return self._context

    def get_config(self):
        return self._config

    def set_minimum_size(self, width, height):
        raise NotImplementedError()

    def set_maximum_size(self, width, height):
        raise NotImplementedError()

    def set_size(self, width, height):
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

        caption = self.get_caption()

        factory = get_factory()
        factory.set_gl_attributes(self.get_config().get_gl_attributes())
        if width and height:
            factory.set_size(width, height)
        elif fullscreen:
            self._windowed_size = self.width, self.height
            self._windowed_location = self.get_location()
            screen = factory.get_screen()
            factory.set_size(screen.width, screen.height)
        elif self._windowed_size:
            factory.set_size(*self._windowed_size)
            factory.set_location(*self._windowed_location)
        factory.set_fullscreen(fullscreen)
        factory.set_context_share(self.get_context())
        factory.replace_window(self)
        self._fullscreen = fullscreen
        self.set_caption(caption)

    def set_exclusive_mouse(self, exclusive=True):
        raise NotImplementedError()

    def set_exclusive_keyboard(self, exclusive=True):
        raise NotImplementedError()

class BasePlatform(object):
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

    def create_window(self, factory):
        '''Subclasses must override to create and return a BaseWindow.
        '''
        raise NotImplementedError()

    def replace_window(self, factory, window):
        '''Subclasses must override to update a window with the factory
        configuration.
        '''
        raise NotImplementedError()

# This is actually following Builder pattern (GoF) now, not AbstractFactory,
# but not worth a name change.
class WindowFactory(object):
    _config = None
    _config_attributes = {}
    _context = None
    _context_share = CONTEXT_SHARE_EXISTING

    _screen = None
    _fullscreen = False
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

    def create_window(self):
        # Create a window based on factory attributes.
        window = self._platform.create_window(self)
        window.switch_to()

        # We should reset now in case someone tries to use the
        # same factory to create more than one window.
        self._context = None

        return window

    def replace_window(self, window):
        # Transform an existing window to use a new configuration.
        self._platform.replace_window(self, window)
        self._context = None
        window.switch_to()

def get_platform():
    return _platform

def get_factory():
    return WindowFactory(_platform)

# Convenience functions for creating simple window with default parameters.
def create(width, height, fullscreen=False):
    factory = get_factory()
    factory.set_size(width, height)
    factory.set_fullscreen(fullscreen)
    factory.set_gl_attribute('doublebuffer', True)
    sys.argv = factory.set_arguments(sys.argv)
    window = factory.create_window()
    window.set_caption(sys.argv[0])
    return window

# Try to determine which platform to use.
if sys.platform == 'darwin':
    from pyglet.window.carbon import CarbonPlatform
    _platform = CarbonPlatform()
elif sys.platform == 'win32':
    from pyglet.window.win32 import Win32Platform
    _platform = Win32Platform()
else:
    from pyglet.window.xlib import XlibPlatform
    _platform = XlibPlatform()
   
