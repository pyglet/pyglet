"""OpenGL 2 batch drawing support."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pyglet
from pyglet.graphics.api.gl.enums import geometry_map
from pyglet.graphics.api.gl.draw import _cached_multidraw
from pyglet.graphics.api.gl2.vertexdomain import (
    IndexedVertexDomain,
    InstancedIndexedVertexDomain,
    InstancedVertexDomain,
    VertexDomain,
)
from pyglet.graphics.draw import _BucketBatch

if TYPE_CHECKING:
    from collections.abc import Callable

    from pyglet.graphics.allocation import RangeAllocator
    from pyglet.graphics.api.gl import OpenGLSurfaceContext
    from pyglet.graphics.draw import DrawContext
    from pyglet.graphics.vertexdomain import VertexDomain as BaseVertexDomain


def get_default_batch() -> GL2Batch:
    """Batch used globally for objects that have no Batch specified."""
    return pyglet.graphics.api.core.get_default_batch()  # type: ignore[return-value]


_domain_class_map: dict[tuple[bool, bool], type[BaseVertexDomain]] = {
    # Indexed, Instanced : Domain
    (False, False): VertexDomain,
    (True, False): IndexedVertexDomain,
    # These placeholders always raise UnsupportedBackendError on construction.
    (False, True): InstancedVertexDomain,  # type: ignore[dict-item]
    (True, True): InstancedIndexedVertexDomain,  # type: ignore[dict-item]
}


class GL2Batch(_BucketBatch):
    """OpenGL 2 batch implementation."""

    _domain_class_map = _domain_class_map
    _geometry_map = geometry_map

    def __init__(self, context: OpenGLSurfaceContext | None = None, initial_count: int = 32) -> None:
        """Initialize the batch for use."""
        super().__init__(context, initial_count)

    @staticmethod
    def _draw_bucket_fn(domain: BaseVertexDomain, buckets: list[RangeAllocator],
                        mode_func: int) -> Callable[[DrawContext], None]:
        if type(domain) not in (VertexDomain, IndexedVertexDomain) or not domain._supports_multi_draw:
            return _BucketBatch._draw_bucket_fn(domain, buckets, mode_func)
        if isinstance(domain, IndexedVertexDomain):
            return _cached_multidraw(domain._context, buckets, mode_func, index_type=domain.index_stream.gl_type,
                                     element_size=domain.index_stream.index_element_size)
        return _cached_multidraw(domain._context, buckets, mode_func)  # type: ignore[arg-type]
