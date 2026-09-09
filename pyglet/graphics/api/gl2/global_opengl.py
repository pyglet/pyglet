from __future__ import annotations

import ctypes
import sys
from typing import Sequence, TYPE_CHECKING, Literal

import pyglet
from pyglet.enums import GraphicsAPI
from pyglet.graphics.api.gl.global_opengl import OpenGLBackend
from pyglet.graphics.shader import AttributeLayout, ShaderProgram, Shader

if TYPE_CHECKING:
    from _ctypes import Array
    from pyglet.graphics.shader import ShaderType

_is_pyglet_doc_run = hasattr(sys, "is_pyglet_doc_run") and sys.is_pyglet_doc_run


class OpenGL2Backend(OpenGLBackend):
    gl_api: GraphicsAPI

    def get_default_configs(self) -> Sequence[pyglet.config.OpenGLUserConfig]:
        """A sequence of configs to use if the user does not specify any.

        These will be used during Window creation.
        """
        return [
            pyglet.config.OpenGLUserConfig(double_buffer=True, depth_size=24, major_version=2, minor_version=0,
                                           api=self.gl_api),
            pyglet.config.OpenGLUserConfig(double_buffer=True, depth_size=16, major_version=2, minor_version=0,
                                           api=self.gl_api),
        ]

    def get_cached_shader(self, name: str, *sources: tuple[str, ShaderType],
                          attribute_layout: AttributeLayout | None) -> ShaderProgram:
        """Create a ShaderProgram from OpenGL GLSL source.

        This is a convenience method that takes one or more tuples of
        (source_string, shader_type), and returns a
        :py:class:`~pyglet.graphics.ShaderProgram` instance.

        ``source_string`` is OpenGL GLSL source code as a str, and ``shader_type``
        is the OpenGL shader type, such as "vertex" or "fragment". See
        :py:class:`~pyglet.graphics.Shader` for more information.

        Args:
            name: Cache key for the linked shader program.
            sources: ``(source_string, shader_type)`` pairs used to build the program when uncached.
            attribute_layout: Default buffer formats for the returned view. Use ``None`` for introspected formats.

        .. note:: This method is cached. Given the same shader sources and
                  attribute layout, the same ShaderProgram instance will be returned. For more
                  control over the ShaderProgram lifecycle, it is recommended
                  to manually create Shaders and link ShaderPrograms.

        .. versionadded:: 2.0.10
        """
        assert self.current_context
        assert isinstance(name, str), "First argument must be a string name for the shader."

        if program := self.current_context.cached_programs.get(name):
            return program if attribute_layout is None else program.get_attribute_view(attribute_layout)

        shaders = (Shader(src, srctype) for (src, srctype) in sources)
        program = ShaderProgram(*shaders, attribute_layout=None)
        self.current_context.cached_programs[name] = program
        return program if attribute_layout is None else program.get_attribute_view(attribute_layout)

