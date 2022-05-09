# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# Copyright (c) 2008-2022 pyglet contributors
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

"""Windowing and user-interface events.

This module allows applications to create and display windows with an
OpenGL context.  Windows can be created with a variety of border styles
or set fullscreen.

You can register event handlers for keyboard, mouse and window events.
For games and kiosks you can also restrict the input to your windows,
for example disabling users from switching away from the application
with certain key combinations or capturing and hiding the mouse.

Getting started
---------------

Call the Window constructor to create a new window::

    from pyglet.window import Window
    win = Window(width=960, height=540)

Attach your own event handlers::

    @win.event
    def on_key_press(symbol, modifiers):
        # ... handle this event ...

Place drawing code for the window within the `Window.on_draw` event handler::

    @win.event
    def on_draw():
        # ... drawing code ...

Call `pyglet.app.run` to enter the main event loop (by default, this
returns when all open windows are closed)::

    from pyglet import app
    app.run()

Creating a game window
----------------------

Use :py:meth:`~pyglet.window.Window.set_exclusive_mouse` to hide the mouse
cursor and receive relative mouse movement events.  Specify ``fullscreen=True``
as a keyword argument to the :py:class:`~pyglet.window.Window` constructor to
render to the entire screen rather than opening a window::

    win = Window(fullscreen=True)
    win.set_exclusive_mouse()

Working with multiple screens
-----------------------------

By default, fullscreen windows are opened on the primary display (typically
set by the user in their operating system settings).  You can retrieve a list
of attached screens and select one manually if you prefer.  This is useful for
opening a fullscreen window on each screen::

    display = pyglet.canvas.get_display()
    screens = display.get_screens()
    windows = []
    for screen in screens:
        windows.append(window.Window(fullscreen=True, screen=screen))

Specifying a screen has no effect if the window is not fullscreen.

Specifying the OpenGL context properties
----------------------------------------

Each window has its own context which is created when the window is created.
You can specify the properties of the context before it is created
by creating a "template" configuration::

    from pyglet import gl
    # Create template config
    config = gl.Config()
    config.stencil_size = 8
    config.aux_buffers = 4
    # Create a window using this config
    win = window.Window(config=config)

To determine if a given configuration is supported, query the screen (see
above, "Working with multiple screens")::

    configs = screen.get_matching_configs(config)
    if not configs:
        # ... config is not supported
    else:
        win = window.Window(config=configs[0])

"""

import sys
from typing import Tuple

import pyglet

from pyglet import gl
from pyglet.math import Mat4
from pyglet.event import EventDispatcher
from pyglet.window import key, event
from pyglet.util import with_metaclass
from pyglet.graphics import shader


_is_pyglet_doc_run = hasattr(sys, "is_pyglet_doc_run") and sys.is_pyglet_doc_run


class WindowException(Exception):
    """The root exception for all window-related errors."""
    pass


class NoSuchDisplayException(WindowException):
    """An exception indicating the requested display is not available."""
    pass


class NoSuchConfigException(WindowException):
    """An exception indicating the requested configuration is not
    available."""
    pass


class NoSuchScreenModeException(WindowException):
    """An exception indicating the requested screen resolution could not be
    met."""
    pass


class MouseCursorException(WindowException):
    """The root exception for all mouse cursor-related errors."""
    pass


class MouseCursor:
    """An abstract mouse cursor."""

    #: Indicates if the cursor is drawn
    #: using OpenGL, or natively.
    gl_drawable = True
    hw_drawable = False

    def draw(self, x, y):
        """Abstract render method.

        The cursor should be drawn with the "hot" spot at the given
        coordinates.  The projection is set to the pyglet default (i.e.,
        orthographic in window-space), however no other aspects of the
        state can be assumed.

        :Parameters:
            `x` : int
                X coordinate of the mouse pointer's hot spot.
            `y` : int
                Y coordinate of the mouse pointer's hot spot.

        """
        pass


class DefaultMouseCursor(MouseCursor):
    """The default mouse cursor set by the operating system."""
    gl_drawable = False
    hw_drawable = True


class ImageMouseCursor(MouseCursor):
    """A user-defined mouse cursor created from an image.

    Use this class to create your own mouse cursors and assign them
    to windows. Cursors can be drawn by OpenGL, or optionally passed
    to the OS to render natively. There are no restrictions on cursors
    drawn by OpenGL, but natively rendered cursors may have some
    platform limitations (such as color depth, or size). In general,
    reasonably sized cursors will render correctly
    """
    def __init__(self, image, hot_x=0, hot_y=0, acceleration=False):
        """Create a mouse cursor from an image.

        :Parameters:
            `image` : `pyglet.image.AbstractImage`
                Image to use for the mouse cursor.  It must have a
                valid ``texture`` attribute.
            `hot_x` : int
                X coordinate of the "hot" spot in the image relative to the
                image's anchor. May be clamped to the maximum image width
                if ``acceleration=True``.
            `hot_y` : int
                Y coordinate of the "hot" spot in the image, relative to the
                image's anchor. May be clamped to the maximum image height
                if ``acceleration=True``.
            `acceleration` : int
                If True, draw the cursor natively instead of usign OpenGL.
                The image may be downsampled or color reduced to fit the
                platform limitations.
        """
        self.texture = image.get_texture()
        self.hot_x = hot_x
        self.hot_y = hot_y

        self.gl_drawable = not acceleration
        self.hw_drawable = acceleration

    def draw(self, x, y):
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        self.texture.blit(x - self.hot_x, y - self.hot_y, 0)
        gl.glDisable(gl.GL_BLEND)


def _PlatformEventHandler(data):
    """Decorator for platform event handlers.

    Apply giving the platform-specific data needed by the window to associate
    the method with an event.  See platform-specific subclasses of this
    decorator for examples.

    The following attributes are set on the function, which is returned
    otherwise unchanged:

    _platform_event
        True
    _platform_event_data
        List of data applied to the function (permitting multiple decorators
        on the same method).
    """
    def _event_wrapper(f):
        f._platform_event = True
        if not hasattr(f, '_platform_event_data'):
            f._platform_event_data = []
        f._platform_event_data.append(data)
        return f

    return _event_wrapper


def _ViewEventHandler(f):
    f._view = True
    return f


class _WindowMetaclass(type):
    """Sets the _platform_event_names class variable on the window
    subclass.
    """

    def __init__(cls, name, bases, dict):
        cls._platform_event_names = set()
        for base in bases:
            if hasattr(base, '_platform_event_names'):
                cls._platform_event_names.update(base._platform_event_names)
        for name, func in dict.items():
            if hasattr(func, '_platform_event'):
                cls._platform_event_names.add(name)
        super(_WindowMetaclass, cls).__init__(name, bases, dict)


class BaseWindow(with_metaclass(_WindowMetaclass, EventDispatcher)):
    """Platform-independent application window.

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
    """

    # Filled in by metaclass with the names of all methods on this (sub)class
    # that are platform event handlers.
    _platform_event_names = set()

    #: The default window style.
    WINDOW_STYLE_DEFAULT = None
    #: The window style for pop-up dialogs.
    WINDOW_STYLE_DIALOG = 'dialog'
    #: The window style for tool windows.
    WINDOW_STYLE_TOOL = 'tool'
    #: A window style without any decoration.
    WINDOW_STYLE_BORDERLESS = 'borderless'
    #: A window style for transparent, interactable windows
    WINDOW_STYLE_TRANSPARENT = 'transparent'
    #: A window style for transparent, topmost, click-through-able overlays
    WINDOW_STYLE_OVERLAY = 'overlay'

    #: The default mouse cursor.
    CURSOR_DEFAULT = None
    #: A crosshair mouse cursor.
    CURSOR_CROSSHAIR = 'crosshair'
    #: A pointing hand mouse cursor.
    CURSOR_HAND = 'hand'
    #: A "help" mouse cursor; typically a question mark and an arrow.
    CURSOR_HELP = 'help'
    #: A mouse cursor indicating that the selected operation is not permitted.
    CURSOR_NO = 'no'
    #: A mouse cursor indicating the element can be resized.
    CURSOR_SIZE = 'size'
    #: A mouse cursor indicating the element can be resized from the top
    #: border.
    CURSOR_SIZE_UP = 'size_up'
    #: A mouse cursor indicating the element can be resized from the
    #: upper-right corner.
    CURSOR_SIZE_UP_RIGHT = 'size_up_right'
    #: A mouse cursor indicating the element can be resized from the right
    #: border.
    CURSOR_SIZE_RIGHT = 'size_right'
    #: A mouse cursor indicating the element can be resized from the lower-right
    #: corner.
    CURSOR_SIZE_DOWN_RIGHT = 'size_down_right'
    #: A mouse cursor indicating the element can be resized from the bottom
    #: border.
    CURSOR_SIZE_DOWN = 'size_down'
    #: A mouse cursor indicating the element can be resized from the lower-left
    #: corner.
    CURSOR_SIZE_DOWN_LEFT = 'size_down_left'
    #: A mouse cursor indicating the element can be resized from the left
    #: border.
    CURSOR_SIZE_LEFT = 'size_left'
    #: A mouse cursor indicating the element can be resized from the upper-left
    #: corner.
    CURSOR_SIZE_UP_LEFT = 'size_up_left'
    #: A mouse cursor indicating the element can be resized vertically.
    CURSOR_SIZE_UP_DOWN = 'size_up_down'
    #: A mouse cursor indicating the element can be resized horizontally.
    CURSOR_SIZE_LEFT_RIGHT = 'size_left_right'
    #: A text input mouse cursor (I-beam).
    CURSOR_TEXT = 'text'
    #: A "wait" mouse cursor; typically an hourglass or watch.
    CURSOR_WAIT = 'wait'
    #: The "wait" mouse cursor combined with an arrow.
    CURSOR_WAIT_ARROW = 'wait_arrow'

    #: True if the user has attempted to close the window.
    #:
    #: :deprecated: Windows are closed immediately by the default
    #:      :py:meth:`~pyglet.window.Window.on_close` handler when `pyglet.app.event_loop` is being
    #:      used.
    has_exit = False

    #: Window display contents validity.  The :py:mod:`pyglet.app` event loop
    #: examines every window each iteration and only dispatches the :py:meth:`~pyglet.window.Window.on_draw`
    #: event to windows that have `invalid` set.  By default, windows always
    #: have `invalid` set to ``True``.
    #:
    #: You can prevent redundant redraws by setting this variable to ``False``
    #: in the window's :py:meth:`~pyglet.window.Window.on_draw` handler, and setting it to True again in
    #: response to any events that actually do require a window contents
    #: update.
    #:
    #: :type: bool
    #: .. versionadded:: 1.1
    invalid = True

    # Instance variables accessible only via properties
    _width = None
    _height = None
    _caption = None
    _resizable = False
    _style = WINDOW_STYLE_DEFAULT
    _fullscreen = False
    _visible = False
    _vsync = False
    _file_drops = False
    _screen = None
    _config = None
    _context = None
    _projection_matrix = pyglet.math.Mat4()
    _view_matrix = pyglet.math.Mat4()
    _viewport = 0, 0, 0, 0

    # Used to restore window size and position after fullscreen
    _windowed_size = None
    _windowed_location = None

    _minimum_size = None
    _maximum_size = None

    _keyboard_exclusive = False

    # Subclasses should update these after relevant events
    _mouse_cursor = DefaultMouseCursor()
    _mouse_x = 0
    _mouse_y = 0
    _mouse_visible = True
    _mouse_exclusive = False
    _mouse_in_window = False

    _event_queue = None
    _enable_event_queue = True     # overridden by EventLoop.
    _allow_dispatch_event = False  # controlled by dispatch_events stack frame

    # Class attributes
    _default_width = 960
    _default_height = 540

    # Create a default ShaderProgram, so the Window instance can
    # update the `WindowBlock` UBO shared by all default shaders.
    _default_vertex_source = """#version 150 core
        in vec4 position;

        uniform WindowBlock
        {
            mat4 projection;
            mat4 view;
        } window;

        void main()
        {
            gl_Position = window.projection * window.view * position;
        }
    """
    _default_fragment_source = """#version 150 core
        out vec4 color;
        
        void main()
        {
            color = vec4(1.0, 0.0, 0.0, 1.0);
        }
    """

    def __init__(self,
                 width=None,
                 height=None,
                 caption=None,
                 resizable=False,
                 style=WINDOW_STYLE_DEFAULT,
                 fullscreen=False,
                 visible=True,
                 vsync=True,
                 file_drops=False,
                 display=None,
                 screen=None,
                 config=None,
                 context=None,
                 mode=None):
        """Create a window.

        All parameters are optional, and reasonable defaults are assumed
        where they are not specified.

        The `display`, `screen`, `config` and `context` parameters form
        a hierarchy of control: there is no need to specify more than
        one of these.  For example, if you specify `screen` the `display`
        will be inferred, and a default `config` and `context` will be
        created.

        `config` is a special case; it can be a template created by the
        user specifying the attributes desired, or it can be a complete
        `config` as returned from `Screen.get_matching_configs` or similar.

        The context will be active as soon as the window is created, as if
        `switch_to` was just called.

        :Parameters:
            `width` : int
                Width of the window, in pixels.  Defaults to 960, or the
                screen width if `fullscreen` is True.
            `height` : int
                Height of the window, in pixels.  Defaults to 540, or the
                screen height if `fullscreen` is True.
            `caption` : str or unicode
                Initial caption (title) of the window.  Defaults to
                ``sys.argv[0]``.
            `resizable` : bool
                If True, the window will be resizable.  Defaults to False.
            `style` : int
                One of the ``WINDOW_STYLE_*`` constants specifying the
                border style of the window.
            `fullscreen` : bool
                If True, the window will cover the entire screen rather
                than floating.  Defaults to False.
            `visible` : bool
                Determines if the window is visible immediately after
                creation.  Defaults to True.  Set this to False if you
                would like to change attributes of the window before
                having it appear to the user.
            `vsync` : bool
                If True, buffer flips are synchronised to the primary screen's
                vertical retrace, eliminating flicker.
            `display` : `Display`
                The display device to use.  Useful only under X11.
            `screen` : `Screen`
                The screen to use, if in fullscreen.
            `config` : `pyglet.gl.Config`
                Either a template from which to create a complete config,
                or a complete config.
            `context` : `pyglet.gl.Context`
                The context to attach to this window.  The context must
                not already be attached to another window.
            `mode` : `ScreenMode`
                The screen will be switched to this mode if `fullscreen` is
                True.  If None, an appropriate mode is selected to accomodate
                `width` and `height.`

        """
        EventDispatcher.__init__(self)
        self._event_queue = []

        if not display:
            display = pyglet.canvas.get_display()

        if not screen:
            screen = display.get_default_screen()

        if not config:
            for template_config in [gl.Config(double_buffer=True, depth_size=24, major_version=3, minor_version=3),
                                    gl.Config(double_buffer=True, depth_size=16, major_version=3, minor_version=3),
                                    None]:
                try:
                    config = screen.get_best_config(template_config)
                    break
                except NoSuchConfigException:
                    pass
            if not config:
                raise NoSuchConfigException('No standard config is available.')

        # Necessary on Windows. More investigation needed:
        if style in ('transparent', 'overlay'):
            config.alpha = 8

        if not config.is_complete():
            config = screen.get_best_config(config)

        if not context:
            context = config.create_context(gl.current_context)

        # Set these in reverse order to above, to ensure we get user preference
        self._context = context
        self._config = self._context.config

        # XXX deprecate config's being screen-specific
        if hasattr(self._config, 'screen'):
            self._screen = self._config.screen
        else:
            self._screen = screen
        self._display = self._screen.display

        if fullscreen:
            if width is None and height is None:
                self._windowed_size = self._default_width, self._default_height
            width, height = self._set_fullscreen_mode(mode, width, height)
            if not self._windowed_size:
                self._windowed_size = width, height
        else:
            if width is None:
                width = self._default_width
            if height is None:
                height = self._default_height

        self._width = width
        self._height = height
        self._resizable = resizable
        self._fullscreen = fullscreen
        self._style = style
        if pyglet.options['vsync'] is not None:
            self._vsync = pyglet.options['vsync']
        else:
            self._vsync = vsync

        self._file_drops = file_drops
        self._caption = caption or sys.argv[0]

        from pyglet import app
        app.windows.add(self)
        self._create()

        self.switch_to()

        self._create_projection()

        if visible:
            self.set_visible(True)
            self.activate()

    def _create_projection(self):
        self._default_program = shader.ShaderProgram(
            shader.Shader(self._default_vertex_source, 'vertex'),
            shader.Shader(self._default_fragment_source, 'fragment'))

        self.ubo = self._default_program.uniform_blocks['WindowBlock'].create_ubo()

        self._viewport = 0, 0, *self.get_framebuffer_size()

        self.view = Mat4()
        self.projection = Mat4.orthogonal_projection(0, self._width, 0, self._height, -255, 255)

    def __del__(self):
        # Always try to clean up the window when it is dereferenced.
        # Makes sure there are no dangling pointers or memory leaks.
        # If the window is already closed, pass silently.
        try:
            self.close()
        except:  # XXX  Avoid a NoneType error if already closed.
            pass

    def __repr__(self):
        return '%s(width=%d, height=%d)' % (self.__class__.__name__, self.width, self.height)

    def _create(self):
        raise NotImplementedError('abstract')

    def _recreate(self, changes):
        """Recreate the window with current attributes.

        :Parameters:
            `changes` : list of str
                List of attribute names that were changed since the last
                `_create` or `_recreate`.  For example, ``['fullscreen']``
                is given if the window is to be toggled to or from fullscreen.
        """
        raise NotImplementedError('abstract')

    def flip(self):
        """Swap the OpenGL front and back buffers.

        Call this method on a double-buffered window to update the
        visible display with the back buffer.  The contents of the back buffer
        is undefined after this operation.

        Windows are double-buffered by default.  This method is called
        automatically by `EventLoop` after the :py:meth:`~pyglet.window.Window.on_draw` event.
        """
        raise NotImplementedError('abstract')

    def switch_to(self):
        """Make this window the current OpenGL rendering context.

        Only one OpenGL context can be active at a time.  This method sets
        the current window's context to be current.  You should use this
        method in preference to `pyglet.gl.Context.set_current`, as it may
        perform additional initialisation functions.
        """
        raise NotImplementedError('abstract')

    def set_fullscreen(self, fullscreen=True, screen=None, mode=None, width=None, height=None):
        """Toggle to or from fullscreen.

        After toggling fullscreen, the GL context should have retained its
        state and objects, however the buffers will need to be cleared and
        redrawn.

        If `width` and `height` are specified and `fullscreen` is True, the
        screen may be switched to a different resolution that most closely
        matches the given size.  If the resolution doesn't match exactly,
        a higher resolution is selected and the window will be centered
        within a black border covering the rest of the screen.

        :Parameters:
            `fullscreen` : bool
                True if the window should be made fullscreen, False if it
                should be windowed.
            `screen` : Screen
                If not None and fullscreen is True, the window is moved to the
                given screen.  The screen must belong to the same display as
                the window.
            `mode` : `ScreenMode`
                The screen will be switched to the given mode.  The mode must
                have been obtained by enumerating `Screen.get_modes`.  If
                None, an appropriate mode will be selected from the given
                `width` and `height`.
            `width` : int
                Optional width of the window.  If unspecified, defaults to the
                previous window size when windowed, or the screen size if
                fullscreen.

                .. versionadded:: 1.2
            `height` : int
                Optional height of the window.  If unspecified, defaults to
                the previous window size when windowed, or the screen size if
                fullscreen.

                .. versionadded:: 1.2
        """
        if (fullscreen == self._fullscreen and
            (screen is None or screen is self._screen) and
            (width is None or width == self._width) and
            (height is None or height == self._height)):
            return

        if not self._fullscreen:
            # Save windowed size
            self._windowed_size = self.get_size()
            self._windowed_location = self.get_location()

        if fullscreen and screen is not None:
            assert screen.display is self.display
            self._screen = screen

        self._fullscreen = fullscreen
        if self._fullscreen:
            self._width, self._height = self._set_fullscreen_mode(mode, width, height)
        else:
            self.screen.restore_mode()

            self._width, self._height = self._windowed_size
            if width is not None:
                self._width = width
            if height is not None:
                self._height = height

        self._recreate(['fullscreen'])

        if not self._fullscreen and self._windowed_location:
            # Restore windowed location.
            self.set_location(*self._windowed_location)

    def _set_fullscreen_mode(self, mode, width, height):
        if mode is not None:
            self.screen.set_mode(mode)
            if width is None:
                width = self.screen.width
            if height is None:
                height = self.screen.height
        elif width is not None or height is not None:
            if width is None:
                width = 0
            if height is None:
                height = 0
            mode = self.screen.get_closest_mode(width, height)
            if mode is not None:
                self.screen.set_mode(mode)
            elif self.screen.get_modes():
                # Only raise exception if mode switching is at all possible.
                raise NoSuchScreenModeException('No mode matching %dx%d' % (width, height))
        else:
            width = self.screen.width
            height = self.screen.height
        return width, height

    def on_resize(self, width, height):
        """A default resize event handler.

        This default handler updates the GL viewport to cover the entire
        window. The bottom-left corner is (0, 0) and the top-right
        corner is the width and height of the window's framebuffer.
        In addition, the projection matrix is set to an orghogonal
        projection based on the same dimensions.
        """
        gl.glViewport(0, 0, *self.get_framebuffer_size())
        self.projection = Mat4.orthogonal_projection(0, width, 0, height, -255, 255)

    def on_close(self):
        """Default on_close handler."""
        self.has_exit = True
        from pyglet import app
        if app.event_loop.is_running:
            self.close()

    def on_key_press(self, symbol, modifiers):
        """Default on_key_press handler."""
        if symbol == key.ESCAPE and not (modifiers & ~(key.MOD_NUMLOCK |
                                                       key.MOD_CAPSLOCK |
                                                       key.MOD_SCROLLLOCK)):
            self.dispatch_event('on_close')

    def close(self):
        """Close the window.

        After closing the window, the GL context will be invalid.  The
        window instance cannot be reused once closed (see also `set_visible`).

        The `pyglet.app.EventLoop.on_window_close` event is dispatched on
        `pyglet.app.event_loop` when this method is called.
        """
        from pyglet import app
        if not self._context:
            return
        app.windows.remove(self)
        self._context.destroy()
        self._config = None
        self._context = None
        if app.event_loop:
            app.event_loop.dispatch_event('on_window_close', self)
        self._event_queue = []

    def draw_mouse_cursor(self):
        """Draw the custom mouse cursor.

        If the current mouse cursor has ``drawable`` set, this method
        is called before the buffers are flipped to render it.

        There is little need to override this method; instead, subclass
        :py:class:`MouseCursor` and provide your own
        :py:meth:`~MouseCursor.draw` method.
        """
        # Draw mouse cursor if set and visible.

        if self._mouse_cursor.gl_drawable and self._mouse_visible and self._mouse_in_window:
            # TODO: consider projection differences
            self._mouse_cursor.draw(self._mouse_x, self._mouse_y)

    # These properties provide read-only access to instance variables.
    @property
    def caption(self):
        """The window caption (title).  Read-only.

        :type: str
        """
        return self._caption

    @property
    def resizeable(self):
        """True if the window is resizable.  Read-only.

        :type: bool
        """
        return self._resizable

    @property
    def style(self):
        """The window style; one of the ``WINDOW_STYLE_*`` constants.
        Read-only.

        :type: int
        """
        return self._style

    @property
    def fullscreen(self):
        """True if the window is currently fullscreen.  Read-only.

        :type: bool
        """
        return self._fullscreen

    @property
    def visible(self):
        """True if the window is currently visible.  Read-only.

        :type: bool
        """
        return self._visible

    @property
    def vsync(self):
        """True if buffer flips are synchronised to the screen's vertical
        retrace.  Read-only.

        :type: bool
        """
        return self._vsync

    @property
    def display(self):
        """The display this window belongs to.  Read-only.

        :type: :py:class:`Display`
        """
        return self._display

    @property
    def screen(self):
        """The screen this window is fullscreen in.  Read-only.

        :type: :py:class:`Screen`
        """
        return self._screen

    @property
    def config(self):
        """A GL config describing the context of this window.  Read-only.

        :type: :py:class:`pyglet.gl.Config`
        """
        return self._config

    @property
    def context(self):
        """The OpenGL context attached to this window.  Read-only.

        :type: :py:class:`pyglet.gl.Context`
        """
        return self._context

    # These are the only properties that can be set
    @property
    def width(self):
        """The width of the window, in pixels.  Read-write.

        :type: int
        """
        return self.get_size()[0]

    @width.setter
    def width(self, new_width):
        self.set_size(new_width, self.height)

    @property
    def height(self):
        """The height of the window, in pixels.  Read-write.

        :type: int
        """
        return self.get_size()[1]

    @height.setter
    def height(self, new_height):
        self.set_size(self.width, new_height)

    @property
    def projection(self):
        """The OpenGL window projection matrix. Read-write.

        The default projection matrix is orthographic (2D),
        but a custom :py:class:`pyglet.math.Mat4` instance
        can be set. Alternatively, you can supply a flat
        tuple of 16 values.

        (2D), but can be changed to any 4x4 matrix desired.
        See :py:class:`pyglet.math.Mat4`.

        :type: :py:class:`pyglet.math.Mat4`
        """
        return self._projection_matrix

    @projection.setter
    def projection(self, matrix: Mat4):

        with self.ubo as window_block:
            window_block.projection[:] = matrix

        self._projection_matrix = matrix

    @property
    def view(self):
        """The OpenGL window view matrix. Read-write.

        The default view is an identity matrix, but a custom
        :py:class:`pyglet.math.Mat4` instance can be set.
        Alternatively, you can supply a flat tuple of 16 values.

        :type: :py:class:`pyglet.math.Mat4`
        """
        return self._view_matrix

    @view.setter
    def view(self, matrix: Mat4):

        with self.ubo as window_block:
            window_block.view[:] = matrix

        self._view_matrix = matrix

    @property
    def viewport(self):
        """The Window viewport

        The Window viewport, expressed as (x, y, width, height).

        :rtype: (int, int, int, int)
        :return: The viewport size as a tuple of four ints.
        """
        return self._viewport

    @viewport.setter
    def viewport(self, values):
        self._viewport = values
        pr = self.get_pixel_ratio()
        x, y, w, h = values
        pyglet.gl.glViewport(int(x * pr), int(y * pr), int(w * pr), int(h * pr))

    def set_caption(self, caption):
        """Set the window's caption.

        The caption appears in the titlebar of the window, if it has one,
        and in the taskbar on Windows and many X11 window managers.

        :Parameters:
            `caption` : str or unicode
                The caption to set.

        """
        raise NotImplementedError('abstract')

    def set_minimum_size(self, width: int, height: int) -> None:
        """Set the minimum size of the window.

        Once set, the user will not be able to resize the window smaller
        than the given dimensions.  There is no way to remove the
        minimum size constraint on a window (but you could set it to 0,0).

        The behaviour is undefined if the minimum size is set larger than
        the current size of the window.

        The window size does not include the border or title bar.

        :Parameters:
            `width` : int
                Minimum width of the window, in pixels.
            `height` : int
                Minimum height of the window, in pixels.

        """
        if width < 1 or height < 1:
            raise ValueError('width and height must be positive integers')

        self._minimum_size = width, height

    def set_maximum_size(self, width: int, height: int) -> None:
        """Set the maximum size of the window.

        Once set, the user will not be able to resize the window larger
        than the given dimensions.  There is no way to remove the
        maximum size constraint on a window (but you could set it to a large
        value).

        The behaviour is undefined if the maximum size is set smaller than
        the current size of the window.

        The window size does not include the border or title bar.

        :Parameters:
            `width` : int
                Maximum width of the window, in pixels.
            `height` : int
                Maximum height of the window, in pixels.

        """
        if width < 1 or height < 1:
            raise ValueError('width and height must be positive integers')

        self._maximum_size = width, height

    def set_size(self, width: int, height: int) -> None:
        """Resize the window.

        The behaviour is undefined if the window is not resizable, or if
        it is currently fullscreen.

        The window size does not include the border or title bar.

        :Parameters:
            `width` : int
                New width of the window, in pixels.
            `height` : int
                New height of the window, in pixels.

        """
        if self._fullscreen:
            raise WindowException('Cannot set size of fullscreen window.')
        if width < 1 or height < 1:
            raise ValueError('width and height must be positive integers')

        self._width, self._height = width, height

    def get_pixel_ratio(self):
        """Return the framebuffer/window size ratio.

        Some platforms and/or window systems support subpixel scaling,
        making the framebuffer size larger than the window size.
        Retina screens on OS X and Gnome on Linux are some examples.

        On a Retina systems the returned ratio would usually be 2.0 as a
        window of size 500 x 500 would have a framebuffer of 1000 x 1000.
        Fractional values between 1.0 and 2.0, as well as values above
        2.0 may also be encountered.

        :rtype: float
        :return: The framebuffer/window size ratio
        """
        return self.get_framebuffer_size()[0] / self.width

    def get_size(self) -> Tuple[int, int]:
        """Return the current size of the window.

        This does not include the windows' border or title bar.

        :rtype: (int, int)
        :return: The width and height of the window, in pixels.
        """
        return self._width, self._height

    def get_framebuffer_size(self):
        """Return the size in actual pixels of the Window framebuffer.

        When using HiDPI screens, the size of the Window's framebuffer
        can be higher than that of the Window size requested. If you
        are performing operations that require knowing the actual number
        of pixels in the window, this method should be used instead of
        :py:func:`Window.get_size()`. For example, setting the Window
        projection or setting the glViewport size.

        :rtype: (int, int)
        :return: The width and height of the Window's framebuffer, in pixels.
        """
        return self.get_size()

    def set_location(self, x, y):
        """Set the position of the window.

        :Parameters:
            `x` : int
                Distance of the left edge of the window from the left edge
                of the virtual desktop, in pixels.
            `y` : int
                Distance of the top edge of the window from the top edge of
                the virtual desktop, in pixels.

        """
        raise NotImplementedError('abstract')

    def get_location(self):
        """Return the current position of the window.

        :rtype: (int, int)
        :return: The distances of the left and top edges from their respective
            edges on the virtual desktop, in pixels.
        """
        raise NotImplementedError('abstract')

    def activate(self):
        """Attempt to restore keyboard focus to the window.

        Depending on the window manager or operating system, this may not
        be successful.  For example, on Windows XP an application is not
        allowed to "steal" focus from another application.  Instead, the
        window's taskbar icon will flash, indicating it requires attention.
        """
        raise NotImplementedError('abstract')

    def set_visible(self, visible: bool = True) -> None:
        """Show or hide the window.

        :Parameters:
            `visible` : bool
                If True, the window will be shown; otherwise it will be
                hidden.
        """
        self._visible = visible

    def minimize(self):
        """Minimize the window.
        """
        raise NotImplementedError('abstract')

    def maximize(self):
        """Maximize the window.

        The behaviour of this method is somewhat dependent on the user's
        display setup.  On a multi-monitor system, the window may maximize
        to either a single screen or the entire virtual desktop.
        """
        raise NotImplementedError('abstract')

    def set_vsync(self, vsync: bool) -> None:
        """Enable or disable vertical sync control.

        When enabled, this option ensures flips from the back to the front
        buffer are performed only during the vertical retrace period of the
        primary display.  This can prevent "tearing" or flickering when
        the buffer is updated in the middle of a video scan.

        Note that LCD monitors have an analogous time in which they are not
        reading from the video buffer; while it does not correspond to
        a vertical retrace it has the same effect.

        Also note that with multi-monitor systems the secondary monitor
        cannot be synchronised to, so tearing and flicker cannot be avoided
        when the window is positioned outside of the primary display.

        :Parameters:
            `vsync` : bool
                If True, vsync is enabled, otherwise it is disabled.

        """
        self._vsync = vsync

    def set_mouse_visible(self, visible=True):
        """Show or hide the mouse cursor.

        The mouse cursor will only be hidden while it is positioned within
        this window.  Mouse events will still be processed as usual.

        :Parameters:
            `visible` : bool
                If True, the mouse cursor will be visible, otherwise it
                will be hidden.

        """
        self._mouse_visible = visible
        self.set_mouse_platform_visible()

    def set_mouse_platform_visible(self, platform_visible=None):
        """Set the platform-drawn mouse cursor visibility.  This is called
        automatically after changing the mouse cursor or exclusive mode.

        Applications should not normally need to call this method, see
        `set_mouse_visible` instead.

        :Parameters:
            `platform_visible` : bool or None
                If None, sets platform visibility to the required visibility
                for the current exclusive mode and cursor type.  Otherwise,
                a bool value will override and force a visibility.

        """
        raise NotImplementedError()

    def set_mouse_cursor(self, cursor=None):
        """Change the appearance of the mouse cursor.

        The appearance of the mouse cursor is only changed while it is
        within this window.

        :Parameters:
            `cursor` : `MouseCursor`
                The cursor to set, or None to restore the default cursor.

        """
        if cursor is None:
            cursor = DefaultMouseCursor()
        self._mouse_cursor = cursor
        self.set_mouse_platform_visible()

    def set_exclusive_mouse(self, exclusive=True):
        """Hide the mouse cursor and direct all mouse events to this
        window.

        When enabled, this feature prevents the mouse leaving the window.  It
        is useful for certain styles of games that require complete control of
        the mouse.  The position of the mouse as reported in subsequent events
        is meaningless when exclusive mouse is enabled; you should only use
        the relative motion parameters ``dx`` and ``dy``.

        :Parameters:
            `exclusive` : bool
                If True, exclusive mouse is enabled, otherwise it is disabled.

        """
        self._mouse_exclusive = exclusive

    def set_exclusive_keyboard(self, exclusive=True):
        """Prevent the user from switching away from this window using
        keyboard accelerators.

        When enabled, this feature disables certain operating-system specific
        key combinations such as Alt+Tab (Command+Tab on OS X).  This can be
        useful in certain kiosk applications, it should be avoided in general
        applications or games.

        :Parameters:
            `exclusive` : bool
                If True, exclusive keyboard is enabled, otherwise it is
                disabled.

        """
        self._keyboard_exclusive = exclusive

    def get_system_mouse_cursor(self, name):
        """Obtain a system mouse cursor.

        Use `set_mouse_cursor` to make the cursor returned by this method
        active.  The names accepted by this method are the ``CURSOR_*``
        constants defined on this class.

        :Parameters:
            `name` : str
                Name describing the mouse cursor to return.  For example,
                ``CURSOR_WAIT``, ``CURSOR_HELP``, etc.

        :rtype: `MouseCursor`
        :return: A mouse cursor which can be used with `set_mouse_cursor`.
        """
        raise NotImplementedError()

    def set_icon(self, *images):
        """Set the window icon.

        If multiple images are provided, one with an appropriate size
        will be selected (if the correct size is not provided, the image
        will be scaled).

        Useful sizes to provide are 16x16, 32x32, 64x64 (Mac only) and
        128x128 (Mac only).

        :Parameters:
            `images` : sequence of `pyglet.image.AbstractImage`
                List of images to use for the window icon.

        """
        pass

    @staticmethod
    def clear():
        """Clear the window.

        This is a convenience method for clearing the color and depth
        buffer.  The window must be the active context (see `switch_to`).
        """
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    def dispatch_event(self, *args):
        if not self._enable_event_queue or self._allow_dispatch_event:
            super().dispatch_event(*args)
        else:
            self._event_queue.append(args)

    def dispatch_events(self):
        """Poll the operating system event queue for new events and call
        attached event handlers.

        This method is provided for legacy applications targeting pyglet 1.0,
        and advanced applications that must integrate their event loop
        into another framework.

        Typical applications should use `pyglet.app.run`.
        """
        raise NotImplementedError('abstract')

    # If documenting, show the event methods.  Otherwise, leave them out
    # as they are not really methods.
    if _is_pyglet_doc_run:
        def on_key_press(self, symbol, modifiers):
            """A key on the keyboard was pressed (and held down).

            Since pyglet 1.1 the default handler dispatches the :py:meth:`~pyglet.window.Window.on_close`
            event if the ``ESC`` key is pressed.

            :Parameters:
                `symbol` : int
                    The key symbol pressed.
                `modifiers` : int
                    Bitwise combination of the key modifiers active.

            :event:
            """

        def on_key_release(self, symbol, modifiers):
            """A key on the keyboard was released.

            :Parameters:
                `symbol` : int
                    The key symbol pressed.
                `modifiers` : int
                    Bitwise combination of the key modifiers active.

            :event:
            """

        def on_text(self, text):
            """The user input some text.

            Typically this is called after :py:meth:`~pyglet.window.Window.on_key_press` and before
            :py:meth:`~pyglet.window.Window.on_key_release`, but may also be called multiple times if the key
            is held down (key repeating); or called without key presses if
            another input method was used (e.g., a pen input).

            You should always use this method for interpreting text, as the
            key symbols often have complex mappings to their unicode
            representation which this event takes care of.

            :Parameters:
                `text` : unicode
                    The text entered by the user.

            :event:
            """

        def on_text_motion(self, motion):
            """The user moved the text input cursor.

            Typically this is called after :py:meth:`~pyglet.window.Window.on_key_press` and before
            :py:meth:`~pyglet.window.Window.on_key_release`, but may also be called multiple times if the key
            is help down (key repeating).

            You should always use this method for moving the text input cursor
            (caret), as different platforms have different default keyboard
            mappings, and key repeats are handled correctly.

            The values that `motion` can take are defined in
            :py:mod:`pyglet.window.key`:

            * MOTION_UP
            * MOTION_RIGHT
            * MOTION_DOWN
            * MOTION_LEFT
            * MOTION_NEXT_WORD
            * MOTION_PREVIOUS_WORD
            * MOTION_BEGINNING_OF_LINE
            * MOTION_END_OF_LINE
            * MOTION_NEXT_PAGE
            * MOTION_PREVIOUS_PAGE
            * MOTION_BEGINNING_OF_FILE
            * MOTION_END_OF_FILE
            * MOTION_BACKSPACE
            * MOTION_DELETE

            :Parameters:
                `motion` : int
                    The direction of motion; see remarks.

            :event:
            """

        def on_text_motion_select(self, motion):
            """The user moved the text input cursor while extending the
            selection.

            Typically this is called after :py:meth:`~pyglet.window.Window.on_key_press` and before
            :py:meth:`~pyglet.window.Window.on_key_release`, but may also be called multiple times if the key
            is help down (key repeating).

            You should always use this method for responding to text selection
            events rather than the raw :py:meth:`~pyglet.window.Window.on_key_press`, as different platforms
            have different default keyboard mappings, and key repeats are
            handled correctly.

            The values that `motion` can take are defined in :py:mod:`pyglet.window.key`:

            * MOTION_UP
            * MOTION_RIGHT
            * MOTION_DOWN
            * MOTION_LEFT
            * MOTION_NEXT_WORD
            * MOTION_PREVIOUS_WORD
            * MOTION_BEGINNING_OF_LINE
            * MOTION_END_OF_LINE
            * MOTION_NEXT_PAGE
            * MOTION_PREVIOUS_PAGE
            * MOTION_BEGINNING_OF_FILE
            * MOTION_END_OF_FILE

            :Parameters:
                `motion` : int
                    The direction of selection motion; see remarks.

            :event:
            """

        def on_mouse_motion(self, x, y, dx, dy):
            """The mouse was moved with no buttons held down.

            :Parameters:
                `x` : int
                    Distance in pixels from the left edge of the window.
                `y` : int
                    Distance in pixels from the bottom edge of the window.
                `dx` : int
                    Relative X position from the previous mouse position.
                `dy` : int
                    Relative Y position from the previous mouse position.

            :event:
            """

        def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
            """The mouse was moved with one or more mouse buttons pressed.

            This event will continue to be fired even if the mouse leaves
            the window, so long as the drag buttons are continuously held down.

            :Parameters:
                `x` : int
                    Distance in pixels from the left edge of the window.
                `y` : int
                    Distance in pixels from the bottom edge of the window.
                `dx` : int
                    Relative X position from the previous mouse position.
                `dy` : int
                    Relative Y position from the previous mouse position.
                `buttons` : int
                    Bitwise combination of the mouse buttons currently pressed.
                `modifiers` : int
                    Bitwise combination of any keyboard modifiers currently
                    active.

            :event:
            """

        def on_mouse_press(self, x, y, button, modifiers):
            """A mouse button was pressed (and held down).

            :Parameters:
                `x` : int
                    Distance in pixels from the left edge of the window.
                `y` : int
                    Distance in pixels from the bottom edge of the window.
                `button` : int
                    The mouse button that was pressed.
                `modifiers` : int
                    Bitwise combination of any keyboard modifiers currently
                    active.

            :event:
            """

        def on_mouse_release(self, x, y, button, modifiers):
            """A mouse button was released.

            :Parameters:
                `x` : int
                    Distance in pixels from the left edge of the window.
                `y` : int
                    Distance in pixels from the bottom edge of the window.
                `button` : int
                    The mouse button that was released.
                `modifiers` : int
                    Bitwise combination of any keyboard modifiers currently
                    active.

            :event:
            """

        def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
            """The mouse wheel was scrolled.

            Note that most mice have only a vertical scroll wheel, so
            `scroll_x` is usually 0.  An exception to this is the Apple Mighty
            Mouse, which has a mouse ball in place of the wheel which allows
            both `scroll_x` and `scroll_y` movement.

            :Parameters:
                `x` : int
                    Distance in pixels from the left edge of the window.
                `y` : int
                    Distance in pixels from the bottom edge of the window.
                `scroll_x` : float
                    Amount of movement on the horizontal axis.
                `scroll_y` : float
                    Amount of movement on the vertical axis.

            :event:
            """

        def on_close(self):
            """The user attempted to close the window.

            This event can be triggered by clicking on the "X" control box in
            the window title bar, or by some other platform-dependent manner.

            The default handler sets `has_exit` to ``True``.  In pyglet 1.1, if
            `pyglet.app.event_loop` is being used, `close` is also called,
            closing the window immediately.

            :event:
            """

        def on_mouse_enter(self, x, y):
            """The mouse was moved into the window.

            This event will not be triggered if the mouse is currently being
            dragged.

            :Parameters:
                `x` : int
                    Distance in pixels from the left edge of the window.
                `y` : int
                    Distance in pixels from the bottom edge of the window.

            :event:
            """

        def on_mouse_leave(self, x, y):
            """The mouse was moved outside of the window.

            This event will not be triggered if the mouse is currently being
            dragged.  Note that the coordinates of the mouse pointer will be
            outside of the window rectangle.

            :Parameters:
                `x` : int
                    Distance in pixels from the left edge of the window.
                `y` : int
                    Distance in pixels from the bottom edge of the window.

            :event:
            """

        def on_expose(self):
            """A portion of the window needs to be redrawn.

            This event is triggered when the window first appears, and any time
            the contents of the window is invalidated due to another window
            obscuring it.

            There is no way to determine which portion of the window needs
            redrawing.  Note that the use of this method is becoming
            increasingly uncommon, as newer window managers composite windows
            automatically and keep a backing store of the window contents.

            :event:
            """

        def on_resize(self, width, height):
            """The window was resized.

            The window will have the GL context when this event is dispatched;
            there is no need to call `switch_to` in this handler.

            :Parameters:
                `width` : int
                    The new width of the window, in pixels.
                `height` : int
                    The new height of the window, in pixels.

            :event:
            """

        def on_move(self, x, y):
            """The window was moved.

            :Parameters:
                `x` : int
                    Distance from the left edge of the screen to the left edge
                    of the window.
                `y` : int
                    Distance from the top edge of the screen to the top edge of
                    the window.  Note that this is one of few methods in pyglet
                    which use a Y-down coordinate system.

            :event:
            """

        def on_activate(self):
            """The window was activated.

            This event can be triggered by clicking on the title bar, bringing
            it to the foreground; or by some platform-specific method.

            When a window is "active" it has the keyboard focus.

            :event:
            """

        def on_deactivate(self):
            """The window was deactivated.

            This event can be triggered by clicking on another application
            window.  When a window is deactivated it no longer has the
            keyboard focus.

            :event:
            """

        def on_show(self):
            """The window was shown.

            This event is triggered when a window is restored after being
            minimised, hidden, or after being displayed for the first time.

            :event:
            """

        def on_hide(self):
            """The window was hidden.

            This event is triggered when a window is minimised
            or hidden by the user.

            :event:
            """

        def on_context_lost(self):
            """The window's GL context was lost.

            When the context is lost no more GL methods can be called until it
            is recreated.  This is a rare event, triggered perhaps by the user
            switching to an incompatible video mode.  When it occurs, an
            application will need to reload all objects (display lists, texture
            objects, shaders) as well as restore the GL state.

            :event:
            """

        def on_context_state_lost(self):
            """The state of the window's GL context was lost.

            pyglet may sometimes need to recreate the window's GL context if
            the window is moved to another video device, or between fullscreen
            or windowed mode.  In this case it will try to share the objects
            (display lists, texture objects, shaders) between the old and new
            contexts.  If this is possible, only the current state of the GL
            context is lost, and the application should simply restore state.

            :event:
            """

        def on_file_drop(self, x, y, paths):
            """File(s) were dropped into the window, will return the position of the cursor and
            a list of paths to the files that were dropped.

            .. versionadded:: 1.5.1

            :event:
            """

        def on_draw(self, dt):
            """The window contents must be redrawn.

            The `EventLoop` will dispatch this event when the window
            should be redrawn.  This will happen during idle time after
            any window events and after any scheduled functions were called.

            The window will already have the GL context, so there is no
            need to call `switch_to`.  The window's `flip` method will
            be called after this event, so your event handler should not.

            You should make no assumptions about the window contents when
            this event is triggered; a resize or expose event may have
            invalidated the framebuffer since the last time it was drawn.

            .. versionadded:: 1.1

            :event:
            """

        def on_refresh(self, dt):
            """The window contents must be redrawn.

            The `EventLoop` will dispatch this event when the window
            should be redrawn.

            The window will already have the GL context, so there is no
            need to call `switch_to`.  The window's `flip` method will
            be called after this event, so your event handler should not.

            You should make no assumptions about the window contents when
            this event is triggered; a resize or expose event may have
            invalidated the framebuffer since the last time it was drawn.

            .. versionadded:: 2.0

            :event:
            """


BaseWindow.register_event_type('on_key_press')
BaseWindow.register_event_type('on_key_release')
BaseWindow.register_event_type('on_text')
BaseWindow.register_event_type('on_text_motion')
BaseWindow.register_event_type('on_text_motion_select')
BaseWindow.register_event_type('on_mouse_motion')
BaseWindow.register_event_type('on_mouse_drag')
BaseWindow.register_event_type('on_mouse_press')
BaseWindow.register_event_type('on_mouse_release')
BaseWindow.register_event_type('on_mouse_scroll')
BaseWindow.register_event_type('on_mouse_enter')
BaseWindow.register_event_type('on_mouse_leave')
BaseWindow.register_event_type('on_close')
BaseWindow.register_event_type('on_expose')
BaseWindow.register_event_type('on_resize')
BaseWindow.register_event_type('on_move')
BaseWindow.register_event_type('on_activate')
BaseWindow.register_event_type('on_deactivate')
BaseWindow.register_event_type('on_show')
BaseWindow.register_event_type('on_hide')
BaseWindow.register_event_type('on_context_lost')
BaseWindow.register_event_type('on_context_state_lost')
BaseWindow.register_event_type('on_file_drop')
BaseWindow.register_event_type('on_draw')
BaseWindow.register_event_type('on_refresh')


class FPSDisplay:
    """Display of a window's framerate.

    This is a convenience class to aid in profiling and debugging.  Typical
    usage is to create an `FPSDisplay` for each window, and draw the display
    at the end of the windows' :py:meth:`~pyglet.window.Window.on_draw` event handler::

        window = pyglet.window.Window()
        fps_display = FPSDisplay(window)

        @window.event
        def on_draw():
            # ... perform ordinary window drawing operations ...

            fps_display.draw()

    The style and position of the display can be modified via the :py:func:`~pyglet.text.Label`
    attribute.  Different text can be substituted by overriding the
    `set_fps` method.  The display can be set to update more or less often
    by setting the `update_period` attribute. Note: setting the `update_period`
    to a value smaller than your Window refresh rate will cause inaccurate readings.

    :Ivariables:
        `label` : Label
            The text label displaying the framerate.

    """

    #: Time in seconds between updates.
    #:
    #: :type: float
    update_period = 0.25

    def __init__(self, window, color=(127, 127, 127, 127), samples=60):
        from time import time
        from statistics import mean
        from collections import deque
        from pyglet.text import Label
        self._time = time
        self._mean = mean

        # Hook into the Window.flip method:
        self._window_flip, window.flip = window.flip, self._hook_flip
        self.label = Label('', x=10, y=10, font_size=24, bold=True, color=color)

        self._elapsed = 0.0
        self._last_time = time()
        self._delta_times = deque(maxlen=samples)

    def update(self):
        """Records a new data point at the current time. This method
        is called automatically when the window buffer is flipped.
        """
        t = self._time()
        delta = t - self._last_time
        self._elapsed += delta
        self._delta_times.append(delta)
        self._last_time = t

        if self._elapsed >= self.update_period:
            self._elapsed = 0
            self._set_fps_text(1 / self._mean(self._delta_times))

    def _set_fps_text(self, fps):
        """Set the label text for the given FPS estimation.

        Called by `update` every `update_period` seconds.

        :Parameters:
            `fps` : float
                Estimated framerate of the window.

        """
        self.label.text = '%.2f' % fps

    def draw(self):
        """Draw the label."""
        self.label.draw()

    def _hook_flip(self):
        self.update()
        self._window_flip()


if _is_pyglet_doc_run:
    # We are building documentation
    Window = BaseWindow
    Window.__name__ = 'Window'
    del BaseWindow

else:
    # Try to determine which platform to use.
    if pyglet.options['headless']:
        from pyglet.window.headless import HeadlessWindow as Window
    elif pyglet.compat_platform == 'darwin':
        from pyglet.window.cocoa import CocoaWindow as Window
    elif pyglet.compat_platform in ('win32', 'cygwin'):
        from pyglet.window.win32 import Win32Window as Window
    else:
        from pyglet.window.xlib import XlibWindow as Window

# Create shadow window. (trickery is for circular import)
if not _is_pyglet_doc_run:
    pyglet.window = sys.modules[__name__]
    gl._create_shadow_window()
