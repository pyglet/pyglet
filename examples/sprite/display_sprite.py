import pyglet

window = pyglet.window.Window(resizable=True)

# Set example resource path.
pyglet.resource.path = ['../resources']
pyglet.resource.reindex()

# Load example image from resource path.
image = pyglet.resource.image("pyglet.png")

# Anchor point on an image is bottom left corner by default.
# Set to center point with anchor properties.
image.anchor_x = image.width // 2
image.anchor_y = image.height // 2

# Create basic sprite in the center of the window.
sprite = pyglet.sprite.Sprite(image, x=window.width // 2, y=window.height // 2)

@window.event
def on_resize(width, height):
    # This will keep sprite at the center of the window as it changes size.
    sprite.update(x=width // 2, y=height // 2)

@window.event
def on_draw():
    window.clear()
    sprite.draw()
    
pyglet.app.run()
