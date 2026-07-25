from __future__ import annotations

import sys
import warnings
from typing import TYPE_CHECKING, Sequence, cast

import js

import pyglet
from pyglet.graphics.api.webgl.context import OpenGLSurfaceContext
from pyglet.graphics.api.base import (
    BackendGlobalObject,
    SurfaceContext,
    NullContext,
)
from pyglet.graphics.shader import Shader, ShaderProgram

if TYPE_CHECKING:

    from pyglet.config import SurfaceConfig
    from pyglet.graphics.shader import ShaderType
    from pyglet.window import Window

_is_pyglet_doc_run = hasattr(sys, "is_pyglet_doc_run") and sys.is_pyglet_doc_run


class ObjectSpace:
    """A container to store shared objects that are to be removed."""

    def __init__(self) -> None:
        """Initialize the context object space."""
        # Objects scheduled for deletion the next time this object space is active.
        self.doomed_textures = []
        self.doomed_buffers = []
        self.doomed_shader_programs = []
        self.doomed_shaders = []
        self.doomed_renderbuffers = []


class WebGLBackend(BackendGlobalObject):
    current_context: OpenGLSurfaceContext | NullContext
    _have_context: bool = False

    def __init__(self) -> None:
        self.initialized = False
        self.current_context = NullContext()

        # When the shadow window is created, a context is made. This is used to help the "real" context to utilize
        # its full capabilities; however, the two contexts have no relationship normally. This is used for the purpose
        # of sharing basic information between contexts. However, in usage, the user or internals should use the
        # "real" context's information to prevent any discrepencies.
        # self.gl_info = GLInfo()  # GL Info is a shared info space.
        super().__init__()

    @property
    def object_space(self) -> ObjectSpace:
        assert self.current_context is not None, "Context has not been created."
        return self.current_context.object_space

    def create_context(self, config: SurfaceConfig, shared: OpenGLSurfaceContext | None) -> OpenGLSurfaceContext:
        return OpenGLSurfaceContext(self, config._window, config, shared)

    def get_surface_context(self, window: Window, config: SurfaceConfig,
                            shared: OpenGLSurfaceContext | None = None) -> SurfaceContext:
        context = self.windows[window] = self.create_context(config, shared)
        self.current_context = context
        self._have_context = True
        return context

    # def get_window_backend_context(self, window: Window, config: OpenGLWindowConfig) -> SurfaceContext:
    #     """We will always only have one context in this Backend."""
    #     assert self.current_context is None
    #     context = self.windows[window] = self.create_context(config, self.current_context)
    #     self.current_context = context
    #     self._have_context = True
    #     return context

    def get_default_configs(self) -> Sequence[pyglet.config.WebGLUserConfig]:
        """A sequence of configs to use if the user does not specify any.

        These will be used during Window creation.
        """
        return [pyglet.config.WebGLUserConfig()]

    def get_config(self, **kwargs: float | str | None) -> pyglet.config.WebGLUserConfig:
        return pyglet.config.WebGLUserConfig(**kwargs)

    @property
    def info(self):
        return self.current_context.info

    def get_info(self):
        return self.info

    def have_extension(self, extension_name: str) -> bool:
        if not self.current_context:
            warnings.warn('No GL context created yet or current context not set.')
            return False

        return self.current_context.info.have_extension(extension_name)

    def have_version(self, major: int, minor: int = 0) -> bool:
        if not self.current_context:
            warnings.warn('No GL context created yet or current context not set.')
            return False

        return self.current_context.info.have_version(major, minor)

    def get_cached_shader(self, name: str, *sources: tuple[str, ShaderType]) -> ShaderProgram:
        """Create a ShaderProgram from OpenGL GLSL source.

        This is a convenience method that takes one or more tuples of
        (source_string, shader_type), and returns a
        :py:class:`~pyglet.graphics.shader.ShaderProgram` instance.

        ``source_string`` is OpenGL GLSL source code as a str, and ``shader_type``
        is the OpenGL shader type, such as "vertex" or "fragment". See
        :py:class:`~pyglet.graphics.shader.Shader` for more information.

        .. note:: This method is cached. Given the same shader sources, the
                  same ShaderProgram instance will be returned. For more
                  control over the ShaderProgram lifecycle, it is recommended
                  to manually create Shaders and link ShaderPrograms.

        .. versionadded:: 2.0.10
        """
        assert self.current_context
        assert isinstance(name, str), "First argument must be a string name for the shader."
        if program := self.current_context.cached_programs.get(name):
            return program

        shaders = (Shader(src, srctype) for (src, srctype) in sources)
        program = ShaderProgram(*shaders)
        self.current_context.cached_programs[name] = program
        return program

    def create_shader_program(self, *shaders: Shader) -> ShaderProgram:
        return ShaderProgram(*shaders)

    def create_shader(self, source_string: str, shader_type: ShaderType) -> Shader:
        return Shader(source_string, shader_type)

    def get_default_batch(self) -> pyglet.graphics.Batch:
        assert self.current_context
        if not hasattr(self.current_context, "default_batch"):
            self.current_context.default_batch = pyglet.graphics.Batch()

        return self.current_context.default_batch

    def set_viewport(self, window, x: int, y: int, width: int, height: int) -> None:
        self.current_context.gl.viewport(x, y, width, height)
