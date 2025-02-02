from __future__ import annotations

from ctypes import (
    Structure,
)
from typing import TYPE_CHECKING

import pyglet
import pyglet.graphics.api.gl.gl_compat as gl

from pyglet.graphics.shader import ShaderSource, ShaderType, ShaderException

from pyglet.graphics.api.gl.shader import ShaderProgram as GLShaderProgram, GLDataType
from pyglet.graphics.api.gl.shader import Shader as GLShader

if TYPE_CHECKING:
    from pyglet.graphics.api.gl.base import OpenGLWindowContext

_debug_api_shaders = pyglet.options['debug_api_shaders']



class UniformBlock:
    """Not supported by OpenGL 2.0."""
    def __init__(self, program: ShaderProgram, name: str, index: int, size: int, binding: int,
                 uniforms: dict[int, tuple[str, GLDataType, int, int]], uniform_count: int) -> None:
        raise NotImplementedError


class UniformBufferObject:
    """Not supported by OpenGL 2.0."""
    def __init__(self, view_class: type[Structure], buffer_size: int, binding: int) -> None:
        """Initialize the Uniform Buffer Object with the specified Structure."""
        raise NotImplementedError



# Shader & program classes:

class GLShaderSource(ShaderSource):
    """GLSL source container for making source parsing simpler.

    We support locating out attributes and applying #defines values.

    .. note:: We do assume the source is neat enough to be parsed this way and doesn't contain several statements in
              one line.
    """
    _type: gl.GLenum
    _lines: list[str]

    def __init__(self, source: str, source_type: gl.GLenum | int) -> None:
        """Create a shader source wrapper."""
        self._lines = source.strip().splitlines()
        self._type = source_type

        if not self._lines:
            msg = "Shader source is empty"
            raise ShaderException(msg)

        self._version = self._find_glsl_version()

        if "es" in pyglet.options.backend:
            self._patch_gles()

    def _patch_gles(self) -> None:
        """Patch the built-in shaders for GLES support.

        Probably will need better handling to not affect user shaders.
        """
        if self._lines[0].strip().startswith("#version"):
            self._lines[0] = ""

            self._lines.insert(0, "precision mediump float;")

            if self._type == gl.GL_VERTEX_SHADER:
                self._lines.insert(1, "uniform mat4 u_projection;")
                self._lines.insert(2, "uniform mat4 u_view;")

                for idx, line in enumerate(self._lines):
                    if "gl_ProjectionMatrix" in line or "gl_ModelViewMatrix" in line:
                        self._lines[idx] = line.replace("gl_ProjectionMatrix", "u_projection").replace(
                            "gl_ModelViewMatrix", "u_view")

        self._version = "es 1.00"

    def validate(self) -> str:
        """Return the validated shader source."""
        return "\n".join(self._lines)

    def _find_glsl_version(self) -> int:
        if self._lines[0].strip().startswith("#version"):
            try:
                return int(self._lines[0].split()[1])
            except (ValueError, IndexError):
                pass

        source = "\n".join(f"{str(i + 1).zfill(3)}: {line} " for i, line in enumerate(self._lines))

        msg = (
            "Cannot find #version flag in shader source. "
            "A #version statement is required on the first line.\n"
            "------------------------------------\n"
            f"{source}"
        )
        raise ShaderException(msg)


class Shader(GLShader):
    """OpenGL shader.

    Shader objects are compiled on instantiation.
    You can reuse a Shader object in multiple ShaderPrograms.
    """
    _context: OpenGLWindowContext | None
    _id: int | None
    type: ShaderType

    @classmethod
    def supported_shaders(cls) -> tuple[ShaderType, ...]:
        return 'vertex', 'fragment'


class ShaderProgram(GLShaderProgram):  # noqa: D101
    _uniform_blocks: None
    __slots__ = '_attributes', '_context', '_id', '_uniform_blocks', '_uniforms'

    def __init__(self, *shaders: Shader) -> None:
        """Initialize the ShaderProgram using at least two Shader instances."""
        super().__init__(*shaders)

    def _get_uniform_blocks(self) -> None:
        """Return Uniform Block information."""
        return


class ComputeShaderProgram:
    """OpenGL Compute Shader Program.

    Not supported by OpenGL 2.0
    """

    def __init__(self, source: str) -> None:
        raise NotImplementedError
