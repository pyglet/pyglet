"""OpenGL batch drawing support."""

from __future__ import annotations

import ctypes
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pyglet
from pyglet.graphics.api.gl import GLint, GLsizei, OpenGLSurfaceContext, vertexdomain
from pyglet.graphics.api.gl.enums import geometry_map
from pyglet.graphics.draw import _BucketBatch

if TYPE_CHECKING:
    from collections.abc import Callable

    from pyglet.graphics.allocation import RangeAllocator
    from pyglet.graphics.draw import DrawContext
    from pyglet.graphics.vertexdomain import VertexDomain
    from pyglet.graphics.vertexstorage import IndexStream


def get_default_batch() -> GLBatch:
    """Batch used globally for objects that have no Batch specified."""
    return pyglet.graphics.api.core.get_default_batch()


_domain_class_map: dict[tuple[bool, bool], type[vertexdomain.GLVertexDomain]] = {
    # Indexed, Instanced : Domain
    (False, False): vertexdomain.GLVertexDomain,
    (True, False): vertexdomain.GLIndexedVertexDomain,
    (False, True): vertexdomain.GLInstancedVertexDomain,
    (True, True): vertexdomain.GLInstancedIndexedVertexDomain,
}


@dataclass
class GLBackendDrawContext:
    """Temporary OpenGL draw data."""

    current_fbo: int | None = None


def _cached_multidraw(context: OpenGLSurfaceContext, buckets: list[RangeAllocator], mode: int,
                      index_stream: IndexStream | None = None) -> Callable[[DrawContext], None]:
    """Keep native draw arrays alive for one compiled GL or GL2 command."""
    element_size = index_stream.index_element_size if index_stream is not None else 1
    start_type = ctypes.c_void_p if index_stream is not None else GLint
    versions = None
    starts = sizes = None
    primcount = 0

    def _draw(_ctx: DrawContext) -> None:
        nonlocal versions, starts, sizes, primcount
        # Dirty flags can be consumed by other readers; versions survive merging.
        if versions is None or any(bucket._version != version for bucket, version in zip(buckets, versions)):
            regions = [region for bucket in buckets for region in bucket.merged_ranges]
            primcount = len(regions)
            starts = (start_type * primcount)(*[start * element_size for start, _ in regions])
            sizes = (GLsizei * primcount)(*[size for _, size in regions])
            versions = tuple(bucket._version for bucket in buckets)

        if index_stream is not None:
            context.glMultiDrawElements(mode, sizes, index_stream.gl_type, starts, primcount)
        else:
            context.glMultiDrawArrays(mode, starts, sizes, primcount)

    return _draw


class GLBatch(_BucketBatch):
    """OpenGL batch implementation."""

    _domain_class_map = _domain_class_map
    _geometry_map = geometry_map

    def __init__(self, context: OpenGLSurfaceContext | None = None, initial_count: int = 32) -> None:
        """Initialize the batch for use."""
        super().__init__(context, initial_count)

    def _create_backend_draw_context(self) -> GLBackendDrawContext:
        return GLBackendDrawContext()

    @staticmethod
    def _draw_bucket_fn(domain: VertexDomain, buckets: list[RangeAllocator], mode_func: int) -> Callable[[DrawContext], None]:
        # Instanced and custom domains retain their own drawing implementations.
        if (type(domain) not in (vertexdomain.GLVertexDomain, vertexdomain.GLIndexedVertexDomain)
                or not domain._supports_multi_draw):
            return _BucketBatch._draw_bucket_fn(domain, buckets, mode_func)

        index_stream = domain.index_stream if isinstance(domain, vertexdomain.GLIndexedVertexDomain) else None
        return _cached_multidraw(domain._context, buckets, mode_func, index_stream)
