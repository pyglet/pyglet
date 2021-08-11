import win32gui
import win32con
import win32api
from pyglet.graphics import Batch
from pyglet.window import Window
from pyglet.text import Label
from pyglet.libs.win32.types import *
from pyglet.libs.win32 import _gdi32, _dwmapi
from pyglet.gl import *

NOSIZE = 1
NOMOVE = 2


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


# def set_working_transparency(hwnd):
#     """
#     This is slow at high resolutions 30fps@4k and appears to be windows-limited
#     """
#
#     window_styles = win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
#
#     # Setting attribs. for our window to support transparency
#     win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, window_styles)
#
#     win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(0, 0, 0), 254,
#                                         win32con.LWA_ALPHA)
#
#     if topmost:
#         win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
#                               NOMOVE | NOSIZE)


topmost = True
batch = Batch()
config = Config(vsync=False, alpha_size=4)
window = Window(500, 500, style=Window.WINDOW_STYLE_TRANSPARENT_OVERLAY, config=config)
label1 = Label("Test", x=100, y=250, batch=batch, font_size=72,
               color=(255, 255, 0, 255))

glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)


@window.event
def on_draw():
    window.clear()
    batch.draw()
    updateTransparency(window._hwnd)
    glFlush()

pyglet.app.run()