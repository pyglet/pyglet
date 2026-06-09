"""Use ``Group.set_camera`` to scope a camera state in batch rendering."""

from __future__ import annotations

import pyglet
from pyglet.window import key
from pyglet.window.camera import Camera2D


# Create a window and a batch
window = pyglet.window.Window(resizable=True)
batch = pyglet.graphics.Batch()

# Key handler for movement
keys = key.KeyStateHandler()
window.push_handlers(keys)

# We still want to use the default camera for now, so assign it to a group.
# Cameras apply the state continuously until changed.
default_group = pyglet.graphics.Group()
default_group.set_camera(window.default_camera)

# If you do not do the above and pass it to your existing objects, those objects may not be shown.
# Alternatively, the default camera does not have to be used.
# For example, a second camera and group can just be utilized to be your new UI camera:
#    ui_camera = Camera2D(window, scroll_speed=450.0, min_zoom=0.1, max_zoom=8.0)
#    ui_group = pyglet.graphics.Group()
#    ui_group.set_camera(ui_camera)
# And then pass ui_group to your UI objects via the group keyword argument.

camera = Camera2D(window, scroll_speed=450.0, min_zoom=0.1, max_zoom=8.0)
# Use center origin point.
camera.set_centered_origin(True)
camera_group = pyglet.graphics.Group()
camera_group.set_camera(camera)

# Create a scene
rect = pyglet.shapes.Rectangle(-25, -25, 50, 50, batch=batch, group=camera_group)
text = pyglet.text.Label(
    "Text works too!", x=0, y=50, color=(255, 0, 0, 255), anchor_x="center", batch=batch, group=camera_group
)

# Create some "UI"
ui_text = pyglet.text.Label(
    "Arrow keys to move camera, +/- zoom",
    anchor_y="bottom",
    group=default_group,
    batch=batch,
)
position_text = pyglet.text.Label("", x=window.width, anchor_x="right", anchor_y="bottom",
                                  group=default_group, batch=batch)


@window.event
def on_draw() -> None:
    # Draw our scene
    window.clear()
    batch.draw()


@window.event
def on_resize(width: float, height: float):
    # Keep position text label to the right
    position_text.x = width


def on_update(dt: float) -> None:
    # Move camera with arrow keys
    if keys[key.UP]:
        camera.offset_y += 50 * dt
    if keys[key.DOWN]:
        camera.offset_y -= 50 * dt
    if keys[key.LEFT]:
        camera.offset_x -= 50 * dt
    if keys[key.RIGHT]:
        camera.offset_x += 50 * dt
    if keys[key.PLUS] or keys[key.EQUAL]:
        camera.zoom += dt
    if keys[key.MINUS]:
        camera.zoom -= dt
    if keys[key._0]:
        camera.zoom = 1.0
        camera.position = (0.0, 0.0)

    # Update position text label
    position_text.text = f"pos=({camera.offset_x:.1f}, {camera.offset_y:.1f}) zoom={camera.zoom:.2f}"

# Start the demo
pyglet.clock.schedule(on_update)
pyglet.app.run()

