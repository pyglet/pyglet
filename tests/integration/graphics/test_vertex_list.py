import unittest
import pytest

import pyglet
from pyglet.enums import GeometryMode
from pyglet.graphics.shader import MissingAttributeException


def _create_quad_vertices(x, y, z, width, height):
    return (x, y, z,
            x + width, y, z,
            x + width, y + height, z,
            x, y + height, z)


def _position_color_program(position_location: int, color_location: int):
    vertex = pyglet.graphics.Shader(f'''#version 330 core
        layout(location = {position_location}) in vec2 position;
        layout(location = {color_location}) in vec4 colors;
        out vec4 vertex_colors;

        void main() {{
            gl_Position = vec4(position, 0.0, 1.0);
            vertex_colors = colors;
        }}
    ''', 'vertex')
    fragment = pyglet.graphics.Shader('''#version 330 core
        in vec4 vertex_colors;
        out vec4 final_colors;

        void main() {
            final_colors = vertex_colors;
        }
    ''', 'fragment')
    return pyglet.graphics.ShaderProgram(vertex, fragment, vertex_layout=None)


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

        assert vertex_list.domain.attribute_meta["colors"].data_type == "B"
        assert vertex_list.domain.storage is storage
        assert indexed_vertex_list.indices == [0, 1, 2]
        assert len(batch._pass_registrations[draw_pass]) == 1
        assert any(buffer._dirty for buffer in vertex_list.domain.vertex_buffers.buffers)

        batch._update_draw_list()  # noqa: SLF001
        assert batch._pass_draw_lists[draw_pass]  # noqa: SLF001

        batch.draw_pass(None)

        assert all(not buffer._dirty for buffer in vertex_list.domain.vertex_buffers.buffers)

        batch.draw_pass(draw_pass)

        assert all(not buffer._dirty for buffer in vertex_list.domain.vertex_buffers.buffers)

    def test_separate_storage_expansion_remains_contiguous(self):
        # Make sure expanded storage will be contiguous for separate
        program = pyglet.graphics.api.get_default_shader()
        batch = pyglet.graphics.Batch()
        group = pyglet.graphics.ShaderGroup(program)
        layout = pyglet.graphics.VertexLayout(position="3f", colors="4f")
        storage = batch.create_vertex_storage(sharing_policy="separate")
        count = 4096
        data = {"position": (0, 0, 0) * count, "colors": (1, 1, 1, 1) * count}

        first = batch.vertex_list(layout, count, GeometryMode.TRIANGLES, group, storage=storage, **data)
        second = batch.vertex_list(layout, count, GeometryMode.TRIANGLES, group, storage=storage, **data)

        allocator = first.domain.vertex_buffers.allocator
        assert first.domain is second.domain
        assert second.start == count
        assert allocator.capacity == count * 2
        assert allocator.get_allocated_regions() == ([0], [count * 2])

    def test_separate_storage_binding_owns_independent_resources(self):
        program = pyglet.graphics.api.get_default_shader()
        batch = pyglet.graphics.Batch()
        group = pyglet.graphics.ShaderGroup(program)
        layout = pyglet.graphics.VertexLayout(position="3f", colors="4f")
        storage = batch.create_vertex_storage(sharing_policy="separate")
        data = {"position": (0, 0, 0) * 3, "colors": (1, 1, 1, 1) * 3}

        triangles = batch.vertex_list_indexed(
            layout, 3, GeometryMode.TRIANGLES, (0, 1, 2), group, storage=storage, **data,
        )
        lines = batch.vertex_list_indexed(
            layout, 3, GeometryMode.LINES, (0, 1, 2), group, storage=storage, **data,
        )

        triangle_binding = triangles.domain.storage_binding
        line_binding = lines.domain.storage_binding
        assert triangle_binding.vertex_stream is triangles.domain.vertex_buffers
        assert triangle_binding.index_stream is triangles.domain.index_stream
        assert triangles.domain.allocator is triangle_binding.vertex_allocator
        assert triangles.domain.index_allocator is triangle_binding.index_allocator
        assert triangle_binding.vertex_stream is not line_binding.vertex_stream
        assert triangle_binding.index_stream is not line_binding.index_stream
        assert triangle_binding.vertex_allocator is not line_binding.vertex_allocator
        assert triangle_binding.index_allocator is not line_binding.index_allocator

    def test_shared_storage_uses_shared_streams_and_allocators(self):
        program = pyglet.graphics.api.get_default_shader()
        batch = pyglet.graphics.Batch()
        group = pyglet.graphics.ShaderGroup(program)
        layout = pyglet.graphics.VertexLayout(position="3f", colors="4f")
        storage = batch.create_vertex_storage(sharing_policy="shared")
        data = {"position": (0, 0, 0) * 3, "colors": (1, 1, 1, 1) * 3}

        triangles = batch.vertex_list_indexed(
            layout, 3, GeometryMode.TRIANGLES, (0, 1, 2), group, storage=storage, **data,
        )
        lines = batch.vertex_list_indexed(
            layout, 3, GeometryMode.LINES, (0, 1, 2), group, storage=storage, **data,
        )

        assert isinstance(storage, pyglet.graphics.VertexStorageShared)
        assert triangles.domain is not lines.domain
        assert triangles.domain.vertex_buffers.allocator is lines.domain.vertex_buffers.allocator
        assert (
            triangles.domain.vertex_buffers.attrib_name_buffers["position"]
            is lines.domain.vertex_buffers.attrib_name_buffers["position"]
        )
        assert triangles.domain.index_stream is lines.domain.index_stream
        assert triangles.domain.allocator is not lines.domain.allocator
        assert triangles.domain.index_allocator is not lines.domain.index_allocator

    def test_storage_indexes_layouts_by_geometry_key(self):
        batch = pyglet.graphics.Batch()
        storage = batch.create_vertex_storage()
        layout = pyglet.graphics.VertexLayout(position="3f", colors="4Bn")

        assert storage.add_layout(layout) is layout
        assert storage.add_layout(pyglet.graphics.VertexLayout(position="3f", colors="4Bn")) is layout
        assert storage.layouts == {layout.key: layout}

    def test_storage_binding_delegates_vertex_and_index_allocation(self):
        program = pyglet.graphics.api.get_default_shader()
        batch = pyglet.graphics.Batch()
        group = pyglet.graphics.ShaderGroup(program)
        layout = pyglet.graphics.VertexLayout(position="3f", colors="4f")
        data = {"position": (0, 0, 0) * 3, "colors": (1, 1, 1, 1) * 3}
        vertex_list = batch.vertex_list_indexed(
            layout, 3, GeometryMode.TRIANGLES, (0, 1, 2), group, **data,
        )
        domain = vertex_list.domain

        vertex_start = domain.safe_alloc(2)
        vertex_start = domain.safe_realloc(vertex_start, 2, 3)
        domain.deallocate_vertices(vertex_start, 3)

        index_start = domain.safe_index_alloc(2)
        index_start = domain.safe_index_realloc(index_start, 2, 3)
        domain.deallocate_indices(index_start, 3)

        assert domain.allocator.get_allocated_regions() == ([0], [3])
        assert domain.index_allocator.get_allocated_regions() == ([0], [3])

    def test_layout_geometry_can_be_created_without_a_shader_and_attached_later(self):
        batch = pyglet.graphics.Batch()
        layout = pyglet.graphics.VertexLayout(position="2f", colors="4Bn")
        positions = (0, 0, 1, 0, 0, 1)
        colors = (255, 0, 0, 255) * 3
        mesh = batch.vertex_list_indexed(
            layout, 3, GeometryMode.TRIANGLES, (0, 1, 2), group=None,
            position=positions, colors=colors,
        )

        assert mesh.group is None
        assert mesh.bucket is None
        assert mesh.domain.vertex_layout == layout
        assert mesh.indices == [0, 1, 2]
        assert tuple(mesh.position[:]) == positions
        assert tuple(mesh.colors[:]) == colors

        first_program = _position_color_program(1, 0)
        second_program = _position_color_program(0, 1)
        first_group = pyglet.graphics.ShaderGroup(first_program)
        second_group = pyglet.graphics.ShaderGroup(second_program)
        try:
            mesh.set_group(first_group)
            domain = mesh.domain
            storage_binding = domain.storage_binding
            start, index_start = mesh.start, mesh.index_start

            assert mesh.bucket is domain.get_drawable_bucket(first_group)
            mesh.set_group(second_group)

            assert mesh.domain is domain
            assert mesh.domain.storage_binding is storage_binding
            assert mesh.start == start
            assert mesh.index_start == index_start
            assert mesh.bucket is domain.get_drawable_bucket(second_group)
            assert tuple(mesh.position[:]) == positions
            assert tuple(mesh.colors[:]) == colors
        finally:
            first_program.delete()
            second_program.delete()

    def test_layout_data_validation_does_not_require_a_shader(self):
        batch = pyglet.graphics.Batch()
        layout = pyglet.graphics.VertexLayout(position="2f", colors="4Bn")

        with pytest.raises(ValueError, match="unknown attributes"):
            batch.vertex_list(
                layout, 3, GeometryMode.TRIANGLES, group=None,
                position=(0, 0) * 3, colors=(255, 0, 0, 255) * 3, normals=(0, 0, 1) * 3,
            )
        with pytest.raises(ValueError, match="require data"):
            batch.vertex_list(layout, 3, GeometryMode.TRIANGLES, group=None, position=(0, 0) * 3)
        with pytest.raises(ValueError, match="Invalid data size for 'colors'"):
            batch.vertex_list(
                layout, 3, GeometryMode.TRIANGLES, group=None,
                position=(0, 0) * 3, colors=(255, 0, 0, 255) * 2,
            )

    def test_vertex_layout_key_includes_instance_divisors(self):
        layout = pyglet.graphics.VertexLayout(position="2f", colors="4Bn")
        instanced_layout = layout.with_divisors(colors=1)
        shorthand_layout = pyglet.graphics.VertexLayout(position="2f", colors="4Bn/1")

        assert layout.key != instanced_layout.key
        assert layout.attribute_formats["colors"].divisor == 0
        assert instanced_layout.attribute_formats["colors"].divisor == 1
        assert shorthand_layout.key == instanced_layout.key
        assert instanced_layout.attribute_formats == shorthand_layout.attribute_formats

    def test_shader_vertex_list_creation_delegates_to_layout_geometry(self):
        batch = pyglet.graphics.Batch()
        program = _position_color_program(1, 0)
        try:
            mesh = program.vertex_list(
                3, GeometryMode.TRIANGLES, batch=batch,
                position=(0, 0, 1, 0, 0, 1), colors=(1, 0, 0, 1) * 3,
            )

            assert mesh.group is not None
            assert mesh.domain.attribute_meta == program.attribute_formats
            assert isinstance(next(iter(mesh.domain.storage.layouts.values())), pyglet.graphics.VertexLayout)
        finally:
            program.delete()

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


def test_vertex_list_requires_all_shader_attributes(test_window):  # noqa: ARG001
    """Each active shader input must be supplied when creating geometry."""
    program = pyglet.graphics.api.get_default_shader()

    with pytest.raises(MissingAttributeException, match="colors"):
        program.vertex_list(3, GeometryMode.TRIANGLES, position=(0, 0, 0) * 3)

