import pyglet

# Import the new codec
import aseprite


window = pyglet.window.Window()
batch = pyglet.graphics.Batch()

# Add image decoders from the loaded codec module.
# This adds support to the image and resource modules.
pyglet.image.codecs.add_decoders(aseprite)

# You can now load a animation of *.ase type:
image = pyglet.image.load_animation("running.ase")
sprite = pyglet.sprite.Sprite(img=image, x=100, y=100, batch=batch)
sprite.scale = 8


@window.event
def on_draw():
    window.clear()
    batch.draw()


if __name__ == "__main__":
    pyglet.app.run()

