import pyglet
from pyglet.gl import *
from pyglet.graphics.shader import Shader, ShaderProgram

import ctypes

config = pyglet.gl.Config(double_buffer=True, buffer_size=24, major_version=3, minor_version=3)
window = pyglet.window.Window(width=960, height=540, resizable=True, config=config)
print("OpenGL Context: {}".format(window.context.get_info().version))


vertex_source = """#version 330 core
    in vec3 vertices;
    in vec4 colors;

    uniform float zoom;

    out vec4 vertex_colors;

    void main()
    {
        gl_Position = vec4(vertices.x, vertices.y, vertices.z, zoom);
        vertex_colors = colors;
        // vertex_colors = vec4(1.0, 0.5, 0.2, 1.0);
    }
"""

fragment_source = """#version 330 core
    in vec4 vertex_colors;
    out vec4 final_colors;

    void main()
    {
        final_colors = vertex_colors;
    }
"""

#########################
# Create a shader program
#########################
vertex_shader = Shader(vertex_source, shader_type="vertex")
fragment_shader = Shader(fragment_source, shader_type="fragment")
program = ShaderProgram(vertex_shader, fragment_shader)

program.use_program()
print("Program ID: {}".format(program.id))

##########################################################
#   TESTS !
##########################################################

vertex_list = pyglet.graphics.vertex_list(3, ('v3f', (-0.6, -0.5, 0,  0.6, -0.5, 0,  0, 0.5, 0)),
                                             ('c3B', (1, 0, 1, 0, 1, 1, 0, 1, 1)))

# TODO: update image library to fix this:
# label = pyglet.text.Label("test label")

###########################################################
# Set the "zoom" uniform value.
###########################################################
program['zoom'] = 5.0


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
        window.clear()
        pyglet.graphics.draw(3, GL_TRIANGLES, ('v3f', (-0.6, -0.5, 0,  0.6, -0.5, 0,  0, 0.5, 0)),
                                              ('c3f', (1, 0.5, 0.2,  1, 0.5, 0.2,  1, 0.5, 0.2)))

        pyglet.graphics.draw(3, GL_TRIANGLES, ('v3f', (-1, -1, 0,  -0.3, -1, 0,  -0.6, 0.2, 0)),
                                              ('c3f', (1, 0.5, 0.2,  1, 0.5, 0.2,  1, 0.5, 0.2)))
        # TODO: fix the Domain.draw method
        # vertex_list.draw(GL_TRIANGLES)

if __name__ == "__main__":
    pyglet.app.run()
