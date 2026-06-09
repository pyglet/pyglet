"""Interactive group behavior test scene.

A test to spot test camera scissors, views, and hierarchy views

1. Same group usage
2. Differing groups / explicit ordering
3. Group hierarchy with parenting
4. Shared state (scissor) via parented groups
5. Camera + camera view grouping behavior (root / outer / inner)
6. Shared + separate camera/scissor scrollbox behavior
"""

from __future__ import annotations

import pyglet
pyglet.options.backend = "gl2"
from pyglet.window import key
from pyglet.window.camera import Camera2D, CameraScissor

WINDOW_W = 1500
WINDOW_H = 920

window = pyglet.window.Window(WINDOW_W, WINDOW_H, "Interactive Group Ordering / Hierarchy Test", resizable=True)
keys = key.KeyStateHandler()
window.push_handlers(keys)

batch = pyglet.graphics.Batch()
refs: list[object] = []
base_camera = Camera2D(window)


def _title(text: str, x: int, y: int) -> None:
    refs.append(
        pyglet.text.Label(
            text,
            x=x,
            y=y,
            weight="bold",
            color=(240, 240, 245, 255),
            batch=batch,
        )
    )


def _body(text: str, x: int, y: int, width: int = 420, color=(220, 220, 228, 255)) -> None:
    refs.append(
        pyglet.text.Label(
            text,
            x=x,
            y=y,
            width=width,
            multiline=True,
            color=color,
            batch=batch,
        )
    )


def _panel(x: int, y: int, w: int, h: int) -> None:
    refs.append(
        pyglet.shapes.BorderedRectangle(
            x,
            y,
            w,
            h,
            border=2,
            color=(25, 27, 34, 255),
            border_color=(88, 93, 112, 255),
            batch=batch,
        )
    )


_panel(20, 480, 460, 410)
_panel(500, 480, 460, 410)
_panel(980, 480, 500, 410)
_panel(20, 20, 710, 430)
_panel(750, 20, 730, 430)

_title("A) Same Group", 36, 860)
_body("Expected: Two squares share one group state and render in that common state.", 36, 830)

shared_group = pyglet.graphics.Group(order=0)
refs.append(pyglet.shapes.Rectangle(75, 615, 120, 120, color=(220, 60, 60, 200), batch=batch, group=shared_group))
refs.append(pyglet.shapes.Rectangle(135, 675, 120, 120, color=(70, 170, 250, 200), batch=batch, group=shared_group))
refs.append(pyglet.text.Label("same group", x=75, y=585, color=(220, 220, 228, 255), batch=batch))

_title("B) Differing Groups / Order", 516, 860)
_body("Expected: Green (order -1) should draw behind orange (order +1).", 516, 830)

back_group = pyglet.graphics.Group(order=0)
front_group = pyglet.graphics.Group(order=1)
refs.append(pyglet.shapes.Rectangle(565, 610, 135, 135, color=(70, 190, 90, 220), batch=batch, group=back_group))
refs.append(pyglet.shapes.Rectangle(630, 670, 135, 135, color=(240, 160, 70, 220), batch=batch, group=front_group))
refs.append(pyglet.text.Label("Different groups + order", x=560, y=585, color=(220, 220, 228, 255), batch=batch))

_title("C) Parented Hierarchy + Shared Scissor", 996, 860)
_body(
    "Expected: Both strips are clipped to the parent scissor panel.\n"
    "Red strip group and blue strip group share one scissor parent state.",
    996,
    830,
    width=470,
)

scissor_data = CameraScissor(1030, 560, 390, 200)
scissor_data2 = CameraScissor(1030, 560, 105, 100)
scissor_parent_group = pyglet.graphics.Group(order=0)
scissor_parent_group.set_scissor(scissor_data)
clip_child_a = pyglet.graphics.Group(parent=scissor_parent_group)
clip_child_a.set_scissor(scissor_data2)
clip_child_b = pyglet.graphics.Group(parent=scissor_parent_group)

refs.append(pyglet.text.Label(
    text="Clipped by outer and inner boxes.",
    multiline=True,
    group=clip_child_a,
    width=120,
    x=1027,
    y=580,
    batch=batch,
))
refs.append(
    pyglet.shapes.BorderedRectangle(
        1030,
        560,
        390,
        200,
        border=2,
        color=(15, 15, 20, 255),
        border_color=(200, 200, 210, 255),
        batch=batch,
    )
)
for i in range(12):
    refs.append(
        pyglet.shapes.Rectangle(
            980 + i * 46,
            595 + (i % 2) * 24,
            120,
            38,
            color=(210, 80, 90, 150),
            batch=batch,
            group=clip_child_a,
        )
    )
for i in range(12):
    refs.append(
        pyglet.shapes.Rectangle(
            1000 + i * 44,
            680 - (i % 3) * 20,
            115,
            28,
            color=(90, 130, 230, 140),
            batch=batch,
            group=clip_child_b,
        )
    )

_title("D) Camera Group Propagation", 36, 420)
_body(
    "Controls: I/K move OUTER view vertically, J/L move INNER view horizontally.\n"
    "Expected: Content remains clipped to the D frame.\n"
    "Expected: Outer rows move only with OUTER, inner tiles inherit OUTER + INNER.",
    36,
    390,
    width=680,
)

D_VIEW_X = 44
D_VIEW_Y = 44
D_VIEW_W = 662
D_VIEW_H = 258

ui_camera = Camera2D(window)
ui_camera.set_scissor(CameraScissor(D_VIEW_X, D_VIEW_Y, D_VIEW_W, D_VIEW_H))
ui_outer_view = ui_camera.create_view(inherit=True)
ui_inner_view = ui_outer_view.create_view(inherit=True)

ui_root_group = pyglet.graphics.Group(order=20)
ui_root_group.set_camera(ui_camera)
ui_outer_group = pyglet.graphics.Group(order=0, parent=ui_root_group)
ui_outer_group.set_camera(ui_outer_view)
ui_inner_group = pyglet.graphics.Group(order=0, parent=ui_outer_group)
ui_inner_group.set_camera(ui_inner_view)

refs.append(
    pyglet.shapes.BorderedRectangle(
        D_VIEW_X,
        D_VIEW_Y,
        D_VIEW_W,
        D_VIEW_H,
        border=2,
        color=(16, 19, 28, 255),
        border_color=(95, 102, 128, 255),
        batch=batch,
        group=ui_root_group,
    )
)
root_fixed_label = pyglet.text.Label(
    "ROOT LABEL (should stay fixed)",
    x=58,
    y=D_VIEW_Y + D_VIEW_H - 22,
    color=(255, 235, 120, 255),
    batch=batch,
    group=ui_root_group,
)
refs.append(root_fixed_label)

for i in range(12):
    y = D_VIEW_Y + 22 + i * 18
    refs.append(
        pyglet.shapes.Rectangle(
            88,
            y,
            250,
            16,
            color=(90, 120 + i * 8, 200, 175),
            batch=batch,
            group=ui_outer_group,
        )
    )
    refs.append(
        pyglet.text.Label(
            f"outer row {i:02d}",
            x=100,
            y=y + 2,
            color=(240, 245, 255, 255),
            batch=batch,
            group=ui_outer_group,
        )
    )

for i in range(14):
    x = 326 + i * 74
    refs.append(
        pyglet.shapes.BorderedRectangle(
            x,
            110,
            62,
            70,
            border=2,
            color=(55, 65, 92, 255),
            border_color=(255, 170, 90, 255),
            batch=batch,
            group=ui_inner_group,
        )
    )
    refs.append(
        pyglet.text.Label(
            str(i),
            x=x + 22,
            y=136,
            color=(255, 225, 190, 255),
            batch=batch,
            group=ui_inner_group,
        )
    )

status_d_label = pyglet.text.Label("", x=44, y=28, color=(220, 220, 228, 255), batch=batch)
refs.append(status_d_label)

_title("E) Two Scrollboxes: Shared + Separate Camera/Scissor", 766, 420)
_body(
    "Controls: Shared T/G (X), R/F (Y), left box V/B (X), right box N/M (Y).\n"
    "Expected: Both boxes inherit shared movement, then apply their own local movement.\n"
    "Expected: Content is clipped by both the shared parent scissor and each box scissor.",
    766,
    390,
    width=700,
)

E_PARENT_X = 772
E_PARENT_Y = 78
E_PARENT_W = 686
E_PARENT_H = 220

E_LEFT_X = 780
E_LEFT_Y = 96
E_LEFT_W = 318
E_LEFT_H = 176

E_RIGHT_X = 1120
E_RIGHT_Y = 96
E_RIGHT_W = 318
E_RIGHT_H = 176

scroll_camera = Camera2D(window)
scroll_parent_view = scroll_camera.create_view(inherit=True)
scroll_parent_view.set_scissor(CameraScissor(E_PARENT_X, E_PARENT_Y, E_PARENT_W, E_PARENT_H))
scroll_left_view = scroll_parent_view.create_view(inherit=True)
scroll_left_view.set_scissor(CameraScissor(E_LEFT_X, E_LEFT_Y, E_LEFT_W, E_LEFT_H))
scroll_right_view = scroll_parent_view.create_view(inherit=True)
scroll_right_view.set_scissor(CameraScissor(E_RIGHT_X, E_RIGHT_Y, E_RIGHT_W, E_RIGHT_H))

scroll_parent_group = pyglet.graphics.Group(order=30)
scroll_parent_group.set_scissor(CameraScissor(E_PARENT_X, E_PARENT_Y, E_PARENT_W, E_PARENT_H))
scroll_left_group = pyglet.graphics.Group(order=0, parent=scroll_parent_group)
scroll_left_group.set_camera(scroll_left_view)
scroll_right_group = pyglet.graphics.Group(order=0, parent=scroll_parent_group)
scroll_right_group.set_camera(scroll_right_view)

refs.append(
    pyglet.shapes.BorderedRectangle(
        E_PARENT_X,
        E_PARENT_Y,
        E_PARENT_W,
        E_PARENT_H,
        border=2,
        color=(18, 22, 30, 255),
        border_color=(106, 112, 135, 255),
        batch=batch,
    )
)
refs.append(
    pyglet.shapes.BorderedRectangle(
        E_LEFT_X,
        E_LEFT_Y,
        E_LEFT_W,
        E_LEFT_H,
        border=2,
        color=(14, 18, 24, 255),
        border_color=(135, 190, 255, 255),
        batch=batch,
    )
)
refs.append(
    pyglet.shapes.BorderedRectangle(
        E_RIGHT_X,
        E_RIGHT_Y,
        E_RIGHT_W,
        E_RIGHT_H,
        border=2,
        color=(14, 18, 24, 255),
        border_color=(255, 190, 130, 255),
        batch=batch,
    )
)
refs.append(pyglet.text.Label("left box", x=E_LEFT_X + 6, y=E_LEFT_Y + E_LEFT_H + 7, color=(210, 220, 235, 255), batch=batch))
refs.append(pyglet.text.Label("right box", x=E_RIGHT_X + 6, y=E_RIGHT_Y + E_RIGHT_H + 7, color=(210, 220, 235, 255), batch=batch))

for i in range(16):
    x = E_LEFT_X - 18 + i * 66
    y = E_LEFT_Y + 24 + (i % 2) * 36
    refs.append(
        pyglet.shapes.BorderedRectangle(
            x,
            y,
            56,
            30,
            border=2,
            color=(52, 74, 108, 235),
            border_color=(145, 196, 255, 235),
            batch=batch,
            group=scroll_left_group,
        )
    )
    refs.append(
        pyglet.text.Label(
            f"L{i:02d}",
            x=x + 14,
            y=y + 9,
            color=(230, 240, 255, 255),
            batch=batch,
            group=scroll_left_group,
        )
    )

for i in range(14):
    y = E_RIGHT_Y - 16 + i * 32
    refs.append(
        pyglet.shapes.Rectangle(
            E_RIGHT_X + 18,
            y,
            266,
            24,
            color=(130, 86 + i * 8, 66, 185),
            batch=batch,
            group=scroll_right_group,
        )
    )
    refs.append(
        pyglet.text.Label(
            f"R{i:02d}",
            x=E_RIGHT_X + 28,
            y=y + 5,
            color=(255, 238, 220, 255),
            batch=batch,
            group=scroll_right_group,
        )
    )

status_e_label = pyglet.text.Label("", x=766, y=50, color=(220, 220, 228, 255), batch=batch)
refs.append(status_e_label)

outer_scroll = 0.0
inner_scroll = 0.0
shared_scroll_x = 0.0
shared_scroll_y = 0.0
left_scroll_x = 0.0
right_scroll_y = 0.0


def _update(dt: float) -> None:
    global outer_scroll, inner_scroll, shared_scroll_x, shared_scroll_y, left_scroll_x, right_scroll_y
    speed = 260.0

    if keys[key.I]:
        outer_scroll += speed * dt
    if keys[key.K]:
        outer_scroll -= speed * dt
    if keys[key.L]:
        inner_scroll += speed * dt
    if keys[key.J]:
        inner_scroll -= speed * dt

    if keys[key.T]:
        shared_scroll_x += speed * dt
    if keys[key.G]:
        shared_scroll_x -= speed * dt
    if keys[key.R]:
        shared_scroll_y += speed * dt
    if keys[key.F]:
        shared_scroll_y -= speed * dt

    if keys[key.V]:
        left_scroll_x += speed * dt
    if keys[key.B]:
        left_scroll_x -= speed * dt

    if keys[key.N]:
        right_scroll_y += speed * dt
    if keys[key.M]:
        right_scroll_y -= speed * dt

    ui_outer_view.position = (0.0, outer_scroll)
    ui_inner_view.position = (inner_scroll, 0.0)
    scroll_parent_view.position = (shared_scroll_x, shared_scroll_y)
    scroll_left_view.position = (left_scroll_x, 0.0)
    scroll_right_view.position = (0.0, right_scroll_y)

    status_d_label.text = f"D outer={outer_scroll:7.1f}   inner={inner_scroll:7.1f}"
    status_e_label.text = (
        f"E shared=({shared_scroll_x:7.1f}, {shared_scroll_y:7.1f})"
        f"   left_x={left_scroll_x:7.1f}   right_y={right_scroll_y:7.1f}"
    )


@window.event
def on_draw() -> None:
    window.clear()
    batch.draw()


pyglet.clock.schedule_interval(_update, 1 / 120)
pyglet.app.run()
