from __future__ import annotations

from ctypes import byref, c_int, c_uint, sizeof

from pyglet import gl
from pyglet.display.win32 import Win32Canvas
from pyglet.gl import gl_info, wgl, wgl_info, wglext_arb
from pyglet.libs.win32 import PIXELFORMATDESCRIPTOR, _gdi32
from pyglet.libs.win32.constants import (
    PFD_DEPTH_DONTCARE,
    PFD_DOUBLEBUFFER,
    PFD_DOUBLEBUFFER_DONTCARE,
    PFD_DRAW_TO_WINDOW,
    PFD_STEREO,
    PFD_STEREO_DONTCARE,
    PFD_SUPPORT_OPENGL,
    PFD_TYPE_RGBA,
)

from .base import DisplayConfig, Config, Context


class Win32Config(Config):  # noqa: D101

    def match(self, canvas: Win32Canvas) -> list[Win32DisplayConfig] | list[Win32DisplayConfigARB]:
        if not isinstance(canvas, Win32Canvas):
            msg = 'Canvas must be instance of Win32Canvas'
            raise RuntimeError(msg)

        # Use ARB API if available
        if gl_info.have_context() and wgl_info.have_extension('WGL_ARB_pixel_format'):
            return self._get_arb_pixel_format_matching_configs(canvas)

        return self._get_pixel_format_descriptor_matching_configs(canvas)

    def _get_pixel_format_descriptor_matching_configs(self, canvas: Win32Canvas) -> list[Win32DisplayConfig]:
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

        pf = _gdi32.ChoosePixelFormat(canvas.hdc, byref(pfd))
        if pf:
            return [Win32DisplayConfig(canvas, pf, self)]
        else:
            return []

    def _get_arb_pixel_format_matching_configs(self, canvas: Win32Canvas) -> list[Win32DisplayConfigARB]:
        """Get configs using the WGL_ARB_pixel_format extension.

        This method assumes a (dummy) GL context is already created.
        """
        # Check for required extensions
        if (self.sample_buffers or self.samples) and not gl_info.have_extension('GL_ARB_multisample'):
            return []

        # Construct array of attributes
        attrs = []
        for name, value in self.get_gl_attributes():
            attr = Win32DisplayConfigARB.attribute_ids.get(name, None)
            if attr and value is not None:
                attrs.extend([attr, int(value)])
        attrs.append(0)
        attrs = (c_int * len(attrs))(*attrs)

        pformats = (c_int * 16)()
        nformats = c_uint(16)
        wglext_arb.wglChoosePixelFormatARB(canvas.hdc, attrs, None, nformats, pformats, nformats)

        formats = [Win32DisplayConfigARB(canvas, pf, self) for pf in pformats[:nformats.value]]
        return formats


class Win32DisplayConfig(DisplayConfig):  # noqa: D101
    def __init__(self, canvas: Win32Canvas, pf: int, config: Win32Config) -> None:  # noqa: D107
        super().__init__(canvas, config)
        self._pf = pf
        self._pfd = PIXELFORMATDESCRIPTOR()

        _gdi32.DescribePixelFormat(canvas.hdc, pf, sizeof(PIXELFORMATDESCRIPTOR), byref(self._pfd))

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

    def compatible(self, canvas: Win32Canvas) -> bool:
        return isinstance(canvas, Win32Canvas)

    def create_context(self, share: Win32Context | None) -> Win32Context:
        return Win32Context(self, share)

    def _set_pixel_format(self, canvas: Win32Canvas) -> None:
        _gdi32.SetPixelFormat(canvas.hdc, self._pf, byref(self._pfd))


class Win32DisplayConfigARB(DisplayConfig):  # noqa: D101
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

    def __init__(self, canvas: Win32Canvas, pf: int, config: Win32Config) -> None:  # noqa: D107
        super().__init__(canvas, config)
        self._pf = pf

        names = list(self.attribute_ids.keys())
        attrs = list(self.attribute_ids.values())
        attrs = (c_int * len(attrs))(*attrs)
        values = (c_int * len(attrs))()

        wglext_arb.wglGetPixelFormatAttribivARB(canvas.hdc, pf, 0, len(attrs), attrs, values)

        for name, value in zip(names, values):
            setattr(self, name, value)

    def compatible(self, canvas: Win32Canvas) -> bool:
        # TODO more careful checking
        return isinstance(canvas, Win32Canvas)

    def create_context(self, share: Win32ARBContext | None) -> Win32ARBContext | Win32Context:
        if wgl_info.have_extension('WGL_ARB_create_context'):
            # Graphics adapters that ONLY support up to OpenGL 3.1/3.2
            # should be using the Win32ARBContext class.
            return Win32ARBContext(self, share)

        return Win32Context(self, share)

    def _set_pixel_format(self, canvas: Win32Canvas) -> None:
        _gdi32.SetPixelFormat(canvas.hdc, self._pf, None)


class _BaseWin32Context(Context):
    def __init__(self, config: Win32DisplayConfig | Win32DisplayConfigARB, share: Win32Context | Win32ARBContext) -> None:
        super().__init__(config, share)
        self._context = None

    def set_current(self) -> None:
        if self._context is not None and self != gl.current_context:
            wgl.wglMakeCurrent(self.canvas.hdc, self._context)
        super().set_current()

    def detach(self) -> None:
        if self.canvas:
            wgl.wglDeleteContext(self._context)
            self._context = None
        super().detach()

    def flip(self) -> None:
        _gdi32.SwapBuffers(self.canvas.hdc)

    def get_vsync(self) -> bool:
        if wgl_info.have_extension('WGL_EXT_swap_control'):
            return bool(wglext_arb.wglGetSwapIntervalEXT())
        return False

    def set_vsync(self, vsync: bool) -> None:
        if wgl_info.have_extension('WGL_EXT_swap_control'):
            wglext_arb.wglSwapIntervalEXT(int(vsync))


class Win32Context(_BaseWin32Context):  # noqa: D101
    config: Win32DisplayConfig
    context_share: Win32Context | None

    def attach(self, canvas: Win32Canvas) -> None:
        super().attach(canvas)

        if not self._context:
            self.config._set_pixel_format(canvas)  # noqa: SLF001
            self._context = wgl.wglCreateContext(canvas.hdc)

        share = self.context_share
        if share:
            if not share.canvas:
                msg = 'Share context has no canvas.'
                raise RuntimeError(msg)
            if not wgl.wglShareLists(share._context, self._context):  # noqa: SLF001
                msg = 'Unable to share contexts.'
                raise gl.ContextException(msg)


class Win32ARBContext(_BaseWin32Context):  # noqa: D101
    config: Win32DisplayConfigARB
    context_share: Win32ARBContext | None

    def attach(self, canvas: Win32Canvas) -> None:
        share = self.context_share
        if share:
            if not share.canvas:
                msg = 'Share context has no canvas.'
                raise RuntimeError(msg)
            share = share._context  # noqa: SLF001

        attribs = []
        if self.config.major_version is not None:
            attribs.extend([wglext_arb.WGL_CONTEXT_MAJOR_VERSION_ARB, self.config.major_version])
        if self.config.minor_version is not None:
            attribs.extend([wglext_arb.WGL_CONTEXT_MINOR_VERSION_ARB, self.config.minor_version])
        flags = 0
        if self.config.forward_compatible:
            flags |= wglext_arb.WGL_CONTEXT_FORWARD_COMPATIBLE_BIT_ARB
        if self.config.debug:
            flags |= wglext_arb.WGL_CONTEXT_DEBUG_BIT_ARB
        if flags:
            attribs.extend([wglext_arb.WGL_CONTEXT_FLAGS_ARB, flags])
        attribs.append(0)
        attribs = (c_int * len(attribs))(*attribs)

        self.config._set_pixel_format(canvas)  # noqa: SLF001
        self._context = wglext_arb.wglCreateContextAttribsARB(canvas.hdc, share, attribs)
        super().attach(canvas)
