"""Clip drawing inside a ``Camera2D`` view with a scissor area."""

from __future__ import annotations

import math

import pyglet
from pyglet.graphics.state import CameraScopeProtocol
from pyglet.window import key
from pyglet.window.camera import Camera2D

window = pyglet.window.Window(850, 550, "Camera scissor", resizable=True)
batch = pyglet.graphics.Batch()
keys = key.KeyStateHandler()
window.push_handlers(keys)

ui_group = pyglet.graphics.Group(order=10)
ui_group.set_camera(window.default_camera)

camera = Camera2D(window, scroll_speed=240.0, min_zoom=0.4, max_zoom=4.0)
camera.set_centered_origin(True)

panel_group = pyglet.graphics.Group(order=0)
panel_group.set_camera(camera.view)

clipped_view = camera.create_view(inherit=True)
# A relative scissor is defined in this view's coordinate space, so it follows
# the camera movement and zoom instead of staying fixed in window pixels.
clipped_view.set_scissor_area_relative(-220, -130, 440, 260)
clipped_group = pyglet.graphics.Group(order=1)
clipped_group.set_camera(clipped_view)

clip_area_shape = pyglet.shapes.BorderedRectangle(
    -220, -130, 440, 260,
    border=4,
    color=(30, 40, 48),
    border_color=(230, 230, 210),
    batch=batch,
    group=panel_group,
)

# These shapes extend well outside the panel, but the clipped group only draws
# the parts inside clipped_view's scissor rectangle.
lines = []
for i in range(18):
    y = -230 + i * 28
    line = pyglet.shapes.Line(
        -360, y, 360, y + 170,
        thickness=12,
        color=(80 + i * 6, 150, 230),
        batch=batch,
        group=clipped_group,
    )
    lines.append(line)

moving_circle = pyglet.shapes.Circle(0, 0, 34, color=(240, 180, 65), batch=batch, group=clipped_group)

help_label = pyglet.text.Label(
    "WASD to move, +/- zoom",
    x=10,
    y=10,
    anchor_y="bottom",
    batch=batch,
    group=ui_group,
)
status_label = pyglet.text.Label("", x=window.width - 10, y=10, anchor_x="right", batch=batch, group=ui_group)


@window.event
def on_draw() -> None:
    window.clear()
    batch.draw()


@window.event
def on_resize(width: int, height: int) -> None:
    status_label.x = width - 10


def update(dt: float) -> None:
    if keys[key.A]:
        camera.offset_x -= camera.scroll_speed * dt
    if keys[key.D]:
        camera.offset_x += camera.scroll_speed * dt
    if keys[key.S]:
        camera.offset_y -= camera.scroll_speed * dt
    if keys[key.W]:
        camera.offset_y += camera.scroll_speed * dt
    if keys[key.PLUS] or keys[key.EQUAL]:
        camera.zoom += camera.zoom_speed * dt
    if keys[key.MINUS]:
        camera.zoom -= camera.zoom_speed * dt

    t = pyglet.clock.get_default().time()
    moving_circle.x = math.sin(t * 1.8) * 280
    moving_circle.y = math.cos(t * 1.3) * 170
    status_label.text = f"scissor_area={clipped_view.scissor_area}"


pyglet.clock.schedule_interval(update, 1 / 60)
pyglet.app.run()
