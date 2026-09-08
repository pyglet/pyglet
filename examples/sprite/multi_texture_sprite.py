"""Basic multi-texture sprite example."""
from __future__ import annotations

import pyglet


window = pyglet.window.Window(width=640, height=480)

# Set example resource path.
pyglet.resource.path = ['../resources']
pyglet.resource.reindex()

# Disable atlas packing so each layer is a standalone texture.
kitten_layer = pyglet.resource.texture("kitten.jpg", atlas=False)
logo_layer = pyglet.resource.texture("pyglet.png", atlas=False)

batch = pyglet.graphics.Batch()

sprite = pyglet.sprite.MultiTextureSprite(
    {
        "background": kitten_layer,
        "logo": logo_layer,
    },
    x=window.width // 2,
    y=window.height // 2,
    anchor=(kitten_layer.width // 2, kitten_layer.height // 2),
    batch=batch,
)
sprite.scale = 0.3
sprite.rotation = 20


@window.event
def on_draw():
    window.clear()
    batch.draw()


pyglet.app.run()
