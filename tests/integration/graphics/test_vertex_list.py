import unittest

import pytest

import pyglet
from pyglet.graphics import GeometryMode

def _create_quad_vertices(x, y, z, width, height):
    return (x, y, z,
            x + width, y, z,
            x + width, y + height, z,
            x, y + height, z)


class VertexListTest(unittest.TestCase):
    def setUp(self):
        self.w = pyglet.window.Window(visible=False)

    def tearDown(self) -> None:
        self.w.close()

    def test_vertex_list_creation(self):
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

    def test_vertex_list_property_set(self):
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

    def test_indexed_vertex_list_creation(self):
        program = pyglet.graphics.api.get_default_shader()

        vertices = _create_quad_vertices(0, 0, 0, 50, 50)
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

    def test_indexed_vertex_list_property_set(self):
        program = pyglet.graphics.api.get_default_shader()

        vertices_1 = _create_quad_vertices(0, 0, 0, 50, 50)
        vertices_2 = _create_quad_vertices(3, 2, 1, 0, 20)
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

    def test_fragmentation(self):
        """This test splits up draws to ensure the vertex list is actually fragmented when another list is deleted.

         Ensure the bucket correctly splits and re-joins when necessary.

         Also initializes the draw to ensure multi-draw does not error.
         """
        program = pyglet.graphics.api.get_default_shader()
        batch = pyglet.graphics.Batch()

        vertices = _create_quad_vertices(0, 0, 0, 50, 50)
        colors = (1, 0.5, 0.2, 1) * 4
        indices = [0, 1, 2, 0, 2, 3]

        vertex_list1 = program.vertex_list_indexed(4, GeometryMode.TRIANGLES, indices,
                                                  batch=batch,
                                                  group=None,
                                                  position=('f', vertices),
                                                  colors=('f', colors))

        vertex_list2 = program.vertex_list_indexed(4, GeometryMode.TRIANGLES, indices,
                                                   batch=batch,
                                                   group=None,
                                                   position=('f', vertices),
                                                   colors=('f', colors))

        vertex_list3 = program.vertex_list_indexed(4, GeometryMode.TRIANGLES, indices,
                                                   batch=batch,
                                                   group=None,
                                                   position=('f', vertices),
                                                   colors=('f', colors))

        shared_bucket = vertex_list1.bucket
        assert vertex_list1.domain == vertex_list2.domain == vertex_list3.domain
        assert vertex_list1.bucket == vertex_list2.bucket == vertex_list3.bucket
        assert len(shared_bucket.merged_ranges) == 1  # All 3 should be merged together.

        vertex_list2.delete()

        assert vertex_list1.bucket == vertex_list3.bucket
        assert len(shared_bucket.merged_ranges) == 2  # Fragmented into 2 calls.

        batch.draw()

        # Add another to make sure fragmentation is filled in where possible.
        vertex_list4 = program.vertex_list_indexed(4, GeometryMode.TRIANGLES, indices,
                                                   batch=batch,
                                                   group=None,
                                                   position=('f', vertices),
                                                   colors=('f', colors))

        shared_bucket = vertex_list1.bucket
        assert vertex_list1.domain == vertex_list4.domain == vertex_list3.domain
        assert vertex_list1.bucket == vertex_list4.bucket == vertex_list3.bucket
        assert len(shared_bucket.merged_ranges) == 1  # All 3 should be merged together again.