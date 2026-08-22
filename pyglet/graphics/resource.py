"""Backend-independent identities for graphics resources."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from itertools import count
from typing import Any, ClassVar, Generic, TypeVar


@dataclass(frozen=True, slots=True)
class ResourceKey:
    """Stable, hashable identity for one logical pyglet graphics resource."""

    value: int


@dataclass(frozen=True, slots=True)
class BufferKey(ResourceKey):
    """Identity for a buffer resource."""


@dataclass(frozen=True, slots=True)
class TextureKey(ResourceKey):
    """Identity for a texture resource."""


@dataclass(frozen=True, slots=True)
class ShaderKey(ResourceKey):
    """Identity for a shader resource."""


@dataclass(frozen=True, slots=True)
class ShaderProgramKey(ResourceKey):
    """Identity for a shader-program resource."""


@dataclass(frozen=True, slots=True)
class FramebufferKey(ResourceKey):
    """Identity for a framebuffer resource."""


@dataclass(frozen=True, slots=True)
class RenderbufferKey(ResourceKey):
    """Identity for a renderbuffer resource."""


@dataclass(frozen=True, slots=True)
class VertexArrayKey(ResourceKey):
    """Identity for a vertex-array resource."""


HandleT = TypeVar("HandleT")
KeyT = TypeVar("KeyT", bound=ResourceKey)


class GraphicsResource(ABC, Generic[HandleT, KeyT]):
    """A graphics resource with separate backend and pyglet identities."""

    key_type: ClassVar[type[ResourceKey]]
    _key_counters: ClassVar[dict[type[ResourceKey], count[int]]] = {}
    _handle: HandleT | None
    _key: KeyT

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

    def __init__(self, *, key: KeyT | None = None) -> None:
        """Create a resource identity."""
        try:
            existing_key = object.__getattribute__(self, "_key")
        except AttributeError:
            key_type = self.key_type
            counter = self._key_counters.setdefault(key_type, count(1))
            self._key = key if key is not None else key_type(next(counter))
        else:
            if key is not None and key != existing_key:
                raise ValueError("A graphics resource key cannot be replaced.")

        try:
            object.__getattribute__(self, "_handle")
        except AttributeError:
            self._handle = None

    @property
    def handle(self) -> HandleT | None:
        """Opaque handle used to operate on the backend resource."""
        return self._handle

    @property
    def key(self) -> KeyT:
        """Stable, hashable identity used by pyglet."""
        return self._key

    @property
    def id(self) -> HandleT | None:
        """Read-only compatibility alias for :attr:`handle`.

        .. deprecated:: 3.0
           Use :attr:`handle` instead.
        """
        return self._handle

    @abstractmethod
    def delete(self) -> None:
        """Release the backend resource."""


class FramebufferResource(GraphicsResource[Any, FramebufferKey], ABC):
    """Base class for framebuffer resources."""

    key_type = FramebufferKey


class RenderbufferResource(GraphicsResource[Any, RenderbufferKey], ABC):
    """Base class for renderbuffer resources."""

    key_type = RenderbufferKey


class VertexArrayResource(GraphicsResource[Any, VertexArrayKey], ABC):
    """Base class for vertex-array resources."""

    key_type = VertexArrayKey
