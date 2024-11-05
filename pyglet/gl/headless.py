from __future__ import annotations

from ctypes import byref

from pyglet import gl
from pyglet.display.headless import HeadlessCanvas
from pyglet.libs.egl import egl


from .base import DisplayConfig, Config, Context

_fake_gl_attributes = {
    'double_buffer': 0,
    'stereo': 0,
    'aux_buffers': 0,
    'accum_red_size': 0,
    'accum_green_size': 0,
    'accum_blue_size': 0,
    'accum_alpha_size': 0,
}


class HeadlessConfig(Config):  # noqa: D101
    def match(self, canvas: HeadlessCanvas) -> list[HeadlessDisplayConfig]:
        if not isinstance(canvas, HeadlessCanvas):
            msg = 'Canvas must be an instance of HeadlessCanvas'
            raise RuntimeError(msg)

        display_connection = canvas.display._display_connection  # noqa: SLF001

        # Construct array of attributes
        attrs = []
        for name, value in self.get_gl_attributes():
            if name == 'double_buffer':
                continue
            attr = HeadlessDisplayConfig.attribute_ids.get(name, None)
            if attr and value is not None:
                attrs.extend([attr, int(value)])
        attrs.extend([egl.EGL_SURFACE_TYPE, egl.EGL_PBUFFER_BIT])
        if self.opengl_api == "gl":
            attrs.extend([egl.EGL_RENDERABLE_TYPE, egl.EGL_OPENGL_BIT])
        elif self.opengl_api == "gles":
            attrs.extend([egl.EGL_RENDERABLE_TYPE, egl.EGL_OPENGL_ES3_BIT])
        else:
            msg = f"Unknown OpenGL API: {self.opengl_api}"
            raise ValueError(msg)
        attrs.extend([egl.EGL_NONE])
        attrs_list = (egl.EGLint * len(attrs))(*attrs)

        num_config = egl.EGLint()
        egl.eglChooseConfig(display_connection, attrs_list, None, 0, byref(num_config))
        configs = (egl.EGLConfig * num_config.value)()
        egl.eglChooseConfig(display_connection, attrs_list, configs,
                            num_config.value, byref(num_config))

        return [HeadlessDisplayConfig(canvas, c, self) for c in configs]


class HeadlessDisplayConfig(DisplayConfig):  # noqa: D101
    canvas: HeadlessCanvas
    config: HeadlessConfig

    attribute_ids = {  # noqa: RUF012
        'buffer_size': egl.EGL_BUFFER_SIZE,
        'level': egl.EGL_LEVEL,  # Not supported
        'red_size': egl.EGL_RED_SIZE,
        'green_size': egl.EGL_GREEN_SIZE,
        'blue_size': egl.EGL_BLUE_SIZE,
        'alpha_size': egl.EGL_ALPHA_SIZE,
        'depth_size': egl.EGL_DEPTH_SIZE,
        'stencil_size': egl.EGL_STENCIL_SIZE,
        'sample_buffers': egl.EGL_SAMPLE_BUFFERS,
        'samples': egl.EGL_SAMPLES,
    }

    def __init__(self, canvas: HeadlessCanvas, egl_config: egl.EGLConfig, config: HeadlessConfig) -> None:  # noqa: D107
        super().__init__(canvas, config)
        self._egl_config = egl_config
        context_attribs = (egl.EGL_CONTEXT_MAJOR_VERSION, config.major_version or 2,
                           egl.EGL_CONTEXT_MINOR_VERSION, config.minor_version or 0,
                           egl.EGL_CONTEXT_OPENGL_FORWARD_COMPATIBLE, config.forward_compatible or 0,
                           egl.EGL_CONTEXT_OPENGL_DEBUG, config.debug or 0,
                           egl.EGL_NONE)
        self._context_attrib_array = (egl.EGLint * len(context_attribs))(*context_attribs)

        for name, attr in self.attribute_ids.items():
            value = egl.EGLint()
            egl.eglGetConfigAttrib(canvas.display._display_connection, egl_config, attr, byref(value))  # noqa: SLF001
            setattr(self, name, value.value)

        for name, value in _fake_gl_attributes.items():
            setattr(self, name, value)

    def compatible(self, canvas: HeadlessCanvas) -> bool:
        return isinstance(canvas, HeadlessCanvas)

    def create_context(self, share: HeadlessContext | None) -> HeadlessContext:
        return HeadlessContext(self, share)


class HeadlessContext(Context):  # noqa: D101
    display_connection: egl.EGLDisplay
    config: HeadlessDisplayConfig

    def __init__(self, config: HeadlessDisplayConfig, share: HeadlessContext | None) -> None:  # noqa: D107
        super().__init__(config, share)

        self.display_connection = config.canvas.display._display_connection  # noqa: SLF001

        self.egl_context = self._create_egl_context(share)
        if not self.egl_context:
            msg = 'Could not create GL context'
            raise gl.ContextException(msg)

    def _create_egl_context(self, share: HeadlessContext | None) -> egl.EGLContext:
        if share:
            share_context = share.egl_context
        else:
            share_context = None

        if self.config.opengl_api == "gl":
            egl.eglBindAPI(egl.EGL_OPENGL_API)
        elif self.config.opengl_api == "gles":
            egl.eglBindAPI(egl.EGL_OPENGL_ES_API)
        return egl.eglCreateContext(self.config.canvas.display._display_connection,  # noqa: SLF001
                                    self.config._egl_config, share_context,  # noqa: SLF001
                                    self.config._context_attrib_array)  # noqa: SLF001

    def attach(self, canvas: HeadlessCanvas) -> None:
        if canvas is self.canvas:
            return

        super().attach(canvas)

        self.egl_surface = canvas.egl_surface
        self.set_current()

    def set_current(self) -> None:
        egl.eglMakeCurrent(
            self.display_connection, self.egl_surface, self.egl_surface, self.egl_context)
        super().set_current()

    def detach(self) -> None:
        if not self.canvas:
            return

        self.set_current()
        gl.glFlush()  # needs to be in try/except?

        super().detach()

        egl.eglMakeCurrent(
            self.display_connection, 0, 0, None)
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
