"""Tests for multi texturing."""

import pyglet
from pyglet import gl

import pytest

from tests.interactive.event_loop_test_base import TestWindow, EventLoopFixture

EMPTY = 0
BLUE_RECTANGLE = 1
GREEN_DOT = 2
RED_CIRCLE = 3


class MultiTextureTestWindow(TestWindow):
    def __init__(self, test_data, *args, **kwargs):
        super(MultiTextureTestWindow, self).__init__(*args, **kwargs)
        self.test_data = test_data
        self.render()

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
                        self.test_data.get_file('images', 'multitexture.png')), 1, 4))
        self.background = pyglet.image.load(
                self.test_data.get_file('images', 'grey_background.png')).get_texture()

        # Create vertex list showing the multi texture
        self.vertex_list = pyglet.graphics.vertex_list(4,
                ('v2f', (32, 332, 64, 332, 64, 364, 32, 364)),
                ('0t3f', self.texture[1].tex_coords),
                ('1t3f', self.texture[2].tex_coords),
                ('2t3f', self.texture[3].tex_coords))

    def on_draw(self):
        super(MultiTextureTestWindow, self).on_draw()

        self._bind_texture(0)
        self._bind_texture(1)
        self._bind_texture(2)
        self.vertex_list.draw(gl.GL_QUADS)
        self._unbind_texture(2)
        self._unbind_texture(1)
        self._unbind_texture(0)

        self.flip()

    def set_textures(self, texture0=EMPTY, texture1=EMPTY, texture2=EMPTY):
        self.vertex_list.multi_tex_coords = [self.texture[texture0].tex_coords,
                                             self.texture[texture1].tex_coords,
                                             self.texture[texture2].tex_coords]

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


class MultiTextureFixture(EventLoopFixture):
    window_class = MultiTextureTestWindow


@pytest.fixture
def multi_texture_fixture(request):
    return MultiTextureFixture(request)


def test_multitexture(multi_texture_fixture, test_data):
        'Verify that multiple textures can be applied to the same object.'
        w = multi_texture_fixture.create_window(test_data=test_data, height=400)
        w.set_textures(GREEN_DOT, RED_CIRCLE, EMPTY)
        multi_texture_fixture.ask_question(
            'Do you see a green dot inside a red circle on a white background?',
        )
        w.set_textures(GREEN_DOT, RED_CIRCLE, BLUE_RECTANGLE)
        multi_texture_fixture.ask_question(
            'Do you see a green dot inside a red circle inside a blue rectangle on a white background?',
        )
        w.set_textures(RED_CIRCLE, RED_CIRCLE, RED_CIRCLE)
        multi_texture_fixture.ask_question(
            'Do you see a red circle on a white background?',
        )

