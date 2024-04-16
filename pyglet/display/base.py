from __future__ import annotations

from typing import TYPE_CHECKING

from pyglet import gl
from pyglet import app
from pyglet import window
from pyglet import display

if TYPE_CHECKING:
    from pyglet.gl import Config
    from pyglet.window import BaseWindow


class Display:
    """A display device supporting one or more screens."""

    name: str = None
    """Name of this display, if applicable."""

    x_screen: int = None
    """The X11 screen number of this display, if applicable."""

    def __init__(self, name: str = None, x_screen: int = None) -> None:
        """Create a display connection for the given name and screen.

        On X11, :attr:`name` is of the form ``"hostname:display"``, where the
        default is usually ``":1"``.  On X11, :attr:`x_screen` gives the X 
        screen number to use with this display.  A pyglet display can only be 
        used with one X screen; open multiple display connections to access
        multiple X screens.  
        
        Note that TwinView, Xinerama, xrandr and other extensions present
        multiple monitors on a single X screen; this is usually the preferred
        mechanism for working with multiple monitors under X11 and allows each
        screen to be accessed through a single pyglet`~pyglet.display.Display`

        On platforms other than X11, :attr:`name` and :attr:`x_screen` are 
        ignored; there is only a single display device on these systems.
        """
        display._displays.add(self)

    def get_screens(self) -> list[Screen]:
        """Get the available screens.

        A typical multi-monitor workstation comprises one :class:`Display`
        with multiple :class:`Screen` s.  This method returns a list of 
        screens which can be enumerated to select one for full-screen display.

        For the purposes of creating an OpenGL config, the default screen
        will suffice.

        :rtype: list of :class:`Screen`
        """
        raise NotImplementedError('abstract')

    def get_default_screen(self) -> Screen:
        """Get the default (primary) screen as specified by the user's operating system
        preferences.
        """
        screens = self.get_screens()
        for screen in screens:
            if screen.x == 0 and screen.y == 0:
                return screen

        # No Primary screen found?
        return screens[0]

    def get_windows(self) -> list[BaseWindow]:
        """Get the windows currently attached to this display."""
        return [win for win in app.windows if win.display is self]


class Screen:
    """A virtual monitor that supports fullscreen windows.

    Screens typically map onto a physical display such as a
    monitor, television or projector.  Selecting a screen for a window
    has no effect unless the window is made fullscreen, in which case
    the window will fill only that particular virtual screen.

    The :attr:`width` and :attr:`height` attributes of a screen give the 
    current resolution of the screen.  The :attr:`x` and :attr:`y` attributes 
    give the global location of the top-left corner of the screen.  This is 
    useful for determining if screens are arranged above or next to one 
    another.
    
    Use :func:`~Display.get_screens` or :func:`~Display.get_default_screen`
    to obtain an instance of this class.
    """

    def __init__(self, display: Display, x: int, y: int, width: int, height: int):
        self.display = display
        """Display this screen belongs to."""
        self.x = x
        """Left edge of the screen on the virtual desktop."""
        self.y = y
        """Top edge of the screen on the virtual desktop."""
        self.width = width
        """Width of the screen, in pixels."""
        self.height = height
        """Height of the screen, in pixels."""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(x={self.x}, y={self.y}, width={self.width}, height={self.height})"

    def get_best_config(self, template: Config = None) -> Config:
        """Get the best available GL config.

        Any required attributes can be specified in ``template``.  If
        no configuration matches the template,
        :class:`~pyglet.window.NoSuchConfigException` will be raised.
        A configuration supported by the platform that best fulfils
        the needs described by the template.

        :deprecated: Use :meth:`pyglet.gl.Config.match`.

        Args:
            template:
                A configuration with desired attributes filled in.
        """
        configs = None
        if template is None:
            for template_config in [gl.Config(double_buffer=True, depth_size=24, major_version=3, minor_version=3),
                                    gl.Config(double_buffer=True, depth_size=16, major_version=3, minor_version=3),
                                    None]:
                try:
                    configs = self.get_matching_configs(template_config)
                    break
                except window.NoSuchConfigException:
                    pass
        else:
            configs = self.get_matching_configs(template)
        if not configs:
            raise window.NoSuchConfigException()
        return configs[0]

    def get_matching_configs(self, template: Config) -> list[Config]:
        """Get a list of configs that match a specification.

        Any attributes specified in `template` will have values equal
        to or greater in each returned config.  If no configs satisfy
        the template, an empty list is returned.

        :deprecated: Use :meth:`pyglet.gl.Config.match`.

        Args:
            template:
                A configuration with desired attributes filled in.
        """
        raise NotImplementedError('abstract')

    def get_modes(self) -> list[ScreenMode]:
        """Get a list of screen modes supported by this screen.

        .. versionadded:: 1.2
        """
        raise NotImplementedError('abstract')

    def get_mode(self) -> ScreenMode:
        """Get the current display mode for this screen.

        .. versionadded:: 1.2
        """
        raise NotImplementedError('abstract')

    def get_closest_mode(self, width: int, height: int) -> ScreenMode:
        """Get the screen mode that best matches a given size.

        If no supported mode exactly equals the requested size, a larger one
        is returned; or ``None`` if no mode is large enough.

        .. versionadded:: 1.2
        """
        # Best mode is one with the smallest resolution larger than width/height,
        # with depth and refresh rate equal to current mode.
        current = self.get_mode()

        best = None
        for mode in self.get_modes():
            # Reject resolutions that are too small
            if mode.width < width or mode.height < height:
                continue

            if best is None:
                best = mode

            # Must strictly dominate dimensions
            if (mode.width <= best.width and mode.height <= best.height and
                    (mode.width < best.width or mode.height < best.height)):
                best = mode

            # Preferably match rate, then depth.
            if mode.width == best.width and mode.height == best.height:
                points = 0
                if mode.rate == current.rate:
                    points += 2
                if best.rate == current.rate:
                    points -= 2
                if mode.depth == current.depth:
                    points += 1
                if best.depth == current.depth:
                    points -= 1
                if points > 0:
                    best = mode
        return best

    def set_mode(self, mode: ScreenMode) -> None:
        """Set the display mode for this screen.

        The mode must be one previously returned by :meth:`get_mode` or 
        :meth:`get_modes`.
        """
        raise NotImplementedError('abstract')

    def restore_mode(self) -> None:
        """Restore the screen mode to the user's default.
        """
        raise NotImplementedError('abstract')

    def get_dpi(self):
        """Get the DPI of the screen.

        :rtype: int
        """
        raise NotImplementedError('abstract')

    def get_scale(self):
        """Get the pixel scale ratio of the screen.

        :rtype: float
        """
        raise NotImplementedError('abstract')


class ScreenMode:
    """Screen resolution and display settings.

    Applications should not construct `ScreenMode` instances themselves; see
    :meth:`Screen.get_modes`.

    The :attr:`depth` and :attr:`rate` variables may be ``None`` if the 
    operating system does not provide relevant data.

    .. versionadded:: 1.2
    """

    width: int = None
    """Width of screen, in pixels."""

    height: int = None
    """Height of screen, in pixels."""

    depth: int = None
    """Pixel color depth, in bits per pixel."""

    rate: int = None
    """Screen refresh rate in Hz."""

    def __init__(self, screen: Screen) -> None:
        self.screen = screen

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(width={self.width!r}, height={self.height!r}, depth={self.depth!r}, rate={self.rate})'


class Canvas:
    """Abstract drawing area.

    Canvases are used internally by pyglet to represent drawing areas --
    either within a window or full-screen.

    .. versionadded:: 1.2
    """

    def __init__(self, display: Display) -> None:
        self.display = display
        """Display this canvas was created on."""
