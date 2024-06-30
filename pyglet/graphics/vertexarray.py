from __future__ import annotations

from typing import TYPE_CHECKING

import pyglet
from pyglet.gl import GLuint, glBindVertexArray, glDeleteVertexArrays, glGenVertexArrays

if TYPE_CHECKING:
    from ctypes import c_uint

    from pyglet.gl import Context

__all__ = ['VertexArray']


class VertexArray:
    """OpenGL Vertex Array Object."""
    _context: Context | None
    _id: c_uint

    def __init__(self) -> None:
        """Create an instance of a Vertex Array object."""
        self._context = pyglet.gl.current_context
        self._id = GLuint()
        glGenVertexArrays(1, self._id)

    @property
    def id(self) -> int:
        return self._id.value

    def bind(self) -> None:
        glBindVertexArray(self._id)

    @staticmethod
    def unbind() -> None:
        glBindVertexArray(0)

    def delete(self) -> None:
        glDeleteVertexArrays(1, self._id)
        self._id = None

    __enter__ = bind

    def __exit__(self, *_) -> None:  # noqa: ANN002
        glBindVertexArray(0)

    def __del__(self) -> None:
        if self._id is not None:
            try:
                self._context.delete_vao(self.id)
                self._id = None
            except (ImportError, AttributeError):
                pass  # Interpreter is shutting down

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self._id.value})"
