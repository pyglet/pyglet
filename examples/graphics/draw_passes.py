"""Compare automatic and individually submitted batch draw passes."""
from __future__ import annotations

import pyglet
from pyglet.enums import GeometryMode


window = pyglet.window.Window(800, 600, "Draw passes", resizable=True)
window.context.set_clear_color(0.6, 0.6, 0.6, 1.0)
batch = pyglet.graphics.Batch()

layout = pyglet.graphics.VertexLayout(position="2f", colors="4Bn")

shadow_vertex_source = """#version 330 core
    in vec2 position;
    in vec4 colors;
    out vec4 vertex_color;

    uniform WindowBlock { mat4 projection; mat4 view; } window;

    void main() {
        vec2 shadow_offset = vec2(18.0, -14.0);
        gl_Position = window.projection * window.view * vec4(position + shadow_offset, 0.0, 1.0);
        vertex_color = vec4(colors.rgb * 0.10, 0.75);
    }
"""

color_vertex_source = """#version 330 core
    in vec2 position;
    in vec4 colors;
    out vec4 vertex_color;

    uniform WindowBlock { mat4 projection; mat4 view; } window;

    void main() {
        gl_Position = window.projection * window.view * vec4(position, 0.0, 1.0);
        vertex_color = colors;
    }
"""

fragment_source = """#version 330 core
    in vec4 vertex_color;
    out vec4 final_color;

    void main() {
        final_color = vertex_color;
    }
"""


def create_program(vertex_source: str, v_layout: pyglet.graphics.VertexLayout | None = None) -> pyglet.graphics.ShaderProgram:
    return pyglet.graphics.ShaderProgram(
        pyglet.graphics.Shader(vertex_source, "vertex"),
        pyglet.graphics.Shader(fragment_source, "fragment"),
        vertex_layout=v_layout,
    )


instance_shadow_vertex_source = """#version 330 core
    in vec2 position;
    in vec4 colors;
    in vec2 instance_offset;
    out vec4 vertex_color;

    uniform WindowBlock { mat4 projection; mat4 view; } window;

    void main() {
        vec2 shadow_offset = vec2(8.0, -6.0);
        gl_Position = window.projection * window.view
            * vec4(position + instance_offset + shadow_offset, 0.0, 1.0);
        vertex_color = vec4(colors.rgb * 0.10, 0.75);
    }
"""

instance_color_vertex_source = """#version 330 core
    in vec2 position;
    in vec4 colors;
    in vec2 instance_offset;
    out vec4 vertex_color;

    uniform WindowBlock { mat4 projection; mat4 view; } window;

    void main() {
        gl_Position = window.projection * window.view * vec4(position + instance_offset, 0.0, 1.0);
        vertex_color = colors;
    }
"""


def create_instance_program(vertex_source: str) -> pyglet.graphics.ShaderProgram:
    return create_program(vertex_source, pyglet.graphics.VertexLayout(instance_offset="2f/1"))


shadow_group = pyglet.graphics.ShaderGroup(create_program(shadow_vertex_source))
color_group = pyglet.graphics.ShaderGroup(create_program(color_vertex_source))
instance_shadow_group = pyglet.graphics.ShaderGroup(create_instance_program(instance_shadow_vertex_source))
instance_color_group = pyglet.graphics.ShaderGroup(create_instance_program(instance_color_vertex_source))

# One indexed mesh and one set of buffers. Its normal batch registration is
# the shadow pass.
mesh = batch.vertex_list_indexed(
    layout,
    7,
    GeometryMode.TRIANGLES,
    (0, 1, 6, 1, 2, 6, 2, 3, 6, 3, 4, 6, 4, 5, 6, 5, 0, 6),
    shadow_group,
    position=(
        400, 500,
        535, 400,
        485, 235,
        400, 285,
        315, 235,
        265, 400,
        400, 390,
    ),
    colors=(
        255, 100, 80, 255,
        255, 190, 70, 255,
        100, 220, 150, 255,
        70, 170, 255, 255,
        125, 105, 255, 255,
        235, 90, 190, 255,
        255, 245, 180, 255,
    ),
)

# Batch.draw submits registered passes after the normal batch draw. The color
# pass therefore lands over the shadow while reading the mesh's existing
# position and color buffers.
color_pass = batch.add_pass(pyglet.graphics.DrawPass(name="color", order=0))
mesh.add_pass(color_pass, group=color_group)

# Instanced lists can also be registered in an additional pass. Every active
# instance is drawn in both the shadow and color passes without duplicating
# its geometry or instance buffers.
instance_layout = pyglet.graphics.VertexLayout(position="2f", colors="4Bn", instance_offset="2f/1")
triangles = batch.vertex_list_instanced(
    instance_layout,
    3,
    GeometryMode.TRIANGLES,
    instance_shadow_group,
    position=(-28, -22, 28, -22, 0, 28),
    colors=(110, 225, 255, 255) * 3,
    instance_offset=(0, 0),
)
triangles.create_instances(
    4,
    instance_offset=(120, 110, 230, 150, 620, 120, 690, 360),
)
instance_color_pass = batch.add_pass(pyglet.graphics.DrawPass(name="instance-color", order=1))
triangles.add_pass(instance_color_pass, group=instance_color_group)


draw_mode = 1
mode_descriptions = {
    1: "Automatic batch draw",
    2: "Default shadow pass only",
    3: "Additional color passes only",
}
instructions = "1: automatic batch draw\n2: shadows only\n3: colors only"
status_label = pyglet.text.Label(
    "",
    x=16,
    y=window.height - 16,
    width=window.width - 32,
    anchor_y="top",
    multiline=True,
    font_size=14,
    color=(255, 255, 255, 255),
)


def update_status_label() -> None:
    status_label.text = f"{instructions}\n\nActive: {mode_descriptions[draw_mode]}"


update_status_label()


@window.event
def on_key_press(symbol: int, modifiers: int) -> None:  # noqa: ARG001
    global draw_mode
    if symbol == pyglet.window.key._1:
        draw_mode = 1
    elif symbol == pyglet.window.key._2:
        draw_mode = 2
    elif symbol == pyglet.window.key._3:
        draw_mode = 3
    else:
        return
    update_status_label()


@window.event
def on_resize(width: int, height: int) -> None:
    status_label.y = height - 16
    status_label.width = width - 32


@window.event
def on_draw() -> None:
    window.clear()
    if draw_mode == 1:
        batch.draw()
    elif draw_mode == 2:
        batch.draw_pass(None)
    else:
        batch.draw_pass(color_pass)
        batch.draw_pass(instance_color_pass)
    status_label.draw()


if __name__ == "__main__":
    pyglet.app.run()
