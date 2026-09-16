import unittest

import pytest

import pyglet
from pyglet.enums import GeometryMode


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
                                          position=vertices,
                                          colors=colors)

        assert vertex_list.count == 3
        assert vertex_list.indexed is False
        assert tuple(vertex_list.position[:]) == pytest.approx(vertices)
        assert tuple(vertex_list.colors[:]) == pytest.approx(colors)

    def test_interned_vertex_layout_creates_vertex_list(self):
        program = pyglet.graphics.api.get_default_shader()
        assert program.get_vertex_view(None) is program.get_vertex_view(pyglet.graphics.VertexLayout())
        with pytest.raises(TypeError):
            program.get_vertex_view(colors="Bn")
        with pytest.raises(ValueError):
            pyglet.graphics.VertexLayout(colors="Bn")
        with pytest.raises(ValueError):
            program.get_vertex_view(pyglet.graphics.VertexLayout(colors="3Bn"))
        layout = program.get_vertex_view(pyglet.graphics.VertexLayout(colors="4Bn"))

        vertex_list = layout.vertex_list(
            3,
            GeometryMode.TRIANGLES,
            position=(0, 0, 0) * 3,
            colors=(255, 128, 0, 255) * 3,
        )

        assert program.get_vertex_view(pyglet.graphics.VertexLayout(colors="4Bn")) is layout
        assert tuple(vertex_list.colors[:]) == (255, 128, 0, 255) * 3

    def test_batch_creates_layout_first_vertex_lists(self):
        program = pyglet.graphics.api.get_default_shader()
        batch = pyglet.graphics.Batch()
        group = pyglet.graphics.ShaderGroup(program)
        layout = pyglet.graphics.VertexLayout(position="3f", colors="4Bn")
        storage = batch.create_vertex_storage(layouts=[layout])
        data = {
            "position": (0, 0, 0, 1, 0, 0, 0, 1, 0),
            "colors": (255, 128, 0, 255) * 3,
        }

        vertex_list = batch.vertex_list(layout, 3, GeometryMode.TRIANGLES, group, storage=storage, **data)
        indexed_vertex_list = batch.vertex_list_indexed(
            layout, 3, GeometryMode.TRIANGLES, (0, 1, 2), group, storage=storage, **data,
        )
        draw_pass = batch.add_pass(pyglet.graphics.DrawPass())
        vertex_list.add_pass(draw_pass, group=group)

        assert vertex_list.domain.attribute_meta["colors"].fmt.data_type == "B"
        assert vertex_list.domain.storage is storage
        assert indexed_vertex_list.indices == [0, 1, 2]
        assert len(batch._pass_registrations[draw_pass]) == 1
        assert any(buffer._dirty for buffer in vertex_list.domain.vertex_buffers.buffers)

        batch._update_draw_list()  # noqa: SLF001
        assert batch._pass_draw_lists[draw_pass]  # noqa: SLF001

        batch.draw_pass(draw_pass)

        assert all(not buffer._dirty for buffer in vertex_list.domain.vertex_buffers.buffers)

    def test_separate_storage_expansion_remains_contiguous(self):
        # Make sure expanded storage will be contiguous for separate
        program = pyglet.graphics.api.get_default_shader()
        batch = pyglet.graphics.Batch()
        group = pyglet.graphics.ShaderGroup(program)
        layout = pyglet.graphics.VertexLayout(position="3f")
        storage = batch.create_vertex_storage(sharing_policy="separate")
        count = 4096
        data = {"position": (0, 0, 0) * count}

        first = batch.vertex_list(layout, count, GeometryMode.TRIANGLES, group, storage=storage, **data)
        second = batch.vertex_list(layout, count, GeometryMode.TRIANGLES, group, storage=storage, **data)

        allocator = first.domain.vertex_buffers.allocator
        assert first.domain is second.domain
        assert second.start == count
        assert allocator.capacity == count * 2
        assert allocator.get_allocated_regions() == ([0], [count * 2])

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
                                          position=vertices_1,
                                          colors=colors)

        assert vertex_list.count == 3
        assert vertex_list.indexed is False
        assert tuple(vertex_list.position[:]) == pytest.approx(vertices_1)

        vertex_list.position[:] = vertices_2

        assert tuple(vertex_list.position[:]) == pytest.approx(vertices_2)

    def test_vertex_list_property_direct_set(self):
        program = pyglet.graphics.api.get_default_shader()

        vertices_1 = (
            100, 300, 0,
            200, 250, 0,
            200, 350, 0,
        )

        vertices_2 = (
            90, 200, 1,
            180, 210, 1,
            260, 340, 1,
        )

        colors = (
            1, 0, 0, 1,
            0, 1, 0, 1,
            0.3, 0.3, 1, 1,
        )

        vertex_list = program.vertex_list(3, GeometryMode.TRIANGLES,
                                          position=vertices_1,
                                          colors=colors)

        vertex_list.position = vertices_2

        assert tuple(vertex_list.position[:]) == pytest.approx(vertices_2)

    def test_indexed_vertex_list_creation(self):
        program = pyglet.graphics.api.get_default_shader()

        vertices = _create_quad_vertices(0, 0, 0, 50, 50)
        colors = (1, 0.5, 0.2, 1) * 4
        indices = [0, 1, 2, 0, 2, 3]

        vertex_list = program.vertex_list_indexed(4, GeometryMode.TRIANGLES, indices,
                                                  batch=None,
                                                  group=None,
                                                  position=vertices,
                                                  colors=colors)

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
                                                  position=vertices_1,
                                                  colors=colors)

        assert tuple(vertex_list.position[:]) == pytest.approx(vertices_1)

        vertex_list.position[:] = vertices_2

        assert tuple(vertex_list.position[:]) == pytest.approx(vertices_2)

    def test_indexed_vertex_list_property_direct_set(self):
        program = pyglet.graphics.api.get_default_shader()

        vertices_1 = _create_quad_vertices(0, 0, 0, 50, 50)
        vertices_2 = _create_quad_vertices(10, 20, 5, 40, 20)
        colors = (1, 0.5, 0.2, 1) * 4
        indices = [0, 1, 2, 0, 2, 3]

        vertex_list = program.vertex_list_indexed(4, GeometryMode.TRIANGLES, indices,
                                                  batch=None,
                                                  group=None,
                                                  position=vertices_1,
                                                  colors=colors)

        vertex_list.position = vertices_2

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
                                                  position=vertices,
                                                  colors=colors)

        vertex_list2 = program.vertex_list_indexed(4, GeometryMode.TRIANGLES, indices,
                                                   batch=batch,
                                                   group=None,
                                                   position=vertices,
                                                   colors=colors)

        vertex_list3 = program.vertex_list_indexed(4, GeometryMode.TRIANGLES, indices,
                                                   batch=batch,
                                                   group=None,
                                                   position=vertices,
                                                   colors=colors)

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
                                                   position=vertices,
                                                   colors=colors)

        shared_bucket = vertex_list1.bucket
        assert vertex_list1.domain == vertex_list4.domain == vertex_list3.domain
        assert vertex_list1.bucket == vertex_list4.bucket == vertex_list3.bucket
        assert len(shared_bucket.merged_ranges) == 1  # All 3 should be merged together again.
