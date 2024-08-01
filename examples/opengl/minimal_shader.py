"""Minimal ShaderProgram example.

This example shows how to use Shaders and ShaderPrograms in pyglet. This is a semi-minimal
example, in that it also goes over pyglet's `Group` and `Batch` objects for easy batched
rendering of GPU resources. The result of this example is a single textured quad, but the
basics shown here will scale easily.

The code shown here illustrates:
  1. Compiling Shaders and linking a ShaderProgram.
  2. Creating a custom `graphics.Group` to control GL state setting (for Batched rendering).
  3. Using the `ShaderProgram.vertex_list_index` helper method to create GPU resources.

"""
import pyglet

from pyglet.gl import (
    glActiveTexture,
    glBindTexture,
    glEnable,
    glBlendFunc,
    glDisable,
    GL_TEXTURE0,
    GL_TRIANGLES,
    GL_BLEND,
    GL_SRC_ALPHA,
    GL_ONE_MINUS_SRC_ALPHA,
)
from pyglet.graphics import Group
from pyglet.graphics.shader import Shader, ShaderProgram


###################################
# Create a Window, and render Batch
###################################
window = pyglet.window.Window()
batch = pyglet.graphics.Batch()

label = pyglet.text.Label("A minimal shader to display a textured quad.", x=5, y=5, batch=batch)


@window.event
def on_draw():
    window.clear()
    batch.draw()


###############################
# Define a basic Shader Program
###############################
_vertex_source = """#version 330 core
    in vec2 position;
    in vec3 tex_coords;
    out vec3 texture_coords;

    uniform WindowBlock 
    {                       // This UBO is defined on Window creation, and available
        mat4 projection;    // in all Shaders. You can modify these matrixes with the
        mat4 view;          // Window.view and Window.projection properties.
    } window;  

    void main()
    {
        gl_Position = window.projection * window.view * vec4(position, 1, 1);
        texture_coords = tex_coords;
    }
"""

_fragment_source = """#version 330 core
    in vec3 texture_coords;
    out vec4 final_colors;

    uniform sampler2D our_texture;

    void main()
    {
        final_colors = texture(our_texture, texture_coords.xy);
    }
"""

vert_shader = Shader(_vertex_source, 'vertex')
frag_shader = Shader(_fragment_source, 'fragment')
shader_program = ShaderProgram(vert_shader, frag_shader)


#####################################################
# Define a custom `Group` to encapsulate OpenGL state
#####################################################
class RenderGroup(Group):
    """A Group that enables and binds a Texture and ShaderProgram.

    RenderGroups are equal if their Texture and ShaderProgram
    are equal.
    """
    def __init__(self, texture, program, order=0, parent=None):
        """Create a RenderGroup.

        :Parameters:
            `texture` : `~pyglet.image.Texture`
                Texture to bind.
            `program` : `~pyglet.graphics.shader.ShaderProgram`
                ShaderProgram to use.
            `order` : int
                Change the order to render above or below other Groups.
            `parent` : `~pyglet.graphics.Group`
                Parent group.
        """
        super().__init__(order, parent)
        self.texture = texture
        self.program = program

    def set_state(self):
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(self.texture.target, self.texture.id)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self.program.use()

    def unset_state(self):
        glDisable(GL_BLEND)

    def __hash__(self):
        return hash((self.texture.target, self.texture.id, self.order, self.parent, self.program))

    def __eq__(self, other):
        return (self.__class__ is other.__class__ and
                self.texture.target == other.texture.target and
                self.texture.id == other.texture.id and
                self.order == other.order and
                self.program == other.program and
                self.parent == other.parent)


#########################################################
# Load a Texture, and create a VertexList from the Shader
#########################################################


def create_quad(x, y, texture):
    x2 = x + texture.width
    y2 = y + texture.height
    return x, y, x2, y, x2, y2, x, y2


tex = pyglet.resource.texture('pyglet.png')
group = RenderGroup(tex, shader_program)
indices = (0, 1, 2, 0, 2, 3)

vertex_positions = create_quad(576, 296, tex)

# count, mode, indices, batch, group, *data
vertex_list = shader_program.vertex_list_indexed(4, GL_TRIANGLES, indices, batch, group,
                                                 position=('f', vertex_positions),
                                                 tex_coords=('f', tex.tex_coords))


#####################
# Enter the main loop
#####################
pyglet.app.run()
