from __future__ import annotations

import warnings
from ctypes import byref, c_int, c_uint
from typing import TYPE_CHECKING

from pyglet.graphics.api import gl
from pyglet.graphics.api.gl import lib, OpenGLSurfaceContext
from pyglet.graphics.api.gl.base import ContextException
from pyglet.graphics.api.gl.xlib import glx_info
from pyglet.libs.linux.glx import glxext_arb, glx, glxext_mesa

if TYPE_CHECKING:
    from pyglet.config.gl.x11 import XlibGLSurfaceConfig
    from pyglet.graphics.api.gl import OpenGLBackend
    from pyglet.window.xlib import XlibWindow
    from pyglet.libs.linux.x11.xlib import Display


class XlibContext(OpenGLSurfaceContext):
    x_display: Display
    glx_context: glx.GLXContext
    glx_window: glx.GLXWindow | None
    _use_video_sync: bool
    _vsync: bool
    config: XlibGLSurfaceConfig
    attached: bool = False

    _have_SGI_swap_control: bool  # noqa: N815
    _have_EXT_swap_control: bool  # noqa: N815
    _have_MESA_swap_control: bool  # noqa: N815
    _have_SGI_video_sync: bool  # noqa: N815

    def __init__(self,
                 opengl_backend: OpenGLBackend,
                 window: XlibWindow,
                 config: XlibGLSurfaceConfig,
                 share: XlibContext | None) -> None:
        self.x_display = window._x_display  # noqa: SLF001
        info = glx_info.GLXInfo(self.x_display)
        super().__init__(opengl_backend, window, config,
                         platform_info=info,
                         context_share=share)

        self.glx_context = self._create_glx_context(share)
        if not self.glx_context:
            # TODO: Check Xlib error generated
            msg = 'Could not create GL context'
            raise ContextException(msg)

        self._have_SGI_video_sync = info.have_extension('GLX_SGI_video_sync')
        self._have_SGI_swap_control = info.have_extension('GLX_SGI_swap_control')
        self._have_EXT_swap_control = info.have_extension('GLX_EXT_swap_control')
        self._have_MESA_swap_control = info.have_extension('GLX_MESA_swap_control')

        # In order of preference:
        # 1. GLX_EXT_swap_control (more likely to work where video_sync will not)
        # 2. GLX_MESA_swap_control (same as above, but supported by MESA drivers)
        # 3. GLX_SGI_video_sync (does not work on Intel 945GM, but that has EXT)
        # 4. GLX_SGI_swap_control (cannot be disabled once enabled)
        self._use_video_sync = (self._have_SGI_video_sync and
                                not (self._have_EXT_swap_control or self._have_MESA_swap_control))

        # XXX Mandate that vsync defaults on across all platforms.
        self._vsync = True
        self.glx_window = None

    def is_direct(self) -> bool:
        return bool(glx.glXIsDirect(self.x_display, self.glx_context))

    def _create_glx_context(self, share: XlibContext | None) -> glx.GLXContext:
        if share:
            share_context = share.glx_context
        else:
            share_context = None

        user_config = self.config.config

        attribs = []
        if user_config.major_version is not None:
            attribs.extend([glxext_arb.GLX_CONTEXT_MAJOR_VERSION_ARB, user_config.major_version])
        if user_config.minor_version is not None:
            attribs.extend([glxext_arb.GLX_CONTEXT_MINOR_VERSION_ARB, user_config.minor_version])

        if user_config.opengl_api == "gl":
            attribs.extend([glxext_arb.GLX_CONTEXT_PROFILE_MASK_ARB, glxext_arb.GLX_CONTEXT_CORE_PROFILE_BIT_ARB])
        elif user_config.opengl_api == "gles":
            attribs.extend([glxext_arb.GLX_CONTEXT_PROFILE_MASK_ARB, glxext_arb.GLX_CONTEXT_ES2_PROFILE_BIT_EXT])

        flags = 0
        if user_config.forward_compatible:
            flags |= glxext_arb.GLX_CONTEXT_FORWARD_COMPATIBLE_BIT_ARB
        if user_config.debug:
            flags |= glxext_arb.GLX_CONTEXT_DEBUG_BIT_ARB

        if flags:
            attribs.extend([glxext_arb.GLX_CONTEXT_FLAGS_ARB, flags])
        attribs.append(0)
        attribs = (c_int * len(attribs))(*attribs)

        return glxext_arb.glXCreateContextAttribsARB(self.window._x_display, self.config.fbconfig,  # noqa: SLF001
                                                     share_context, True, attribs)

    def attach(self, window: XlibWindow) -> None:
        if self.attached:
            return

        super().attach(window)

        self.glx_window = glx.glXCreateWindow(self.x_display,
                                              self.config.fbconfig, self.window._x_window,  # noqa: SLF001
                                              None)
        self.set_current()
        self.attached = True

    def set_current(self) -> None:
        glx.glXMakeContextCurrent(self.x_display, self.glx_window, self.glx_window, self.glx_context)
        super().set_current()

    def detach(self) -> None:
        if not self.attached:
            return

        self.set_current()
        gl.glFlush()

        super().detach()

        self.attached = False

        glx.glXMakeContextCurrent(self.x_display, 0, 0, None)
        if self.glx_window:
            glx.glXDestroyWindow(self.x_display, self.glx_window)
            self.glx_window = None

    def destroy(self) -> None:
        super().destroy()
        if self.glx_window:
            glx.glXDestroyWindow(self.x_display, self.glx_window)
            self.glx_window = None
        if self.glx_context:
            glx.glXDestroyContext(self.x_display, self.glx_context)
            self.glx_context = None

    def set_vsync(self, vsync: bool = True) -> None:
        self._vsync = vsync
        interval = (vsync and 1) or 0
        try:
            if not self._use_video_sync and self._have_EXT_swap_control:
                glxext_arb.glXSwapIntervalEXT(self.x_display, glx.glXGetCurrentDrawable(), interval)
            elif not self._use_video_sync and self._have_MESA_swap_control:
                glxext_mesa.glXSwapIntervalMESA(interval)
            elif self._have_SGI_swap_control:
                glxext_arb.glXSwapIntervalSGI(interval)
        except lib.MissingFunctionException as e:
            warnings.warn(str(e))

    def get_vsync(self) -> bool:
        return self._vsync

    def _wait_vsync(self) -> None:
        if self._vsync and self._have_SGI_video_sync and self._use_video_sync:
            count = c_uint()
            glxext_arb.glXGetVideoSyncSGI(byref(count))
            glxext_arb.glXWaitVideoSyncSGI(2, (count.value + 1) % 2, byref(count))

    def flip(self) -> None:
        if not self.glx_window:
            return

        if self._vsync:
            self._wait_vsync()

        glx.glXSwapBuffers(self.x_display, self.glx_window)
