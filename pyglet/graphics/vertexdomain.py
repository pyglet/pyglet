"""Manage related vertex attributes within a single vertex domain.

A vertex "domain" consists of a set of attribute descriptions that together
describe the layout of one or more vertex buffers which are used together to
specify the vertices in a primitive.  Additionally, the domain manages the
buffers used to store the data and will resize them as necessary to accommodate
new vertices.

Domains can optionally be indexed, in which case they also manage a buffer
containing vertex indices.  This buffer is grown separately and has no size
relation to the attribute buffers.

Applications can create vertices (and optionally, indices) within a domain
with the :py:meth:`VertexDomain.create` method.  This returns a
:py:class:`VertexListBase` representing the list of vertices created.  The vertex
attribute data within the group can be modified, and the changes will be made
to the underlying buffers automatically.

The entire domain can be efficiently drawn in one step with the
:py:meth:`VertexDomain.draw` method, assuming all the vertices comprise
primitives of the same OpenGL primitive mode.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Sequence, Protocol, Iterable, NoReturn

import pyglet
from pyglet.graphics import allocation
from pyglet.graphics.shader import Attribute, AttributeView, GraphicsAttribute, DataTypeTuple

if TYPE_CHECKING:
    from ctypes import Array
    from pyglet.customtypes import DataTypes
    from pyglet.graphics.api.base import SurfaceContext
    from pyglet.graphics.instance import InstanceBucket, VertexInstanceBase, BaseInstanceDomain
    from pyglet.graphics.buffer import AttributeBufferObject, IndexedBufferObject
    from pyglet.graphics import GeometryMode, Group


def _nearest_pow2(v: int) -> int:
    # From http://graphics.stanford.edu/~seander/bithacks.html#RoundUpPowerOf2
    # Credit: Sean Anderson
    v -= 1
    v |= v >> 1
    v |= v >> 2
    v |= v >> 4
    v |= v >> 8
    v |= v >> 16
    return v + 1


def _make_attribute_property(name: str) -> property:
    def _attribute_getter(self: VertexListBase) -> Array[float | int]:
        buffer = self.domain.attrib_name_buffers[name]
        region = buffer.get_attribute_region(name, self.start, self.count)
        buffer.invalidate_attribute_region(name, self.start, self.count)
        return region

    def _attribute_setter(self: VertexListBase, data: Any) -> None:
        buffer = self.domain.attrib_name_buffers[name]
        buffer.set_region(self.start, self.count, data)

    return property(_attribute_getter, _attribute_setter)


class VertexListBase:
    """A list of vertices within a :py:class:`VertexDomain`.

    Use :py:meth:`VertexDomain.create` to construct this list.
    """
    count: int
    start: int
    domain: VertexDomainBase
    indexed: bool = False
    instanced: bool = False
    initial_attribs: dict

    def __init__(self, domain: VertexDomainBase, group: Group, start: int, count: int) -> None:  # noqa: D107
        self.domain = domain
        self.group = group
        self.start = start
        self.count = count
        self.initial_attribs = domain.attribute_meta
        self.bucket = None

    def draw(self, mode: GeometryMode) -> None:
        """Draw this vertex list in the given OpenGL mode.

        Args:
            mode:
                OpenGL drawing mode, e.g. ``GL_POINTS``, ``GL_LINES``, etc.
        """
        self.domain.draw_subset(mode, self)

    def resize(self, count: int, index_count: int | None = None) -> None:  # noqa: ARG002
        """Resize this group.

        Args:
            count:
                New number of vertices in the list.
            index_count:
                Ignored for non indexed VertexDomains

        """
        new_start = self.domain.safe_realloc(self.start, self.count, count)
        if new_start != self.start:
            # Copy contents to new location
            for buffer in self.domain.attrib_name_buffers.values():
                old_data = buffer.get_region(self.start, self.count)
                buffer.set_region(new_start, self.count, old_data)
        self.start = new_start
        self.count = count

    def delete(self) -> None:
        """Delete this group."""
        self.domain.vertex_buffers.allocator.dealloc(self.start, self.count)
        self.domain.dealloc_from_group(self)

    def migrate(self, domain: VertexDomainBase, group: Group) -> None:
        """Move this group from its current domain and add to the specified one.

        Attributes on domains must match.
        (In practice, used to change parent state of some vertices).

        Args:
            domain:
                Domain to migrate this vertex list to.
            group:
                The group this vertex list belongs to.
        """
        assert list(domain.attribute_names.keys()) == list(self.domain.attribute_names.keys()), (
            'Domain attributes must match.'
        )

        new_start = domain.safe_alloc(self.count)
        # Copy data to new stream.
        self.domain.dealloc_from_group(self)
        self.domain.vertex_buffers.copy_data(new_start, domain.vertex_buffers, self.start, self.count)
        self.domain.vertex_buffers.allocator.dealloc(self.start, self.count)
        self.domain = domain
        self.start = new_start
        domain.alloc_to_group(self, group)
        assert self.bucket is not None

    def update_group(self, group: Group) -> None:
        current_bucket = self.bucket
        self.domain.dealloc_from_group(self)
        new_bucket = self.domain.alloc_to_group(self, group)
        assert new_bucket != current_bucket, "Changing group resulted in the same bucket."

    def set_attribute_data(self, name: str, data: Any) -> None:
        stream = self.domain.attrib_name_buffers[name]
        buffer = stream.attrib_name_buffers[name]

        array_start = buffer.element_count * self.start
        array_end = buffer.element_count * self.count + array_start
        try:
            buffer.data[array_start:array_end] = data
            buffer.invalidate_region(self.start, self.count)
        except ValueError:
            msg = f"Invalid data size for '{name}'. Expected {array_end - array_start}, got {len(data)}."
            raise ValueError(msg) from None


class InstanceVertexListBase(VertexListBase):
    """A list of vertices within an :py:class:`InstancedVertexDomain` that are not indexed."""
    domain: InstancedVertexDomainBase
    instanced: bool = True

    def __init__(self, domain: VertexDomainBase, group: Group, start: int, count: int, bucket: InstanceBucket) -> None:  # noqa: D107
        super().__init__(domain, group, start, count)
        self.instance_bucket = bucket
        self.instance_bucket.create_instance()

    def create_instance(self, **attributes: Any) -> VertexInstanceBase:
        return self.instance_bucket.create_instance(**attributes)

    def set_attribute_data(self, name: str, data: Any) -> None:
        if self.initial_attribs[name].fmt.is_instanced:
            stream = self.instance_bucket.stream
            count = 1
            start = 0
        else:
            stream = self.domain.attrib_name_buffers[name]
            count = self.count
            start = self.start
        buffer = stream.attrib_name_buffers[name]

        array_start = buffer.element_count * start
        array_end = buffer.element_count * count + array_start
        try:
            buffer.data[array_start:array_end] = data
            buffer.invalidate_region(start, count)
        except ValueError:
            msg = f"Invalid data size for '{buffer}'. Expected {array_end - array_start}, got {len(data)}."
            raise ValueError(msg) from None


class _IndexSupportBase:
    domain: IndexedVertexDomainBase | InstancedIndexedVertexDomainBase
    start: int
    count: int
    bucket: None

    def migrate(self, domain: IndexedVertexDomainBase | InstancedIndexedVertexDomainBase, group: Group):
        self.domain.dealloc_from_group(self)
        new_start = domain.safe_alloc(self.count)
        # Copy data to new stream.
        self.domain.vertex_buffers.copy_data(new_start, domain.vertex_buffers, self.start, self.count)
        self.domain.vertex_buffers.allocator.dealloc(self.start, self.count)
        self.domain = domain
        self.start = new_start

class _LocalIndexSupport(_IndexSupportBase):
    """When BaseVertex is supported by the version, this class will be mixed in.

    Will allow the class to use local index values instead of incrementing each mesh.
    """
    __slots__: tuple[str, ...] = ()

    supports_base_vertex: bool = True

    domain: IndexedVertexDomainBase | InstancedIndexedVertexDomainBase
    index_count: int
    index_start: int

    @property
    def indices(self) -> list[int]:
        return self.domain.index_stream.get_region(self.index_start, self.index_count)[:]

    @indices.setter
    def indices(self, local: Sequence[int]) -> None:  # type: ignore[override]
        self.domain.index_stream.set_region(self.index_start, self.index_count, local)

    def migrate(self, domain: IndexedVertexDomainBase | InstancedIndexedVertexDomainBase, group: Group) -> None:  # type: ignore[override]
        old_dom = self.domain
        src_idx_start = self.index_start
        src_idx_count = self.index_count

        super().migrate(domain, group)

        data = old_dom.index_stream.get_region(src_idx_start, src_idx_count)
        old_dom.index_stream.allocator.dealloc(src_idx_start, src_idx_count)

        new_idx_start = self.domain.safe_index_alloc(src_idx_count)
        self.domain.index_stream.set_region(new_idx_start, src_idx_count, data)
        self.index_start = new_idx_start
        domain.alloc_to_group(self, group)  # Allocate after new index start.


class _RunningIndexSupport(_IndexSupportBase):
    """Used to mixin an IndexedVertexListBase class.

    Keeps an incrementing count for indices in the buffer.
    """

    domain: IndexedVertexDomainBase | InstancedIndexedVertexDomainBase
    index_count: int
    index_start: int
    start: int

    supports_base_vertex: bool = False

    @property
    def indices(self) -> list[int]:
        stored = self.domain.index_stream.get_region(self.index_start, self.index_count)
        base = self.start
        return [i - base for i in stored]

    @indices.setter
    def indices(self, local: Sequence[int]) -> None:
        base: int = self.start
        stored: list[int] = [i + base for i in local]
        self.domain.index_stream.set_region(self.index_start, self.index_count, stored)

    def migrate(self, domain: IndexedVertexDomainBase | InstancedIndexedVertexDomainBase, group: Group) -> None:
        old_dom = self.domain
        old_start: int = self.start
        src_idx_start = self.index_start
        src_idx_count = self.index_count

        super().migrate(domain, group)

        data = old_dom.index_stream.get_region(src_idx_start, src_idx_count)
        old_dom.index_stream.allocator.dealloc(src_idx_start, src_idx_count)

        delta: int = self.start - old_start
        if delta:
            data = [i + delta for i in data]

        new_idx_start = self.domain.safe_index_alloc(src_idx_count)
        self.domain.index_stream.set_region(new_idx_start, src_idx_count, data)
        self.index_start = new_idx_start
        domain.alloc_to_group(self, group)  # Allocate after new index start.


class IndexedVertexListBase(VertexListBase):
    """A list of vertices within an :py:class:`IndexedVertexDomainBase` that are indexed.

    Use :py:meth:`IndexedVertexDomainBase.create` to construct this list.
    """
    domain: IndexedVertexDomainBase
    indexed: bool = True

    index_count: int
    index_start: int

    def __init__(self, domain: IndexedVertexDomainBase, group: Group, start: int, count: int, index_start: int,  # noqa: D107
                 index_count: int) -> None:
        super().__init__(domain, group, start, count)
        self.index_start = index_start
        self.index_count = index_count

    def delete(self) -> None:
        """Delete this group."""
        super().delete()
        self.domain.index_stream.dealloc(self.index_start, self.index_count)

    @property
    def indices(self) -> list[int]:
        """Array of index data."""
        return self.domain.index_stream.get_region(self.index_start, self.index_count)

    @indices.setter
    def indices(self, data: Sequence[int]) -> None:
        # The vertex data is offset in the buffer, so offset the index values to match. Ex:
        # vertex_buffer: [_, _, _, _, 1, 2, 3, 4]
        self.domain.index_stream.set_region(self.index_start, self.index_count, data)


class InstanceIndexedVertexListBase(VertexListBase):
    """A list of vertices within an :py:class:`IndexedVertexDomain` that are indexed.

    Use :py:meth:`IndexedVertexDomain.create` to construct this list.
    """
    domain: IndexedVertexDomainBase | InstancedIndexedVertexDomainBase
    indexed: bool = True
    instanced: bool = True

    index_count: int
    index_start: int

    instance_bucket: InstanceBucket
    supports_base_vertex: bool = False

    def __init__(self, domain: InstancedIndexedVertexDomainBase, group: Group, start: int, count: int,
                 index_start: int, index_count: int, index_type: DataTypes, base_vertex: int,
                 instance_bucket: InstanceBucket) -> None:
        self.index_start = index_start
        self.index_count = index_count
        self.index_type = index_type
        self.base_vertex = base_vertex
        self.instance_bucket = instance_bucket
        self.instance_bucket.create_instance()
        self.start_base_vertex = start if self.supports_base_vertex else 0
        super().__init__(domain, group, start, count)

    def delete(self) -> None:
        """Delete this group."""
        raise Exception
        super().delete()
        self.domain.index_allocator.dealloc(self.index_start, self.index_count)

    def migrate(self, domain: InstancedIndexedVertexDomainBase) -> None:
        old_domain = self.domain

        # Moved vertex data here.
        super().migrate(domain)

        # Remove from bucket and enter into new bucket.
        new_bucket = domain.instance_domain.get_elements_bucket(mode=0,
                                                    first_index=self.index_start,
                                                   index_count=self.index_count,
                                                   index_type="I")

        # Move instance data.
        old_domain.instance_domain.move_all(self.instance_bucket, new_bucket)

    def create_instance(self, **attributes: Any) -> None:
        return self.instance_bucket.create_instance(**attributes)

    def set_attribute_data(self, name: str, data: Any) -> None:
        if self.initial_attribs[name].fmt.is_instanced:
            stream = self.instance_bucket.stream
            count = 1
            start = 0
        else:
            stream = self.domain.attrib_name_buffers[name]
            count = self.count
            start = self.start
        buffer = stream.attrib_name_buffers[name]

        array_start = buffer.element_count * start
        array_end = buffer.element_count * count + array_start
        try:
            buffer.data[array_start:array_end] = data
            buffer.invalidate_region(start, count)
        except ValueError:
            msg = f"Invalid data size for '{buffer}'. Expected {array_end - array_start}, got {len(data)}."
            raise ValueError(msg) from None

    def dealloc_from_group(self, vertex_list):
        """Removes a vertex list from a specific state in this domain."""
        vertex_list.bucket.remove_vertex_list(vertex_list)

class VertexDomainBase(ABC):
    """Management of a set of vertex lists.

    Construction of a vertex domain is usually done with the
    :py:func:`create_domain` function.
    """

    attribute_meta: dict[str, Attribute]
    buffer_attributes: list[tuple[AttributeBufferObject, Attribute]]
    attribute_names: dict[str, Attribute]
    attrib_name_buffers: dict[str, VertexStream | InstanceStream]
    vertex_stream: VertexStream

    _property_dict: dict[str, property]
    _vertexlist_class: type

    _vertex_class: type[VertexListBase] = VertexListBase

    def __init__(self, context: SurfaceContext, initial_count: int, attribute_meta: dict[str, Attribute]) -> None:
        self._context = context or pyglet.graphics.api.core.current_context
        self.attribute_meta = attribute_meta
        self.attrib_name_buffers = {}
        self._supports_multi_draw = self._has_multi_draw_extension(self._context)

        # Separate attributes.
        self.per_vertex: list[Attribute] = []
        self.per_instance: list[Attribute] = []
        for attrib in attribute_meta.values():
            if not attrib.fmt.is_instanced:
                self.per_vertex.append(attrib)
            else:
                self.per_instance.append(attrib)

        self.vertex_buffers = None

        # This function should set vertex_buffers
        self._streams = self._create_streams(initial_count)
        self.vao = self._create_vao()
        self._vertex_buckets = {}

        for name, attrib in attribute_meta.items():
            if not attrib.fmt.is_instanced:
                self.attrib_name_buffers[name] = self.vertex_buffers

        # Make a custom VertexListBase class w/ properties for each attribute
        self._vertexlist_class = self._create_vertex_class()

    @abstractmethod
    def _has_multi_draw_extension(self, ctx: SurfaceContext) -> bool:
        raise NotImplementedError

    @abstractmethod
    def _create_streams(self, size: int) -> list[VertexStream | IndexStream | InstanceStream]:
        ...

    @abstractmethod
    def _create_vao(self) -> VertexArrayBinding:
        ...

    def bind_vao(self) -> None:
        """Binds the VAO as well as commit any pending buffer changes to the GPU."""
        self.vao.bind()
        for stream in self._streams:
            stream.commit()

    @property
    def attribute_names(self):
        return self.vertex_buffers.attribute_names

    def safe_alloc(self, count: int) -> int:
        """Allocate vertices, resizing the buffers if necessary."""
        return self.vertex_buffers.alloc(count)

    def safe_realloc(self, start: int, count: int, new_count: int) -> int:
        """Reallocate vertices, resizing the buffers if necessary."""
        return self.vertex_buffers.realloc(start, count, new_count)

    def create(self, group: Group, count: int, indices: Sequence[int] | None = None) -> VertexListBase:  # noqa: ARG002
        """Create a :py:class:`VertexListBase` in this domain.

        Args:
            group:
                The :py:class:`Group` the resulting vertex list will be drawn with.
            count:
                Number of vertices to create.
            indices:
                Ignored for non indexed VertexDomains
        """
        start = self.safe_alloc(count)
        vlist = self._vertexlist_class(self, group, start, count)
        self.alloc_to_group(vlist, group)
        return vlist

    def get_drawable_bucket(self, group: Group) -> VertexGroupBucket | None:
        """Get a bucket that exists and has vertices to draw (not empty)."""
        bucket = self._vertex_buckets.get(group)
        if bucket is None or (bucket and bucket.is_empty):
            return None

        return bucket

    def alloc_to_group(self, vertex_list, group) -> VertexGroupBucket:
        """Assigns a vertex list to a specific state in this domain.

        A state bucket does not allocate any vertices or allocates any GPU resources, it is simply to track the
        data required for drawing in a specific state.

        Args:
            vertex_list:
                The vertex list to allocate.
            group:
                The group affecting the vertices.

        Returns:
            The new state bucket object.
        """
        state_bucket = self._get_state_bucket(group)
        state_bucket.add_vertex_list(vertex_list)
        vertex_list.bucket = state_bucket
        return state_bucket

    def dealloc_from_group(self, vertex_list):
        """Removes a vertex list from a specific state in this domain."""
        assert vertex_list.bucket is not None
        vertex_list.bucket.remove_vertex_list(vertex_list)
        vertex_list.bucket = None

    def _get_state_bucket(self, group: Group) -> VertexGroupBucket:
        """Get a drawable bucket to assign vertex list information to a specific group."""
        bucket = self._vertex_buckets.get(group)
        if bucket is None:
            bucket = self._vertex_buckets[group] = VertexGroupBucket()
        return bucket

    def has_bucket(self, group: Group) -> bool:
        return group in self._vertex_buckets

    @abstractmethod
    def draw(self, mode: int) -> None:
        """Draw all vertices in the domain.

        All vertices in the domain are drawn at once. This is the
        most efficient way to render primitives.

        Args:
            mode:
                OpenGL drawing mode, e.g. ``GL_POINTS``, ``GL_LINES``, etc.

        """

    @abstractmethod
    def draw_subset(self, mode: GeometryMode, vertex_list: VertexListBase) -> None:
        """Draw a specific VertexListBase in the domain.

        The `vertex_list` parameter specifies a :py:class:`VertexListBase`
        to draw. Only primitives in that list will be drawn.

        Args:
            mode:
                OpenGL drawing mode, e.g. ``GL_POINTS``, ``GL_LINES``, etc.
            vertex_list:
                Vertex list to draw.

        """

    @property
    def is_empty(self) -> bool:
        """If the domain has no vertices."""
        return not self.vertex_buffers.allocator.starts

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}@{id(self):x} vertex_alloc={self.vertex_buffers.allocator}>'


class IndexedVertexDomainBase(VertexDomainBase):
    """Management of a set of indexed vertex lists.

    Construction of an indexed vertex domain is usually done with the
    :py:func:`create_domain` function.
    """
    _initial_index_count = 16
    _vertex_class = IndexedVertexListBase
    index_stream: IndexStream

    def __init__(self, context: SurfaceContext, initial_count: int, attribute_meta: dict[str, Attribute],
                 index_type: DataTypes = "I") -> None:
        self.index_type = index_type
        self._supports_base_vertex = context.get_info().have_extension("GL_ARB_draw_elements_base_vertex")
        super().__init__(context, initial_count, attribute_meta)

    def get_group_bucket(self, group: Group) -> IndexedVertexGroupBucket:
        """Get a drawable bucket to assign vertex list information to a specific group."""
        bucket = self._vertex_buckets.get(group)
        if bucket is None:
            bucket = self._vertex_buckets[group] = IndexedVertexGroupBucket()
        return bucket

    def safe_index_alloc(self, count: int) -> int:
        """Allocate indices, resizing the buffers if necessary."""
        return self.index_stream.alloc(count)

    def safe_index_realloc(self, start: int, count: int, new_count: int) -> int:
        """Reallocate indices, resizing the buffers if necessary."""
        return self.index_stream.realloc(start, count, new_count)

    def create(self, group: Group, count: int, indices: Sequence[int] | None = None) -> IndexedVertexListBase:
        """Create an :py:class:`IndexedVertexList` in this domain.

        Args:
            group:
                The :py:class:`Group` the resulting vertex list will be drawn with.
            count:
                Number of vertices to create
            indices:
                The indices used for this vertex list.

        """
        index_count = len(indices)
        start = self.safe_alloc(count)
        index_start = self.safe_index_alloc(index_count)
        vertex_list = self._vertexlist_class(self, group, start, count, index_start, index_count)
        vertex_list.indices = indices  # Move into class at some point?
        self.alloc_to_group(vertex_list, group)
        return vertex_list

    def _get_state_bucket(self, group: Group) -> IndexedVertexGroupBucket:
        """Get a drawable bucket to assign vertex list information to a specific group."""
        bucket = self._vertex_buckets.get(group)
        if bucket is None:
            bucket = self._vertex_buckets[group] = IndexedVertexGroupBucket()
        return bucket

    def draw(self, mode: int) -> None:
        """Draw all vertices in the domain.

        All vertices in the domain are drawn at once. This is the
        most efficient way to render primitives.

        Args:
            mode:
                OpenGL drawing mode, e.g. ``GL_POINTS``, ``GL_LINES``, etc.

        """

    def draw_subset(self, mode: GeometryMode, vertex_list: IndexedVertexListBase) -> None:
        """Draw a specific IndexedVertexListBase in the domain.

        The `vertex_list` parameter specifies a :py:class:`IndexedVertexListBase`
        to draw. Only primitives in that list will be drawn.

        Args:
            mode:
                OpenGL drawing mode, e.g. ``GL_POINTS``, ``GL_LINES``, etc.
            vertex_list:
                Vertex list to draw.
        """


class InstancedVertexDomainBase(VertexDomainBase):
    def __init__(self, context: SurfaceContext, initial_count: int, attribute_meta: dict[str, Attribute]) -> None:
        super().__init__(context, initial_count, attribute_meta)
        self.instance_domain = self.create_instance_domain(initial_count)
        self._instance_map = {}

    @abstractmethod
    def create_instance_domain(self, size: int) -> BaseInstanceDomain:
        ...

    def _create_vao(self) -> None:
        """Handled by buckets."""

    def bind_vao(self):
        self.vertex_buffers.commit()

    def alloc_to_group(self, vertex_list, group):
        super().alloc_to_group(vertex_list, group)
        key = (vertex_list.start, vertex_list.count)
        self._instance_map[key] = vertex_list.instance_bucket

    def create(self, group: Group, count: int, indices: Sequence[int] | None = None) -> VertexListBase:  # noqa: ARG002
        start = self.safe_alloc(count)
        bucket = self.instance_domain.get_arrays_bucket(mode=0, first_vertex=start, vertex_count=count)
        vlist = self._vertexlist_class(self, group, start, count, bucket)
        self.alloc_to_group(vlist, group)
        return vlist

class InstancedIndexedVertexDomainBase(IndexedVertexDomainBase):
    def __init__(self, context: SurfaceContext, initial_count: int, attribute_meta: dict[str, Attribute],
                 index_type: DataTypes = "I") -> None:
        super().__init__(context, initial_count, attribute_meta, index_type)
        self.instance_domain = self.create_instance_domain(initial_count)
        self._instance_map = {}

    @abstractmethod
    def create_instance_domain(self, size: int) -> BaseInstanceDomain:
        ...

    def _create_vao(self) -> None:
        """Handled by buckets."""

    def bind_vao(self):
        # VAO's are actually bound when instance buckets are drawn, but we can update the shared buffers atleast.
        self.vertex_buffers.commit()
        self.index_stream.commit()

    def alloc_to_group(self, vertex_list, group):
        super().alloc_to_group(vertex_list, group)
        key = (vertex_list.index_start, vertex_list.index_count)
        self._instance_map[key] = vertex_list.instance_bucket

    def create(self, group: Group, count: int, indices: Sequence[int] | None) -> InstanceIndexedVertexListBase:
        """Create an :py:class:`IndexedVertexList` in this domain.

        Args:
            group:
                The :py:class:`Group` the resulting vertex list will be drawn with.
            count:
                Number of vertices to create
            indices:
                Indices used for this vertex list.

        """
        index_count = len(indices)
        start = self.safe_alloc(count)
        index_start = self.safe_index_alloc(index_count)
        base_vertex = start if self._supports_base_vertex else 0
        bucket = self.instance_domain.get_elements_bucket(
            mode=0,  # Separate Mode from draw call into bucket at some point?
            first_index=index_start,
            index_count=index_count,
            index_type=self.index_type,
            base_vertex=base_vertex,
        )
        vertex_list = self._vertexlist_class(self, group, start, count, index_start, index_count, self.index_type, base_vertex, bucket)
        vertex_list.indices = indices
        self.alloc_to_group(vertex_list, group)
        return vertex_list

    def _create_vertex_class(self) -> type:
        mixin = _LocalIndexSupport if self._supports_base_vertex else _RunningIndexSupport
        # Make a custom VertexList class w/ properties for each attribute in the ShaderProgram:
        return type(self._vertex_class.__name__, (mixin, self._vertex_class),
                                      self.vertex_buffers._property_dict)  # noqa: SLF001

class BaseStream(ABC):
    """A container that handles a set of buffers to be used with domains."""
    def __init__(self, size: int) -> None:
        """Initialize the stream and create an allocator.

        Args:
            size: Initial allocator and buffer size.
        """
        self._capacity = size
        self.allocator = allocation.Allocator(size)
        self.buffers = []

    def commit(self) -> None:
        """Binds buffers and commits all pending data to the graphics API."""
        for buf in self.buffers:
            buf.commit()

    @abstractmethod
    def bind_into(self, vao) -> None:
        """Record this stream into the VAO.

        The VAO should be bound before this function is called.
        """

    def alloc(self, count: int) -> int:
        """Allocate a region of data, resizing the buffers if necessary."""
        try:
            return self.allocator.alloc(count)
        except allocation.AllocatorMemoryException as e:
            capacity = _nearest_pow2(e.requested_capacity)
            self.resize(capacity)
            return self.allocator.alloc(count)

    def resize(self, capacity: int) -> None:
        """Resize all buffers to the specified capacity.

        Size is passed as capacity * stride.
        """
        if capacity <= self.allocator.capacity:
            return
        self.allocator.set_capacity(capacity)
        for buf in self.buffers:
            buf.resize(capacity * buf.stride)

    def dealloc(self, start: int, count: int) -> None:
        self.allocator.dealloc(start, count)

    def realloc(self, start: int, count: int, new_count: int) -> int:
        """Reallocate a region of data, resizing the buffers if necessary."""
        try:
            return self.allocator.realloc(start, count, new_count)
        except allocation.AllocatorMemoryException as e:
            capacity = _nearest_pow2(e.requested_capacity)
            self.resize(capacity)
            return self.allocator.realloc(start, count, new_count)
    @abstractmethod
    def set_region(self, start: int, count: int, data) -> None: ...


class VertexStream(BaseStream):
    """A stream of buffers to be used with per-vertex attributes."""
    attrib_name_buffers: dict[str, AttributeBufferObject]
    attribute_meta: Sequence[Attribute]
    def __init__(self, ctx: SurfaceContext, initial_size: int, attrs: Sequence[Attribute], *, divisor: int = 0):
        super().__init__(initial_size)
        self._ctx = ctx
        self.attribute_names = {}  # name: attribute
        self.buffers = []
        self.attrib_name_buffers = {}  # dict of AttributeName: AttributeBufferObject (for VertexLists)

        self._property_dict = {}
        self.attribute_meta = attrs
        self._allocate_buffers()

    def get_buffer(self, size, attribute):
        raise NotImplementedError

    def get_graphics_attribute(self, attribute: Attribute, view: AttributeView) -> GraphicsAttribute:
        raise NotImplementedError

    def _create_separate_buffers(self, attributes: Sequence[Attribute]) -> None:
        """Takes the attributes and creates a separate buffer for each attribute."""
        for attribute in attributes:
            name = attribute.fmt.name

            stride = attribute.fmt.components * attribute.element_size
            view = AttributeView(offset=0, stride=stride)
            self.attribute_names[name] = attribute = self.get_graphics_attribute(attribute, view)

            self.attrib_name_buffers[name] = buffer = self.get_buffer(stride * self.allocator.capacity, attribute)

            self.buffers.append(buffer)

            # Create custom property to be used in the VertexListBase:
            self._property_dict[name] = _make_attribute_property(name)

    def _create_interleaved_buffers(self) -> NoReturn:
        """Creates a single buffer for all passed attributes."""
        raise NotImplementedError

    def _allocate_buffers(self) -> None:
        for attrib in self.attribute_meta:
            fmt_dt = attrib.fmt.data_type
            assert fmt_dt in DataTypeTuple, f"'{fmt_dt}' is not a valid attribute format for '{attrib.fmt.name}'."

        # Only support separate buffers per attrib currently.
        self._create_separate_buffers(self.attribute_meta)

    def set_region(self, start: int, count: int, data_by_attr: dict[str, Any]):
        for name, buf in self.attrib_name_buffers.items():
            buf.set_region(start, count, data_by_attr[name])

    def set_attribute_region(self, name: str, start: int, count: int, data: Any):
        buf = self.attrib_name_buffers[name]
        return buf.set_region(start, count)

    def get_attribute_region(self, name: str, start: int, count: int):
        buf = self.attrib_name_buffers[name]
        return buf.get_region(start, count)

    def invalidate_attribute_region(self, name: str, start: int, count: int):
        buf = self.attrib_name_buffers[name]
        buf.invalidate_region(start, count)

    def copy_data(
        self,
        dst_slot: int,
        dst_stream: VertexStream | InstanceStream,
        src_slot: int,
        count: int = 1,
        attrs: Iterable[str] | None = None,
        *,
        strict: bool = False,
    ) -> None:
        if attrs is None:
            dst_names = set(dst_stream.attrib_name_buffers.keys())
            src_names = set(self.attrib_name_buffers.keys())
            names = dst_names & src_names
            if strict and dst_names != src_names:
                err = (f"Attribute layout mismatch: missing in dst={sorted(src_names - dst_names)}, "
                       f"missing in src={sorted(dst_names - src_names)}")
                raise ValueError(err)
        else:
            names = [n for n in attrs if n in self.attrib_name_buffers and n in dst_stream.attrib_name_buffers]
            if strict and len(names) != len(list(attrs)):
                err = f"Requested attribute not present in both streams. {names}, {attrs}"
                raise ValueError(err)

        for name in names:
            dst_buf = dst_stream.attrib_name_buffers[name]
            src_buf = self.attrib_name_buffers[name]

            data = src_buf.get_region(src_slot, count)
            dst_buf.set_region(dst_slot, count, data)

    def __repr__(self):
        return f'{self.__class__.__name__}(attributes={list(self.attribute_meta)}, alloc={self.allocator})'

class InstanceStream(VertexStream):
    """Handles a stream of buffers to be used with the per-instance attributes."""

class IndexStream(BaseStream):
    """A container to manage an index buffer for a domain."""

    def __init__(self, ctx, data_type: DataTypes, initial_elems: int):
        super().__init__(initial_elems)
        self.ctx = ctx
        self.data_type = data_type
        self.buffer = self._create_buffer()
        self.buffers = [self.buffer]

    def _create_buffer(self) -> IndexedBufferObject:
        raise NotImplementedError

    def commit(self) -> None:
        self.buffer.commit()

    def get_region(self, start: int, count: int) -> Any:
        return self.buffer.get_region(start, count)

    def bind_into(self, vao) -> None:
        self.buffer.bind_to_index_buffer()

    def set_region(self, start: int, count: int, data) -> None:
        self.buffer.set_region(start, count, data)

    def copy_region(self, dst: int, src: int, count: int) -> None:
        self.buffer.copy_region(dst, src, count)


class VertexArrayProtocol(Protocol):
    def bind(self): ...
    def unbind(self): ...


class VertexArrayBinding:
    """A wrapper for a Vertex Array Object that binds streams.

    VAO's store which attribute layouts are used, as well as which buffer object each attribute pulls from.

    In the case of instanced drawing, each instance needs its own VAO as their per-instance data are separate buffers.
    """
    streams: list[VertexStream | InstanceStream | IndexStream]

    def __init__(self, ctx: SurfaceContext, streams: list[VertexStream | InstanceStream | IndexStream]):
        # attr_map: semantic/name -> location (from ShaderProgram inspection)
        self._ctx = ctx
        self.vao = self._create_vao()
        self.streams = streams
        self._link()

    def bind(self):
        raise NotImplementedError

    def _create_vao(self) -> VertexArrayProtocol: ...

    def _link(self):
        """Link the all streams to the VAO."""

    def __repr__(self):
        return f'<{self.__class__.__name__}@{id(self):x} vao={self.vao}, streams={self.streams}>'



class VertexGroupBucket(allocation.RangeAllocator):
    """A grouping of vertex lists belonging to a single group in a domain.

    Vertex lists are still owned by the domain, but this allows states to be rendered together if possible.
    """

    __slots__ = ("_merged", "_ranges", "is_dirty")

    def __init__(self) -> None:
        super().__init__()

    def add_vertex_list(self, vl: VertexListBase) -> None:
        self.add(vl.start, vl.count)

    def remove_vertex_list(self, vl: VertexListBase) -> None:
        self.remove(vl.start, vl.count)


class IndexedVertexGroupBucket(allocation.RangeAllocator):
    """A grouping of indexed vertex lists belonging to a single group in a domain.

    Vertex lists are still owned by the domain, but this allows states to be rendered together if possible.
    """
    __slots__ = ("_merged", "_ranges", "is_dirty")

    def add_vertex_list(self, vl: IndexedVertexListBase) -> None:
        self.add(vl.index_start, vl.index_count)

    def remove_vertex_list(self, vl: IndexedVertexListBase) -> None:
        self.remove(vl.index_start, vl.index_count)
