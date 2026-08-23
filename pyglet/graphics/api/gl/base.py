from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyglet.graphics.api.gl.context import OpenGLSurfaceContext


class GLSharedObjectSpace:
    """Queues OpenGL objects for deletion by any context in a share group."""

    def __init__(self) -> None:  # noqa: D107
        self._textures: list[int] = []
        self._buffers: list[int] = []
        self._shader_programs: list[int] = []
        self._shaders: list[int] = []
        self._renderbuffers: list[int] = []

    def defer_texture(self, texture_id: int) -> None:
        self._textures.append(texture_id)

    def defer_buffer(self, buffer_id: int) -> None:
        self._buffers.append(buffer_id)

    def defer_shader_program(self, program_id: int) -> None:
        self._shader_programs.append(program_id)

    def defer_shader(self, shader_id: int) -> None:
        self._shaders.append(shader_id)

    def defer_renderbuffer(self, renderbuffer_id: int) -> None:
        self._renderbuffers.append(renderbuffer_id)

    def flush(self, context: OpenGLSurfaceContext) -> None:
        """Delete queued objects using a current context in this share group."""
        if self._textures:
            context._delete_objects(self._textures, context.glDeleteTextures)  # noqa: SLF001
        if self._buffers:
            context._delete_objects(self._buffers, context.glDeleteBuffers) # noqa: SLF001
        if self._shader_programs:
            context._delete_objects_one_by_one(self._shader_programs, context.glDeleteProgram) # noqa: SLF001
        if self._shaders:
            context._delete_objects_one_by_one(self._shaders, context.glDeleteShader) # noqa: SLF001
        if self._renderbuffers:
            context._delete_objects(self._renderbuffers, context.glDeleteRenderbuffers) # noqa: SLF001


class ContextException(Exception):
    pass


class ConfigException(Exception):
    pass


