from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

import pytest

import pyglet
from pyglet.enums import GeometryMode
from pyglet.graphics.vertexdomain import IndexedVertexGroupBucket, IndexedVertexList
from tests.annotations import GraphicsAPIGroups, skip_graphics_api

if TYPE_CHECKING:
    from pyglet.window import Window


@pytest.fixture(params=[False, pytest.param(True, marks=skip_graphics_api(GraphicsAPIGroups.GL2))])
def indexed_vertex_list(test_window: Window, request: pytest.FixtureRequest) -> Iterator[IndexedVertexList]:
    test_window.switch_to()
    program = pyglet.graphics.api.get_default_shader()
    instanced = request.param
    if instanced:
        program = program.get_vertex_view(pyglet.graphics.VertexLayout(colors="4f/1"))
    create = program.vertex_list_instanced_indexed if instanced else program.vertex_list_indexed
    vertex_list = create(
        3, mode=GeometryMode.TRIANGLES, indices=(0, 1, 2), batch=pyglet.graphics.Batch(),
        position=(0.0, 0.0, 0.0) * 3,
        colors=(1.0, 1.0, 1.0, 1.0) if instanced else (1.0, 1.0, 1.0, 1.0) * 3,
    )
    yield vertex_list
    if not vertex_list.domain.is_empty:
        vertex_list.delete()


def test_indexed_creation_without_indices(indexed_vertex_list: IndexedVertexList) -> None:
    vertex_list = indexed_vertex_list.domain.create(None, 3)
    try:
        assert vertex_list.count == 3
        assert vertex_list.index_count == 0
        assert vertex_list.indices == []
        assert vertex_list.group is None
    finally:
        vertex_list.delete()


def test_indexed_deletion_releases_vertex_and_index_storage(indexed_vertex_list: IndexedVertexList) -> None:
    domain = indexed_vertex_list.domain
    assert domain.allocator.get_allocated_regions() == ([0], [3])
    assert domain.index_allocator.get_allocated_regions() == ([0], [3])

    indexed_vertex_list.delete()

    assert domain.allocator.get_allocated_regions() == ([], [])
    assert domain.index_allocator.get_allocated_regions() == ([], [])
    if indexed_vertex_list.instanced:
        assert domain._instance_map == {}


def test_indexed_bucket_tracks_index_ranges(indexed_vertex_list: IndexedVertexList) -> None:
    bucket = indexed_vertex_list.bucket
    assert isinstance(bucket, IndexedVertexGroupBucket)
    assert bucket.ranges == [(indexed_vertex_list.index_start, indexed_vertex_list.index_count)]

    indexed_vertex_list.delete()

    assert bucket.is_empty
