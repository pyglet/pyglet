import pytest

import pyglet
from pyglet.graphics import GeometryMode

def create_quad_vertex_list(x, y, z, width, height):
    return (x, y, z,
            x + width, y, z,
            x + width, y + height, z,
            x, y + height, z)

def test_vertex_list_creation():
    program = pyglet.graphics.api.get_default_shader()

    vertices = (
        100, 300, 0,
        200, 250, 0,
        200, 350, 0,
    )

    colors = (
        1, 0, 0, 1,
        0, 1, 0, 1,
        0.3, 0.3, 1, 1,
    )

    vertex_list = program.vertex_list(3, GeometryMode.TRIANGLES,
                                      position=('f', vertices),
                                      colors=('f', colors))

    assert vertex_list.count == 3
    assert vertex_list.indexed is False
    assert tuple(vertex_list.position[:]) == pytest.approx(vertices)
    assert tuple(vertex_list.colors[:]) == pytest.approx(colors)

def test_vertex_list_property_set():
    program = pyglet.graphics.api.get_default_shader()

    vertices_1 = (
        100, 300, 0,
        200, 250, 0,
        200, 350, 0,
    )

    vertices_2 = (
        100, 300, 0,
        200, 250, 0,
        200, 350, 0,
    )

    colors = (
        1, 0, 0, 1,
        0, 1, 0, 1,
        0.3, 0.3, 1, 1,
    )

    vertex_list = program.vertex_list(3, GeometryMode.TRIANGLES,
                                      position=('f', vertices_1),
                                      colors=('f', colors))

    assert vertex_list.count == 3
    assert vertex_list.indexed is False
    assert tuple(vertex_list.position[:]) == pytest.approx(vertices_1)

    vertex_list.position[:] = vertices_2

    assert tuple(vertex_list.position[:]) == pytest.approx(vertices_2)

def test_indexed_vertex_list_creation():
    program = pyglet.graphics.api.get_default_shader()

    vertices = create_quad_vertex_list(0, 0, 0, 50, 50)
    colors = (1, 0.5, 0.2, 1) * 4
    indices = [0, 1, 2, 0, 2, 3]

    vertex_list = program.vertex_list_indexed(4, GeometryMode.TRIANGLES, indices,
                                              batch=None,
                                              group=None,
                                              position=('f', vertices),
                                              colors=('f', colors))

    assert vertex_list.count == 4
    assert vertex_list.indexed is True
    assert tuple(vertex_list.position[:]) == pytest.approx(vertices)
    assert tuple(vertex_list.colors[:])  == pytest.approx(colors)
    assert vertex_list.indices == indices

def test_indexed_vertex_list_property_set():
    program = pyglet.graphics.api.get_default_shader()

    vertices_1 = create_quad_vertex_list(0, 0, 0, 50, 50)
    vertices_2 = create_quad_vertex_list(3, 2, 1, 0, 20)
    colors = (1, 0.5, 0.2, 1) * 4
    indices = [0, 1, 2, 0, 2, 3]

    vertex_list = program.vertex_list_indexed(4, GeometryMode.TRIANGLES, indices,
                                              batch=None,
                                              group=None,
                                              position=('f', vertices_1),
                                              colors=('f', colors))

    assert tuple(vertex_list.position[:]) == pytest.approx(vertices_1)

    vertex_list.position[:] = vertices_2

    assert tuple(vertex_list.position[:]) == pytest.approx(vertices_2)