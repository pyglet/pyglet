from types import SimpleNamespace

from js import Object  # noqa: F821
import pyglet
import pytest

from pyglet.graphics.allocation import RangeAllocator
from pyglet.graphics.api.webgl.draw import WebGLBatch
from pyglet.graphics.api.webgl.gl import GL_TRIANGLES, GL_UNSIGNED_SHORT
from pyglet.graphics.api.webgl.vertexdomain import WebGLIndexedVertexDomain, WebGLVertexDomain


@pytest.mark.parametrize("indexed", [False, True])
def test_webgl_multidraw_caches_native_arrays_and_invalidates_after_merging(indexed):
    calls = []
    domain = object.__new__(WebGLIndexedVertexDomain if indexed else WebGLVertexDomain)
    domain._supports_multi_draw = True
    if indexed:
        domain.index_stream = SimpleNamespace(index_element_size=2, gl_type=GL_UNSIGNED_SHORT)
        domain._multi_draw_elements = lambda mode, sizes, sizes_offset, gl_type, starts, starts_offset, count: calls.append(
            (starts, sizes, count))
    else:
        domain._multi_draw_array = lambda mode, starts, starts_offset, sizes, sizes_offset, count: calls.append(
            (starts, sizes, count))
    first, second = RangeAllocator(), RangeAllocator()
    first.add(0, 3)
    second.add(6, 3)
    draw = WebGLBatch._draw_bucket_fn(domain, [first, second], GL_TRIANGLES)
    draw(None)
    starts, sizes, count = calls[-1]
    assert starts.constructor.name == sizes.constructor.name == "Int32Array"
    assert list(starts.to_py()) == [0, 12 if indexed else 6]
    assert list(sizes.to_py()) == [3, 3]
    draw(None)
    assert getattr(Object, "is")(calls[-1][0], starts)
    assert getattr(Object, "is")(calls[-1][1], sizes)

    first.add(3, 3)
    assert first.merged_ranges == [(0, 6)]
    draw(None)
    assert list(calls[-1][1].to_py()) == [6, 3]
    first.clear()
    second.clear()
    draw(None)
    assert calls[-1][2] == 0
    assert calls[-1][0].length == 0


@pytest.mark.parametrize("indexed", [False, True])
def test_webgl_without_multidraw_uses_existing_draw_path(indexed):
    domain = object.__new__(WebGLIndexedVertexDomain if indexed else WebGLVertexDomain)
    domain._supports_multi_draw = False
    calls = []
    domain.draw_buckets = lambda mode, buckets: calls.append((mode, buckets))
    buckets = [RangeAllocator()]
    WebGLBatch._draw_bucket_fn(domain, buckets, GL_TRIANGLES)(None)
    assert calls == [(GL_TRIANGLES, buckets)]


def test_webgl_multidraw_extension_receives_reused_native_arrays(webgl_window):
    if webgl_window.context.gl.getExtension("WEBGL_multi_draw") is None:
        pytest.skip("WEBGL_multi_draw is unavailable")

    batch = pyglet.graphics.Batch()
    image = pyglet.image.SolidColorImagePattern().create_image(4, 4)
    first = pyglet.sprite.Sprite(image, batch=batch)
    second = pyglet.sprite.Sprite(image, x=10, batch=batch)
    domain = first._vertex_list.domain
    original = domain._multi_draw_elements
    calls = []

    def record(mode, sizes, sizes_offset, index_type, starts, starts_offset, count):
        calls.append((starts, sizes))
        original(mode, sizes, sizes_offset, index_type, starts, starts_offset, count)

    domain._multi_draw_elements = record
    try:
        batch.draw()
        batch.draw()
        assert len(calls) == 2
        assert getattr(Object, "is")(calls[0][0], calls[1][0])
        assert getattr(Object, "is")(calls[0][1], calls[1][1])
        second.delete()
        second = None
        batch.draw()
        assert not getattr(Object, "is")(calls[-1][0], calls[-2][0])
        assert list(calls[-1][1].to_py()) == [6]
    finally:
        domain._multi_draw_elements = original
        first.delete()
        if second is not None:
            second.delete()
