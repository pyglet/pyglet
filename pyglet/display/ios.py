from __future__ import annotations

from pyglet.libs.darwin.cocoapy import ObjCClass

from .base import Display, Screen, ScreenMode


UIScreen = ObjCClass('UIScreen')


class IOSDisplay(Display):
    """The single display from UIKit."""

    def get_screens(self) -> list[IOSScreen]:
        return [IOSScreen(self, UIScreen.mainScreen())]


class IOSScreen(Screen):
    def __init__(self, display: IOSDisplay, ui_screen) -> None:
        self._ui_screen = ui_screen
        bounds = ui_screen.bounds()
        scale = ui_screen.nativeScale()
        super().__init__(display, 0, 0, round(bounds.size.width * scale), round(bounds.size.height * scale))

    def get_modes(self) -> list[ScreenMode]:
        return [self.get_mode()]

    def get_mode(self) -> ScreenMode:
        mode = ScreenMode(self)
        mode.width, mode.height, mode.depth, mode.rate = self.width, self.height, None, None
        return mode

    def set_mode(self, mode: ScreenMode) -> None:
        return None

    def restore_mode(self) -> None:
        return None

    def get_dpi(self) -> int:
        return round(96 * self.get_scale())

    def get_scale(self) -> float:
        return float(self._ui_screen.nativeScale())

    def get_display_id(self) -> str:
        return 'main'

    def get_monitor_name(self) -> str:
        return 'iOS Display'
