from __future__ import annotations

from typing import TYPE_CHECKING

import pyglet
from pyglet.graphics.api.gl.text import (
    decoration_fragment_source,
    decoration_vertex_source,
    layout_fragment_image_source,
    layout_fragment_source,
    layout_vertex_source,
    scrollable_decoration_fragment_source,
    scrollable_decoration_vertex_source,
    scrollable_layout_fragment_image_source,
    scrollable_layout_fragment_source,
    scrollable_layout_vertex_source,
)

if TYPE_CHECKING:
    from pyglet.graphics.api.webgl import ShaderProgram


def get_default_layout_shader() -> ShaderProgram:
    return pyglet.graphics.api.get_cached_shader(
        "default_text_layout",
        (layout_vertex_source, "vertex"),
        (layout_fragment_source, "fragment"),
        vertex_layout=pyglet.graphics.VertexLayout(colors="4Bn"),
    )


def get_default_scrollable_layout_shader() -> ShaderProgram:
    return pyglet.graphics.api.get_cached_shader(
        "default_scrollable_text_layout",
        (scrollable_layout_vertex_source, "vertex"),
        (scrollable_layout_fragment_source, "fragment"),
        vertex_layout=pyglet.graphics.VertexLayout(colors="4Bn"),
    )


def get_default_image_layout_shader() -> ShaderProgram:
    return pyglet.graphics.api.get_cached_shader(
        "default_text_image",
        (layout_vertex_source, "vertex"),
        (layout_fragment_image_source, "fragment"),
        vertex_layout=pyglet.graphics.VertexLayout(colors="4Bn"),
    )


def get_default_scrollable_image_layout_shader() -> ShaderProgram:
    return pyglet.graphics.api.get_cached_shader(
        "default_scrollable_text_image",
        (scrollable_layout_vertex_source, "vertex"),
        (scrollable_layout_fragment_image_source, "fragment"),
        vertex_layout=pyglet.graphics.VertexLayout(colors="4Bn"),
    )


def get_default_decoration_shader() -> ShaderProgram:
    return pyglet.graphics.api.get_cached_shader(
        "default_text_decoration",
        (decoration_vertex_source, "vertex"),
        (decoration_fragment_source, "fragment"),
        vertex_layout=pyglet.graphics.VertexLayout(colors="4Bn"),
    )


def get_default_scrollable_decoration_shader() -> ShaderProgram:
    return pyglet.graphics.api.get_cached_shader(
        "default_scrollable_text_decoration",
        (scrollable_decoration_vertex_source, "vertex"),
        (scrollable_decoration_fragment_source, "fragment"),
        vertex_layout=pyglet.graphics.VertexLayout(colors="4Bn"),
    )
