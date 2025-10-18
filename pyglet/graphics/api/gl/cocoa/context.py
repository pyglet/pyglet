from __future__ import annotations

from ctypes import byref, c_int
from typing import TYPE_CHECKING

from pyglet.config.gl.macos import os_x_release, _os_x_version, CocoaGLSurfaceConfig
from pyglet.graphics.api.gl.base import ContextException
from pyglet.graphics.api.gl import OpenGLSurfaceContext
from pyglet.libs.darwin import cocoapy

if TYPE_CHECKING:
    from pyglet.graphics.api.gl.global_opengl import OpenGLBackend
    from pyglet.window.cocoa import CocoaWindow

NSOpenGLPixelFormat = cocoapy.ObjCClass('NSOpenGLPixelFormat')
NSOpenGLContext = cocoapy.ObjCClass('NSOpenGLContext')


class CocoaContext(OpenGLSurfaceContext):

    def __init__(self,
                 opengl_backend: OpenGLBackend,
                 window: CocoaWindow,
                 config: CocoaGLSurfaceConfig,
                 nscontext: NSOpenGLContext,
                 share: CocoaContext | None) -> None:
        super().__init__(opengl_backend, window, config, platform_info=None, context_share=share)
        self.config = config
        self._nscontext = nscontext

    def attach(self, window: CocoaWindow) -> None:
        # See if we want OpenGL 3 in a non-Lion OS
        if _os_x_version < os_x_release['lion']:
            msg = 'OpenGL 3 not supported'
            raise ContextException(msg)

        super().attach(window)
        # The NSView instance should be attached to a nondeferred window before calling
        # setView, otherwise you get an "invalid drawable" message.
        self._nscontext.setView_(window._nsview)  # noqa: SLF001

        self.set_current()

    def detach(self) -> None:
        super().detach()
        self._nscontext.clearDrawable()

    def set_current(self) -> None:
        self._nscontext.makeCurrentContext()
        super().set_current()

    def update_geometry(self) -> None:
        # Need to call this method whenever the context drawable (an NSView)
        # changes size or location.
        self._nscontext.update()

    def set_full_screen(self) -> None:
        self._nscontext.makeCurrentContext()
        self._nscontext.setFullScreen()

    def destroy(self) -> None:
        super().destroy()
        self._nscontext.release()
        self._nscontext = None

    def set_vsync(self, vsync: bool = True) -> None:
        vals = c_int(vsync)
        self._nscontext.setValues_forParameter_(byref(vals), cocoapy.NSOpenGLCPSwapInterval)

    def get_vsync(self) -> bool:
        vals = c_int()
        self._nscontext.getValues_forParameter_(byref(vals), cocoapy.NSOpenGLCPSwapInterval)
        return bool(vals.value)

    def flip(self) -> None:
        self._nscontext.flushBuffer()
