"""Test that multiple windows can share or isolate contexts."""

from ctypes import *

import pyglet

from pyglet import window
from pyglet.graphics.api.gl import *


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

    w2 = window.Window(200, 200, context=w1.context)
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
    w2 = None

    try:
        w1.switch_to()
        textures = c_uint()
        glGenTextures(1, byref(textures))
        texture = textures.value

        glBindTexture(GL_TEXTURE_2D, texture)
        data = (c_ubyte * 4)()
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 1, 1, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
        assert glIsTexture(texture)

        w2 = window.Window(200, 200, context=None)
        w2.switch_to()
        assert not glIsTexture(texture)
    finally:
        w1.close()
        if w2:
            w2.close()
