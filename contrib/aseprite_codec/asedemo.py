import pyglet
from pyglet.gl import *

# Import the new codec
import aseprite


window = pyglet.window.Window()

# Add image decoders from the loaded codec module.
# This adds support to the image and resource modules.
pyglet.image.codecs.add_decoders(aseprite)

# You can now load a animation of *.ase type:
image = pyglet.image.load_animation("running.ase")
sprite = pyglet.sprite.Sprite(img=image, x=50, y=50)
sprite.scale = 8


@window.event
def on_draw():
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    window.clear()
    sprite.draw()


if __name__ == "__main__":
    pyglet.app.run()

