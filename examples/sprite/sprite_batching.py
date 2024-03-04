import pyglet
import random

window = pyglet.window.Window(vsync=False)

# Set example resource path.
pyglet.resource.path = ['../resources']
pyglet.resource.reindex()

# Load example image from resource path.
# Avoid using pyglet.image.load as it creates multiple textures.
# Resource will load images into a texture atlas, allowing significantly faster performance.
image = pyglet.resource.image("pyglet.png")

# Anchor point on an image is bottom left corner by default.
# Set to center point with anchor properties.
image.anchor_x = image.width // 2
image.anchor_y = image.height // 2

# Batching allows rendering groups of objects all at once instead of drawing one by one.
batch = pyglet.graphics.Batch()

scales = [1.0, 0.75, 0.5, 0.25]

sprites = []
# Create 1000 sprites at various scales.
for i in range(1000):
    sprite = pyglet.sprite.Sprite(image,
                                  x=random.randint(0, window.width),
                                  y=random.randint(0, window.height),
                                  batch=batch)  # specify the batch to enter the sprites in.
    
    # Randomize scale.
    sprite.scale = random.choice(scales)
    
    # Random color multiplier.
    sprite.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    
    # Add sprites to keep in memory, like a list. Otherwise they will get GC'd when out of scope.
    sprites.append(sprite)  

@window.event
def on_draw():
    window.clear()
    batch.draw()
    
pyglet.app.run()
