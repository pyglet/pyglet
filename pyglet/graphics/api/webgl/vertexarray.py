from __future__ import annotations

from typing import TYPE_CHECKING

import pyglet

if TYPE_CHECKING:
    from pyglet.graphics.api.webgl import OpenGLSurfaceContext
    from pyglet.graphics.api.webgl.webgl_js import WebGLVertexArrayObject

__all__ = ['VertexArray']


class VertexArray:
    """OpenGL Vertex Array Object."""

    _context: OpenGLSurfaceContext | None
    _id: WebGLVertexArrayObject

    def __init__(self, context: OpenGLSurfaceContext) -> None:
        """Create an instance of a Vertex Array object."""
        self._context = context
        self._gl = self._context.gl
        self._id = self._gl.createVertexArray()

    @property
    def id(self) -> WebGLVertexArrayObject | int:
        return self._id

    def bind(self) -> None:
        self._gl.bindVertexArray(self._id)

    def unbind(self) -> None:
        self._gl.bindVertexArray(None)

    def delete(self) -> None:
        self._gl.deleteVertexArray(self._id)
        self._id = None

    __enter__ = bind

    def __exit__(self, *_) -> None:  # noqa: ANN002
        self._gl.bindVertexArray(None)

    def __del__(self) -> None:
        if self._id is not None:
            try:
                self._context.delete_vao(self.id)
                self._id = None
            except (ImportError, AttributeError):
                pass  # Interpreter is shutting down

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self._id})"
