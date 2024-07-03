"""Concept for higher level instance generation and organization."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, Sequence

if TYPE_CHECKING:
    from pyglet.graphics import Batch
    from pyglet.graphics.vertexdomain import VertexInstance, VertexList


class VertexListObject(Protocol):
    batch: Batch
    _vertex_list: VertexList


class InstanceSourceMixin:
    _vertex_list: VertexList

    def __init__(self, attributes: Sequence[str]) -> None:
        self._attributes = tuple(attributes)
        self._instances = []

    @property
    def instances(self) -> list[VertexInstance]:
        return self._instances

    def create_instance(self, **kwargs: Any) -> VertexInstance:
        instance = self._vertex_list.add_instance(**kwargs)
        self._instances.append(instance)
        return instance

    def pop(self) -> VertexInstance:
        instance = self._instances.pop()
        instance.delete()
        return instance


class InstanceGenerator:
    _attributes: tuple[str, ...]

    def __init__(self, source: VertexListObject, attributes: Sequence[str]) -> None:
        self.source = source
        self._attributes = tuple(attributes)
        self._instances = []

        if self.source._vertex_list is None:
            raise Exception("No vertex list")

        if self.source.batch is None:
            raise Exception("No batch")

        self.migrate()

    @property
    def instance_attributes(self) -> tuple[str, ...]:
        return self._attributes

    def migrate(self) -> None:
        vlist = self.source._vertex_list
        batch = self.source.batch

        instanced_domain = batch._convert_to_instanced(vlist.domain, self._attributes)
        vlist.set_instance_source(instanced_domain, self._attributes)

    @property
    def instances(self) -> list[VertexInstance]:
        return self._instances

    def create(self, **kwargs: Any) -> VertexInstance:
        instance = self.source._vertex_list.add_instance(**kwargs)
        self._instances.append(instance)
        return instance

    def pop(self) -> VertexInstance:
        instance = self._instances.pop()
        instance.delete()
        return instance
