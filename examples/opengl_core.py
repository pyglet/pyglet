import pyglet
from pyglet.gl import *
from pyglet.graphics.shader import Shader, ShaderProgram

import ctypes

config = pyglet.gl.Config(double_buffer=True, buffer_size=24, major_version=3, minor_version=3)
window = pyglet.window.Window(width=960, height=540, resizable=True, config=config)
print("OpenGL Context: {}".format(window.context.get_info().version))


vertex_source = """#version 330
    in vec3 position;
    in vec4 color;

    uniform float zoom;

    out vec4 vertex_color;

    void main()
    {
        gl_Position = vec4(position.x, position.y, position.z, zoom);
        // vertex_color = vec4(1.0, 0.5, 0.2, 1.0);
        vertex_color = color;
    }
"""

fragment_source = """#version 330
    in vec4 vertex_color;
    out vec4 final_color;

    void main()
    {
        final_color = vertex_color;
    }
"""


##################################
# Define a simple Vertex Structure
##################################
class VERTEX(ctypes.Structure):
    _fields_ = [
        ('position', GLfloat * 3),
        ('color', GLfloat * 4),
    ]

#########################
# Create a shader program
#########################
vertex_shader = Shader(vertex_source, shader_type="vertex")
fragment_shader = Shader(fragment_source, shader_type="fragment")
program = ShaderProgram(vertex_shader, fragment_shader)

##########################################################
# Create some vertex instances, and upload them to the GPU
##########################################################
vertices = (VERTEX * 3)(((-0.6, -0.5, 0.0), (1.0, 0.0, 0.0, 1.0)),
                        ((0.6, -0.5, 0.0), (0.0, 1.0, 0.0, 1.0)),
                        ((0.0, 0.5, 0.0), (0.0, 0.0, 1.0, 1.0)))
program.upload_data(vertices, "position", 3, ctypes.sizeof(VERTEX), VERTEX.position.offset)
program.upload_data(vertices, "color", 4, ctypes.sizeof(VERTEX), VERTEX.color.offset)

##########################################################
#   TESTS !
##########################################################

vertex_list = pyglet.graphics.vertex_list(2, ('v3f', (10, 15, 5, 30, 35, 5)),
                                             ('c3B', (0, 0, 255, 0, 255, 0)))


###########################################################
# Set the "zoom" uniform value.
###########################################################
program['zoom'] = 5.0


##########################################################
# Modify the "zoom" Uniform value scrolling the mouse
##########################################################
@window.event
def on_mouse_scroll(x, y, mouse, direction):
    program['zoom'] += direction / 4
    if program['zoom'] < 0.1:
        program['zoom'] = 0.1


#############################################################
# When using an OpenGL Core profile, you must override the
# defaul Window.on_resize method. This is due to legacy
# OpenGL functions that it normally calls.
#############################################################
# @window.event
# def on_resize(w, h):
#     glViewport(0, 0, w, h)
#     return pyglet.event.EVENT_HANDLED


###########################################################
# Shader Programs can be used as context managers as shown
# below. You can also manually call the use_program and
# stop_program methods on the Program object, as needed.
###########################################################
@window.event
def on_draw():
    with program:
        window.clear()
        program.draw(mode=GL_TRIANGLES, size=3)

        vertex_list.draw(pyglet.gl.GL_LINES)

if __name__ == "__main__":
    pyglet.app.run()
