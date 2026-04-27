"""Instanced ordering helpers.

Instances inside a single instanced vertex list share one group. Because of
that, Group ordering cannot order individual instances within that list.
"""

from __future__ import annotations

import random

import pyglet
from pyglet.enums import GeometryMode
from pyglet.window import key

window = pyglet.window.Window(width=720, height=420, caption="Instancing Order")

batch = pyglet.graphics.Batch()

vertex_source = """#version 330 core
    in vec3 position;
    in vec3 translate;
    in vec4 colors;
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

fragment_source = """#version 330 core
    in vec4 vertex_colors;
    out vec4 final_colors;

    void main()
    {
        final_colors = vertex_colors;
    }
"""

program = pyglet.graphics.ShaderProgram(
    pyglet.graphics.Shader(vertex_source, "vertex"),
    pyglet.graphics.Shader(fragment_source, "fragment"),
)

group = pyglet.graphics.ShaderGroup(program=program)
vlist = program.vertex_list_instanced_indexed(
    4,
    mode=GeometryMode.TRIANGLES,
    indices=[0, 1, 2, 0, 2, 3],
    instance_attributes={"translate": 1, "colors": 1},
    batch=batch,
    group=group,
    position=("f", (0, 0, 0, 180, 0, 0, 180, 180, 0, 0, 180, 0)),
    translate=("f", (220, 120, 0)),
    colors=("f", (1, 0, 0, 1)),
)

instances_by_name = {
    "Red": vlist.create_instance(translate=(220, 120, 0), colors=(1.0, 0.0, 0.0, 1.0)),
    "Green": vlist.create_instance(translate=(230, 130, 0), colors=(0.0, 1.0, 0.0, 1.0)),
    "Blue": vlist.create_instance(translate=(240, 140, 0), colors=(0.0, 0.0, 1.0, 1.0)),
    "Yellow": vlist.create_instance(translate=(250, 150, 0), colors=(1.0, 1.0, 0.0, 1.0)),
}
name_by_instance = {instance: name for name, instance in instances_by_name.items()}

instructions = pyglet.text.Label(
    "1: Move Blue to back\n"
    "2: Move Blue to top\n"
    "3: Swap Red/Yellow\n"
    "4: Move Green to index 0\n"
    "5: Explicit full order\n"
    "6: Random full order",
    x=12,
    y=window.height - 12,
    anchor_x="left",
    anchor_y="top",
    multiline=True,
    width=window.width - 24,
)
order_label = pyglet.text.Label(
    "",
    x=12,
    y=14,
    anchor_x="left",
    anchor_y="bottom",
)


def update_order_label() -> None:
    names = []
    for i in range(vlist.instance_count):
        instance = vlist.get_instance_by_index(i)
        names.append(name_by_instance[instance])
    order_label.text = f"Current draw order (first -> last): {names}"


update_order_label()


@window.event
def on_key_press(symbol: int, modifiers: int) -> None:  # noqa: ARG001
    if symbol == key._1:
        vlist.move_to_back([instances_by_name["Blue"]])
    elif symbol == key._2:
        vlist.move_to_top([instances_by_name["Blue"]])
    elif symbol == key._3:
        vlist.swap_instances(instances_by_name["Red"], instances_by_name["Yellow"])
    elif symbol == key._4:
        vlist.move_instance_to_index(instances_by_name["Green"], 0)
    elif symbol == key._5:
        vlist.set_instance_order(
            [
                instances_by_name["Yellow"],
                instances_by_name["Blue"],
                instances_by_name["Green"],
                instances_by_name["Red"],
            ],
        )
    elif symbol == key._6:
        randomized = list(instances_by_name.values())
        random.shuffle(randomized)
        vlist.set_instance_order(randomized)
    else:
        return

    update_order_label()


@window.event
def on_draw() -> None:
    window.clear()
    batch.draw()
    instructions.draw()
    order_label.draw()


if __name__ == "__main__":
    pyglet.app.run()
