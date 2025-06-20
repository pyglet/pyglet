from __future__ import annotations

import warnings
from ctypes import POINTER, byref, c_int, c_uint, cast
from typing import TYPE_CHECKING, NoReturn

from pyglet.graphics.api import gl
from pyglet.graphics.api.gl import lib, OpenGLSurfaceContext
from pyglet.graphics.api.gl.base import OpenGLConfig, OpenGLWindowConfig, ContextException
from pyglet.graphics.api.gl.xlib import glxext_arb, glx, glx_info, glxext_mesa
from pyglet.libs.linux.x11 import xlib

if TYPE_CHECKING:
    from pyglet.graphics.api.gl import OpenGLBackend
    from pyglet.window.xlib import XlibWindow
    from pyglet.libs.linux.x11 import Display


class XlibOpenGLConfig(OpenGLConfig):

    def match(self, window: XlibWindow) -> XlibGLWindowConfig | None:
        x_display = window._x_display  # noqa: SLF001
        x_screen = window._x_screen_id  # noqa: SLF001

        # Construct array of attributes
        attrs = []
        for name, value in self.get_gl_attributes():
            attr = XlibGLWindowConfig.attribute_ids.get(name, None)
            if attr and value is not None:
                attrs.extend([attr, int(value)])

        attrs.extend([glx.GLX_X_RENDERABLE, True])
        attrs.extend([0, 0])  # attrib_list must be null terminated

        attrib_list = (c_int * len(attrs))(*attrs)

        elements = c_int()
        configs = glx.glXChooseFBConfig(x_display, x_screen, attrib_list, byref(elements))
        if not configs:
            return None

        configs = cast(configs, POINTER(glx.GLXFBConfig * elements.value)).contents

        result = [XlibGLWindowConfig(window, c, self) for c in configs]

        # If we intend to have a transparent framebuffer.
        if self.transparent_framebuffer:
            result = [fb_cf for fb_cf in result if fb_cf.transparent]

        # Can't free array until all XlibGLConfig's are GC'd.  Too much
        # hassle, live with leak. XXX
        # xlib.XFree(configs)
        return result[0]


class XlibGLWindowConfig(OpenGLWindowConfig):
    _glx_info: glx_info.GLXInfo

    attribute_ids = {  # noqa: RUF012
        'buffer_size': glx.GLX_BUFFER_SIZE,
        'level': glx.GLX_LEVEL,  # Not supported
        'double_buffer': glx.GLX_DOUBLEBUFFER,
        'stereo': glx.GLX_STEREO,
        'aux_buffers': glx.GLX_AUX_BUFFERS,
        'red_size': glx.GLX_RED_SIZE,
        'green_size': glx.GLX_GREEN_SIZE,
        'blue_size': glx.GLX_BLUE_SIZE,
        'alpha_size': glx.GLX_ALPHA_SIZE,
        'depth_size': glx.GLX_DEPTH_SIZE,
        'stencil_size': glx.GLX_STENCIL_SIZE,
        'accum_red_size': glx.GLX_ACCUM_RED_SIZE,
        'accum_green_size': glx.GLX_ACCUM_GREEN_SIZE,
        'accum_blue_size': glx.GLX_ACCUM_BLUE_SIZE,
        'accum_alpha_size': glx.GLX_ACCUM_ALPHA_SIZE,

        'sample_buffers': glx.GLX_SAMPLE_BUFFERS,
        'samples': glx.GLX_SAMPLES,

        # Not supported in current pyglet API:
        # 'render_type': glx.GLX_RENDER_TYPE,
        # 'drawable_type': glx.GLX_DRAWABLE_TYPE,
        # 'config_caveat': glx.GLX_CONFIG_CAVEAT,
        # 'transparent_type': glx.GLX_TRANSPARENT_TYPE,
        # 'transparent_index_value': glx.GLX_TRANSPARENT_INDEX_VALUE,
        # 'transparent_red_value': glx.GLX_TRANSPARENT_RED_VALUE,
        # 'transparent_green_value': glx.GLX_TRANSPARENT_GREEN_VALUE,
        # 'transparent_blue_value': glx.GLX_TRANSPARENT_BLUE_VALUE,
        # 'transparent_alpha_value': glx.GLX_TRANSPARENT_ALPHA_VALUE,

        # Used internally
        'x_renderable': glx.GLX_X_RENDERABLE,
    }

    def __init__(self, window: XlibWindow, fbconfig: glx.GLXFBConfig,
                 config: XlibOpenGLConfig) -> None:
        super().__init__(window, config)

        self.transparent = False

        self._fbconfig = fbconfig

        for name, attr in self.attribute_ids.items():
            value = c_int()
            result = glx.glXGetFBConfigAttrib(self._window._x_display, self._fbconfig, attr,  # noqa: SLF001
                                              byref(value))
            if result >= 0:
                setattr(self, name, value.value)

        # If user intends for a transparent framebuffer, the visual info needs to be
        # queried for it. Even if a config supports alpha_size 8 and depth_size 32, there is no
        # guarantee the visual info supports that same configuration.
        if config.transparent_framebuffer:
            xvi_ptr = glx.glXGetVisualFromFBConfig(self._window._x_display, self._fbconfig)  # noqa: SLF001
            if xvi_ptr:
                self.transparent = window._is_visual_transparent(xvi_ptr.contents.visual)  # noqa: SLF001
                xlib.XFree(xvi_ptr)

    def get_visual_info(self) -> glx.XVisualInfo:
        return glx.glXGetVisualFromFBConfig(self._window._x_display, self._fbconfig).contents  # noqa: SLF001

    def create_context(self, opengl_backend: OpenGLBackend, share: XlibContext | None) -> XlibContext:
        return XlibContext(opengl_backend, self._window, self, share)

    def _create_glx_context(self, _share: None) -> NoReturn:
        raise NotImplementedError

    def apply_format(self) -> None:
        pass

    def is_complete(self) -> bool:
        return True


class XlibContext(OpenGLSurfaceContext):
    x_display: Display
    glx_context: glx.GLXContext
    glx_window: glx.GLXWindow | None
    _use_video_sync: bool
    _vsync: bool
    config: XlibGLWindowConfig
    attached: bool = False

    _have_SGI_swap_control: bool  # noqa: N815
    _have_EXT_swap_control: bool  # noqa: N815
    _have_MESA_swap_control: bool  # noqa: N815
    _have_SGI_video_sync: bool  # noqa: N815

    def __init__(self,
                 opengl_backend: OpenGLBackend,
                 window: XlibWindow,
                 config: XlibGLWindowConfig,
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

        attribs = []
        if self.config.major_version is not None:
            attribs.extend([glxext_arb.GLX_CONTEXT_MAJOR_VERSION_ARB, self.config.major_version])
        if self.config.minor_version is not None:
            attribs.extend([glxext_arb.GLX_CONTEXT_MINOR_VERSION_ARB, self.config.minor_version])

        if self.config.opengl_api == "gl":
            attribs.extend([glxext_arb.GLX_CONTEXT_PROFILE_MASK_ARB, glxext_arb.GLX_CONTEXT_CORE_PROFILE_BIT_ARB])
        elif self.config.opengl_api == "gles":
            attribs.extend([glxext_arb.GLX_CONTEXT_PROFILE_MASK_ARB, glxext_arb.GLX_CONTEXT_ES2_PROFILE_BIT_EXT])

        flags = 0
        if self.config.forward_compatible:
            flags |= glxext_arb.GLX_CONTEXT_FORWARD_COMPATIBLE_BIT_ARB
        if self.config.debug:
            flags |= glxext_arb.GLX_CONTEXT_DEBUG_BIT_ARB

        if flags:
            attribs.extend([glxext_arb.GLX_CONTEXT_FLAGS_ARB, flags])
        attribs.append(0)
        attribs = (c_int * len(attribs))(*attribs)

        return glxext_arb.glXCreateContextAttribsARB(self.window._x_display, self.config._fbconfig,  # noqa: SLF001
                                                     share_context, True, attribs)

    def attach(self, window: XlibWindow) -> None:
        if self.attached:
            return

        super().attach(window)

        self.glx_window = glx.glXCreateWindow(self.x_display,
                                              self.config._fbconfig, self.window._x_window,  # noqa: SLF001
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
