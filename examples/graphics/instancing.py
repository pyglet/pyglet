"""This is a simple example that displays how instances are created from vertex lists."""
from __future__ import annotations
import random

import pyglet
from pyglet.graphics import GeometryMode


window = pyglet.window.Window(width=540, height=540, resizable=True)


window.context.set_clear_color(0.2, 0.3, 0.3, 1)


batch = pyglet.graphics.Batch()


_vertex_source: str = """#version 330 core
    in vec3 position;
    in vec3 translate;
    in vec4 colors;
    in vec3 tex_coords;
    out vec4 vertex_colors;

    uniform WindowBlock
    {
        mat4 projection;
        mat4 view;
    } window;

    void main()
    {
         mat4 m_translate = mat4(1.0);
         m_translate[3][0] = translate.x;
         m_translate[3][1] = translate.y;
         m_translate[3][2] = translate.z;

        gl_Position = window.projection * window.view * m_translate * vec4(position, 1.0);

        vertex_colors = colors;
    }
"""

_fragment_source: str = """#version 330 core
    in vec4 vertex_colors;
    out vec4 final_colors;

    void main()
    {
        final_colors = vertex_colors;
    }
"""

program = pyglet.graphics.ShaderProgram(pyglet.graphics.Shader(_vertex_source, "vertex"),
                                        pyglet.graphics.Shader(_fragment_source, "fragment"))


def _get_quad_vertices(size: int) -> list[int]:
    x1 = 0
    y1 = 0
    x2 = x1 + size
    y2 = y1 + size

    return [x1, y1, 0, x2, y1, 0, x2, y2, 0, x1, y2, 0]

def _get_triangle_vertices(size: int) -> list[int]:
    return [0, 0, 0,
            size, 0, 0,
            size, size, 0]


background_group = pyglet.graphics.ShaderGroup(program, order=0)
BORDER = 25
background_group.set_scissor(BORDER, BORDER,  window.width - BORDER * 2, window.height - BORDER * 2)
foreground_group = pyglet.graphics.ShaderGroup(program, order=1)

vertex_list = program.vertex_list(3, GeometryMode.TRIANGLES,
                                  position=('f', (100, 300, 0,  200, 250, 0,  200, 350, 0)),
                                  colors=('f', (1, 0, 0, 1,  0, 1, 0, 1,  0.3, 0.3, 1, 1)))


vlist_1_size = 15
vlist_1 = program.vertex_list_instanced_indexed(4, mode=GeometryMode.TRIANGLES, indices=[0, 1, 2, 0, 2, 3],
                                                instance_attributes={"colors": 1, "translate": 1},
                                                batch=batch,
                                                group=background_group,
                                                position=('f', _get_quad_vertices(vlist_1_size)),
                                                colors=('f', (1, 0, 0, 1)),
                                                translate=('f', (0, 0, 0)))

for i in range(40):
    for j in range(40):
        f = vlist_1.create_instance(colors=(random.random(), random.random(), random.random(), 1),
                                    translate=(i * vlist_1_size, j * vlist_1_size, 0))

vlist_2_size = 5
vlist_2 = program.vertex_list_instanced_indexed(4, mode=GeometryMode.TRIANGLES, indices=[0, 1, 2, 0, 2, 3],
                                                instance_attributes={"colors": 1, "translate": 1},
                                                batch=batch,
                                                group=foreground_group,
                                                position=('f', _get_quad_vertices(vlist_2_size)),
                                                colors=('f', (1, 0, 0, 1)),
                                                translate=('f', (0, 0, 0)))
for i in range(40):
    for j in range(40):
        m = vlist_2.create_instance(colors=(random.random(), random.random(), random.random(), 1),
                                    translate=(i * vlist_2_size, j * vlist_2_size, 0))

vlist_2_1_size = 50
vlist_2_1 = program.vertex_list_instanced_indexed(4, mode=GeometryMode.TRIANGLES, indices=[0, 1, 2, 0, 2, 3],
                                                instance_attributes={"colors": 1, "translate": 1},
                                                batch=batch,
                                                group=foreground_group,
                                                position=('f', _get_quad_vertices(vlist_2_1_size)),
                                                colors=('f', (1, 0, 0, 1)),
                                                translate=('f', (300, 300, 0)))
for i in range(4):
    for j in range(4):
        m = vlist_2_1.create_instance(colors=(random.random(), random.random(), random.random(), 1),
                                    translate=(300 + i * vlist_2_1_size, 300 + j * vlist_2_1_size, 0))


vlist_3_size = 15
vlist_3 = program.vertex_list_instanced(3, mode=GeometryMode.TRIANGLES,
                                        instance_attributes={"colors": 1, "translate": 1},
                                        batch=batch,
                                        group=foreground_group,
                                        position=('f', _get_triangle_vertices(vlist_3_size)),
                                        colors=('f', (1, 0, 0, 1)),
                                        translate=('f', (0, 0, 0)))
for i in range(20):
    for j in range(20):
        m = vlist_3.create_instance(colors=(random.random(), random.random(), random.random(), 1),
                                    translate=(250 + i * vlist_3_size,
                                               0 + j * vlist_3_size, 0))


@window.event
def on_draw():
    window.clear()
    batch.draw()

if __name__ == "__main__":
    pyglet.app.run()
