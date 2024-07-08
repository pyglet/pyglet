from __future__ import annotations

import warnings
from ctypes import POINTER, byref, c_int, c_uint, cast
from typing import TYPE_CHECKING, NoReturn

from pyglet import gl
from pyglet.canvas.xlib import XlibCanvas
from pyglet.gl import glx, glx_info, glxext_arb, glxext_mesa, lib

from .base import CanvasConfig, Config, Context

if TYPE_CHECKING:
    from pyglet.libs.x11.xlib import Display

    from .glx_info import GLXInfo


class XlibConfig(Config):  # noqa: D101

    def match(self, canvas: XlibCanvas) -> list[XlibCanvasConfig]:
        if not isinstance(canvas, XlibCanvas):
            msg = 'Canvas must be an instance of XlibCanvas'
            raise RuntimeError(msg)

        x_display = canvas.display._display  # noqa: SLF001
        x_screen = canvas.display.x_screen

        info = glx_info.GLXInfo(x_display)

        # Construct array of attributes
        attrs = []
        for name, value in self.get_gl_attributes():
            attr = XlibCanvasConfig.attribute_ids.get(name, None)
            if attr and value is not None:
                attrs.extend([attr, int(value)])

        attrs.extend([glx.GLX_X_RENDERABLE, True])
        attrs.extend([0, 0])  # attrib_list must be null terminated

        attrib_list = (c_int * len(attrs))(*attrs)

        elements = c_int()
        configs = glx.glXChooseFBConfig(x_display, x_screen, attrib_list, byref(elements))
        if not configs:
            return []

        configs = cast(configs, POINTER(glx.GLXFBConfig * elements.value)).contents

        result = [XlibCanvasConfig(canvas, info, c, self) for c in configs]

        # Can't free array until all XlibGLConfig's are GC'd.  Too much
        # hassle, live with leak. XXX
        # xlib.XFree(configs)

        return result


class XlibCanvasConfig(CanvasConfig):  # noqa: D101
    glx_info: GLXInfo

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
        'render_type': glx.GLX_RENDER_TYPE,
        'config_caveat': glx.GLX_CONFIG_CAVEAT,
        'transparent_type': glx.GLX_TRANSPARENT_TYPE,
        'transparent_index_value': glx.GLX_TRANSPARENT_INDEX_VALUE,
        'transparent_red_value': glx.GLX_TRANSPARENT_RED_VALUE,
        'transparent_green_value': glx.GLX_TRANSPARENT_GREEN_VALUE,
        'transparent_blue_value': glx.GLX_TRANSPARENT_BLUE_VALUE,
        'transparent_alpha_value': glx.GLX_TRANSPARENT_ALPHA_VALUE,

        # Used internally
        'x_renderable': glx.GLX_X_RENDERABLE,
    }

    def __init__(self, canvas: XlibCanvas, info: GLXInfo, fbconfig: glx.GLXFBConfig,  # noqa: D107
                 config: XlibConfig) -> None:
        super().__init__(canvas, config)

        self.glx_info = info
        self.fbconfig = fbconfig

        for name, attr in self.attribute_ids.items():
            value = c_int()
            result = glx.glXGetFBConfigAttrib(canvas.display._display, self.fbconfig, attr,  # noqa: SLF001
                                              byref(value))
            if result >= 0:
                setattr(self, name, value.value)

    def get_visual_info(self) -> glx.XVisualInfo:
        return glx.glXGetVisualFromFBConfig(self.canvas.display._display, self.fbconfig).contents  # noqa: SLF001

    def create_context(self, share: XlibContext | None) -> XlibContext:
        return XlibContext(self, share)

    def compatible(self, canvas: XlibCanvas) -> bool:
        # TODO check more
        return isinstance(canvas, XlibCanvas)

    def _create_glx_context(self, _share: None) -> NoReturn:
        raise NotImplementedError

    def is_complete(self) -> bool:
        return True


class XlibContext(Context):  # noqa: D101
    x_display: Display
    glx_context: glx.GLXContext
    glx_window: glx.GLXWindow | None
    _use_video_sync: bool
    _vsync: bool
    config: XlibCanvasConfig

    _have_SGI_swap_control: bool  # noqa: N815
    _have_EXT_swap_control: bool  # noqa: N815
    _have_MESA_swap_control: bool  # noqa: N815
    _have_SGI_video_sync: bool  # noqa: N815

    def __init__(self, config: XlibCanvasConfig, share: XlibContext | None) -> None:  # noqa: D107
        super().__init__(config, share)

        self.x_display = config.canvas.display._display  # noqa: SLF001

        self.glx_context = self._create_glx_context(share)
        if not self.glx_context:
            # TODO: Check Xlib error generated
            msg = 'Could not create GL context'
            raise gl.ContextException(msg)

        self._have_SGI_video_sync = config.glx_info.have_extension('GLX_SGI_video_sync')
        self._have_SGI_swap_control = config.glx_info.have_extension('GLX_SGI_swap_control')
        self._have_EXT_swap_control = config.glx_info.have_extension('GLX_EXT_swap_control')
        self._have_MESA_swap_control = config.glx_info.have_extension('GLX_MESA_swap_control')

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

        return glxext_arb.glXCreateContextAttribsARB(self.config.canvas.display._display,  # noqa: SLF001
                                                     self.config.fbconfig, share_context, True, attribs)

    def attach(self, canvas: XlibCanvas) -> None:
        if canvas is self.canvas:
            return

        super().attach(canvas)

        self.glx_window = glx.glXCreateWindow(self.x_display, self.config.fbconfig, canvas.x_window, None)
        self.set_current()

    def set_current(self) -> None:
        glx.glXMakeContextCurrent(self.x_display, self.glx_window, self.glx_window, self.glx_context)
        super().set_current()

    def detach(self) -> None:
        if not self.canvas:
            return

        self.set_current()
        gl.glFlush()

        super().detach()

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
        interval = vsync and 1 or 0
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
