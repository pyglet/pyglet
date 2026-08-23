from __future__ import annotations

import ctypes
import random

import pytest

from pyglet.enums import GeometryMode
from tests.annotations import GraphicsAPIGroups, skip_graphics_api


pytestmark = [skip_graphics_api(GraphicsAPIGroups.GL2)]


_vertex_source: str = """#version 330 core
    in vec3 position;
    in vec3 translate;
    in vec4 colors;
    in vec3 tex_coords;
    out vec4 vertex_colors;

    uniform WindowBlock
    {
        mat4 projection;
        mat4 view;
    } window;

    void main()
    {
         mat4 m_translate = mat4(1.0);
         m_translate[3][0] = translate.x;
         m_translate[3][1] = translate.y;
         m_translate[3][2] = translate.z;

        gl_Position = window.projection * window.view * m_translate * vec4(position, 1.0);

        vertex_colors = colors;
    }
"""

_fragment_source: str = """#version 330 core
    in vec4 vertex_colors;
    out vec4 final_colors;

    void main()
    {
        final_colors = vertex_colors;
    }
"""


@pytest.fixture(scope="module")
def shader_program(test_window):
    """Compile and link the ShaderProgram once per module, and delete at the end."""
    from pyglet.graphics import ShaderProgram, Shader
    vertex = Shader(_vertex_source, "vertex")
    fragment = Shader(_fragment_source, "fragment")
    program = ShaderProgram(vertex, fragment)
    program.set_instance_attributes(colors=1, translate=1)
    try:
        yield program
    finally:
        # Ensures deletion even if a test failed
        program.delete()


@pytest.fixture
def vlist_factory(shader_program):
    """Helper to create a fresh instanced vertex list bound to the shared program."""
    from pyglet.enums import GeometryMode
    def make(verts, indices=(0,1,2,0,2,3), batch=None, group=None):
        return shader_program.vertex_list_instanced_indexed(
            4,
            mode=GeometryMode.TRIANGLES,
            indices=list(indices),
            batch=batch,
            group=group,
            position=tuple(verts),
            colors=(1.0, 0.0, 0.0, 1.0),
            translate=(500.0, 500.0, 0.0),
        )
    return make


@pytest.fixture
def vlist_non_indexed_factory(shader_program):
    """Helper to create a fresh non-indexed instanced vertex list bound to the shared program."""
    from pyglet.enums import GeometryMode

    def make(verts, batch=None, group=None):
        return shader_program.vertex_list_instanced(
            3,
            mode=GeometryMode.TRIANGLES,
            batch=batch,
            group=group,
            position=tuple(verts),
            colors=(1.0, 0.0, 0.0, 1.0),
            translate=(500.0, 500.0, 0.0),
        )

    return make


def test_instancing_count(vlist_factory):
    """Ensure the instance count is correct."""
    verts = (
        0.0, 0.0, 0.0,
        1.0, 0.0, 0.0,
        1.0, 1.0, 0.0,
        0.0, 1.0, 0.0,
    )
    vlist = vlist_factory(verts)

    size = 128.0
    instance_count = 25
    for i in range(instance_count):
        vlist.create_instance(
            colors=(random.random(), random.random(), random.random(), 1.0),
            translate=(i * size, i * size, 0.0),
        )

    assert vlist.instance_bucket is not None
    assert vlist.instance_bucket.instance_count == instance_count  # the initial list


def test_bulk_instance_collection(vlist_factory):
    """Ensure bulk collections manage their data, count, and storage lifetime."""
    vlist = vlist_factory((0.0,) * 12)
    collection = vlist.create_instance_collection(
        3,
        capacity=8,
        colors=(1.0, 0.0, 0.0, 1.0) * 3,
        translate=(0.0, 0.0, 0.0, 10.0, 0.0, 0.0, 20.0, 0.0, 0.0),
    )

    assert vlist.instance_bucket.stream.allocator.get_allocated_regions() == ([0], [8])
    assert collection.count == 3
    assert collection.capacity == 8
    assert len(collection) == 3
    assert vlist.instance_count == 3

    collection.set_count(1)
    assert vlist.instance_count == 1
    assert collection.capacity == 8

    collection.set_count(3)
    collection.set(
        start=1,
        count=2,
        translate=(11.0, 0.0, 0.0, 21.0, 0.0, 0.0),
    )
    assert tuple(collection.get("translate")) == (0.0, 0.0, 0.0, 11.0, 0.0, 0.0, 21.0, 0.0, 0.0)

    collection.insert(
        1,
        colors=(0.0, 1.0, 0.0, 1.0),
        translate=(5.0, 0.0, 0.0),
    )
    assert collection.count == 4
    assert tuple(collection.get("translate")) == (
        0.0, 0.0, 0.0,
        5.0, 0.0, 0.0,
        11.0, 0.0, 0.0,
        21.0, 0.0, 0.0,
    )

    collection.remove(2)
    assert collection.count == 3
    assert tuple(collection.get("translate")) == (
        0.0, 0.0, 0.0,
        5.0, 0.0, 0.0,
        21.0, 0.0, 0.0,
    )
    vlist.draw(GeometryMode.TRIANGLES)

    with pytest.raises(RuntimeError):
        vlist.create_instance(colors=(1.0, 1.0, 1.0, 1.0), translate=(0.0, 0.0, 0.0))

    collection.delete()
    assert vlist.instance_count == 0
    assert vlist.instance_bucket.stream.allocator.get_allocated_regions() == ([], [])


def test_get_instance_by_index_non_indexed(vlist_non_indexed_factory):
    """Ensure non-indexed lists maintain instance lookup after deletion."""
    vlist = vlist_non_indexed_factory(
        (
            0.0, 0.0, 0.0,
            1.0, 0.0, 0.0,
            0.0, 1.0, 0.0,
        ),
    )

    inst0 = vlist.create_instance(colors=(1, 0, 0, 1), translate=(0, 0, 0))
    inst1 = vlist.create_instance(colors=(0, 1, 0, 1), translate=(10, 0, 0))
    inst2 = vlist.create_instance(colors=(0, 0, 1, 1), translate=(20, 0, 0))

    assert vlist.instance_count == 3
    assert vlist.get_instance_by_index(0) is inst0
    assert vlist.get_instance_by_index(1) is inst1
    assert vlist.get_instance_by_index(2) is inst2
    assert vlist.get_instance_by_index(3) is None
    assert vlist.get_instance_index(inst0) == 0
    assert vlist.get_instance_index(inst1) == 1
    assert vlist.get_instance_index(inst2) == 2

    inst1.delete()

    # Deletion compacts slots by moving the last instance into the freed slot.
    assert vlist.instance_count == 2
    assert vlist.get_instance_by_index(1) is inst2
    assert vlist.get_instance_by_index(2) is None
    assert vlist.get_instance_index(inst1) is None
    assert vlist.get_instance_index(inst2) == 1


def test_get_instance_by_index_indexed(vlist_factory):
    """Ensure indexed lists maintain instance lookup after deletion."""
    vlist = vlist_factory((0.0,) * 12)

    inst0 = vlist.create_instance(colors=(1, 0, 0, 1), translate=(0, 0, 0))
    inst1 = vlist.create_instance(colors=(0, 1, 0, 1), translate=(10, 0, 0))
    inst2 = vlist.create_instance(colors=(0, 0, 1, 1), translate=(20, 0, 0))

    assert vlist.instance_count == 3
    assert vlist.get_instance_by_index(0) is inst0
    assert vlist.get_instance_by_index(1) is inst1
    assert vlist.get_instance_by_index(2) is inst2
    assert vlist.get_instance_by_index(3) is None
    assert vlist.get_instance_index(inst0) == 0
    assert vlist.get_instance_index(inst1) == 1
    assert vlist.get_instance_index(inst2) == 2

    inst1.delete()

    # Deletion compacts slots by moving the last instance into the freed slot.
    assert vlist.instance_count == 2
    assert vlist.get_instance_by_index(1) is inst2
    assert vlist.get_instance_by_index(2) is None
    assert vlist.get_instance_index(inst1) is None
    assert vlist.get_instance_index(inst2) == 1


def _assert_instance_order(vlist, expected) -> None:
    assert vlist.instance_count == len(expected)
    for index, instance in enumerate(expected):
        assert vlist.get_instance_by_index(index) is instance
        assert vlist.get_instance_index(instance) == index


def test_instance_reorder_helpers_non_indexed(vlist_non_indexed_factory):
    """Ensure non-indexed instance ordering helpers preserve requested order."""
    vlist = vlist_non_indexed_factory(
        (
            0.0, 0.0, 0.0,
            1.0, 0.0, 0.0,
            0.0, 1.0, 0.0,
        ),
    )

    inst_a = vlist.create_instance(colors=(1, 0, 0, 1), translate=(0, 0, 0))
    inst_b = vlist.create_instance(colors=(0, 1, 0, 1), translate=(10, 0, 0))
    inst_c = vlist.create_instance(colors=(0, 0, 1, 1), translate=(20, 0, 0))
    inst_d = vlist.create_instance(colors=(1, 1, 0, 1), translate=(30, 0, 0))

    _assert_instance_order(vlist, [inst_a, inst_b, inst_c, inst_d])

    vlist.swap_instances(inst_a, inst_d)
    _assert_instance_order(vlist, [inst_d, inst_b, inst_c, inst_a])

    vlist.move_instance_to_index(inst_a, 1)
    _assert_instance_order(vlist, [inst_d, inst_a, inst_b, inst_c])

    vlist.move_to_back([inst_c, inst_d])
    _assert_instance_order(vlist, [inst_c, inst_d, inst_a, inst_b])

    vlist.move_to_top([inst_c, inst_a])
    _assert_instance_order(vlist, [inst_d, inst_b, inst_c, inst_a])

    vlist.set_instance_order([inst_b, inst_a, inst_d, inst_c])
    _assert_instance_order(vlist, [inst_b, inst_a, inst_d, inst_c])

    with pytest.raises(IndexError):
        vlist.move_instance_to_index(inst_a, 8)

    with pytest.raises(ValueError):
        vlist.set_instance_order([inst_a, inst_b, inst_c])  # missing one instance


def test_instance_reorder_helpers_indexed(vlist_factory):
    """Ensure indexed instance ordering helpers preserve requested order."""
    vlist = vlist_factory((0.0,) * 12)

    inst_a = vlist.create_instance(colors=(1, 0, 0, 1), translate=(0, 0, 0))
    inst_b = vlist.create_instance(colors=(0, 1, 0, 1), translate=(10, 0, 0))
    inst_c = vlist.create_instance(colors=(0, 0, 1, 1), translate=(20, 0, 0))
    inst_d = vlist.create_instance(colors=(1, 1, 0, 1), translate=(30, 0, 0))

    _assert_instance_order(vlist, [inst_a, inst_b, inst_c, inst_d])

    vlist.swap_instances(inst_a, inst_d)
    _assert_instance_order(vlist, [inst_d, inst_b, inst_c, inst_a])

    vlist.move_instance_to_index(inst_a, 1)
    _assert_instance_order(vlist, [inst_d, inst_a, inst_b, inst_c])

    vlist.move_to_back([inst_c, inst_d])
    _assert_instance_order(vlist, [inst_c, inst_d, inst_a, inst_b])

    vlist.move_to_top([inst_c, inst_a])
    _assert_instance_order(vlist, [inst_d, inst_b, inst_c, inst_a])

    vlist.set_instance_order([inst_b, inst_a, inst_d, inst_c])
    _assert_instance_order(vlist, [inst_b, inst_a, inst_d, inst_c])


def test_batch_migrate_instanced_indexed_vertex_list(shader_program, vlist_factory):
    """Ensure batch migration preserves indexed geometry and instance data."""
    from pyglet.graphics import Batch, ShaderGroup

    source_batch = Batch()
    target_batch = Batch()
    source_group = ShaderGroup(program=shader_program)
    target_group = ShaderGroup(program=shader_program)
    source_vertices = (
        0.0, 0.0, 0.0,
        1.0, 0.0, 0.0,
        1.0, 1.0, 0.0,
        0.0, 1.0, 0.0,
    )
    source_indices = (0, 1, 2, 0, 2, 3)

    source = vlist_factory(source_vertices, source_indices, batch=source_batch, group=source_group)
    target = vlist_factory((1.0,) * 12, batch=target_batch, group=target_group)

    old_domain = source.domain
    old_bucket = source.instance_bucket

    inst0 = source.create_instance(colors=(1, 0, 0, 1), translate=(0, 0, 0))
    inst1 = source.create_instance(colors=(0, 1, 0, 1), translate=(5, 0, 0))

    source_batch.migrate(source, GeometryMode.TRIANGLES, target_group, target_batch)

    assert source.domain is target.domain
    assert source.group is target_group
    assert tuple(source.position[:]) == pytest.approx(source_vertices)
    assert tuple(source.indices) == source_indices
    assert source.instance_bucket is not old_bucket
    assert source.instance_bucket.instance_count == 2
    assert old_bucket.instance_count == 0
    assert old_bucket.stream.allocator.get_allocated_regions() == ([], [])
    assert source.instance_bucket.stream.allocator.get_allocated_regions() == ([0], [2])
    assert source.get_instance_by_index(0) is inst0
    assert source.get_instance_by_index(1) is inst1
    assert inst0.bucket is source.instance_bucket
    assert inst1.bucket is source.instance_bucket
    assert tuple(inst0.colors[:]) == pytest.approx((1, 0, 0, 1))
    assert tuple(inst0.translate[:]) == pytest.approx((0, 0, 0))
    assert tuple(inst1.colors[:]) == pytest.approx((0, 1, 0, 1))
    assert tuple(inst1.translate[:]) == pytest.approx((5, 0, 0))
    assert source.domain is not old_domain
    assert source.domain._instance_map[(source.index_start, source.index_count)] is source.instance_bucket
    source.draw(GeometryMode.TRIANGLES)


def test_instanced_indexed_vertex_list_delete_clears_instances(vlist_factory):
    """Ensure deleting an indexed list releases all of its instance storage."""
    vlist = vlist_factory((0.0,) * 12)

    inst0 = vlist.create_instance(colors=(1, 0, 0, 1), translate=(0, 0, 0))
    inst1 = vlist.create_instance(colors=(0, 1, 0, 1), translate=(10, 0, 0))

    assert vlist.instance_bucket.instance_count == 2
    assert vlist.instance_bucket.stream.allocator.get_allocated_regions() == ([0], [2])

    vlist.delete()

    assert vlist.instance_count == 0
    assert vlist.get_instance_by_index(0) is None
    assert vlist.get_instance_index(inst0) is None
    assert vlist.get_instance_index(inst1) is None
    assert inst0.slot == -1
    assert inst1.slot == -1
    assert vlist.instance_bucket.stream.allocator.get_allocated_regions() == ([], [])


def test_instanced_nonindexed_vertex_list_delete_releases_instance_range(vlist_non_indexed_factory):
    """Ensure deleting a non-indexed list releases its instance stream range."""
    vlist = vlist_non_indexed_factory((0.0,) * 9)
    vlist.create_instances(
        3,
        colors=(1.0, 1.0, 1.0, 1.0) * 3,
        translate=(0.0, 0.0, 0.0) * 3,
    )

    allocator = vlist.instance_bucket.stream.allocator
    assert allocator.get_allocated_regions() == ([0], [3])
    vlist.draw(GeometryMode.TRIANGLES)

    vlist.delete()

    assert allocator.get_allocated_regions() == ([], [])


def test_instanced_vertex_list_migrate_new_domain_and_group(shader_program, vlist_non_indexed_factory):
    """Ensure migration moves non-indexed geometry and instances to a new domain."""
    from pyglet.enums import GeometryMode
    from pyglet.graphics import Batch, ShaderGroup

    verts = (
        0.0, 0.0, 0.0,
        1.0, 0.0, 0.0,
        0.0, 1.0, 0.0,
    )
    source_batch = Batch()
    target_batch = Batch()
    source_group = ShaderGroup(program=shader_program, order=0)
    target_group = ShaderGroup(program=shader_program, order=1)

    source = vlist_non_indexed_factory(verts, batch=source_batch, group=source_group)
    target = vlist_non_indexed_factory(verts, batch=target_batch, group=target_group)

    old_domain = source.domain
    old_instance_bucket = source.instance_bucket
    instance = source.create_instance(colors=(1.0, 0.0, 0.0, 1.0), translate=(5.0, 0.0, 0.0))

    source_batch.migrate(source, GeometryMode.TRIANGLES, target_group, target_batch)

    assert source.domain is target.domain
    assert source.domain is not old_domain
    assert source.group is target_group
    assert source.bucket is source.domain.get_drawable_bucket(target_group)
    assert (source.start, source.count) in source.bucket.ranges
    assert old_domain.get_drawable_bucket(source_group) is None
    assert source.instance_bucket is not old_instance_bucket
    assert old_instance_bucket.stream.allocator.get_allocated_regions() == ([], [])
    assert source.instance_bucket.stream.allocator.get_allocated_regions() == ([0], [1])
    assert instance.bucket is source.instance_bucket
    assert source.domain._instance_map[(source.start, source.count)] is source.instance_bucket
    source.draw(GeometryMode.TRIANGLES)


def test_instanced_vertex_list_migrate_new_group_same_domain(shader_program, vlist_non_indexed_factory):
    """Ensure changing groups retains non-indexed instance storage in its domain."""
    from pyglet.enums import GeometryMode
    from pyglet.graphics import Batch, ShaderGroup

    verts = (
        0.0, 0.0, 0.0,
        1.0, 0.0, 0.0,
        0.0, 1.0, 0.0,
    )
    batch = Batch()
    source_group = ShaderGroup(program=shader_program, order=0)
    target_group = ShaderGroup(program=shader_program, order=1)

    vlist = vlist_non_indexed_factory(verts, batch=batch, group=source_group)
    old_domain = vlist.domain
    old_bucket = vlist.bucket

    batch.migrate(vlist, GeometryMode.TRIANGLES, target_group, batch)

    assert vlist.domain is old_domain
    assert vlist.bucket is not old_bucket
    assert vlist.group is target_group
    assert vlist.bucket is old_domain.get_drawable_bucket(target_group)
    assert (vlist.start, vlist.count) in vlist.bucket.ranges
    assert old_domain.get_drawable_bucket(source_group) is None


def test_missing_instance_attribute_raises(vlist_factory):
    """Test that ensures that an exception is raised if an instance attribute is missing."""
    verts = (0.0,) * 12
    vlist = vlist_factory(verts)
    with pytest.raises(KeyError):
        vlist.create_instance(colors=(1,1,1,1))  # missing translate


def _divisor_of(loc: int) -> int:
    from pyglet.graphics.api.gl import gl
    val = gl.GLint()
    gl.glGetVertexAttribiv(loc, gl.GL_VERTEX_ATTRIB_ARRAY_DIVISOR, ctypes.byref(val))
    return int(val.value)


def test_attribute_divisors(shader_program, vlist_factory):
    """Ensure the attribute divisor is set correctly in the VAO."""
    vlist = vlist_factory((0.0,) * 12)

    # Bind the VAO that vlist configured
    vlist.instance_bucket.vao.bind()

    pos_loc = shader_program._attributes["position"].location
    col_loc = shader_program._attributes["colors"].location
    trn_loc = shader_program._attributes["translate"].location

    assert _divisor_of(pos_loc) == 0
    assert _divisor_of(col_loc) == 1
    assert _divisor_of(trn_loc) == 1


def test_instance_deletion(shader_program, vlist_factory):
    """Ensure instance slots stay contiguous when one is deleted."""
    vlist = vlist_factory((0.0,) * 12)

    instances = []
    for i in range(10):
        instances.append(vlist.create_instance(colors=(1, 1, 1, 1), translate=(100 * i, 100, 0)))

    assert [inst.slot for inst in instances] == list(range(10))
    assert vlist.instance_bucket.stream.allocator.get_allocated_regions() == ([0], [10])

    last_instance = instances[-1]

    # Delete instance in center.
    test_instance = instances[5]
    assert test_instance.slot == 5
    test_instance.delete()

    # Previous instance should stay the same
    assert instances[4].slot == 4

    # Last instance should move to fill the spot.
    assert last_instance.slot == 5
    assert vlist.instance_bucket.stream.allocator.get_allocated_regions() == ([0], [9])
