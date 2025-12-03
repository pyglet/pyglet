from __future__ import annotations

import warnings
from ctypes import c_int, c_uint, sizeof, byref
from dataclasses import asdict

from typing import TYPE_CHECKING
from pyglet.config.gl import GLSurfaceConfig
from pyglet.libs.win32 import PIXELFORMATDESCRIPTOR, _gdi32, wglext_arb, wgl
from pyglet.libs.win32.constants import PFD_DRAW_TO_WINDOW, PFD_SUPPORT_OPENGL, PFD_DOUBLEBUFFER, \
    PFD_DOUBLEBUFFER_DONTCARE, PFD_STEREO, PFD_STEREO_DONTCARE, PFD_DEPTH_DONTCARE, PFD_TYPE_RGBA
from pyglet.libs.win32.wgl import WGLFunctions
from pyglet.util import asstr

if TYPE_CHECKING:
    from pyglet.config import OpenGLConfig
    from pyglet.window.win32 import Win32Window
    from pyglet.graphics.api import OpenGLBackend
    from pyglet.graphics.api.gl.win32.context import Win32ARBContext, Win32Context


class _WGL:
    """This is a staging area for WGL function loading.

    WGL requires a context to be active before many functions can be called. Paradoxically, to create a WGL context,
    another context has to already exist. Therefore, a bare temporary context is created and then destroyed after WGL
    proc addresses are loaded and stored.
    """
    def __init__(self):
        self._funcs = None
        self._loaded = False
        self._extensions = []

    @property
    def funcs(self):
        return self._funcs

    @property
    def loaded(self) -> bool:
        return self._loaded

    def have_extension(self, extension: str) -> bool:
        return extension in self._extensions

    def create(self) -> bool:
        from pyglet.window import _shadow_window  # noqa: PLC0415
        funcs = self._initialize_wgl_funcs(_shadow_window)
        if funcs:
            self._loaded = True
            self._funcs = funcs
            self._extensions = asstr(funcs.wglGetExtensionsStringEXT()).split()
            return True

        return False

    def _initialize_wgl_funcs(self, shadow_window: Win32Window) -> WGLFunctions | None:
        """Creates a temporary context, creates WGL functions to proc addresses, then destroys the context."""
        pfd = PIXELFORMATDESCRIPTOR()
        pfd.nSize = sizeof(PIXELFORMATDESCRIPTOR)
        pfd.nVersion = 1
        pfd.dwFlags = PFD_DRAW_TO_WINDOW | PFD_SUPPORT_OPENGL | PFD_DOUBLEBUFFER
        pfd.iPixelType = PFD_TYPE_RGBA
        pfd.cColorBits = 24

        shadow_dc = shadow_window.dc
        assert shadow_dc is not None

        # !!! # Will break transparent windows if using the main visible window.
        #  Must use the shadow window here as once a pixel format is set for a Window it cannot be altered.
        pf = _gdi32.ChoosePixelFormat(shadow_dc, byref(pfd))
        if pf:
            if not _gdi32.SetPixelFormat(shadow_dc, pf, byref(pfd)):
                warnings.warn("Unable to set pixel format.")
                return None
        else:
            warnings.warn("Unable to find a pixel format.")
            return None

        dummy_ctx = wgl.wglCreateContext(shadow_dc)
        if not dummy_ctx:
            warnings.warn("Unable to create dummy context.")
            return None

        current_dc = wgl.wglGetCurrentDC()
        current_ctx = wgl.wglGetCurrentContext()

        if not wgl.wglMakeCurrent(shadow_dc, dummy_ctx):
            print("Unable to make dummy context current.")
            # Set back to old context and dc and delete dummy context.
            wgl.wglMakeCurrent(current_dc, current_ctx)
            wgl.wglDeleteContext(dummy_ctx)
            return None

        funcs = WGLFunctions()
        wgl.wglMakeCurrent(current_dc, current_ctx)
        wgl.wglDeleteContext(dummy_ctx)
        return funcs

# A global WGL instance object that has retrieved all the proc addresses for WGL functions.
_global_wgl = _WGL()

def match(config: OpenGLConfig, window: Win32Window) -> GLSurfaceConfig | None:
    if not _global_wgl.loaded:
        _global_wgl.create()

    if _global_wgl.have_extension('WGL_ARB_pixel_format'):
         finalized_config = _get_arb_pixel_format_matching_configs(config, window)
    else:
        finalized_config = _get_pixel_format_descriptor_matching_configs(config, window)

    return finalized_config

def _get_pixel_format_descriptor_matching_configs(config: OpenGLConfig, window: Win32Window) -> GLLegacyConfig | None:
    """Get matching configs using standard PIXELFORMATDESCRIPTOR technique."""
    pfd = PIXELFORMATDESCRIPTOR()
    pfd.nSize = sizeof(PIXELFORMATDESCRIPTOR)
    pfd.nVersion = 1
    pfd.dwFlags = PFD_DRAW_TO_WINDOW | PFD_SUPPORT_OPENGL

    if config.double_buffer:
        pfd.dwFlags |= PFD_DOUBLEBUFFER
    else:
        pfd.dwFlags |= PFD_DOUBLEBUFFER_DONTCARE

    if config.stereo:
        pfd.dwFlags |= PFD_STEREO
    else:
        pfd.dwFlags |= PFD_STEREO_DONTCARE

    #  Not supported in pyglet API: swap_copy: PFD_SWAP_COPY and swap_exchange: PFD_SWAP_EXCHANGE

    if not config.depth_size:
        pfd.dwFlags |= PFD_DEPTH_DONTCARE

    pfd.iPixelType = PFD_TYPE_RGBA
    pfd.cColorBits = config.buffer_size or 0
    pfd.cRedBits = config.red_size or 0
    pfd.cGreenBits = config.green_size or 0
    pfd.cBlueBits = config.blue_size or 0
    pfd.cAlphaBits = config.alpha_size or 0
    pfd.cAccumRedBits = config.accum_red_size or 0
    pfd.cAccumGreenBits = config.accum_green_size or 0
    pfd.cAccumBlueBits = config.accum_blue_size or 0
    pfd.cAccumAlphaBits = config.accum_alpha_size or 0
    pfd.cDepthBits = config.depth_size or 0
    pfd.cStencilBits = config.stencil_size or 0
    pfd.cAuxBuffers = config.aux_buffers or 0

    pf = _gdi32.ChoosePixelFormat(window.dc, byref(pfd))
    if pf:
        return GLLegacyConfig(window, pf, config)

    return None

def _get_arb_pixel_format_matching_configs(config: OpenGLConfig, window: Win32Window) -> GLSurfaceConfig | None:
    """Get configs using the WGL_ARB_pixel_format extension.

    This method assumes a (dummy) GL context is already created.
    """
    # # Check for required extensions
    # if (self.sample_buffers or self.samples) and not global_backend.have_extension('GL_ARB_multisample'):
    #     return None

    # Construct array of attributes
    attrs = []
    for name, value in asdict(config).items():
        attr = GLSurfaceConfig.attribute_ids.get(name, None)
        if attr and value is not None:
            attrs.extend([attr, int(value)])
    attrs.append(0)
    attrs = (c_int * len(attrs))(*attrs)

    pformats = (c_int * 16)()
    nformats = c_uint(16)

    _global_wgl.funcs.wglChoosePixelFormatARB(window.dc, attrs, None, nformats, pformats, nformats)

    # Only choose the first format, because these are in order of best matching from driver.
    # (Maybe not always the case?)
    if pformats[0]:
        pf = pformats[:nformats.value][0]
        m =GLSurfaceConfig(window, pf, config)
        return m

    return None



class GLLegacyConfig(GLSurfaceConfig):
    def __init__(self, window: Win32Window, pf: int, user_config: OpenGLConfig) -> None:
        super().__init__(window, user_config, pf)
        self._pf = pf
        self._pfd = PIXELFORMATDESCRIPTOR()

        _gdi32.DescribePixelFormat(window.dc, pf, sizeof(PIXELFORMATDESCRIPTOR), byref(self._pfd))

        self.double_buffer = bool(self._pfd.dwFlags & PFD_DOUBLEBUFFER)
        self.sample_buffers = 0
        self.samples = 0
        self.stereo = bool(self._pfd.dwFlags & PFD_STEREO)
        self.buffer_size = self._pfd.cColorBits
        self.red_size = self._pfd.cRedBits
        self.green_size = self._pfd.cGreenBits
        self.blue_size = self._pfd.cBlueBits
        self.alpha_size = self._pfd.cAlphaBits
        self.accum_red_size = self._pfd.cAccumRedBits
        self.accum_green_size = self._pfd.cAccumGreenBits
        self.accum_blue_size = self._pfd.cAccumBlueBits
        self.accum_alpha_size = self._pfd.cAccumAlphaBits
        self.depth_size = self._pfd.cDepthBits
        self.stencil_size = self._pfd.cStencilBits
        self.aux_buffers = self._pfd.cAuxBuffers

    def apply_format(self) -> None:
        _gdi32.SetPixelFormat(self._window.dc, self._pf, byref(self._pfd))

    def create_context(self, opengl_backend: OpenGLBackend, share: Win32ARBContext | None) -> Win32ARBContext | Win32Context:
        from pyglet.graphics.api.gl.win32.context import Win32Context  # noqa: PLC0415
        return Win32Context(opengl_backend, self._window, self, share)


class GLSurfaceConfig(GLSurfaceConfig):
    attribute_ids = {  # noqa: RUF012
        'double_buffer': wglext_arb.WGL_DOUBLE_BUFFER_ARB,
        'stereo': wglext_arb.WGL_STEREO_ARB,
        'buffer_size': wglext_arb.WGL_COLOR_BITS_ARB,
        'aux_buffers': wglext_arb.WGL_AUX_BUFFERS_ARB,
        'sample_buffers': wglext_arb.WGL_SAMPLE_BUFFERS_ARB,
        'samples': wglext_arb.WGL_SAMPLES_ARB,
        'red_size': wglext_arb.WGL_RED_BITS_ARB,
        'green_size': wglext_arb.WGL_GREEN_BITS_ARB,
        'blue_size': wglext_arb.WGL_BLUE_BITS_ARB,
        'alpha_size': wglext_arb.WGL_ALPHA_BITS_ARB,
        'depth_size': wglext_arb.WGL_DEPTH_BITS_ARB,
        'stencil_size': wglext_arb.WGL_STENCIL_BITS_ARB,
        'accum_red_size': wglext_arb.WGL_ACCUM_RED_BITS_ARB,
        'accum_green_size': wglext_arb.WGL_ACCUM_GREEN_BITS_ARB,
        'accum_blue_size': wglext_arb.WGL_ACCUM_BLUE_BITS_ARB,
        'accum_alpha_size': wglext_arb.WGL_ACCUM_ALPHA_BITS_ARB,
    }

    def __init__(self, window: Win32Window, pf: int, user_config: OpenGLConfig) -> None:
        super().__init__(window, user_config, pf)
        self._pf = pf

        names = list(self.attribute_ids.keys())
        attrs = list(self.attribute_ids.values())
        attrs = (c_int * len(attrs))(*attrs)
        values = (c_int * len(attrs))()
        _global_wgl.funcs.wglGetPixelFormatAttribivARB(window.dc, pf, 0, len(attrs), attrs, values)

        for name, value in zip(names, values):
            setattr(self, name, value)

    def apply_format(self) -> None:
        _gdi32.SetPixelFormat(self._window.dc, self._pf, None)

    def create_context(
        self, opengl_backend: OpenGLBackend, share: Win32ARBContext | None,
    ) -> Win32ARBContext | Win32Context:
        #super().create_context(opengl_backend, share)
        from pyglet.graphics.api.gl.win32.context import Win32ARBContext, Win32Context  # noqa: PLC0415
        if _global_wgl.have_extension('WGL_ARB_create_context'):
            # Graphics adapters that ONLY support up to OpenGL 3.1/3.2 should be using the Win32ARBContext class.
            return Win32ARBContext(opengl_backend, self._window, self, share)

        return Win32Context(opengl_backend, self._window, self, share)
