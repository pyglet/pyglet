import unittest
from unittest.mock import patch, MagicMock

GL_TRIANGLES = 4

# The default shader attributes.
# Update this if you change the default shader.
default_shader_attributes = {
    'colors': {'type': 35666, 'size': 1, 'location': 1, 'count': 4, 'format': 'f', 'instance': False},
    'position': {'type': 35665, 'size': 1, 'location': 0, 'count': 3, 'format': 'f', 'instance': False},
    'tex_coords': {'type': 35665, 'size': 1, 'location': 2, 'count': 3, 'format': 'f', 'instance': False},
}


class TestDefaultShader(unittest.TestCase):

    def setUp(self):
        """Setup the fake ShaderProgram for all of the tests."""
        patcher = patch.multiple(
            'pyglet.graphics.shader',
            _link_program=patch('pyglet.graphics.shader._link_program', return_value=1).start(),
            _introspect_attributes=patch('pyglet.graphics.shader._introspect_attributes',
                                         return_value=default_shader_attributes).start(),
            _introspect_uniforms=patch('pyglet.graphics.shader._introspect_uniforms',
                                       return_value={}).start(),
            _introspect_uniform_blocks=patch('pyglet.graphics.shader._introspect_uniform_blocks',
                                             return_value={}).start(),
            glEnableVertexAttribArray=patch('pyglet.graphics.shader.glEnableVertexAttribArray', new_callable=MagicMock()).start(),
            glVertexAttribPointer=patch('pyglet.graphics.shader.glVertexAttribPointer',
                                            new_callable=MagicMock()).start(),
        )
        self.addCleanup(patcher.stop)

        patcher_gl = patch.multiple(
            'pyglet.gl',
            current_context=patch('pyglet.gl.current_context', create=True).start(),
            glUseProgram=patch('pyglet.gl.glUseProgram').start(),
            glDeleteProgram=patch('pyglet.gl.glDeleteProgram').start(),
            glGenVertexArrays=patch('pyglet.gl.glGenVertexArrays').start(),
        )
        self.addCleanup(patcher_gl.stop)
        
        # These are imported already before this test runs, so we need to override them. Imports fixed.
        patcher_vertexbuffer = patch.multiple(
            'pyglet.graphics.vertexbuffer',
            glBindBuffer=MagicMock(),
            glBufferData=MagicMock(),
            glBufferSubData=MagicMock(),
            glGenBuffers=MagicMock(),
        )
        self.addCleanup(patcher_vertexbuffer.stop)
        patcher_vertexbuffer.start()
        
        patcher_vertexarray = patch.multiple(
            'pyglet.graphics.vertexarray',
            glGenVertexArrays=MagicMock(),
            glBindVertexArray=MagicMock(),
        )
        self.addCleanup(patcher_vertexarray.stop)
        patcher_vertexarray.start()
        
        # Create mock shaders
        mock_shader1 = MagicMock()
        mock_shader2 = MagicMock()

        from pyglet.graphics import Batch
        from pyglet.graphics.shader import ShaderProgram

        # Patch default batch.
        patch('pyglet.graphics.get_default_batch', return_value=Batch()).start()

        self.program = ShaderProgram(mock_shader1, mock_shader2)

        self.batch = Batch()

    def test_index_vertex_list_create_no_batch_no_group(self):
        vlist = self.program._vertex_list_create(  # noqa: SLF001
            count=4,
            mode=GL_TRIANGLES,
            indices=[0, 1, 2, 0, 2, 3],
            instances=None,
            batch=None,
            group=None,
            position=('f', (400, 400, 0, 400 + 50, 400, 0, 400 + 50, 400 + 50, 0, 400, 400 + 50, 0)),
            colors=('f', (1, 0.5, 0.2, 1, 1, 0.5, 0.2, 1, 1, 0.5, 0.2, 1, 1, 0.5, 0.2, 1)),
        )

        assert vlist is not None
        assert vlist.count == 4

    def test_index_vertex_list_create_batch_no_group(self):
        vlist = self.program._vertex_list_create(  # noqa: SLF001
            count=4,
            mode=GL_TRIANGLES,
            indices=[0, 1, 2, 0, 2, 3],
            instances=None,
            batch=self.batch,
            group=None,
            position=('f', (400, 400, 0, 400 + 50, 400, 0, 400 + 50, 400 + 50, 0, 400, 400 + 50, 0)),
            colors=('f', (1, 0.5, 0.2, 1, 1, 0.5, 0.2, 1, 1, 0.5, 0.2, 1, 1, 0.5, 0.2, 1)),
        )

        assert vlist is not None
        assert vlist.count == 4
        
    def test_index_vertex_list_create_batch_group(self):
        from pyglet.graphics import Group
        vlist = self.program._vertex_list_create(  # noqa: SLF001
            count=4,
            mode=GL_TRIANGLES,
            indices=[0, 1, 2, 0, 2, 3],
            instances=None,
            batch=self.batch,
            group=Group(),
            position=('f', (400, 400, 0, 400 + 50, 400, 0, 400 + 50, 400 + 50, 0, 400, 400 + 50, 0)),
            colors=('f', (1, 0.5, 0.2, 1, 1, 0.5, 0.2, 1, 1, 0.5, 0.2, 1, 1, 0.5, 0.2, 1)),
        )

        assert vlist is not None
        assert vlist.count == 4
        
    def test_index_vertex_list_create_no_batch_group(self):
        from pyglet.graphics import Group
        vlist = self.program._vertex_list_create(  # noqa: SLF001
            count=4,
            mode=GL_TRIANGLES,
            indices=[0, 1, 2, 0, 2, 3],
            instances=None,
            batch=None,
            group=Group(),
            position=('f', (400, 400, 0, 400 + 50, 400, 0, 400 + 50, 400 + 50, 0, 400, 400 + 50, 0)),
            colors=('f', (1, 0.5, 0.2, 1, 1, 0.5, 0.2, 1, 1, 0.5, 0.2, 1, 1, 0.5, 0.2, 1)),
        )

        assert vlist is not None
        assert vlist.count == 4
        
if __name__ == '__main__':
    unittest.main()
