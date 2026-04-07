from typing import Any

from pyglet.enums import GraphicsAPI
from pyglet.window import Window


class UserConfig:
    """User configuration information."""
    api: GraphicsAPI


class SurfaceConfig:
    """Surface configuration information returned by a platform.

    This describes the information a desired surface or window can support.
    """
    def __init__(self, window: Window, config: UserConfig, handle: Any) -> None:
        """A config representing the capabilities of a specific surface.

        This is returned by the platform on a specific window and is not meant to be created by users.

        Args:
            window:
                The current window or display.
            config:
                The requested user configuration.
            handle:
                A handle to the underlying configuration unique to each platform.
        """
        self._window = window
        self.config = config
        self.handle = handle

    @property
    def attributes(self) -> dict[str, Any]:
        """The public attributes of this configuration."""
        return {attrib: value for attrib, value in self.__dict__.items() if attrib[0] != '_'}

    @property
    def is_finalized(self) -> bool:
        return True
