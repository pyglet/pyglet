"""An example of sorting sprites in the Z axis based on the Y axis, and a standard projection."""
from __future__ import annotations

import pyglet
from pyglet.enums import BlendFactor, CompareOp
import random
import math

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyglet.graphics import Group, ShaderProgram
    from pyglet.graphics.texture import TextureBase

# Standard projection Z is 0 to 255. Keep window within that.
# You will have to change window projection if you wish to go beyond this.
window = pyglet.window.Window(width=900, height=250)

vertex_source: str = """#version 150 core
    in vec3 translate;
    in vec4 colors;
    in vec3 tex_coords;
    in vec2 scale;
    in vec3 position;
    in float rotation;

    out vec4 vertex_colors;
    out vec3 texture_coords;

    uniform WindowBlock
    {
        mat4 projection;
        mat4 view;
    } window;

    mat4 m_scale = mat4(1.0);
    mat4 m_rotation = mat4(1.0);
    mat4 m_translate = mat4(1.0);

    void main()
    {
        m_scale[0][0] = scale.x;
        m_scale[1][1] = scale.y;
        m_translate[3][0] = translate.x;
        m_translate[3][1] = translate.y;
        m_translate[3][2] = translate.z;
        m_rotation[0][0] =  cos(-radians(rotation));
        m_rotation[0][1] =  sin(-radians(rotation));
        m_rotation[1][0] = -sin(-radians(rotation));
        m_rotation[1][1] =  cos(-radians(rotation));

        gl_Position = window.projection * window.view * m_translate * m_rotation * m_scale * vec4(position, 1.0);

        vertex_colors = colors;
        texture_coords = tex_coords;
    }
"""

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
    def __init__(self, texture: TextureBase, blend_src: BlendFactor, blend_dest: BlendFactor, program: ShaderProgram,
                 parent: Group | None = None) -> None:
        super().__init__(texture, blend_src, blend_dest, program, parent)
        self.set_depth_test(CompareOp.LESS)


class DepthSprite(pyglet.sprite.Sprite):
    group_class = DepthSpriteGroup


# Set example resource path.
pyglet.resource.path = ['../resources']
pyglet.resource.reindex()

image = pyglet.resource.texture("pyglet.png")
batch = pyglet.graphics.Batch()

sprites = []

# Reuse vertex source and create new shader with alpha testing.
vertex_shader = pyglet.graphics.Shader(vertex_source, "vertex")
fragment_shader = pyglet.graphics.Shader(fragment_source, "fragment")
depth_shader = pyglet.graphics.ShaderProgram(vertex_shader, fragment_shader)


def make_sprite(zvalue):
    sprite = DepthSprite(image, x=0, y=0, z=zvalue, batch=batch, program=depth_shader)
    # Random color multiplier.
    sprite.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    # Add sprites to keep in memory, like a list. Otherwise, they will get GC'd when out of scope.
    sprites.append(sprite)


sprite_count = 10
for i in range(sprite_count):
    make_sprite(i)


elapsed = 0


def update(dt):
    global elapsed  # noqa: PLW0603
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
