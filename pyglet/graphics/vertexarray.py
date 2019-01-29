from pyglet.gl import GLuint, glGenVertexArrays, glBindVertexArray


class VertexArray:
    """OpenGL Vertex Array Object"""

    def __init__(self):
        """Create an instance of a Vertex Array object."""
        self.id = GLuint()
        glGenVertexArrays(1, self.id)

    def bind(self):
        glBindVertexArray(self.id)

    def unbind(self):
        glBindVertexArray(0)
