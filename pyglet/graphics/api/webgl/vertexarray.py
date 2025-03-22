from __future__ import annotations

from typing import TYPE_CHECKING

import pyglet
from pyglet.graphics.api.webgl.gl import glCreateVertexArray, glDeleteVertexArray, glBindVertexArray

if TYPE_CHECKING:
    from ctypes import c_uint

    from pyglet.graphics.api.gl import OpenGLWindowContext

__all__ = ['VertexArray']


class VertexArray:
    """OpenGL Vertex Array Object."""
    _context: OpenGLWindowContext | None
    _id: c_uint

    def __init__(self) -> None:
        """Create an instance of a Vertex Array object."""
        self._context = pyglet.graphics.api.global_backend.current_context
        self._id = glCreateVertexArray()

    @property
    def id(self) -> int:
        return self._id.value

    def bind(self) -> None:
        glBindVertexArray(self._id)

    @staticmethod
    def unbind() -> None:
        glBindVertexArray(None)

    def delete(self) -> None:
        glDeleteVertexArray(self._id)
        self._id = None

    __enter__ = bind

    def __exit__(self, *_) -> None:  # noqa: ANN002
        glBindVertexArray(None)

    def __del__(self) -> None:
        if self._id is not None:
            try:
                self._context.delete_vao(self.id)
                self._id = None
            except (ImportError, AttributeError):
                pass  # Interpreter is shutting down

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self._id.value})"
