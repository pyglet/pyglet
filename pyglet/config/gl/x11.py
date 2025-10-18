from __future__ import annotations

from dataclasses import asdict
from typing import NoReturn, TYPE_CHECKING

from ctypes import c_int, cast, byref, POINTER, _Pointer

from pyglet.libs.linux.glx import glx
from pyglet.libs.linux.x11 import xlib
from pyglet.libs.linux.x11.xrender import XRenderFindVisualFormat
from pyglet.config import SurfaceConfig

if TYPE_CHECKING:
    from pyglet.graphics.api.gl.xlib.context import XlibContext
    from pyglet.graphics.api import OpenGLBackend
    from pyglet.config import OpenGLConfig
    from pyglet.graphics.api.gl.xlib import glx_info
    from pyglet.window.xlib import XlibWindow


def match(config: OpenGLConfig, window: XlibWindow) -> XlibGLSurfaceConfig | None:
    x_display = window._x_display  # noqa: SLF001
    x_screen = window._x_screen_id  # noqa: SLF001

    # Construct array of attributes
    attrs = []
    for name, value in asdict(config).items():
        attr = XlibGLSurfaceConfig.attribute_ids.get(name, None)
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

    result = [XlibGLSurfaceConfig(window, c, config) for c in configs]

    # If we intend to have a transparent framebuffer.
    if config.transparent_framebuffer:
        result = [fb_cf for fb_cf in result if fb_cf.transparent]

    # If we intend to have a transparent framebuffer.
    if config.transparent_framebuffer:
        result = [fb_cf for fb_cf in result if fb_cf.transparent]

    # Can't free array until all XlibGLConfig's are GC'd.  Too much
    # hassle, live with leak. XXX
    # xlib.XFree(configs)
    return result[0]


class XlibGLSurfaceConfig(SurfaceConfig):
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
                 config: OpenGLConfig) -> None:
        super().__init__(window, config, fbconfig)

        self.fbconfig = fbconfig
        self.transparent = False

        for name, attr in self.attribute_ids.items():
            value = c_int()
            result = glx.glXGetFBConfigAttrib(self._window._x_display, self.fbconfig, attr,  # noqa: SLF001
                                              byref(value))
            if result >= 0:
                setattr(self, name, value.value)

        # If user intends for a transparent framebuffer, the visual info needs to be
        # queried for it. Even if a config supports alpha_size 8 and depth_size 32, there is no
        # guarantee the visual info supports that same configuration.
        if config.transparent_framebuffer:
            xvi_ptr = glx.glXGetVisualFromFBConfig(self._window._x_display, self.fbconfig)  # noqa: SLF001
            if xvi_ptr:
                self.transparent = window._is_visual_transparent(xvi_ptr.contents.visual)  # noqa: SLF001
                xlib.XFree(xvi_ptr)

    def _is_visual_transparent(self, visual: _Pointer[xlib.Visual]) -> bool:
        if not XRenderFindVisualFormat:
            return False

        xrender_format = XRenderFindVisualFormat(self.canvas.display._display, visual)
        return xrender_format and xrender_format.contents.direct.alphaMask != 0

    def get_visual_info(self) -> glx.XVisualInfo:
        return glx.glXGetVisualFromFBConfig(self._window._x_display, self.fbconfig).contents  # noqa: SLF001

    def create_context(self, opengl_backend: OpenGLBackend, share: XlibContext | None) -> XlibContext:
        from pyglet.graphics.api.gl.xlib.context import XlibContext  # noqa: PLC0415
        return XlibContext(opengl_backend, self._window, self, share)

    def _create_glx_context(self, _share: None) -> NoReturn:
        raise NotImplementedError

    def apply_format(self) -> None:
        pass

    def is_complete(self) -> bool:
        return True
