from __future__ import annotations

import random

import pytest
import ctypes

from tests.annotations import skip_graphics_api, GraphicsAPI


pytestmark = [skip_graphics_api(GraphicsAPI.GL2)]


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
def shader_program(gl3_context):
    """Compile and link the ShaderProgram once per module, and delete at the end."""
    from pyglet.graphics import ShaderProgram, Shader
    vertex = Shader(_vertex_source, "vertex")
    fragment = Shader(_fragment_source, "fragment")
    program = ShaderProgram(vertex, fragment)
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
            instance_attributes={"colors": 1, "translate": 1},
            batch=batch,
            group=group,
            position=("f", tuple(verts)),
            colors=("f", (1.0, 0.0, 0.0, 1.0)),
            translate=("f", (500.0, 500.0, 0.0)),
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
            instance_attributes={"colors": 1, "translate": 1},
            batch=batch,
            group=group,
            position=("f", tuple(verts)),
            colors=("f", (1.0, 0.0, 0.0, 1.0)),
            translate=("f", (500.0, 500.0, 0.0)),
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


def test_get_instance_by_index_non_indexed(vlist_non_indexed_factory):
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


def test_instanced_indexed_migrate_moves_instances(shader_program, vlist_factory):
    from pyglet.graphics import Batch, ShaderGroup

    source_batch = Batch()
    target_batch = Batch()
    source_group = ShaderGroup(program=shader_program)
    target_group = ShaderGroup(program=shader_program)

    source = vlist_factory((0.0,) * 12, batch=source_batch, group=source_group)
    target = vlist_factory((1.0,) * 12, batch=target_batch, group=target_group)

    old_domain = source.domain
    old_bucket = source.instance_bucket

    inst0 = source.create_instance(colors=(1, 0, 0, 1), translate=(0, 0, 0))
    inst1 = source.create_instance(colors=(0, 1, 0, 1), translate=(5, 0, 0))

    source.migrate(target.domain, target.group)

    assert source.domain is target.domain
    assert source.instance_bucket is not old_bucket
    assert source.instance_bucket.instance_count == 2
    assert old_bucket.instance_count == 0
    assert source.get_instance_by_index(0) is inst0
    assert source.get_instance_by_index(1) is inst1
    assert inst0.bucket is source.instance_bucket
    assert inst1.bucket is source.instance_bucket
    assert source.domain is not old_domain


def test_instanced_indexed_vertex_list_delete_clears_instances(vlist_factory):
    vlist = vlist_factory((0.0,) * 12)

    inst0 = vlist.create_instance(colors=(1, 0, 0, 1), translate=(0, 0, 0))
    inst1 = vlist.create_instance(colors=(0, 1, 0, 1), translate=(10, 0, 0))

    assert vlist.instance_bucket.instance_count == 2

    vlist.delete()

    assert vlist.instance_count == 0
    assert vlist.get_instance_by_index(0) is None
    assert vlist.get_instance_index(inst0) is None
    assert vlist.get_instance_index(inst1) is None
    assert inst0.slot == -1
    assert inst1.slot == -1


def test_instanced_vertex_list_migrate_new_domain_and_group(shader_program, vlist_non_indexed_factory):
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

    source_batch.migrate(source, GeometryMode.TRIANGLES, target_group, target_batch)

    assert source.domain is target.domain
    assert source.domain is not old_domain
    assert source.group is target_group
    assert source.bucket is source.domain.get_drawable_bucket(target_group)
    assert (source.start, source.count) in source.bucket.ranges
    assert old_domain.get_drawable_bucket(source_group) is None


def test_instanced_vertex_list_migrate_new_group_same_domain(shader_program, vlist_non_indexed_factory):
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

    last_instance = instances[-1]

    # Delete instance in center.
    test_instance = instances[5]
    assert test_instance.slot == 5
    test_instance.delete()

    # Previous instance should stay the same
    assert instances[4].slot == 4

    # Last instance should move to fill the spot.
    assert last_instance.slot == 5
