
from dataclasses import dataclass
from typing import Any, ItemsView, Sequence

from . import app as app
from . import canvas as canvas
from . import clock as clock
from . import customtypes as customtypes
from . import event as event
from . import font as font
from . import gl as gl
from . import graphics as graphics
from . import gui as gui
from . import image as image
from . import input as input
from . import lib as lib
from . import math as math
from . import media as media
from . import model as model
from . import resource as resource
from . import shapes as shapes
from . import sprite as sprite
from . import text as text
from . import window as window

version: str
MIN_PYTHON_VERSION: tuple[int, int]
MIN_PYTHON_VERSION_STR: str
compat_platform: str
env: str
value: str

@dataclass
class Options:
    audio: Sequence[str]
    debug_font: bool
    debug_gl: bool
    debug_gl_trace: bool
    debug_gl_trace_args: bool
    debug_gl_shaders: bool
    debug_graphics_batch: bool
    debug_lib: bool
    debug_media: bool
    debug_texture: bool
    debug_trace: bool
    debug_trace_args: bool
    debug_trace_depth: int
    debug_trace_flush: bool
    debug_win32: bool
    debug_input: bool
    debug_x11: bool
    shadow_window: bool
    vsync: bool | None
    xsync: bool
    xlib_fullscreen_override_redirect: bool
    search_local_libs: bool
    win32_gdi_font: bool
    headless: bool
    headless_device: int
    win32_disable_shaping: bool
    dw_legacy_naming: bool
    win32_disable_xinput: bool
    com_mta: bool
    osx_alt_loop: bool
    shader_bind_management: bool

    def get(self, item: str, default: Any = None) -> Any:
        ...

    def items(self) -> ItemsView[str, Any]:
        ...

    def __getitem__(self, item: str) -> Any:
        ...

options: Options
