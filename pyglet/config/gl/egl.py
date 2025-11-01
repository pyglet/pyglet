from __future__ import annotations

from ctypes import byref
from dataclasses import asdict
from typing import TYPE_CHECKING

from pyglet import options
from pyglet.graphics.api.gl.egl.context import EGLContext
from pyglet.libs import egl
from pyglet.config import SurfaceConfig

if TYPE_CHECKING:
    from pyglet.graphics.api import OpenGLBackend
    from pyglet.config import OpenGLConfig
    from pyglet.window.headless import HeadlessWindow
    from pyglet.window.wayland import WaylandWindow

_fake_gl_attributes = {
    'double_buffer': True,
    'stereo': 0,
    'aux_buffers': 0,
    'accum_red_size': 0,
    'accum_green_size': 0,
    'accum_blue_size': 0,
    'accum_alpha_size': 0,
}


def match(config: OpenGLConfig, window: HeadlessWindow | WaylandWindow) -> EGLSurfaceConfig:
    display_connection = window.egl_display_connection  # noqa: SLF001
    assert display_connection is not None

    # Construct array of attributes
    attrs = []
    for name, value in asdict(config).items():
        if name == 'double_buffer':
            continue
        attr = EGLSurfaceConfig.attribute_ids.get(name, None)
        if attr and value is not None:
            attrs.extend([attr, int(value)])

    if options.headless:
        attrs.extend([egl.EGL_SURFACE_TYPE, egl.EGL_PBUFFER_BIT])
    else:
        attrs.extend([egl.EGL_SURFACE_TYPE, egl.EGL_WINDOW_BIT])
        attrs.extend([egl.EGL_RED_SIZE, 8])
        attrs.extend([egl.EGL_GREEN_SIZE, 8])
        attrs.extend([egl.EGL_BLUE_SIZE, 8])
        attrs.extend([egl.EGL_ALPHA_SIZE, 8])
        attrs.extend([egl.EGL_DEPTH_SIZE, 8])

    if config.opengl_api == "gl":
        attrs.extend([egl.EGL_RENDERABLE_TYPE, egl.EGL_OPENGL_BIT])
    elif config.opengl_api == "gles":
        attrs.extend([egl.EGL_RENDERABLE_TYPE, egl.EGL_OPENGL_ES3_BIT])
    else:
        msg = f"Unknown OpenGL API: {config.opengl_api}"
        raise ValueError(msg)

    attrs.extend([egl.EGL_NONE])
    attrs_list = (egl.EGLint * len(attrs))(*attrs)

    num_config = egl.EGLint()
    egl.eglChooseConfig(display_connection, attrs_list, None, 0, byref(num_config))
    configs = (egl.EGLConfig * num_config.value)()
    egl.eglChooseConfig(display_connection, attrs_list, configs, num_config.value, byref(num_config))

    result = [EGLSurfaceConfig(window, c, config) for c in configs]
    return result[0]


class EGLSurfaceConfig(SurfaceConfig):
    window: HeadlessWindow | WaylandWindow

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

    def __init__(self, window: HeadlessWindow | WaylandWindow, egl_config: egl.EGLConfig, config: OpenGLConfig) -> None:
        super().__init__(window, config, egl_config)
        self._egl_config = egl_config

        context_attribs = [egl.EGL_CONTEXT_MAJOR_VERSION, config.major_version or 2,
                           egl.EGL_CONTEXT_MINOR_VERSION, config.minor_version or 0]

        if config.opengl_api == "gl" and config.forward_compatible:
            context_attribs.extend([egl.EGL_CONTEXT_OPENGL_FORWARD_COMPATIBLE, 1])

        if config.debug:
            context_attribs.extend([egl.EGL_CONTEXT_OPENGL_DEBUG, config.debug])

        context_attribs.append(egl.EGL_NONE)

        self._context_attrib_array = (egl.EGLint * len(context_attribs))(*context_attribs)

        for name, attr in self.attribute_ids.items():
            value = egl.EGLint()
            result = egl.eglGetConfigAttrib(window.egl_display_connection, egl_config, attr, byref(value))  # noqa: SLF001
            if result == egl.EGL_TRUE:
                setattr(self, name, value.value)

        # TODO: real attributes?
        for name, value in _fake_gl_attributes.items():
            setattr(self, name, value)

    def create_context(self, opengl_backend: OpenGLBackend, share: EGLContext | None) -> EGLContext:
        return EGLContext(opengl_backend, self._window, self, share)

    def apply_format(self) -> None:
        pass

