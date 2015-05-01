"""Tests for multi texturing."""

import pyglet
from pyglet import gl

from tests.interactive.windowed_test_base import WindowedTestCase

EMPTY = 0
BLUE_RECTANGLE = 1
GREEN_DOT = 2
RED_CIRCLE = 3


class MultiTextureTest(WindowedTestCase):
    texture0 = EMPTY
    texture1 = EMPTY
    texture2 = EMPTY

    def on_expose(self):
        self.draw()

    def render(self):
        # Enable blending
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        # Enable transparency
        gl.glEnable(gl.GL_ALPHA_TEST)
        gl.glAlphaFunc(gl.GL_GREATER, .1)

        # Load textures
        self.texture = pyglet.image.TextureGrid(
                pyglet.image.ImageGrid(
                    pyglet.image.load(
                        self.get_test_data_file('images', 'multitexture.png')), 1, 4))
        self.background = pyglet.image.load(
                self.get_test_data_file('images', 'grey_background.png')).get_texture()

        # Create vertex list showing the multi texture
        self.vertex_list = pyglet.graphics.vertex_list(4,
                ('v2f', (32, 32, 64, 32, 64, 64, 32, 64)),
                ('0t3f', self.texture[1].tex_coords),
                ('1t3f', self.texture[2].tex_coords),
                ('2t3f', self.texture[3].tex_coords))
        self._set_multi_tex_coords()

    def draw(self):
        self.window.clear()
        self.background.blit(0, 0)

        self._bind_texture(0)
        self._bind_texture(1)
        self._bind_texture(2)
        self.vertex_list.draw(gl.GL_QUADS)
        self._unbind_texture(2)
        self._unbind_texture(1)
        self._unbind_texture(0)

        self.window.flip()

    def _set_multi_tex_coords(self):
        self.vertex_list.multi_tex_coords = [self.texture[self.texture0].tex_coords,
                                             self.texture[self.texture1].tex_coords,
                                             self.texture[self.texture2].tex_coords]

    def _bind_texture(self, i):
        gl.glActiveTexture((gl.GL_TEXTURE0, gl.GL_TEXTURE1, gl.GL_TEXTURE2)[i])
        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture[i].id)
        gl.glTexEnvf(gl.GL_TEXTURE_ENV, gl.GL_TEXTURE_ENV_MODE, gl.GL_COMBINE)
        gl.glTexEnvf(gl.GL_TEXTURE_ENV, gl.GL_COMBINE_ALPHA, gl.GL_REPLACE if i == 0 else gl.GL_ADD)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)

    def _unbind_texture(self, i):
        gl.glActiveTexture((gl.GL_TEXTURE0, gl.GL_TEXTURE1, gl.GL_TEXTURE2)[i])
        gl.glDisable(gl.GL_TEXTURE_2D)


MultiTextureTest.create_test_case(
        name="test_multitexture_1",
        description='Verify that multiple textures can be applied to the same object.',
        question='Do you see a green dot inside a red circle on a grey background?',
        texture0=GREEN_DOT,
        texture1=RED_CIRCLE,
        texture2=EMPTY
        )

MultiTextureTest.create_test_case(
        name="test_multitexture_2",
        description='Verify that multiple textures can be applied to the same object.',
        question='Do you see a green dot inside a red circle inside a blue rectangle on a grey background?',
        texture0=GREEN_DOT,
        texture1=RED_CIRCLE,
        texture2=BLUE_RECTANGLE
        )

MultiTextureTest.create_test_case(
        name="test_multitexture_3",
        description='Verify that multiple textures can be applied to the same object.',
        question='Do you see a red circle on a grey background?',
        texture0=RED_CIRCLE,
        texture1=RED_CIRCLE,
        texture2=RED_CIRCLE
        )

