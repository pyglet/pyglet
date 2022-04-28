"""This example shows how to use multiple textures in a shader with Pyglet."""

import pyglet
from pyglet.gl import *
import random

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
        final_colors = texture(kitten_texture, texture_coords.xy) * texture(pyglet_texture, texture_coords.xy) * vertex_colors;
    }
"""


class MultiTextureSpriteGroup(pyglet.sprite.SpriteGroup):
    """A sprite group that uses multiple active textures.
    """

    def __init__(self, textures, blend_src, blend_dest, program=None, order=0, parent=None):
        """Create a sprite group for multiple textures and samplers.
           All textures must share the same target type.

        :Parameters:
            `textures` : `dict`
                Textures in samplername : texture.
            `blend_src` : int
                OpenGL blend source mode; for example,
                ``GL_SRC_ALPHA``.
            `blend_dest` : int
                OpenGL blend destination mode; for example,
                ``GL_ONE_MINUS_SRC_ALPHA``.
            `parent` : `~pyglet.graphics.Group`
                Optional parent group.
        """
        self.textures = textures
        texture = list(self.textures.values())[0]
        self.target = texture.target
        super().__init__(texture, blend_src, blend_dest, program, order, parent)

    def set_state(self):
        self.program.use()

        for idx, name in enumerate(self.textures):
            self.program[name] = idx

        for i, texture in enumerate(self.textures.values()):
            glActiveTexture(GL_TEXTURE0 + i)
            glBindTexture(self.target, texture.id)

        glEnable(GL_BLEND)
        glBlendFunc(self.blend_src, self.blend_dest)

    def unset_state(self):
        glDisable(GL_BLEND)
        self.program.stop()
        glActiveTexture(GL_TEXTURE0)

    def __repr__(self):
        return '%s(%r-%d)' % (self.__class__.__name__, self.texture, self.texture.id)

    def __eq__(self, other):
        return (other.__class__ is self.__class__ and
                self.program is other.program and
                self.textures == other.textures and
                self.blend_src == other.blend_src and
                self.blend_dest == other.blend_dest)

    def __hash__(self):
        return hash((id(self.parent),
                     id(self.textures),
                     self.blend_src, self.blend_dest))


class MultiTextureSprite(pyglet.sprite.AdvancedSprite):
    group_class = MultiTextureSpriteGroup

    def __init__(self,
                 imgs, x=0, y=0, z=0,
                 blend_src=GL_SRC_ALPHA,
                 blend_dest=GL_ONE_MINUS_SRC_ALPHA,
                 batch=None,
                 group=None,
                 subpixel=False,
                 program=None):
        # Ensure the images are textures.
        textures = {}
        for name, img in imgs.items():
            textures[name] = img.get_texture()

        same_target = all([texture.target for texture in textures.values()])
        assert same_target is True, "All textures need to be the same target."
        self._x = x
        self._y = y
        self._z = z
        self._program = program

        # Use first image as base.
        self._texture = list(textures.values())[0]

        self._batch = batch or graphics.get_default_batch()
        self._group = self.group_class(textures, blend_src, blend_dest, self._program, 0, group)
        self._subpixel = subpixel
        self._create_vertex_list()


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
