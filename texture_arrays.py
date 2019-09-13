import pyglet
pyglet.options['debug_gl'] = True
import timeit

window = pyglet.window.Window()

array = pyglet.image.TextureArray.create(256, 256, max_depth=5)
print(array)

orange = pyglet.image.load("pyglet.png")
blue = pyglet.image.load("pyglet2.png")
green_large = pyglet.image.load("pyglet3.png")
purple = pyglet.image.load("pyglet4.png")
large_texture = pyglet.image.load("large_texture.png")


# Allocate as many as you want. Unpack a list or manually enter yourself.
array.allocate(orange,blue)

# Supports one at at time as well.
array.allocate(green_large)

# List assignment will overwrite existing data.
array[2] = purple
print(array[2])


# Restricts large files fot fitting.
#array[2] = large_texture

# Supports slice assignment, reassign them all back to normal.
array[:2] = (orange, blue)

# From an ImageGrid
grid = pyglet.image.ImageGrid(orange, 1, 5)
grid_array = pyglet.image.TextureArray.create_for_image_grid(grid)
print(grid_array)

batch = pyglet.graphics.Batch()

a = pyglet.sprite.Sprite(array.items[0], x=10, y=10, batch=batch)

b = pyglet.sprite.Sprite(array.items[1], x=200, y=10, batch=batch)

c = pyglet.sprite.Sprite(array.items[2], x=500, y=10, batch=batch)

# Can even get a region within the TextureArrayRegion.
region = array[1].get_region(50, 50, 50, 50)
d = pyglet.sprite.Sprite(region, x=10, y=300, batch=batch)

@window.event
def on_draw():
    window.clear()
    batch.draw()
    
pyglet.app.run()