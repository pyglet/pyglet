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
:py:class:`VertexList` representing the list of vertices created.  The vertex
attribute data within the group can be modified, and the changes will be made
to the underlying buffers automatically.

The entire domain can be efficiently drawn in one step with the
:py:meth:`VertexDomain.draw` method, assuming all the vertices comprise
primitives of the same OpenGL primitive mode.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Sequence, Protocol, Iterable, NoReturn

from pyglet.graphics import allocation
from pyglet.graphics.shader import Attribute, AttributeView, GraphicsAttribute, DataTypeTuple

if TYPE_CHECKING:
    from ctypes import Array
    from pyglet.customtypes import CType, DataTypes
    from pyglet.graphics.api.base import SurfaceContext
    from pyglet.graphics.instance import InstanceBucket, VertexInstanceBase
    from pyglet.graphics.buffer import AttributeBufferObject, IndexedBufferObject
    from pyglet.graphics import GeometryMode
    from pyglet.graphics.allocation import Allocator


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
    def _attribute_getter(self: VertexList) -> Array[float | int]:
        buffer = self.domain.attrib_name_buffers[name]
        region = buffer.get_attribute_region(name, self.start, self.count)
        buffer.invalidate_attribute_region(name, self.start, self.count)
        return region

    def _attribute_setter(self: VertexList, data: Any) -> None:
        buffer = self.domain.attrib_name_buffers[name]
        buffer.set_region(self.start, self.count, data)

    return property(_attribute_getter, _attribute_setter)


class VertexList:
    """A list of vertices within a :py:class:`VertexDomain`.

    Use :py:meth:`VertexDomain.create` to construct this list.
    """
    count: int
    start: int
    domain: VertexDomain
    indexed: bool = False
    instanced: bool = False
    initial_attribs: dict

    def __init__(self, domain: VertexDomain, start: int, count: int) -> None:  # noqa: D107
        self.domain = domain
        self.start = start
        self.count = count
        self.initial_attribs = domain.attribute_meta

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
        self.domain.allocator.dealloc(self.start, self.count)

    def migrate(self, domain: VertexDomain) -> None:
        """Move this group from its current domain and add to the specified one.

        Attributes on domains must match.
        (In practice, used to change parent state of some vertices).

        Args:
            domain:
                Domain to migrate this vertex list to.

        """
        assert list(domain.attribute_names.keys()) == list(self.domain.attribute_names.keys()), \
            'Domain attributes must match.'

        new_start = domain.safe_alloc(self.count)
        for name, old_buffer in self.domain.attrib_name_buffers.items():
            new_buffer = domain.attrib_name_buffers[name]
            old_data = old_buffer.get_region(self.start, self.count)
            new_buffer.set_region(new_start, self.count, old_data)

        self.domain.allocator.dealloc(self.start, self.count)
        self.domain = domain
        self.start = new_start

    def set_attribute_data(self, name: str, data: Any) -> None:
        buffer = self.domain.attrib_name_buffers[name]
        count = self.count

        array_start = buffer.count * self.start
        array_end = buffer.count * count + array_start
        try:
            buffer.data[array_start:array_end] = data
            buffer.invalidate_region(self.start, count)
        except ValueError:
            msg = f"Invalid data size for '{name}'. Expected {array_end - array_start}, got {len(data)}."
            raise ValueError(msg) from None


class InstanceVertexList(VertexList):
    """A list of vertices within an :py:class:`InstanceVertexDomain` that are instanced."""
    domain: InstancedVertexDomain
    instanced: bool = True




class _LocalIndexSupport:
    """When BaseVertex is supported by the version, this class will be mixed in.

    Will allow the class to use local index values instead of incrementing each mesh.
    """
    __slots__: tuple[str, ...] = ()

    supports_base_vertex: bool = True

    domain: IndexedVertexDomain | InstancedIndexedVertexDomain
    index_count: int
    index_start: int

    @property
    def indices(self) -> list[int]:
        return self.domain.index_stream.get_region(self.index_start, self.index_count)[:]

    @indices.setter
    def indices(self, local: Sequence[int]) -> None:  # type: ignore[override]
        self.domain.index_stream.set_region(self.index_start, self.index_count, local)

    def migrate(self, dest_domain: IndexedVertexDomain | InstancedIndexedVertexDomain) -> None:  # type: ignore[override]
        old_dom = self.domain
        src_idx_start = self.index_start
        src_idx_count = self.index_count

        super().migrate(dest_domain)

        data = old_dom.index_stream.get_region(src_idx_start, src_idx_count)
        old_dom.index_stream.allocator.dealloc(src_idx_start, src_idx_count)

        new_idx_start = self.domain.safe_index_alloc(src_idx_count)
        self.domain.index_stream.set_region(new_idx_start, src_idx_count, data)
        self.index_start = new_idx_start


class _RunningIndexSupport:
    """Used to mixin an IndexedVertexList class.

    Keeps an incrementing count for indices in the buffer.
    """
    __slots__: tuple[str, ...] = ()

    domain: IndexedVertexDomain | InstancedIndexedVertexDomain
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

    def migrate(self, dst_domain: IndexedVertexDomain | InstancedIndexedVertexDomain) -> None:
        old_dom = self.domain
        old_start: int = self.start
        src_idx_start = self.index_start
        src_idx_count = self.index_count

        super().migrate(dst_domain)

        data = old_dom.index_stream.get_region(src_idx_start, src_idx_count)
        old_dom.index_stream.allocator.dealloc(src_idx_start, src_idx_count)

        delta: int = self.start - old_start
        if delta:
            data = [i + delta for i in data]

        new_idx_start = self.domain.safe_index_alloc(src_idx_count)
        self.domain.index_stream.set_region(new_idx_start, src_idx_count, data)
        self.index_start = new_idx_start


class IndexedVertexList(VertexList):
    """A list of vertices within an :py:class:`IndexedVertexDomain` that are indexed.

    Use :py:meth:`IndexedVertexDomain.create` to construct this list.
    """
    domain: IndexedVertexDomain
    indexed: bool = True

    index_count: int
    index_start: int

    def __init__(self, domain: IndexedVertexDomain, start: int, count: int, index_start: int,  # noqa: D107
                 index_count: int) -> None:
        super().__init__(domain, start, count)
        self.index_start = index_start
        self.index_count = index_count

    def delete(self) -> None:
        """Delete this group."""
        super().delete()
        self.domain.index_allocator.dealloc(self.index_start, self.index_count)

    def migrate(self, domain: IndexedVertexDomain) -> None:
        """Move this group from its current indexed domain and add to the specified one.

        Attributes on domains must match.  (In practice, used
        to change parent state of some vertices).

        Args:
            domain:
                Indexed domain to migrate this vertex list to.
        """
        old_start = self.start
        old_domain = self.domain
        super().migrate(domain)

        # Note: this code renumber the indices of the *original* domain
        # because the vertices are in a new position in the new domain
        if old_start != self.start:
            diff = self.start - old_start
            old_indices = old_domain.index_buffer.get_region(self.index_start, self.index_count)
            old_domain.index_buffer.set_region(self.index_start, self.index_count, [i + diff for i in old_indices])

        # copy indices to new domain
        old_array = old_domain.index_buffer.get_region(self.index_start, self.index_count)
        # must delloc before calling safe_index_alloc or else problems when same
        # batch is migrated to because index_start changes after dealloc
        old_domain.index_allocator.dealloc(self.index_start, self.index_count)

        new_start = self.domain.safe_index_alloc(self.index_count)
        self.domain.index_buffer.set_region(new_start, self.index_count, old_array)

        self.index_start = new_start

    @property
    def indices(self) -> list[int]:
        """Array of index data."""
        start = self.start
        return [i - start for i in self.domain.index_buffer.get_region(self.index_start, self.index_count)]

    @indices.setter
    def indices(self, data: Sequence[int]) -> None:
        start = self.start
        # The vertex data is offset in the buffer, so offset the index values to match. Ex:
        # vertex_buffer: [_, _, _, _, 1, 2, 3, 4]
        self.domain.index_buffer.set_region(self.index_start, self.index_count, tuple(i + start for i in data))


class InstanceIndexedVertexList(VertexList):
    domain: InstancedIndexedVertexDomain
    indexed: bool = True
    instanced: bool = True

    index_count: int
    index_start: int

    bucket: InstanceBucket

    def create_instance(self, **attributes: Any) -> VertexInstanceBase:
        return self.bucket.create_instance(**attributes)

class VertexDomain:
    """Management of a set of vertex lists.

    Construction of a vertex domain is usually done with the
    :py:func:`create_domain` function.
    """

    attribute_meta: dict[str, dict[str, Any]]
    buffer_attributes: list[tuple[AttributeBufferObject, Attribute]]
    attribute_names: dict[str, Attribute]
    attrib_name_buffers: dict[str, VertexStream | InstanceStream]
    vertex_stream: VertexStream

    _property_dict: dict[str, property]
    _vertexlist_class: type

    _vertex_class: type[VertexList] = VertexList

    def __init__(self, attribute_meta: dict[str, dict[str, Any]]) -> None:  # noqa: D107
        raise NotImplementedError

    def safe_alloc(self, count: int) -> int:
        """Allocate vertices, resizing the buffers if necessary."""
        try:
            return self.allocator.alloc(count)
        except allocation.AllocatorMemoryException as e:
            capacity = _nearest_pow2(e.requested_capacity)
            for buffer, _ in self.buffer_attributes:
                buffer.resize(capacity * buffer.stride)
            self.allocator.set_capacity(capacity)
            return self.allocator.alloc(count)

    def safe_realloc(self, start: int, count: int, new_count: int) -> int:
        """Reallocate vertices, resizing the buffers if necessary."""
        try:
            return self.allocator.realloc(start, count, new_count)
        except allocation.AllocatorMemoryException as e:
            capacity = _nearest_pow2(e.requested_capacity)
            for buffer, _ in self.buffer_attributes:
                buffer.resize(capacity * buffer.stride)
            self.allocator.set_capacity(capacity)
            return self.allocator.realloc(start, count, new_count)

    def create(self, count: int, indices: Sequence[int] | None = None) -> VertexList:  # noqa: ARG002
        """Create a :py:class:`VertexList` in this domain.

        Args:
            count:
                Number of vertices to create.
            indices:
                A sequence of indices to create or None if not an indexed vertex list.
        """
        start = self.safe_alloc(count)
        return self._vertexlist_class(self, start, count)

    def draw(self, mode: int) -> None:
        """Draw all vertices in the domain.

        All vertices in the domain are drawn at once. This is the
        most efficient way to render primitives.

        Args:
            mode:
                OpenGL drawing mode, e.g. ``GL_POINTS``, ``GL_LINES``, etc.

        """

    def draw_subset(self, mode: GeometryMode, vertex_list: VertexList) -> None:
        """Draw a specific VertexList in the domain.

        The `vertex_list` parameter specifies a :py:class:`VertexList`
        to draw. Only primitives in that list will be drawn.

        Args:
            mode:
                OpenGL drawing mode, e.g. ``GL_POINTS``, ``GL_LINES``, etc.
            vertex_list:
                Vertex list to draw.

        """

    @property
    def is_empty(self) -> bool:
        return not self.allocator.starts

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}@{id(self):x} {self.allocator}>'


class IndexedVertexDomain(VertexDomain):
    """Management of a set of indexed vertex lists.

    Construction of an indexed vertex domain is usually done with the
    :py:func:`create_domain` function.
    """
    index_allocator: Allocator
    index_gl_type: int
    index_c_type: CType
    index_element_size: int
    index_buffer: IndexedBufferObject
    _initial_index_count = 16
    _vertex_class = IndexedVertexList
    index_stream: IndexStream

    def __init__(self, attribute_meta: dict[str, dict[str, Any]],  # noqa: D107
                 index_gl_type) -> None:
        super().__init__(attribute_meta)


    def safe_index_alloc(self, count: int) -> int:
        """Allocate indices, resizing the buffers if necessary."""
        try:
            return self.index_allocator.alloc(count)
        except allocation.AllocatorMemoryException as e:
            capacity = _nearest_pow2(e.requested_capacity)
            self.index_buffer.resize(capacity * self.index_element_size)
            self.index_allocator.set_capacity(capacity)
            return self.index_allocator.alloc(count)

    def safe_index_realloc(self, start: int, count: int, new_count: int) -> int:
        """Reallocate indices, resizing the buffers if necessary."""
        try:
            return self.index_allocator.realloc(start, count, new_count)
        except allocation.AllocatorMemoryException as e:
            capacity = _nearest_pow2(e.requested_capacity)
            self.index_buffer.resize(capacity * self.index_element_size)
            self.index_allocator.set_capacity(capacity)
            return self.index_allocator.realloc(start, count, new_count)

    def create(self, count: int, index_count: int) -> IndexedVertexList:
        """Create an :py:class:`IndexedVertexList` in this domain.

        Args:
            count:
                Number of vertices to create
            index_count:
                Number of indices to create

        """
        start = self.safe_alloc(count)
        index_start = self.safe_index_alloc(index_count)
        return self._vertexlist_class(self, start, count, index_start, index_count)

    def draw(self, mode: int) -> None:
        """Draw all vertices in the domain.

        All vertices in the domain are drawn at once. This is the
        most efficient way to render primitives.

        Args:
            mode:
                OpenGL drawing mode, e.g. ``GL_POINTS``, ``GL_LINES``, etc.

        """

    def draw_subset(self, mode: GeometryMode, vertex_list: IndexedVertexList) -> None:
        """Draw a specific IndexedVertexList in the domain.

        The `vertex_list` parameter specifies a :py:class:`IndexedVertexList`
        to draw. Only primitives in that list will be drawn.

        Args:
            mode:
                OpenGL drawing mode, e.g. ``GL_POINTS``, ``GL_LINES``, etc.
            vertex_list:
                Vertex list to draw.
        """

class InstancedVertexDomain(VertexDomain):
    ...

class InstancedIndexedVertexDomain(IndexedVertexDomain):
    ...


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

            # Create custom property to be used in the VertexList:
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
    """Program-specific VAO that binds streams."""

    def __init__(self, ctx, streams: list[VertexStream | InstanceStream | IndexStream]):
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


class _MultiDrawCache:
    def __init__(self):
        self._starts = None
        self._sizes = None
        self._primcount = 0
        self.is_dirty = True

    def rebuild_from_regions(self, regions, index_element_size):
        primcount = len(regions)
        if primcount == 0:
            self._starts = self._sizes = None
            self._primcount = 0
            self.is_dirty = False
            return

        intptr_array = (GLintptr * primcount)(
            *(r[0] * index_element_size for r in regions),
        )
        self._starts = (ctypes.POINTER(GLvoid) * primcount)(
            *[ctypes.cast(ctypes.c_void_p(addr), ctypes.POINTER(GLvoid)) for addr in intptr_array],
        )
        self._sizes = (GLsizei * primcount)(*(r[1] for r in regions))
        self._primcount = primcount
        self.is_dirty = False

    def bind_and_draw(self, ctx, mode, gl_type):
        if self._primcount:
            ctx.glMultiDrawElements(mode, self._sizes, gl_type, self._starts, self._primcount)



class VertexGroupBucket(allocation.RangeAllocator):
    """A grouping of vertex lists belonging to a single group in a domain.

    Vertex lists are still owned by the domain, but this allows states to be rendered together if possible.
    """

    __slots__ = ("_merged", "_ranges", "is_dirty")

    def __init__(self) -> None:
        super().__init__()

    def add_vertex_list(self, vl: VertexList) -> None:
        self.add(vl.start, vl.count)
        vl.bucket = vl

    def remove_vertex_list(self, vl: VertexList) -> None:
        self.remove(vl.start, vl.count)
        vl.bucket = None

    def draw(self, domain, mode: int) -> None:
        """Draw all contiguous ranges."""
        for start, count in self.merged_ranges:
            domain.draw_range(mode, start, count)


class IndexedVertexGroupBucket(allocation.RangeAllocator):
    """A grouping of indexed vertex lists belonging to a single group in a domain.

    Vertex lists are still owned by the domain, but this allows states to be rendered together if possible.
    """
    __slots__ = ("_merged", "_ranges", "is_dirty")

    def add_vertex_list(self, vl: IndexedVertexList) -> None:
        self.add(vl.index_start, vl.index_count)
        vl.bucket = self

    def remove_vertex_list(self, vl: IndexedVertexList) -> None:
        self.remove(vl.index_start, vl.index_count)
        vl.bucket = None

    def draw(self, domain, mode: int) -> None:
        """Draw all contiguous ranges."""
        for start, count in self.merged_ranges:
            domain.draw_range(mode, start, count)
