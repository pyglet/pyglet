from __future__ import annotations

from ctypes import c_int

from pyglet.enums import GraphicsAPI
from pyglet.graphics.api.base import NullContext
from pyglet.graphics.api.gl.base import ContextException
from pyglet.graphics.api.gl.context import OpenGLSurfaceContext
from pyglet.libs.win32 import wgl
from pyglet.libs.win32.wgl import WGLFunctions
from pyglet.graphics.api.gl.win32.wgl_info import WGLInfo
from pyglet.libs.win32 import _gdi32
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyglet.config.gl.windows import GLSurfaceConfig, GLLegacyConfig
    from pyglet.graphics.api.gl.global_opengl import OpenGLBackend
    from pyglet.window.win32 import Win32Window


class _Win32Context(OpenGLSurfaceContext['Win32Window']):
    def __init__(self,
                 opengl_backend: OpenGLBackend,
                 window: Win32Window,
                 config: GLSurfaceConfig | GLLegacyConfig,
                 share: Win32Context | Win32ARBContext | None) -> None:
        super().__init__(opengl_backend, window, config,
                         platform_info=WGLInfo(), context_share=share, platform_func_class=WGLFunctions)

    def set_current(self) -> None:
        if self._context is not None and self != self.core.current_context:
            wgl.wglMakeCurrent(self.window._dc, self._context)  # noqa: SLF001
        super().set_current()

    def detach(self) -> None:
        if self._context:
            wgl.wglDeleteContext(self._context)
            self._context = None
        super().detach()

    def present(self) -> None:
        _gdi32.SwapBuffers(self.window._dc)  # noqa: SLF001

    def get_vsync(self) -> bool:
        if self.platform_func is not None and self._info.have_extension('WGL_EXT_swap_control'):
            return bool(self.platform_func.wglGetSwapIntervalEXT())
        return False

    def set_vsync(self, vsync: bool) -> None:
        if self.platform_func is not None and self._info.have_extension('WGL_EXT_swap_control'):
            self.platform_func.wglSwapIntervalEXT(int(vsync))


class Win32Context(_Win32Context):
    config: GLLegacyConfig
    context_share: Win32Context | None

    def attach(self, window: Win32Window) -> None:
        if not self._context:
            self.config.apply_format()
            self._context = wgl.wglCreateContext(window.dc)

        share = self.context_share
        if share:
            if not share.window:
                msg = 'Share context has no window.'
                raise RuntimeError(msg)
            if not wgl.wglShareLists(share._context, self._context):  # noqa: SLF001
                msg = 'Unable to share contexts.'
                raise ContextException(msg)

        super().attach(window)


class Win32ARBContext(_Win32Context):
    config: GLSurfaceConfig
    context_share: Win32ARBContext | None

    def attach(self, window: Win32Window) -> None:
        share = self.context_share
        share_handle = None
        if share:
            if not share.window:
                msg = 'Share context has no window.'
                raise RuntimeError(msg)
            share_handle = share._context  # noqa: SLF001

        attribs = []
        user_config = self.config.config
        if user_config.major_version is not None:
            attribs.extend([wgl.WGL_CONTEXT_MAJOR_VERSION_ARB, user_config.major_version])
        if user_config.minor_version is not None:
            attribs.extend([wgl.WGL_CONTEXT_MINOR_VERSION_ARB, user_config.minor_version])
        flags = 0
        if user_config.forward_compatible and not user_config.api:
            flags |= wgl.WGL_CONTEXT_FORWARD_COMPATIBLE_BIT_ARB
        if user_config.debug:
            flags |= wgl.WGL_CONTEXT_DEBUG_BIT_ARB
        if user_config.api in (GraphicsAPI.OPENGL_ES_2, GraphicsAPI.OPENGL_ES_3):
            attribs.extend([wgl.WGL_CONTEXT_PROFILE_MASK_ARB, wgl.WGL_CONTEXT_ES2_PROFILE_BIT_EXT])
        if flags:
            attribs.extend([wgl.WGL_CONTEXT_FLAGS_ARB, flags])
        attribs.append(0)
        attrib_array = (c_int * len(attribs))(*attribs)

        self.config.apply_format()

        from pyglet.config.gl.windows import _global_wgl
        self._context = _global_wgl.funcs.wglCreateContextAttribsARB(window.dc, share_handle, attrib_array)
        super().attach(window)
