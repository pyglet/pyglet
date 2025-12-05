from __future__ import annotations

import ctypes
import sys
from typing import Sequence, TYPE_CHECKING

import pyglet
from pyglet.graphics.api.gl.global_opengl import OpenGLBackend
from pyglet.graphics.api.base import WindowTransformations
from pyglet.graphics.api.gl2.shader import ShaderProgram, Shader

from pyglet.math import Mat4

if TYPE_CHECKING:
    from _ctypes import Array
    from pyglet.graphics.shader import ShaderType
    from pyglet.window import Window

_is_pyglet_doc_run = hasattr(sys, "is_pyglet_doc_run") and sys.is_pyglet_doc_run


class OpenGL2_Matrices(WindowTransformations):
    def __init__(self, window: Window, backend: OpenGL2Backend):
        self.backend = backend
        self._viewport = (0, 0, *window.get_framebuffer_size())

        width, height = window.get_size()
        super().__init__(window, Mat4.orthogonal_projection(0, width, 0, height, -255, 255), Mat4(), Mat4())

        self.projection = self._projection
        self.view = self._view

    @staticmethod
    def _get_mat_float_array(matrix: Mat4) -> Array[ctypes.c_float]:
        return (ctypes.c_float * 16)(*matrix)

    @property
    def projection(self) -> Mat4:
        return self._projection

    @projection.setter
    def projection(self, projection: Mat4) -> None:
        self._projection = projection

        projection_array = tuple(self._projection)
        for program in self.backend.current_context.cached_programs.values():
            with program:
                program["u_projection"] = projection_array

    @property
    def view(self) -> Mat4:
        return self._view

    @view.setter
    def view(self, view: Mat4) -> None:
        self._view = view
        view_array = tuple(self._view)
        for program in self.backend.current_context.cached_programs.values():
            with program:
                program["u_view"] = view_array

    @property
    def model(self) -> Mat4:
        return self._model

    @model.setter
    def model(self, model: Mat4) -> None:
        self._model = model

class OpenGL2Backend(OpenGLBackend):

    def get_default_configs(self) -> Sequence[pyglet.config.OpenGLConfig]:
        """A sequence of configs to use if the user does not specify any.

        These will be used during Window creation.
        """
        return [
            pyglet.config.OpenGLConfig(double_buffer=True, depth_size=24, major_version=2, minor_version=0,
                                                opengl_api=self.gl_api),
            pyglet.config.OpenGLConfig(double_buffer=True, depth_size=16, major_version=2, minor_version=0,
                                                opengl_api=self.gl_api),
        ]

    def get_cached_shader(self, name: str, *sources: tuple[str, ShaderType]) -> ShaderProgram:
        """Create a ShaderProgram from OpenGL GLSL source.

        This is a convenience method that takes one or more tuples of
        (source_string, shader_type), and returns a
        :py:class:`~pyglet.graphics.ShaderProgram` instance.

        ``source_string`` is OpenGL GLSL source code as a str, and ``shader_type``
        is the OpenGL shader type, such as "vertex" or "fragment". See
        :py:class:`~pyglet.graphics.Shader` for more information.

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

        # With GLES it doesn't support glMatrixMode's and no UBO's.
        # Set the projection for each shader manually.
        if not self.current_context.window._shadow:  # Do not set if it's the shadow window?  # noqa: SLF001
            with program:
                program["u_projection"] = tuple(self.current_context.window._matrices.projection)
                program["u_view"] = tuple(self.current_context.window._matrices.view)

        return program

    def initialize_matrices(self, window: Window) -> OpenGL2_Matrices:
        return OpenGL2_Matrices(window, self)
