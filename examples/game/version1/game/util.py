import pyglet

# Give pyglet a list of folders that contain resources:
pyglet.resource.path = ['../resources']
pyglet.resource.reindex()


def center_texture(texture, x_divisor=2.0, y_divisor=2.0):
    """Sets a texture's anchor point."""
    texture.anchor_x = texture.width / x_divisor
    texture.anchor_y = texture.height / y_divisor


def load_centered(filename, x_divisor=2.0, y_divisor=2.0):
    texture = pyglet.resource.texture(filename)
    center_texture(texture, x_divisor, y_divisor)
    return texture
