from __future__ import annotations

from typing import TYPE_CHECKING

import pyglet
from pyglet.graphics.api.gl import GLuint

if TYPE_CHECKING:
    from ctypes import c_uint
    from pyglet.graphics.api.gl.context import OpenGLSurfaceContext

__all__ = ['VertexArray']


class VertexArray:
    """OpenGL Vertex Array Object."""
    _context: OpenGLSurfaceContext | None
    _id: c_uint

    def __init__(self, context: OpenGLSurfaceContext) -> None:
        """Create an instance of a Vertex Array object."""
        self._context = context
        self._id = GLuint()
        self._context.glGenVertexArrays(1, self._id)

    @property
    def id(self) -> int:
        return self._id.value

    def bind(self) -> None:
        self._context.glBindVertexArray(self._id)

    def unbind(self) -> None:
        self._context.glBindVertexArray(0)

    def delete(self) -> None:
        self._context.glDeleteVertexArrays(1, self._id)
        self._id = None

    __enter__ = bind

    def __exit__(self, *_) -> None:  # noqa: ANN002
        self.glBindVertexArray(0)

    def __del__(self) -> None:
        if self._id is not None:
            try:
                self._context.delete_vao(self.id)
                self._id = None
            except (ImportError, AttributeError):
                pass  # Interpreter is shutting down

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self._id.value})"
