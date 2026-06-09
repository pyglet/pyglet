"""WebGL batch drawing support."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pyglet
from pyglet.graphics.api.webgl import vertexdomain
from pyglet.graphics.api.webgl.enums import geometry_map
from pyglet.graphics.draw import _BucketBatch

if TYPE_CHECKING:
    from pyglet.graphics.api.webgl.context import OpenGLSurfaceContext


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

    def __init__(self, context: OpenGLSurfaceContext | None = None, initial_count: int = 32) -> None:
        """Initialize the batch for use."""
        super().__init__(context, initial_count)
