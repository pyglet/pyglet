import pyglet

from pyglet.gl import GLuint, glGenVertexArrays, glDeleteVertexArrays, glBindVertexArray


__all__ = ['VertexArray']


class VertexArray:
    """OpenGL Vertex Array Object"""

    def __init__(self):
        """Create an instance of a Vertex Array object."""
        self._context = pyglet.gl.current_context
        self._id = GLuint()
        glGenVertexArrays(1, self._id)

    @property
    def id(self):
        return self._id.value

    def bind(self):
        glBindVertexArray(self._id)

    @staticmethod
    def unbind():
        glBindVertexArray(0)

    def delete(self):
        try:
            glDeleteVertexArrays(1, self._id)
        except Exception:
            pass

    __enter__ = bind

    def __exit__(self, *_):
        glBindVertexArray(0)

    def __del__(self):
        try:
            self._context.delete_vao(self.id)
        # Python interpreter is shutting down:
        except ImportError:
            pass

    def __repr__(self):
        return "{}(id={})".format(self.__class__.__name__, self._id.value)
