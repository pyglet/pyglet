"""WebGL batch drawing support."""

from __future__ import annotations

from typing import TYPE_CHECKING

from js import Int32Array  # noqa: F821
from pyodide.ffi import to_js  # noqa: F821

import pyglet
from pyglet.graphics.api.webgl import vertexdomain
from pyglet.graphics.api.webgl.enums import geometry_map
from pyglet.graphics.draw import _BucketBatch

if TYPE_CHECKING:
    from pyglet.graphics.api.webgl.context import WebGL2SurfaceContext


def get_default_batch() -> WebGLBatch:
    """Batch used globally for objects that have no Batch specified."""
    return pyglet.graphics.api.core.get_default_batch()


_domain_class_map: dict[tuple[bool, bool], type[vertexdomain.WebGLVertexDomain]] = {
    # Indexed, Instanced : Domain
    (False, False): vertexdomain.WebGLVertexDomain,
    (True, False): vertexdomain.WebGLIndexedVertexDomain,
    (False, True): vertexdomain.WebGLInstancedVertexDomain,
    (True, True): vertexdomain.WebGLInstancedIndexedVertexDomain,
}


class WebGLBatch(_BucketBatch):
    """WebGL batch implementation."""

    _domain_class_map = _domain_class_map
    _geometry_map = geometry_map

    def __init__(self, context: WebGL2SurfaceContext | None = None, initial_count: int = 32) -> None:
        """Initialize the batch for use."""
        super().__init__(context, initial_count)

    @staticmethod
    def _draw_bucket_fn(domain, buckets, mode_func):
        if (type(domain) not in (vertexdomain.WebGLVertexDomain, vertexdomain.WebGLIndexedVertexDomain)
                or not domain._supports_multi_draw):
            return _BucketBatch._draw_bucket_fn(domain, buckets, mode_func)

        index_stream = domain.index_stream if isinstance(domain, vertexdomain.WebGLIndexedVertexDomain) else None
        element_size = index_stream.index_element_size if index_stream is not None else 1
        versions = None
        starts = sizes = None
        primcount = 0

        def _draw(_ctx):
            nonlocal versions, starts, sizes, primcount
            if versions is None or any(bucket._version != version for bucket, version in zip(buckets, versions)):
                regions = [region for bucket in buckets for region in bucket.merged_ranges]
                primcount = len(regions)
                starts = Int32Array.new(to_js([start * element_size for start, _ in regions]))
                sizes = Int32Array.new(to_js([size for _, size in regions]))
                versions = tuple(bucket._version for bucket in buckets)

            if index_stream is not None:
                domain._multi_draw_elements(mode_func, sizes, 0, index_stream.gl_type, starts, 0, primcount)
            else:
                domain._multi_draw_array(mode_func, starts, 0, sizes, 0, primcount)

        return _draw
