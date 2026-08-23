from __future__ import annotations

import pyglet


def test_shapes_and_sprites_draw_in_one_batch(webgl_window):
    batch = pyglet.graphics.Batch()
    rectangle = pyglet.shapes.Rectangle(4, 5, 24, 16, color=(255, 0, 0), batch=batch)
    circle = pyglet.shapes.Circle(48, 32, 12, color=(0, 255, 0), batch=batch)
    image = pyglet.image.SolidColorImagePattern((0, 0, 255, 255)).create_image(8, 8)
    sprite = pyglet.sprite.Sprite(image, x=72, y=24, batch=batch)

    try:
        rectangle.rotation = 15
        circle.opacity = 192
        sprite.scale = 2
        webgl_window.clear()
        batch.draw()
    finally:
        rectangle.delete()
        circle.delete()
        sprite.delete()


def test_label_layout_and_draw(webgl_window):
    label = pyglet.text.Label(
        "WebGL pytest",
        x=8,
        y=8,
        font_size=12,
        color=(255, 255, 255, 255),
    )

    try:
        assert label.content_width > 0
        assert label.content_height > 0
        webgl_window.clear()
        label.draw()
    finally:
        label.delete()
