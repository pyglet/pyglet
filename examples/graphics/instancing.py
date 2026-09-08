"""This is a simple example that displays how instances are created from vertex lists."""
from __future__ import annotations
import random
from dataclasses import dataclass

import pyglet
from pyglet.enums import GeometryMode

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
program.set_instance_attributes(colors=1, translate=1)


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


def _get_instance_data(columns: int, rows: int, spacing: int, x: int = 0, y: int = 0) -> tuple[list[float], list[int]]:
    colors = []
    translations = []
    for i in range(columns):
        for j in range(rows):
            colors.extend((random.random(), random.random(), random.random(), 1.0))
            translations.extend((x + i * spacing, y + j * spacing, 0))
    return colors, translations


background_group = pyglet.graphics.ShaderGroup(program, order=0)
BORDER = 25


@dataclass(frozen=True)
class ScissorData:
    x: int
    y: int
    width: int
    height: int

    @property
    def area(self):
        return self.x, self.y, self.width, self.height


scissor = ScissorData(BORDER, BORDER, window.width - BORDER * 2, window.height - BORDER * 2)
background_group.set_scissor(scissor)
foreground_group = pyglet.graphics.ShaderGroup(program, order=1)

vertex_list = program.vertex_list(3, GeometryMode.TRIANGLES,
                                  position=(100, 300, 0, 200, 250, 0, 200, 350, 0),
                                  colors=(1, 0, 0, 1, 0, 1, 0, 1, 0.3, 0.3, 1, 1))

vlist_1_size = 15
vlist_1 = program.vertex_list_instanced_indexed(4, mode=GeometryMode.TRIANGLES, indices=[0, 1, 2, 0, 2, 3],
                                                batch=batch,
                                                group=background_group,
                                                position=_get_quad_vertices(vlist_1_size),
                                                colors=(1, 0, 0, 1),
                                                translate=(0, 0, 0))

colors, translations = _get_instance_data(40, 40, vlist_1_size)
vlist_1.create_instances(40 * 40, colors=colors, translate=translations)

vlist_2_size = 5
vlist_2 = program.vertex_list_instanced_indexed(4, mode=GeometryMode.TRIANGLES, indices=[0, 1, 2, 0, 2, 3],
                                                batch=batch,
                                                group=foreground_group,
                                                position=_get_quad_vertices(vlist_2_size),
                                                colors=(1, 0, 0, 1),
                                                translate=(0, 0, 0))
colors, translations = _get_instance_data(40, 40, vlist_2_size)

# Use create_instances when the full set of instance data is already known.
vlist_2.create_instances(40 * 40 - 1, colors=colors[:-4], translate=translations[:-3])
# Use create_instance when adding a single instance to an existing vertex list.
vlist_2.create_instance(colors=colors[-4:], translate=translations[-3:])

vlist_2_1_size = 50
vlist_2_1 = program.vertex_list_instanced_indexed(4, mode=GeometryMode.TRIANGLES, indices=[0, 1, 2, 0, 2, 3],
                                                  batch=batch,
                                                  group=foreground_group,
                                                  position=_get_quad_vertices(vlist_2_1_size),
                                                  colors=(1, 0, 0, 1),
                                                  translate=(300, 300, 0))
colors, translations = _get_instance_data(4, 4, vlist_2_1_size, 300, 300)
vlist_2_1.create_instances(4 * 4, colors=colors, translate=translations)

vlist_3_size = 15
vlist_3 = program.vertex_list_instanced(3, mode=GeometryMode.TRIANGLES,
                                        batch=batch,
                                        group=foreground_group,
                                        position=_get_triangle_vertices(vlist_3_size),
                                        colors=(1, 0, 0, 1),
                                        translate=(0, 0, 0))
colors, translations = _get_instance_data(20, 20, vlist_3_size, 250)
vlist_3.create_instances(20 * 20, colors=colors, translate=translations)


@window.event
def on_draw():
    window.clear()
    batch.draw()


if __name__ == "__main__":
    pyglet.app.run()
