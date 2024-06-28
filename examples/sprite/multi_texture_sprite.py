"""This example shows how to use multiple textures in a shader with Pyglet."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pyglet
from pyglet.gl import glActiveTexture, GL_TEXTURE0, glBindTexture, glEnable, GL_BLEND, glBlendFunc, glDisable, \
    glClearColor, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA

if TYPE_CHECKING:
    from pyglet.image import Texture, AbstractImage
    from pyglet.graphics import Batch, Group
    from pyglet.graphics.shader import ShaderProgram

vertex_source = """#version 150 core
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

    uniform sampler2D kitten_texture;
    uniform sampler2D pyglet_texture;

    void main()
    {
        final_colors = texture(kitten_texture, texture_coords.xy) * texture(pyglet_texture, texture_coords.xy) * 
        vertex_colors;
    }
"""


class MultiTextureSpriteGroup(pyglet.sprite.SpriteGroup):
    """A sprite group that uses multiple active textures."""

    def __init__(self, textures: dict[str, Texture], blend_src: int, blend_dest: int,
                 program: ShaderProgram | None = None, parent: Group | None = None) -> None:
        """Create a sprite group for multiple textures and samplers.

        All textures must share the same target type.

        Args:
            textures:
                A dictionary of textures, with the keys being the GLSL sampler name.
            blend_src:
                OpenGL blend source mode; for example, ``GL_SRC_ALPHA``.
            blend_dest:
                OpenGL blend destination mode; for example, ``GL_ONE_MINUS_SRC_ALPHA``.
            parent:
                Optional parent group.
        """
        self.textures = textures
        texture = list(self.textures.values())[0]
        self.target = texture.target
        super().__init__(texture, blend_src, blend_dest, program, parent)

    def set_state(self) -> None:
        self.program.use()

        for idx, name in enumerate(self.textures):
            self.program[name] = idx

        for i, texture in enumerate(self.textures.values()):
            glActiveTexture(GL_TEXTURE0 + i)
            glBindTexture(self.target, texture.id)

        glEnable(GL_BLEND)
        glBlendFunc(self.blend_src, self.blend_dest)

    def unset_state(self) -> None:
        glDisable(GL_BLEND)
        self.program.stop()
        glActiveTexture(GL_TEXTURE0)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.texture}-{self.texture.id})'

    def __eq__(self, other: object | Group | MultiTextureSpriteGroup) -> bool:
        return (other.__class__ is self.__class__ and
                self.program is other.program and
                self.textures == other.textures and
                self.blend_src == other.blend_src and
                self.blend_dest == other.blend_dest)

    def __hash__(self) -> int:
        return hash((id(self.parent),
                     id(self.textures),
                     self.blend_src, self.blend_dest))


class MultiTextureSprite(pyglet.sprite.Sprite):
    """An example of a Sprite that can utilize multiple textures for an effect."""
    group_class = MultiTextureSpriteGroup

    def __init__(self,
                 images: dict[str, AbstractImage],
                 x: float = 0, y: float = 0, z: float = 0,
                 blend_src: int = GL_SRC_ALPHA,
                 blend_dest: int = GL_ONE_MINUS_SRC_ALPHA,
                 batch: Batch | None = None,
                 group: Group | None = None,
                 subpixel: bool = False,
                 program: ShaderProgram | None = None) -> None:
        """Create a Sprite instance.

        Args:
            images:
                A dictionary of images, with the keys being the GLSL sampler name.
            x:
                X coordinate of the sprite.
            y:
                Y coordinate of the sprite.
            z:
                Z coordinate of the sprite.
            blend_src:
                OpenGL blend source mode.  The default is suitable for
                compositing sprites drawn from back-to-front.
            blend_dest:
                OpenGL blend destination mode.  The default is suitable for
                compositing sprites drawn from back-to-front.
            batch:
                Optional batch to add the sprite to.
            group:
                Optional parent group of the sprite.
            subpixel:
                Allow floating-point coordinates for the sprite. By default,
                coordinates are restricted to integer values.
            program:
                A specific shader program to initialize the sprite with. By default, a pre-made shader will be chosen
                based on the texture type passed.
        """
        # Ensure the images are textures.
        self.textures: dict[str, Texture] = {name: img.get_texture() for name, img in images.items()}
        assert all(tex.target for tex in self.textures.values()) is True, "All textures need to be the same target."

        # Use first image as base.
        super().__init__(list(self.textures.values())[0], x, y, z, blend_src, blend_dest, batch, group, subpixel,
                         program)

    def get_sprite_group(self) -> MultiTextureSpriteGroup:
        return self.group_class(self.textures, self._blend_src, self._blend_dest, self._program, self._user_group)


window = pyglet.window.Window()

# Set example resource path.
pyglet.resource.path = ['../resources']
pyglet.resource.reindex()

# Load example image from resource path.
# Resource will load images into a texture atlas, disable atlas loading, so they can be separate textures.
pyglet_image = pyglet.resource.image("pyglet.png", atlas=False)
kitten_image = pyglet.resource.image("kitten.jpg", atlas=False)

window.set_size(kitten_image.width, kitten_image.height)

# Batching allows rendering groups of objects all at once instead of drawing one by one.
batch = pyglet.graphics.Batch()

# Create our new shader that handles both texture sprites.
multi_vert_shader = pyglet.graphics.shader.Shader(vertex_source, 'vertex')
multi_frag_shader = pyglet.graphics.shader.Shader(fragment_source, 'fragment')

# Our new shader just multiplies both images together.
multitex_shader_program = pyglet.graphics.shader.ShaderProgram(multi_vert_shader, multi_frag_shader)

# Give our shader names and textures.
shader_images = {
    "kitten_texture": kitten_image,
    "pyglet_texture": pyglet_image,
}

sprite = MultiTextureSprite(shader_images,
                            x=0,
                            y=0,
                            batch=batch,
                            program=multitex_shader_program)

glClearColor(1.0, 1.0, 1.0, 1.0)


@window.event
def on_draw():
    window.clear()
    batch.draw()


pyglet.app.run()
