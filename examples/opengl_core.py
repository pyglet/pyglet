import pyglet
from pyglet.gl import *
from pyglet.graphics.shader import Shader, ShaderProgram

import os

# config = pyglet.gl.Config(major_version=3, minor_version=3)
window = pyglet.window.Window(width=540, height=540, resizable=True)
print("OpenGL Context: {}".format(window.context.get_info().version))


vertex_source = """#version 330 core
    in vec4 vertices;
    in vec4 colors;
    in vec2 tex_coords;
    out vec4 vertex_colors;
    out vec2 texture_coords;

    uniform float zoom;

    void main()
    {
        gl_Position = vec4(vertices.x, vertices.y, vertices.z, vertices.w * zoom);
        vertex_colors = colors;
        // vertex_colors = vec4(1.0, 0.5, 0.2, 1.0);
        texture_coords = tex_coords;
    }
"""

fragment_source = """#version 330 core
    in vec4 vertex_colors;
    in vec2 texture_coords;
    out vec4 final_colors;

    uniform sampler2D our_texture;


    void main()
    {
        //final_colors = vertex_colors;
        final_colors = texture(our_texture, texture_coords) * vertex_colors;
    }
"""

#########################
# Create a shader program
#########################
vertex_shader = Shader(vertex_source, shader_type="vertex")
fragment_shader = Shader(fragment_source, shader_type="fragment")
program = ShaderProgram(vertex_shader, fragment_shader)
print("Program ID: {}".format(program.id))

##########################################################
#   TESTS !
##########################################################

# vertex_list = pyglet.graphics.vertex_list(3, ('v3f', (-0.6, -0.5, 0,  0.6, -0.5, 0,  0, 0.5, 0)),
#                                              ('c3f', (1, 0, 1, 0, 1, 1, 0, 1, 0)))

batch = pyglet.graphics.Batch()          # bl, tr, tl, bl, tr, rb
batch.add_indexed(4, GL_TRIANGLES, None, [0, 1, 3, 1, 2, 3],
                  ('v3f', (0.5, 0.5, 0,  0.5, -0.5, 0,  -0.5, -0.5, 0,  -0.5, 0.5, 0)),
                  ('c3f', (1, 0.5, 0.2,  1, 0.5, 0.2,  1, 0.5, 0.2,  1, 0.5, 0.2)),
                  ('t2f', (1, 1,  1, 0,  0, 0,  0, 1,)))


# batch.add(3, GL_TRIANGLES, None, ('v3f', (-1, -1, 0,  1, 1, 0,  1, -1, 0)),
#                                  ('c3f', (1, 0.5, 0.2, 1, 0.5, 0.2, 1, 0.5, 0.2)))


# TODO: update image library to fix this:
# label = pyglet.text.Label("test label")

# TODO: Add code to send the proper data to the uniform.
os.chdir('..')
img = pyglet.image.load("examples/pyglet.png")
tex = img.texture

###########################################################
# Set the "zoom" uniform value.
###########################################################
program.use_program()
program['zoom'] = 2


##########################################################
# Modify the "zoom" Uniform value scrolling the mouse
##########################################################
@window.event
def on_mouse_scroll(x, y, mouse, direction):
    program.use_program()
    program['zoom'] += direction / 4
    if program['zoom'] < 0.1:
        program['zoom'] = 0.1


###########################################################
# Shader Programs can be used as context managers as shown
# below. You can also manually call the use_program and
# stop_program methods on the Program object, as needed.
###########################################################
@window.event
def on_draw():
    with program:
        glClearColor(0.2, 0.3, 0.3, 1)
        window.clear()
        # pyglet.graphics.draw(3, GL_TRIANGLES, ('v3f', (-0.6, -0.5, 0,  0.6, -0.5, 0,  0, 0.5, 0)),
        #                                       ('c3f', (1, 0.5, 0.2,  1, 0.5, 0.2,  1, 0.5, 0.2)))

        # vertex_list.draw(GL_TRIANGLES)

        batch.draw()

if __name__ == "__main__":
    pyglet.app.run()
