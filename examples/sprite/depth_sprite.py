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
    out vec4 final_color;

    uniform sampler2D sprite_texture;

    const float _alpha_clip = 0.01;

    const mat4 dither_matrix = mat4(
        vec4(0.0625, 0.5625, 0.1875, 0.6875),
        vec4(0.8125, 0.3125, 0.9375, 0.4375),
        vec4(0.25, 0.75, 0.125, 0.625),
        vec4(1.0, 0.5, 0.875, 0.375)
    );

    float getValue(int x, int y) {
        int mx = x % 4;
        int my = y % 4;
        return dither_matrix[mx][my];
    }

    void main() {
        vec4 color = texture(sprite_texture, texture_coords.xy) * vertex_colors;

        float limit = getValue(int(gl_FragCoord.x), int(gl_FragCoord.y));

        if (color.a < limit) {
             discard;
        }

        final_color = vec4(color.rgb, 1.0);

    }
"""


class DepthSpriteGroup(pyglet.sprite.SpriteGroup):
    def set_state(self):
        self.program.use()

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(self.texture.target, self.texture.id)

        glEnable(GL_BLEND)
        glBlendFunc(self.blend_src, self.blend_dest)

        # glEnable(GL_DEPTH_TEST)
        # glDepthFunc(GL_LESS)

    def unset_state(self):
        # glDisable(GL_BLEND)
        # glDisable(GL_DEPTH_TEST)
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
    sprite.color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
    sprite.opacity = 60
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
        # sprite.opacity = sprite.y + 50
    elapsed += dt


pyglet.clock.schedule_interval(update, 1 / 60.0)


@window.event
def on_draw():
    window.clear()
    batch.draw()


pyglet.app.run()
