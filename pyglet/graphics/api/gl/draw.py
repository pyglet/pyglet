"""OpenGL batch drawing support."""

from __future__ import annotations

from dataclasses import dataclass

import pyglet
from pyglet.graphics.api.gl import OpenGLSurfaceContext, vertexdomain
from pyglet.graphics.api.gl.enums import geometry_map
from pyglet.graphics.draw import _BucketBatch


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


class GLBatch(_BucketBatch):
    """OpenGL batch implementation."""

    _domain_class_map = _domain_class_map
    _geometry_map = geometry_map

    def __init__(self, context: OpenGLSurfaceContext | None = None, initial_count: int = 32) -> None:
        """Initialize the batch for use."""
        super().__init__(context, initial_count)

    def _create_backend_draw_context(self) -> GLBackendDrawContext:
        return GLBackendDrawContext()
