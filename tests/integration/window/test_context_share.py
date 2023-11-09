"""Test that multiple windows share objects by default.
"""

from ctypes import *

import pyglet

from pyglet import window
from pyglet.gl import *


def create_context(share):
    display = pyglet.display.get_display()
    screen = display.get_default_screen()
    config = screen.get_best_config()
    return config.create_context(share)


def test_context_share_texture():
    w1 = window.Window(200, 200)
    w1.switch_to()
    textures = c_uint()
    glGenTextures(1, byref(textures))
    texture = textures.value

    glBindTexture(GL_TEXTURE_2D, texture)
    data = (c_ubyte * 4)()
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 1, 1, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
    assert glIsTexture(texture)

    w2 = window.Window(200, 200)
    w2.switch_to()
    assert glIsTexture(texture)

    glDeleteTextures(1, byref(textures))
    assert not glIsTexture(texture)

    w1.switch_to()
    assert not glIsTexture(texture)

    w1.close()
    w2.close()


def test_context_noshare_texture():
    w1 = window.Window(200, 200)
    w1.switch_to()
    textures = c_uint()
    glGenTextures(1, byref(textures))
    texture = textures.value

    glBindTexture(GL_TEXTURE_2D, texture)
    data = (c_ubyte * 4)()
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 1, 1, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
    assert glIsTexture(texture)

    w2 = window.Window(200, 200, context=create_context(None))
    w2.switch_to()
    assert not glIsTexture(texture)

    w1.close()
    w2.close()
