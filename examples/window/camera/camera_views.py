"""Show multiple ``Camera2D`` views, including inherited and non-inherited child views."""

from __future__ import annotations

import math
import random

import pyglet
from pyglet.window import key
from pyglet.window.camera import Camera2D

window = pyglet.window.Window(900, 600, "Camera views", resizable=True)
batch = pyglet.graphics.Batch()
shapes = []
keys = key.KeyStateHandler()
window.push_handlers(keys)

# Draw UI with the window default camera so it stays fixed on screen.
ui_group = pyglet.graphics.Group(order=10)
ui_group.set_camera(window.default_camera)

world_camera = Camera2D(window, scroll_speed=260.0, min_zoom=0.25, max_zoom=4.0)
world_camera.set_centered_origin(True)

# The root view is the main world view.
world_group = pyglet.graphics.Group(order=1)
world_group.set_camera(world_camera.view)

# This child inherits the root view. It moves/zooms with the world camera, and
# also receives its own local offset/zoom below.
inherited_view = world_camera.create_view(inherit=True)
inherited_group = pyglet.graphics.Group(order=3)
inherited_group.set_camera(inherited_view)

# Create a sibling from the inherited view, but do not inherit that view's local
# transform. We use it as a parallax layer by assigning a smaller local offset.
parallax_view = inherited_view.create_view(inherit=False)
parallax_group = pyglet.graphics.Group(order=0)
parallax_group.set_camera(parallax_view)

# Simple generated scene: stars in the parallax layer, a grid in the world, and
# one marker in the inherited view.
rng = random.Random(1)
for _ in range(90):
    x = rng.randint(-1800, 1800)
    y = rng.randint(-1200, 1200)
    radius = rng.choice((2, 3, 4))
    shapes.append(pyglet.shapes.Circle(x, y, radius, color=(110, 140, 180), batch=batch, group=parallax_group))

for x in range(-1200, 1201, 100):
    color = (70, 70, 85) if x else (180, 90, 90)
    shapes.append(pyglet.shapes.Line(x, -900, x, 900, thickness=1, color=color, batch=batch, group=world_group))
for y in range(-900, 901, 100):
    color = (70, 70, 85) if y else (180, 90, 90)
    shapes.append(pyglet.shapes.Line(-1200, y, 1200, y, thickness=1, color=color, batch=batch, group=world_group))

shapes.append(pyglet.shapes.Rectangle(-40, -40, 80, 80, color=(80, 170, 230), batch=batch, group=world_group))


shapes.append(pyglet.shapes.BorderedRectangle(
    -60, -40, 120, 80,
    border=4,
    color=(235, 160, 70),
    border_color=(255, 230, 170),
    batch=batch,
    group=inherited_group,
))
pyglet.text.Label("inherited child", x=0, y=55, anchor_x="center", batch=batch, group=inherited_group)

help_label = pyglet.text.Label(
    "Arrow keys to Move, +/- zoom, 0 reset. Orange view inherits the world camera.",
    x=10,
    y=10,
    anchor_y="bottom",
    batch=batch,
    group=ui_group,
)
status_label = pyglet.text.Label("", x=window.width - 10, y=10, anchor_x="right", batch=batch, group=ui_group)
animation_time = 0.0


@window.event
def on_draw() -> None:
    window.clear()
    batch.draw()


@window.event
def on_resize(width: int, height: int) -> None:
    status_label.x = width - 10


def update(dt: float) -> None:
    global animation_time

    if keys[key.LEFT]:
        world_camera.offset_x -= world_camera.scroll_speed * dt
    if keys[key.RIGHT]:
        world_camera.offset_x += world_camera.scroll_speed * dt
    if keys[key.DOWN]:
        world_camera.offset_y -= world_camera.scroll_speed * dt
    if keys[key.UP]:
        world_camera.offset_y += world_camera.scroll_speed * dt
    if keys[key.PLUS] or keys[key.EQUAL]:
        world_camera.zoom += world_camera.zoom_speed * dt
    if keys[key.MINUS]:
        world_camera.zoom -= world_camera.zoom_speed * dt
    if keys[key._0]:
        world_camera.position = (0, 0)
        world_camera.zoom = 1.0

    animation_time += dt
    inherited_view.offset_x = math.sin(animation_time * 0.45) * 35
    inherited_view.offset_y = math.cos(animation_time * 0.35) * 18
    inherited_view.zoom = 1.0 + math.sin(animation_time * 0.3) * 0.05

    # Parallax is a sibling of the inherited view, so it ignores that orange
    # view's local animation. The negative offset cancels most of root movement.
    parallax_view.offset_x = -world_camera.offset_x * 0.75
    parallax_view.offset_y = -world_camera.offset_y * 0.75

    status_label.text = f"camera=({world_camera.offset_x:.0f}, {world_camera.offset_y:.0f}) zoom={world_camera.zoom:.2f}"


pyglet.clock.schedule_interval(update, 1 / 60)
pyglet.app.run()
