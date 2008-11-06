#!/usr/bin/python
# $Id:$

from pyglet import app
from pyglet import gl

class Display(object):
    '''A display device supporting one or more screens.

    :Ivariables:
        `name` : str
            Name of this display, if applicable.
        `x_screen` : int
            The X11 screen number of this display, if applicable.

    :since: pyglet 1.2
    '''
    name = None
    x_screen = None

    def __init__(self, name=None, x_screen=None):
        '''Create a display connection for the given name and screen.

        On X11, `name` is of the form ``"hostname:display"``, where the
        default is usually ``":1"``.  On X11, `x_screen` gives the X screen
        number to use with this display.  A pyglet display can only be used
        with one X screen; open multiple display connections to access
        multiple X screens.  
        
        Note that TwinView, Xinerama, xrandr and other extensions present
        multiple monitors on a single X screen; this is usually the preferred
        mechanism for working with multiple monitors under X11 and allows each
        screen to be accessed through a single pyglet `Display`.

        On platforms other than X11, `name` and `x_screen` are ignored; there is
        only a single display device on these systems.

        :Parameters:
            `name` : str
                The name of the display to connect to.
            `x_screen` : int
                The X11 screen number to use.

        '''
        app.displays.add(self)

    def get_screens(self):
        '''Get the available screens.

        A typical multi-monitor workstation comprises one `Display` with
        multiple `Screen` s.  This method returns a list of screens which
        can be enumerated to select one for full-screen display.

        For the purposes of creating an OpenGL config, the default screen
        will suffice.

        :rtype: list of `Screen`
        '''
        raise NotImplementedError('abstract')    

    def get_default_screen(self):
        '''Get the default screen as specified by the user's operating system
        preferences.

        :rtype: `Screen`
        '''
        return self.get_screens()[0]

    def get_windows(self):
        '''Get the windows currently attached to this display.

        :rtype: sequence of `Window`
        '''
        return [window for window in windows if window.display is self]

class Screen(object):
    '''A virtual monitor that supports fullscreen windows.

    Screens typically map onto a physical display such as a
    monitor, television or projector.  Selecting a screen for a window
    has no effect unless the window is made fullscreen, in which case
    the window will fill only that particular virtual screen.

    The `width` and `height` attributes of a screen give the current
    resolution of the screen.  The `x` and `y` attributes give the global
    location of the top-left corner of the screen.  This is useful for
    determining if screens arranged above or next to one another.  
    
    Use `Display.get_screens` or `Display.get_default_screen` to obtain an
    instance of this class.

    :Ivariables:
        `display` : `Display`
            Display this screen belongs to.
        `x` : int
            Left edge of the screen on the virtual desktop.
        `y` : int
            Top edge of the screen on the virtual desktop.
        `width` : int
            Width of the screen, in pixels.
        `height` : int
            Height of the screen, in pixels.

    '''

    def __init__(self, display, x, y, width, height):
        self.display = display
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def __repr__(self):
        return '%s(x=%d, y=%d, width=%d, height=%d)' % \
            (self.__class__.__name__, self.x, self.y, self.width, self.height)

    def get_best_config(self, template=None):
        '''Get the best available GL config.

        Any required attributes can be specified in `template`.  If
        no configuration matches the template, `NoSuchConfigException` will
        be raised.

        :deprecated: Use `pyglet.gl.Config.match`.

        :Parameters:
            `template` : `pyglet.gl.Config`
                A configuration with desired attributes filled in.

        :rtype: `pyglet.gl.Config`
        :return: A configuration supported by the platform that best
            fulfils the needs described by the template.
        '''
        if template is None:
            template = gl.Config()
        configs = self.get_matching_configs(template)
        if not configs:
            raise gl.NoSuchConfigException()
        return configs[0]

    def get_matching_configs(self, template):
        '''Get a list of configs that match a specification.

        Any attributes specified in `template` will have values equal
        to or greater in each returned config.  If no configs satisfy
        the template, an empty list is returned.

        :deprecated: Use `pyglet.gl.Config.match`.

        :Parameters:
            `template` : `pyglet.gl.Config`
                A configuration with desired attributes filled in.

        :rtype: list of `pyglet.gl.Config`
        :return: A list of matching configs.
        '''
        raise NotImplementedError('abstract')

    def get_modes(self):
        '''
        TODO doc
        '''
        raise NotImplementedError('abstract')

class ScreenMode(object):
    '''TODO doc
    '''

    width = None
    height = None
    depth = None
    rate = None

    def __init__(self, screen):
        self.screen = screen

    def __repr__(self):
        return '%s(width=%r, height=%r, depth=%r, rate=%r)' % (
            self.__class__.__name__, 
            self.width, self.height, self.depth, self.rate)

class Canvas(object):
    '''TODO doc

    Canvas is an abstract base class.  Windows provide their drawing area as a
    canvas, for example.

    :since: pyglet 1.2
    '''
    def __init__(self, display):
        self.display = display
