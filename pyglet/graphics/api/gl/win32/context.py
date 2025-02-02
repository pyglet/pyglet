from __future__ import annotations

from ctypes import c_int, c_uint

from _ctypes import sizeof, byref

from pyglet.graphics.api.gl.base import OpenGLConfig, OpenGLWindowConfig, OpenGLWindowContext, ContextException
from pyglet.graphics.api.gl.win32 import wglext_arb, wgl
from pyglet.graphics.api.gl.win32.wgl_info import WGLInfo
from pyglet.libs.win32 import PIXELFORMATDESCRIPTOR, _gdi32
from pyglet.libs.win32.constants import PFD_DRAW_TO_WINDOW, PFD_SUPPORT_OPENGL, PFD_DOUBLEBUFFER, \
    PFD_DOUBLEBUFFER_DONTCARE, PFD_STEREO, PFD_STEREO_DONTCARE, PFD_DEPTH_DONTCARE, PFD_TYPE_RGBA
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyglet.graphics.api.gl.global_opengl import OpenGLBackend
    from pyglet.window.win32 import Win32Window


class Win32OpenGLConfig(OpenGLConfig):

    def match(self, window: Win32Window) -> Win32OpenGLWindowConfig | None:
        # Backend may not be done loading during the match process, load in func.
        from pyglet.graphics.api import global_backend

        if global_backend.current_context and global_backend.get_info().have_extension('WGL_ARB_pixel_format'):
            finalized_config = self._get_arb_pixel_format_matching_configs(window, global_backend)
        else:
            finalized_config = self._get_pixel_format_descriptor_matching_configs(window)

        return finalized_config

    def _get_pixel_format_descriptor_matching_configs(self, window: Win32Window) -> Win32OpenGLLegacyConfig | None:
        """Get matching configs using standard PIXELFORMATDESCRIPTOR technique."""
        pfd = PIXELFORMATDESCRIPTOR()
        pfd.nSize = sizeof(PIXELFORMATDESCRIPTOR)
        pfd.nVersion = 1
        pfd.dwFlags = PFD_DRAW_TO_WINDOW | PFD_SUPPORT_OPENGL

        if self.double_buffer:
            pfd.dwFlags |= PFD_DOUBLEBUFFER
        else:
            pfd.dwFlags |= PFD_DOUBLEBUFFER_DONTCARE

        if self.stereo:
            pfd.dwFlags |= PFD_STEREO
        else:
            pfd.dwFlags |= PFD_STEREO_DONTCARE

        #  Not supported in pyglet API: swap_copy: PFD_SWAP_COPY and swap_exchange: PFD_SWAP_EXCHANGE

        if not self.depth_size:
            pfd.dwFlags |= PFD_DEPTH_DONTCARE

        pfd.iPixelType = PFD_TYPE_RGBA
        pfd.cColorBits = self.buffer_size or 0
        pfd.cRedBits = self.red_size or 0
        pfd.cGreenBits = self.green_size or 0
        pfd.cBlueBits = self.blue_size or 0
        pfd.cAlphaBits = self.alpha_size or 0
        pfd.cAccumRedBits = self.accum_red_size or 0
        pfd.cAccumGreenBits = self.accum_green_size or 0
        pfd.cAccumBlueBits = self.accum_blue_size or 0
        pfd.cAccumAlphaBits = self.accum_alpha_size or 0
        pfd.cDepthBits = self.depth_size or 0
        pfd.cStencilBits = self.stencil_size or 0
        pfd.cAuxBuffers = self.aux_buffers or 0

        pf = _gdi32.ChoosePixelFormat(window.dc, byref(pfd))
        if pf:
            return Win32OpenGLLegacyConfig(window, pf, self)

        return None

    def _get_arb_pixel_format_matching_configs(self, window: Win32Window, global_backend: OpenGLBackend) -> Win32ARBOpenGLWindowConfig | None:
        """Get configs using the WGL_ARB_pixel_format extension.

        This method assumes a (dummy) GL context is already created.
        """
        # Check for required extensions
        if (self.sample_buffers or self.samples) and not global_backend.current_context.get_info().have_extension('GL_ARB_multisample'):
            return None

        # Construct array of attributes
        attrs = []
        for name, value in self.get_gl_attributes():
            attr = Win32ARBOpenGLWindowConfig.attribute_ids.get(name, None)
            if attr and value is not None:
                attrs.extend([attr, int(value)])
        attrs.append(0)
        attrs = (c_int * len(attrs))(*attrs)

        pformats = (c_int * 16)()
        nformats = c_uint(16)
        wglext_arb.wglChoosePixelFormatARB(window.dc, attrs, None, nformats, pformats, nformats)

        # Only choose the first format, because these are in order of best matching from driver.
        # (Maybe not always the case?)
        if pformats[0]:
            pf = pformats[:nformats.value][0]
            return Win32ARBOpenGLWindowConfig(window, pf, self)

        return None


class Win32OpenGLWindowConfig(OpenGLWindowConfig):
    ...


class Win32OpenGLLegacyConfig(Win32OpenGLWindowConfig):
    def __init__(self, window: Win32Window, pf: int, user_config: Win32OpenGLConfig ) -> None:
        super().__init__(window, user_config)
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
        return Win32Context(opengl_backend, self._window, self, share)


class Win32ARBOpenGLWindowConfig(Win32OpenGLWindowConfig):
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

    def __init__(self, window: Win32Window, pf: int, user_config: Win32OpenGLConfig) -> None:
        super().__init__(window, user_config)
        self._pf = pf

        names = list(self.attribute_ids.keys())
        attrs = list(self.attribute_ids.values())
        attrs = (c_int * len(attrs))(*attrs)
        values = (c_int * len(attrs))()

        wglext_arb.wglGetPixelFormatAttribivARB(window.dc, pf, 0, len(attrs), attrs, values)

        for name, value in zip(names, values):
            setattr(self, name, value)

    def apply_format(self) -> None:
        _gdi32.SetPixelFormat(self._window.dc, self._pf, None)

    def create_context(self, opengl_backend: OpenGLBackend, share: Win32ARBContext | None) -> Win32ARBContext | Win32Context:
        super().create_context(opengl_backend, share)
        if opengl_backend.get_info().have_extension('WGL_ARB_create_context'):
            # Graphics adapters that ONLY support up to OpenGL 3.1/3.2
            # should be using the Win32ARBContext class.
            return Win32ARBContext(opengl_backend, self._window, self, share)

        return Win32Context(opengl_backend, self._window, self, share)


class _BaseWin32Context(OpenGLWindowContext):
    def __init__(self,
                 opengl_backend: OpenGLBackend,
                 window: Win32Window,
                 config: Win32OpenGLWindowConfig,
                 share: Win32Context | Win32ARBContext) -> None:
        super().__init__(opengl_backend, window, config, share)
        self.get_info().platform_info = WGLInfo()
        self._context = None

    def set_current(self) -> None:
        if self._context is not None and self != self.global_ctx.current_context:
            wgl.wglMakeCurrent(self.window._dc, self._context)  # noqa: SLF001
        super().set_current()

    def detach(self) -> None:
        if self._context:
            wgl.wglDeleteContext(self._context)
            self._context = None
        super().detach()

    def flip(self) -> None:
        _gdi32.SwapBuffers(self.window._dc)  # noqa: SLF001

    def get_vsync(self) -> bool:
        if self._info.have_extension('WGL_EXT_swap_control'):
            return bool(wglext_arb.wglGetSwapIntervalEXT())
        return False

    def set_vsync(self, vsync: bool) -> None:
        if self._info.have_extension('WGL_EXT_swap_control'):
            wglext_arb.wglSwapIntervalEXT(int(vsync))


class Win32Context(_BaseWin32Context):
    config: Win32OpenGLLegacyConfig
    context_share: Win32Context | None

    def attach(self, window: Win32Window) -> None:
        super().attach(window)

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



class Win32ARBContext(_BaseWin32Context):
    config: Win32OpenGLWindowConfig
    context_share: Win32ARBContext | None

    def attach(self, window: Win32Window) -> None:
        share = self.context_share
        if share:
            if not share.window:
                msg = 'Share context has no window.'
                raise RuntimeError(msg)
            share = share._context  # noqa: SLF001

        attribs = []
        if self.config.major_version is not None:
            attribs.extend([wglext_arb.WGL_CONTEXT_MAJOR_VERSION_ARB, self.config.major_version])
        if self.config.minor_version is not None:
            attribs.extend([wglext_arb.WGL_CONTEXT_MINOR_VERSION_ARB, self.config.minor_version])
        flags = 0
        if self.config.forward_compatible and not self.config.opengl_api:
            flags |= wglext_arb.WGL_CONTEXT_FORWARD_COMPATIBLE_BIT_ARB
        if self.config.debug:
            flags |= wglext_arb.WGL_CONTEXT_DEBUG_BIT_ARB
        if self.config.opengl_api == "gles":
            attribs.extend([wglext_arb.WGL_CONTEXT_PROFILE_MASK_ARB, wglext_arb.WGL_CONTEXT_ES_PROFILE_BIT_EXT])
        if flags:
            attribs.extend([wglext_arb.WGL_CONTEXT_FLAGS_ARB, flags])
        attribs.append(0)
        attribs = (c_int * len(attribs))(*attribs)

        self.config.apply_format()
        self._context = wglext_arb.wglCreateContextAttribsARB(window.dc, share, attribs)
        super().attach(window)
