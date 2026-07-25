from __future__ import annotations

from typing import Literal

from pyglet.display.base import Display, Screen
import js

class EmscriptenDisplay(Display):

    def __init__(self):
        super().__init__()

    def get_screens(self):
        return [EmscriptenScreen(self)]


class EmscriptenScreen(Screen):
    def __init__(self, display: EmscriptenDisplay):
        width = js.window.screen.width
        height = js.window.screen.height
        super().__init__(display, 0, 0, width, height)

    def get_display_id(self) -> int:
        return 0

    def get_monitor_name(self) -> str | Literal["Unknown"]:
        return "BROWSER"

    def get_modes(self):
        pass

    def get_mode(self):
        pass

    def set_mode(self, mode):
        pass

    def restore_mode(self):
        pass
