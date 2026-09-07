"""EAGL-backed OpenGL ES context for UIKit windows."""
from __future__ import annotations

from ctypes import byref
from typing import TYPE_CHECKING

from pyglet.enums import GraphicsAPI
from pyglet.graphics.api.gl import OpenGLSurfaceContext
from pyglet.graphics.api.gl.base import ContextException
from pyglet.graphics.api.gl.gl import (
    GL_COLOR_ATTACHMENT0,
    GL_DEPTH_ATTACHMENT,
    GL_DEPTH_COMPONENT16,
    GL_FRAMEBUFFER,
    GL_FRAMEBUFFER_COMPLETE,
    GL_RENDERBUFFER,
    GLuint,
)
from pyglet.libs.darwin.cocoapy import ObjCClass

if TYPE_CHECKING:
    from pyglet.config.gl.ios import IOSGLSurfaceConfig
    from pyglet.graphics.api.gl.global_opengl import OpenGLBackend
    from pyglet.window.apple.ios import IOSWindow

# Embedded Apple GL Context.
EAGLContext = ObjCClass('EAGLContext')
kEAGLRenderingAPIOpenGLES1 = 1
kEAGLRenderingAPIOpenGLES2 = 2
kEAGLRenderingAPIOpenGLES3 = 3


class IOSContext(OpenGLSurfaceContext):
    config: IOSGLSurfaceConfig

    def __init__(self, opengl_backend: OpenGLBackend, window: IOSWindow,
                 config: IOSGLSurfaceConfig, share: IOSContext | None) -> None:
        super().__init__(opengl_backend, window, config=config, context_share=share)
        api = kEAGLRenderingAPIOpenGLES3 if config.config.api == GraphicsAPI.OPENGL_ES_3 else kEAGLRenderingAPIOpenGLES2
        self.eagl_context = EAGLContext.alloc().initWithAPI_(api)
        if not self.eagl_context:
            raise ContextException('Could not create an EAGL context')

        self._framebuffer = GLuint()
        self._color_renderbuffer = GLuint()
        self._depth_renderbuffer = GLuint()
        self._vsync = True

    def attach(self, window: IOSWindow) -> None:
        super().attach(window)
        self.set_current()
        self._create_default_fbo()

    def _create_default_fbo(self) -> None:
        # On iOS there is no default window framebuffer; create it ourselves.
        # Use Framebuffer object later?
        self._delete_default_fbo()
        self.glGenFramebuffers(1, byref(self._framebuffer))
        self.glBindFramebuffer(GL_FRAMEBUFFER, self._framebuffer)
        self.glGenRenderbuffers(1, byref(self._color_renderbuffer))
        self.glBindRenderbuffer(GL_RENDERBUFFER, self._color_renderbuffer)
        if not self.eagl_context.renderbufferStorage_fromDrawable_(GL_RENDERBUFFER, self.window._ios_layer):  # noqa: SLF001
            raise ContextException('Could not allocate an EAGL drawable')
        self.glFramebufferRenderbuffer(
            GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_RENDERBUFFER, self._color_renderbuffer,
        )

        if self.config.depth_size:
            self.glGenRenderbuffers(1, byref(self._depth_renderbuffer))
            self.glBindRenderbuffer(GL_RENDERBUFFER, self._depth_renderbuffer)
            self.glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT16, self.window._width, self.window._height)  # noqa: SLF001
            self.glFramebufferRenderbuffer(
                GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, self._depth_renderbuffer,
            )

        if self.glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            raise ContextException('The EAGL framebuffer is incomplete')

    def _delete_default_fbo(self) -> None:
        if self._depth_renderbuffer.value:
            self.glDeleteRenderbuffers(1, byref(self._depth_renderbuffer))
            self._depth_renderbuffer = GLuint()
        if self._color_renderbuffer.value:
            self.glDeleteRenderbuffers(1, byref(self._color_renderbuffer))
            self._color_renderbuffer = GLuint()
        if self._framebuffer.value:
            self.glDeleteFramebuffers(1, byref(self._framebuffer))
            self._framebuffer = GLuint()

    def set_current(self) -> None:
        if not EAGLContext.setCurrentContext_(self.eagl_context):
            raise ContextException('Could not make the EAGL context current')
        super().set_current()

    def _bind_default_fbo(self) -> None:
        """Bind the EAGL drawable used as this window's default framebuffer."""
        self.glBindFramebuffer(GL_FRAMEBUFFER, self._framebuffer)

    def frame_begin(self) -> None:
        super().frame_begin()
        self._bind_default_fbo()

    def update_geometry(self) -> None:
        self.set_current()
        self._create_default_fbo()

    def detach(self) -> None:
        if self.eagl_context:
            EAGLContext.setCurrentContext_(None)
        super().detach()

    def destroy(self) -> None:
        if self.eagl_context:
            self.set_current()
            self._delete_default_fbo()
        super().destroy()
        if self.eagl_context:
            self.eagl_context.release()
            self.eagl_context = None

    def set_vsync(self, vsync: bool = True) -> None:
        # Does nothing. Timing is controlled by UIKit's display loop.
        self._vsync = vsync

    def get_vsync(self) -> bool:
        return self._vsync

    def present(self) -> None:
        self._bind_default_fbo()
        self.glBindRenderbuffer(GL_RENDERBUFFER, self._color_renderbuffer)
        self.eagl_context.presentRenderbuffer_(GL_RENDERBUFFER)
