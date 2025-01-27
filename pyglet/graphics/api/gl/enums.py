from __future__ import annotations

from pyglet.graphics import GeometryMode
from pyglet.graphics.api.gl import (
    GL_LINEAR, GL_NEAREST, GL_TEXTURE_1D, GL_TEXTURE_2D, GL_TEXTURE_3D, \
    GL_TEXTURE_CUBE_MAP, \
    GL_TEXTURE_1D_ARRAY, GL_TEXTURE_2D_ARRAY, GL_TEXTURE_CUBE_MAP_ARRAY, GL_TEXTURE_WRAP_R, GL_TEXTURE_WRAP_S, \
    GL_TEXTURE_WRAP_T,
    GL_POINTS, GL_LINES, GL_LINE_STRIP, GL_TRIANGLES, GL_TRIANGLE_STRIP,
    GL_TRIANGLE_FAN,
    GL_ZERO, GL_ONE, GL_SRC_COLOR, GL_ONE_MINUS_SRC_COLOR, GL_DST_COLOR,
    GL_ONE_MINUS_DST_COLOR, GL_SRC_ALPHA, \
    GL_ONE_MINUS_SRC_ALPHA, GL_DST_ALPHA, GL_ONE_MINUS_DST_ALPHA, GL_CONSTANT_COLOR,
    GL_ONE_MINUS_CONSTANT_COLOR, \
    GL_CONSTANT_ALPHA, GL_ONE_MINUS_CONSTANT_ALPHA)

from pyglet.enums import BlendFactor, TextureFilter, TextureType, TextureWrapping

geometry_map = {
    GeometryMode.POINTS: GL_POINTS,
    GeometryMode.LINES: GL_LINES,
    GeometryMode.LINE_STRIP: GL_LINE_STRIP,
    GeometryMode.TRIANGLES: GL_TRIANGLES,
    GeometryMode.TRIANGLE_STRIP: GL_TRIANGLE_STRIP,
    GeometryMode.TRIANGLE_FAN: GL_TRIANGLE_FAN,
}

blend_factor_map = {
    BlendFactor.ZERO: GL_ZERO,
    BlendFactor.ONE: GL_ONE,
    BlendFactor.SRC_COLOR: GL_SRC_COLOR,
    BlendFactor.ONE_MINUS_SRC_COLOR: GL_ONE_MINUS_SRC_COLOR,
    BlendFactor.DST_COLOR: GL_DST_COLOR,
    BlendFactor.ONE_MINUS_DST_COLOR: GL_ONE_MINUS_DST_COLOR,
    BlendFactor.SRC_ALPHA: GL_SRC_ALPHA,
    BlendFactor.ONE_MINUS_SRC_ALPHA: GL_ONE_MINUS_SRC_ALPHA,
    BlendFactor.DST_ALPHA: GL_DST_ALPHA,
    BlendFactor.ONE_MINUS_DST_ALPHA: GL_ONE_MINUS_DST_ALPHA,
    BlendFactor.CONSTANT_COLOR: GL_CONSTANT_COLOR,
    BlendFactor.ONE_MINUS_CONSTANT_COLOR: GL_ONE_MINUS_CONSTANT_COLOR,
    BlendFactor.CONSTANT_ALPHA: GL_CONSTANT_ALPHA,
    BlendFactor.ONE_MINUS_CONSTANT_ALPHA: GL_ONE_MINUS_CONSTANT_ALPHA,
}

texture_map = {
    # Filters
    TextureFilter.LINEAR: GL_LINEAR,
    TextureFilter.NEAREST: GL_NEAREST,

    # Texture Types
    TextureType.TYPE_1D: GL_TEXTURE_1D,
    TextureType.TYPE_2D: GL_TEXTURE_2D,
    TextureType.TYPE_3D: GL_TEXTURE_3D,
    TextureType.TYPE_CUBE_MAP: GL_TEXTURE_CUBE_MAP,
    TextureType.TYPE_1D_ARRAY: GL_TEXTURE_1D_ARRAY,
    TextureType.TYPE_2D_ARRAY: GL_TEXTURE_2D_ARRAY,
    TextureType.TYPE_CUBE_MAP_ARRAY: GL_TEXTURE_CUBE_MAP_ARRAY,

    # Wrapping
    TextureWrapping.WRAP_R: GL_TEXTURE_WRAP_R,
    TextureWrapping.WRAP_S: GL_TEXTURE_WRAP_S,
    TextureWrapping.WRAP_T: GL_TEXTURE_WRAP_T,
}
