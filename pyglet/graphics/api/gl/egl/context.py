from __future__ import annotations

from typing import TYPE_CHECKING

from pyglet.graphics.api.gl import OpenGLSurfaceContext
from pyglet.graphics.api.gl.base import ContextException
from pyglet.libs import egl

if TYPE_CHECKING:
    from pyglet.config.gl.egl import EGLSurfaceConfig
    from pyglet.graphics.api.gl.base import OpenGLBackend
    from pyglet.window.wayland import WaylandWindow
    from pyglet.window.headless import HeadlessWindow


class EGLContext(OpenGLSurfaceContext):
    display_connection: egl.EGLDisplay
    config: EGLSurfaceConfig

    def __init__(self,
                 opengl_backend: OpenGLBackend,
                 window: HeadlessWindow | WaylandWindow,
                 config: EGLSurfaceConfig,
                 share: EGLContext | None) -> None:
        super().__init__(opengl_backend, window, config=config, context_share=share)

        self.display_connection = window.egl_display_connection  # noqa: SLF001
        self._extensions = []

        self.egl_context = self._create_egl_context(share)
        if not self.egl_context:
            msg = 'Could not create GL context'
            raise ContextException(msg)

    def _create_egl_context(self, share: EGLContext | None) -> egl.EGLContext:
        if share:
            share_context = share.egl_context
        else:
            share_context = None

        user_config = self.config.config

        if user_config.opengl_api == "gl":
            egl.eglBindAPI(egl.EGL_OPENGL_API)
        elif user_config.opengl_api == "gles":
            egl.eglBindAPI(egl.EGL_OPENGL_ES_API)
        return egl.eglCreateContext(
            self.window.egl_display_connection,  # noqa: SLF001
            self.config._egl_config,
            share_context,
            self.config._context_attrib_array,
        )

    def get_extensions(self) -> list[str]:
        if not self._extensions:
            self._extensions = egl.eglQueryString(self.window._egl_display_connection, egl.EGL_EXTENSIONS).decode().split()
        return self._extensions

    def attach(self, window: HeadlessWindow | WaylandWindow) -> None:
        super().attach(window)

        self.egl_surface = window.egl_surface  # noqa: SLF001
        self.set_current()

    def set_current(self) -> None:
        success = egl.eglMakeCurrent(self.display_connection, self.egl_surface, self.egl_surface, self.egl_context)
        super().set_current()

    def detach(self) -> None:
        if not self.window:
            return

        self.set_current()
        #gl.glFlush()  # needs to be in try/except?

        super().detach()

        egl.eglMakeCurrent(self.display_connection, 0, 0, None)

        self.egl_surface = None

    def destroy(self) -> None:
        super().destroy()
        if self.egl_context:
            egl.eglDestroyContext(self.display_connection, self.egl_context)
            self.egl_context = None

    def flip(self) -> None:
        if not self.egl_surface:
            return

        egl.eglSwapBuffers(self.display_connection, self.egl_surface)
