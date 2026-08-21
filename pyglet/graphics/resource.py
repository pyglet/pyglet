"""Backend-independent identities for graphics resources."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from itertools import count
from typing import Any, ClassVar, Generic, TypeVar, cast


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


HandleT = TypeVar("HandleT")
KeyT = TypeVar("KeyT", bound=ResourceKey)


class GraphicsResource(ABC, Generic[HandleT, KeyT]):
    """A graphics resource with separate backend and pyglet identities."""

    key_type: ClassVar[type[ResourceKey]]
    _key_counter: ClassVar[count[int]]
    _handle: HandleT | None
    _key: KeyT

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # The class that declares a key type owns its allocator. Backend-specific
        # subclasses inherit that allocator, keeping keys unique across them.
        if "key_type" in cls.__dict__:
            cls._key_counter = count(1)

    def __init__(self, *, key: KeyT | None = None) -> None:
        """Create a resource identity."""
        if hasattr(self, "_key"):
            if key is not None and key != self._key:
                raise ValueError("A graphics resource key cannot be replaced.")
        else:
            self._key = key if key is not None else cast("KeyT", self.key_type(next(self._key_counter)))

        if not hasattr(self, "_handle"):
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
        return self.handle

    @abstractmethod
    def delete(self) -> None:
        """Release the backend resource."""
