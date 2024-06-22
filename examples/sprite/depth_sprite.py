"""An example of sorting sprites in the Z axis based on the Y axis, and a standard projection."""
import pyglet
from pyglet.gl import *
import random
import math

# Standard projection Z is 0 to 255. Keep window within that.
# You will have to change window projection if you wish to go beyond this.
window = pyglet.window.Window(height=250)

fragment_source = """#version 150 core
    in vec4 vertex_colors;
    in vec3 texture_coords;
    out vec4 final_colors;

    uniform sampler2D sprite_texture;

    void main()
    {
        final_colors = texture(sprite_texture, texture_coords.xy) * vertex_colors;
        
        // No GL_ALPHA_TEST in core, use shader to discard.
        if(final_colors.a < 0.01){
            discard;
        }
    }
"""


class DepthSpriteGroup(pyglet.sprite.SpriteGroup):
    def set_state(self):
        self.program.use()

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(self.texture.target, self.texture.id)

        glEnable(GL_BLEND)
        glBlendFunc(self.blend_src, self.blend_dest)

        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)

    def unset_state(self):
        glDisable(GL_BLEND)
        glDisable(GL_DEPTH_TEST)
        self.program.stop()


class DepthSprite(pyglet.sprite.Sprite):
    group_class = DepthSpriteGroup


# Set example resource path.
pyglet.resource.path = ['../resources']
pyglet.resource.reindex()

image = pyglet.resource.image("pyglet.png")
batch = pyglet.graphics.Batch()

sprites = []

# Re-use vertex source and create new shader with alpha testing.
vertex_shader = pyglet.graphics.shader.Shader(pyglet.sprite.vertex_source, "vertex")
fragment_shader = pyglet.graphics.shader.Shader(fragment_source, "fragment")
depth_shader = pyglet.graphics.shader.ShaderProgram(vertex_shader, fragment_shader)


def make_sprite(zvalue):
    sprite = DepthSprite(image, x=0, y=0, z=zvalue, batch=batch, program=depth_shader)
    # Random color multiplier.
    sprite.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    # Add sprites to keep in memory, like a list. Otherwise, they will get GC'd when out of scope.
    sprites.append(sprite)


sprite_count = 10
for i in range(sprite_count):
    make_sprite(i)


global elapsed
elapsed = 0


def update(dt):
    global elapsed
    for i, sprite in enumerate(sprites):
        sprite.update(x=i * .75 * (image.width - 15),
                      y=.25 * window.height * (1 + math.cos(2 * elapsed + i * math.pi / sprite_count)))
        sprite.z = sprite.y
    elapsed += dt


pyglet.clock.schedule_interval(update, 1 / 60.0)


@window.event
def on_draw():
    window.clear()
    batch.draw()


pyglet.app.run()
