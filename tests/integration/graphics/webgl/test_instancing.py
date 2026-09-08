from __future__ import annotations

import pytest

import pyglet
from pyglet.enums import GeometryMode


VERTEX_SOURCE = """#version 300 es
in vec2 position;
in vec2 translation;
in vec4 colors;
out vec4 vertex_colors;
void main() {
    gl_Position = vec4(position + translation, 0.0, 1.0);
    vertex_colors = colors;
}
"""

FRAGMENT_SOURCE = """#version 300 es
precision mediump float;
in vec4 vertex_colors;
out vec4 final_color;
void main() {
    final_color = vertex_colors;
}
"""


def _create_program():
    vertex_shader = pyglet.graphics.Shader(VERTEX_SOURCE, "vertex")
    fragment_shader = pyglet.graphics.Shader(FRAGMENT_SOURCE, "fragment")
    program = pyglet.graphics.ShaderProgram(vertex_shader, fragment_shader)
    program.set_instance_attributes(translation=1, colors=1)
    return program, vertex_shader, fragment_shader


def test_instance_collection(webgl_window):
    """Ensure an indexed instance collection renders and releases its storage."""
    program, vertex_shader, fragment_shader = _create_program()
    vertex_list = program.vertex_list_instanced_indexed(
        4,
        mode=GeometryMode.TRIANGLES,
        indices=(0, 1, 2, 0, 2, 3),
        position=(-0.1, -0.1, 0.1, -0.1, 0.1, 0.1, -0.1, 0.1),
        translation=(0.0, 0.0),
        colors=(1.0, 1.0, 1.0, 1.0),
    )

    collection = vertex_list.create_instance_collection(
        3,
        capacity=8,
        translation=(-0.5, 0.0, 0.0, 0.0, 0.5, 0.0),
        colors=(1.0, 0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0),
    )
    allocator = vertex_list.instance_bucket.stream.allocator

    try:
        assert collection.count == vertex_list.instance_count == 3
        assert collection.capacity == 8

        collection.set_count(2)
        assert vertex_list.instance_count == 2
        collection.set(translation=(-0.25, 0.0, 0.25, 0.0))

        webgl_window.clear()
        vertex_list.draw(GeometryMode.TRIANGLES)
    finally:
        vertex_list.delete()
        program.delete()
        vertex_shader.delete()
        fragment_shader.delete()

    with pytest.raises(RuntimeError):
        collection.set_count(1)
    assert allocator.get_allocated_regions() == ([], [])


def test_create_instances(webgl_window):
    """Ensure bulk-created WebGL instances upload data and render."""
    program, vertex_shader, fragment_shader = _create_program()
    vertex_list = program.vertex_list_instanced(
        3,
        mode=GeometryMode.TRIANGLES,
        position=(-0.1, -0.1, 0.1, -0.1, 0.0, 0.1),
        translation=(0.0, 0.0),
        colors=(1.0, 1.0, 1.0, 1.0),
    )

    try:
        instances = vertex_list.create_instances(
            2,
            translation=(-0.25, 0.0, 0.25, 0.0),
            colors=(1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0),
        )

        assert vertex_list.instance_count == 2
        assert tuple(instances[0].translation[:]) == pytest.approx((-0.25, 0.0))
        assert tuple(instances[1].colors[:]) == pytest.approx((0.0, 0.0, 1.0, 1.0))

        webgl_window.clear()
        vertex_list.draw(GeometryMode.TRIANGLES)
    finally:
        vertex_list.delete()
        program.delete()
        vertex_shader.delete()
        fragment_shader.delete()


def test_nonindexed_instance_collection_migration(webgl_window):
    """Ensure migrating a collection updates its WebGL instance bucket."""
    program, vertex_shader, fragment_shader = _create_program()
    source_batch = pyglet.graphics.Batch()
    target_batch = pyglet.graphics.Batch()
    source_group = pyglet.graphics.ShaderGroup(program)
    target_group = pyglet.graphics.ShaderGroup(program)
    positions = (-0.1, -0.1, 0.1, -0.1, 0.0, 0.1)

    source = program.vertex_list_instanced(
        3,
        mode=GeometryMode.TRIANGLES,
        batch=source_batch,
        group=source_group,
        position=positions,
        translation=(0.0, 0.0),
        colors=(1.0, 1.0, 1.0, 1.0),
    )
    target = program.vertex_list_instanced(
        3,
        mode=GeometryMode.TRIANGLES,
        batch=target_batch,
        group=target_group,
        position=positions,
        translation=(0.0, 0.0),
        colors=(1.0, 1.0, 1.0, 1.0),
    )
    collection = source.create_instance_collection(
        2,
        capacity=4,
        translation=(-0.25, 0.0, 0.25, 0.0),
        colors=(1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0),
    )
    old_domain = source.domain
    old_instance_bucket = source.instance_bucket

    try:
        source_batch.migrate(source, GeometryMode.TRIANGLES, target_group, target_batch)

        assert source.domain is target.domain
        assert source.instance_bucket is not old_instance_bucket
        assert old_instance_bucket.stream.allocator.get_allocated_regions() == ([], [])
        assert source.instance_bucket.stream.allocator.get_allocated_regions() == ([0], [4])
        assert collection.bucket is source.instance_bucket
        assert source.domain._instance_map[(source.start, source.count)] is source.instance_bucket
        assert old_domain is not source.domain

        webgl_window.clear()
        source.draw(GeometryMode.TRIANGLES)
    finally:
        source.delete()
        target.delete()
        program.delete()
        vertex_shader.delete()
        fragment_shader.delete()
