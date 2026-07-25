"""Uniform Buffer Object region example.

This example uses one shader program with three material UBO regions. Each
group binds a different region before its shape is drawn.
"""

from __future__ import annotations

import math

import pyglet
from pyglet.enums import GeometryMode, GraphicsAPI


if pyglet.options.backend != GraphicsAPI.OPENGL:
    raise RuntimeError("This example uses OpenGL 3.3 shader syntax. Run it with the OpenGL backend.")


window = pyglet.window.Window(width=720, height=480, caption="Uniform Buffer Object", resizable=True)
batch = pyglet.graphics.Batch()


vertex_source = """#version 330 core
    in vec2 position;

    uniform WindowBlock
    {
        mat4 projection;
        mat4 view;
    } window;

    layout(std140) uniform MaterialBlock
    {
        vec4 color;
        vec4 offset_scale;
    } material;

    out vec4 vertex_color;

    void main()
    {
        vec2 scaled_position = position * material.offset_scale.zw;
        vec2 world_position = scaled_position + material.offset_scale.xy;
        gl_Position = window.projection * window.view * vec4(world_position, 0.0, 1.0);
        vertex_color = material.color;
    }
"""

fragment_source = """#version 330 core
    in vec4 vertex_color;
    out vec4 final_color;

    void main()
    {
        final_color = vertex_color;
    }
"""

program = pyglet.graphics.ShaderProgram(
    pyglet.graphics.Shader(vertex_source, "vertex"),
    pyglet.graphics.Shader(fragment_source, "fragment"),
)

material_block = program.uniform_blocks["MaterialBlock"]


def create_material(color: tuple[float, float, float, float],
                    offset_scale: tuple[float, float, float, float]):
    region = material_block.create_ubo_region()
    # When creating the material, ensure it has some initial data.
    with region as material_region:
        material_region.color[:] = color
        material_region.offset_scale[:] = offset_scale
    return region


triangle_vertices = (
    -0.6, -0.5,
     0.6, -0.5,
     0.0,  0.6,
)

quad_vertices = (
    -0.5, -0.5,
     0.5, -0.5,
     0.5,  0.5,
    -0.5,  0.5,
)

materials = [
    create_material((0.95, 0.30, 0.22, 1.0), (160.0, 240.0, 100.0, 100.0)),
    create_material((0.18, 0.64, 0.96, 1.0), (360.0, 240.0, 120.0, 120.0)),
    create_material((0.90, 0.82, 0.28, 1.0), (560.0, 240.0, 90.0, 90.0)),
]
elapsed_time = 0.0

groups = []
# Give each separate material its own group, so the dirty regions can be committed during draw.
for material in materials:
    group = pyglet.graphics.ShaderGroup(program)
    group.set_uniform_buffer(material)
    groups.append(group)

triangle_1 = program.vertex_list(
    3,
    GeometryMode.TRIANGLES,
    batch=batch,
    group=groups[0],
    position=("f", triangle_vertices),
)
triangle_2 = program.vertex_list_indexed(
    4,
    GeometryMode.TRIANGLES,
    indices=(0, 1, 2, 0, 2, 3),
    batch=batch,
    group=groups[1],
    position=("f", quad_vertices),
)
triangle_3 = program.vertex_list(
    3,
    GeometryMode.TRIANGLES,
    batch=batch,
    group=groups[2],
    position=("f", triangle_vertices),
)


def update_materials(dt: float) -> None:
    global elapsed_time
    elapsed_time += dt

    for index, region in enumerate(materials):
        angle = elapsed_time * 1.6 + index * 2.1
        center_x = 360.0 + math.cos(angle) * (120.0 + index * 18.0)
        center_y = 240.0 + math.sin(angle * 0.8) * (70.0 + index * 12.0)

        with region as material_region:
            material_region.offset_scale[0] = center_x
            material_region.offset_scale[1] = center_y


@window.event
def on_draw() -> None:
    window.clear()
    batch.draw()


pyglet.clock.schedule_interval(update_materials, 1 / 60)


if __name__ == "__main__":
    pyglet.app.run()
