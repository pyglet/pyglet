"""
Demonstrates creation of a basic overlay window in pyglet
"""

from pyglet.graphics import Batch
from pyglet.window import Window
from pyglet.text import Label
from pyglet.libs.win32.types import *
from pyglet.libs.win32 import _gdi32, _dwmapi
from pyglet.gl import *


class DWM_BLURBEHIND(ctypes.Structure):
    _fields_ = [
        ("dwFlags", DWORD),
        ("fEnable", BOOL),
        ("hRgnBlur", HRGN),
        ("fTransitionOnMaximized", DWORD),
    ]


DWM_BB_ENABLE = 0x00000001
DWM_BB_BLURREGION = 0x00000002
DWM_BB_TRANSITIONONMAXIMIZED = 0x00000004


def updateTransparency(hwnd):
    region = _gdi32.CreateRectRgn(0, 0, -1, -1)
    bb = DWM_BLURBEHIND()
    bb.dwFlags = DWM_BB_ENABLE | DWM_BB_BLURREGION
    bb.hRgnBlur = region
    bb.fEnable = True

    _dwmapi.DwmEnableBlurBehindWindow(hwnd, ctypes.byref(bb))
    _gdi32.DeleteObject(region)


topmost = True
batch = Batch()
config = Config(vsync=False)
window = Window(500, 500, style=Window.WINDOW_STYLE_OVERLAY, config=config)
label1 = Label("Test", x=100, y=250, batch=batch, font_size=72,
               color=(255, 255, 0, 255))


@window.event
def on_draw():
    window.clear()
    batch.draw()
    updateTransparency(window._hwnd)
    glFlush()


pyglet.app.run()
