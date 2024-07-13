import pyglet
import random

from pyglet.gl import GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_TRIANGLES
from pyglet.graphics.instance import InstanceSourceMixin

window = pyglet.window.Window(1920, 1080, vsync=False)

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


class SpriteInstanceSource(pyglet.sprite.Sprite, InstanceSourceMixin):
    """Subclass example."""

    def __init__(self, img, attributes, x=0, y=0, z=0, blend_src=GL_SRC_ALPHA, blend_dest=GL_ONE_MINUS_SRC_ALPHA, batch=None,
                 group=None, subpixel=False):
        self.instance_attributes = attributes
        InstanceSourceMixin.__init__(self, attributes)
        pyglet.sprite.Sprite.__init__(self, img, x, y, z, blend_src, blend_dest, batch, group, subpixel)


    def _create_vertex_list(self):
        self._vertex_list = self.program.vertex_list_instanced_indexed(
            4, GL_TRIANGLES, [0, 1, 2, 0, 2, 3], self.instance_attributes,
            self._batch, self._group,
            position=('f', self._get_vertices()),
            colors=('Bn', (*self._rgb, int(self._opacity)) * (1 if 'colors' in self.instance_attributes else 4)),
            translate=('f', (self._x, self._y, self._z) * (1 if 'translate' in self.instance_attributes else 4)),
            scale=('f', (self._scale*self._scale_x, self._scale*self._scale_y) * (1 if 'scale' in self.instance_attributes else 4)),
            rotation=('f', (self._rotation,) * (1 if 'rotation' in self.instance_attributes else 4)),
            tex_coords=('f', self._texture.tex_coords))


sprites = []
# Create 1000 sprites at various scales.
sprite = SpriteInstanceSource(image, ('translate', 'colors'),
                              x=random.randint(0, window.width),
                              y=random.randint(0, window.height),
                              batch=batch)

instance = sprite.create_instance(translate=(100, 50, 0), colors=(255, 255, 255, 255))

for i in range(10):
    sprite_instance = sprite.create_instance(
        translate=(random.randint(0, window.width), random.randint(0, window.height), 0),
        colors=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255),
    )

    #Randomize scale.
    #sprite_instance.scale = random.choice(scales)

    #Random color multiplier.
    #sprite_instance.colors = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    # Add sprites to keep in memory, like a list. Otherwise they will get GC'd when out of scope.
    sprites.append(sprite_instance)

#fps = pyglet.window.FPSDisplay(window)

@window.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.SPACE:
        instance.translate = (random.randint(0, window.width), random.randint(0, window.height), 0)
        # instance.translate[:] = (random.randint(0, window.width), random.randint(0, window.height), 0)
    elif symbol == pyglet.window.key.DELETE:
        del_instance = instance_sprite.pop()
        sprites.remove(del_instance)
    elif symbol == pyglet.window.key.INSERT:
        sprite_instance = instance_sprite.create(
            translate=(random.randint(0, window.width), random.randint(0, window.height), 0),
            colors=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255),
        )
        sprites.append(sprite_instance)

@window.event
def on_draw():
    window.clear()
    batch.draw()
    #fps.draw()


pyglet.app.run(0)

