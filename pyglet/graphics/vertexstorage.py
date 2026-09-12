"""Vertex and index buffer streams owned by graphics vertex domains.

This module contains the storage layer beneath :mod:`vertexdomain`: streams
manage GPU buffers and allocators, bindings connect those streams to vertex
input state, and :class:`VertexStorage` coordinates reusable streams for a
batch.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Literal, NoReturn, Protocol, Sequence

from pyglet.graphics import allocation
from pyglet.graphics.attributes import Attribute, AttributeView, DataTypeTuple, GraphicsAttribute, VertexLayout

if TYPE_CHECKING:
    from ctypes import Array

    from pyglet.customtypes import DataTypes
    from pyglet.graphics.api.base import SurfaceContext
    from pyglet.graphics.buffer import AttributeBufferObject, IndexedBufferObject
    from pyglet.graphics.draw import Batch
    from pyglet.graphics.vertexdomain import VertexDomain


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
    def _attribute_getter(self: Any) -> Array[float | int]:
        stream = self.domain.attrib_name_buffers[name]
        region = stream.get_attribute_region(name, self.start, self.count)
        stream.invalidate_attribute_region(name, self.start, self.count)
        return region

    def _attribute_setter(self: Any, data: Any) -> None:
        stream = self.domain.attrib_name_buffers[name]
        stream.set_attribute_region(name, self.start, self.count, data)

    return property(_attribute_getter, _attribute_setter)


class Stream(ABC):
    """A container that handles a set of buffers used by domains."""

    def __init__(self, size: int) -> None:
        """Initialize the stream and create an allocator.

        Args:
            size: Initial allocator and buffer size.
        """
        self._capacity = size
        self.allocator = allocation.Allocator(size)
        self.buffers = []

    def commit(self) -> None:
        """Bind buffers and commit all pending data to the graphics API."""
        for buf in self.buffers:
            buf.commit()

    @property
    def starts(self) -> list[int]:
        """Starts of allocated regions in this stream."""
        return self.allocator.starts

    @property
    def sizes(self) -> list[int]:
        """Sizes of allocated regions in this stream."""
        return self.allocator.sizes

    def get_allocated_regions(self) -> tuple[list[int], list[int]]:
        """Return allocated region starts and sizes."""
        return self.allocator.get_allocated_regions()

    @property
    def has_persistent_buffers(self) -> bool:
        """Whether resizing this stream can replace its GPU buffer handles."""
        return False

    def rebind_buffers(self) -> None:
        """Refresh bindings after buffer handles change."""

    @abstractmethod
    def bind_into(self, vao: Any) -> None:
        """Record this stream into a bound vertex-input object."""

    def alloc(self, count: int) -> int:
        """Allocate a region of data, resizing buffers if necessary."""
        try:
            return self.allocator.alloc(count)
        except allocation.AllocatorMemoryException as exc:
            self.resize(_nearest_pow2(exc.requested_capacity))
            return self.allocator.alloc(count)

    def resize(self, capacity: int) -> None:
        """Resize all buffers to the specified capacity."""
        if capacity <= self.allocator.capacity:
            return
        self.allocator.set_capacity(capacity)
        for buf in self.buffers:
            buf.resize(capacity * buf.stride)

    def dealloc(self, start: int, count: int) -> None:
        self.allocator.dealloc(start, count)

    def realloc(self, start: int, count: int, new_count: int) -> int:
        """Reallocate a region of data, resizing buffers if necessary."""
        try:
            return self.allocator.realloc(start, count, new_count)
        except allocation.AllocatorMemoryException as exc:
            self.resize(_nearest_pow2(exc.requested_capacity))
            return self.allocator.realloc(start, count, new_count)

    @abstractmethod
    def set_region(self, start: int, count: int, data: Any) -> None: ...


class VertexStream(Stream):
    """A stream of buffers used with per-vertex attributes."""

    attrib_name_buffers: dict[str, AttributeBufferObject]
    attribute_meta: Sequence[Attribute]

    def __init__(self, ctx: SurfaceContext, initial_size: int, attrs: Sequence[Attribute], *, divisor: int = 0):
        super().__init__(initial_size)
        self._ctx = ctx
        self.attribute_names = {}
        self.buffers = []
        self.attrib_name_buffers = {}
        self._property_dict = {}
        self.attribute_meta = attrs
        self._allocate_buffers()

    def get_buffer(self, size: int, attribute: GraphicsAttribute) -> AttributeBufferObject:
        raise NotImplementedError

    def get_graphics_attribute(self, attribute: Attribute, view: AttributeView) -> GraphicsAttribute:
        raise NotImplementedError

    def _create_separate_buffers(self, attributes: Sequence[Attribute]) -> None:
        """Create a separate buffer for each attribute."""
        for attribute in attributes:
            name = attribute.fmt.name
            stride = attribute.fmt.components * attribute.element_size
            view = AttributeView(offset=0, stride=stride)
            self.attribute_names[name] = attribute = self.get_graphics_attribute(attribute, view)
            self.attrib_name_buffers[name] = buffer = self.get_buffer(stride * self.allocator.capacity, attribute)
            self.buffers.append(buffer)
            self._property_dict[name] = _make_attribute_property(name)

    def _create_interleaved_buffers(self) -> NoReturn:
        """Create a single buffer for all passed attributes."""
        raise NotImplementedError

    def _allocate_buffers(self) -> None:
        for attrib in self.attribute_meta:
            fmt_dt = attrib.fmt.data_type
            assert fmt_dt in DataTypeTuple, f"'{fmt_dt}' is not a valid attribute format for '{attrib.fmt.name}'."
        self._create_separate_buffers(self.attribute_meta)

    def set_region(self, start: int, count: int, data_by_attr: dict[str, Any]) -> None:
        for name, buf in self.attrib_name_buffers.items():
            buf.set_region(start, count, data_by_attr[name])

    def set_attribute_region(self, name: str, start: int, count: int, data: Any) -> None:
        self.attrib_name_buffers[name].set_region(start, count, data)

    def get_attribute_region(self, name: str, start: int, count: int) -> Any:
        return self.attrib_name_buffers[name].get_region(start, count)

    def invalidate_attribute_region(self, name: str, start: int, count: int) -> None:
        self.attrib_name_buffers[name].invalidate_region(start, count)

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
            dst_names = set(dst_stream.attrib_name_buffers)
            src_names = set(self.attrib_name_buffers)
            names = dst_names & src_names
            if strict and dst_names != src_names:
                raise ValueError(
                    f"Attribute layout mismatch: missing in dst={sorted(src_names - dst_names)}, "
                    f"missing in src={sorted(dst_names - src_names)}"
                )
        else:
            names = [name for name in attrs if name in self.attrib_name_buffers and name in dst_stream.attrib_name_buffers]
            if strict and len(names) != len(list(attrs)):
                raise ValueError(f"Requested attribute not present in both streams. {names}, {attrs}")

        for name in names:
            data = self.attrib_name_buffers[name].get_region(src_slot, count)
            dst_stream.attrib_name_buffers[name].set_region(dst_slot, count, data)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(attributes={list(self.attribute_meta)}, alloc={self.allocator})'


class InstanceStream(VertexStream):
    """A stream of buffers used with per-instance attributes."""


class IndexStream(Stream):
    """A stream that manages an index buffer for a domain."""

    def __init__(self, ctx: SurfaceContext, data_type: DataTypes, initial_elems: int):
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

    def bind_into(self, vao: Any) -> None:
        self.buffer.bind_to_index_buffer()

    def set_region(self, start: int, count: int, data: Any) -> None:
        self.buffer.set_region(start, count, data)

    def copy_region(self, dst: int, src: int, count: int) -> None:
        self.buffer.copy_region(dst, src, count)


class VertexArrayProtocol(Protocol):
    def bind(self) -> None: ...
    def unbind(self) -> None: ...


class VertexInputBinding(Protocol):
    """The vertex-input state required to issue a draw call."""

    def bind(self) -> None:
        """Make this vertex-input state current."""


class VertexArrayBinding:
    """A wrapper for vertex-input state that binds streams."""

    streams: list[VertexStream | InstanceStream | IndexStream]

    def __init__(self, ctx: SurfaceContext, streams: list[VertexStream | InstanceStream | IndexStream]):
        self._ctx = ctx
        self.vao = self._create_vao()
        self.streams = streams
        self._link()

    def bind(self) -> None:
        raise NotImplementedError

    def _create_vao(self) -> VertexArrayProtocol: ...

    def _link(self) -> None:
        """Link all streams to the vertex-input object."""

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}@{id(self):x} vao={self.vao}, streams={self.streams}>'


class VertexStreamPool:
    """Own compatible attribute buffers shared by multiple vertex streams."""

    def __init__(self, chunk_size: int) -> None:
        self.chunk_size = chunk_size
        self._attribute_buffers: dict[tuple[str, int, str, bool, int], Any] = {}
        self._streams: list[VertexStream] = []
        self._allocator: allocation.Allocator | None = None

    def attach_domain(self, domain: VertexDomain) -> None:
        """Share compatible buffers with a domain's existing vertex stream."""
        self._attach_stream(domain)

    @staticmethod
    def _attribute_buffer_key(attribute: Any) -> tuple[str, int, str, bool, int]:
        fmt = attribute.fmt
        return fmt.name, fmt.components, fmt.data_type, fmt.normalized, fmt.divisor

    def _attach_stream(self, domain: VertexDomain) -> None:
        stream = domain.vertex_buffers
        if self._allocator is None:
            self._allocator = stream.allocator
        else:
            stream.allocator = self._allocator

        changed_buffers = False
        for name, attribute in domain.attribute_meta.items():
            if attribute.fmt.is_instanced:
                continue
            key = self._attribute_buffer_key(attribute)
            buffer = stream.attrib_name_buffers[name]
            shared_buffer = self._attribute_buffers.setdefault(key, buffer)
            if shared_buffer is not buffer:
                stream.attrib_name_buffers[name] = shared_buffer
                changed_buffers = True

        if changed_buffers:
            stream.buffers = list(stream.attrib_name_buffers.values())

        self._streams.append(stream)
        self._resize_attribute_buffers(self._allocator.capacity)
        domain.allocator = allocation.ChunkAllocator(
            self.chunk_size, self._allocate_attribute_chunk, self._allocator.dealloc,
        )
        if changed_buffers:
            domain.vao = domain._create_vao()

    def _allocate_attribute_chunk(self, count: int) -> int:
        assert self._allocator is not None
        try:
            return self._allocator.alloc(count)
        except allocation.AllocatorMemoryException as exc:
            self._resize_attribute_buffers(1 << (exc.requested_capacity - 1).bit_length())
            return self._allocator.alloc(count)

    def _resize_attribute_buffers(self, capacity: int) -> None:
        assert self._allocator is not None
        if capacity > self._allocator.capacity:
            self._allocator.set_capacity(capacity)
        resized = False
        for buffer in self._attribute_buffers.values():
            size = capacity * buffer.stride
            if size > buffer.size:
                buffer.resize(size)
                resized = True

        if resized:
            for stream in self._streams:
                if stream.has_persistent_buffers:
                    stream.rebind_buffers()


class VertexStorage:
    """A batch-owned namespace for reusable, layout-compatible geometry."""

    def __init__(
        self,
        batch: Batch,
        layouts: Iterable[VertexLayout] = (),
        *,
        chunk_size: int = 4096,
        sharing_policy: Literal['separate', 'shared'] = 'separate',
    ) -> None:
        if chunk_size < 1:
            raise ValueError('chunk_size must be positive.')
        if sharing_policy not in ('separate', 'shared'):
            raise ValueError("sharing_policy must be 'separate' or 'shared'.")
        self._batch = batch
        self.chunk_size = chunk_size
        self.sharing_policy = sharing_policy
        self.layouts: list[VertexLayout] = []
        self.attribute_formats: dict[str, set[str]] = {}
        self._vertex_streams: list[VertexStream] = []
        self._vertex_stream_pool = VertexStreamPool(chunk_size) if sharing_policy == 'shared' else None
        self._index_streams: list[Any] = []
        self._shared_index_streams: dict[str, Any] = {}
        for layout in layouts:
            self.add_layout(layout)

    def add_layout(self, layout: VertexLayout) -> VertexLayout:
        if not isinstance(layout, VertexLayout):
            raise TypeError('layout must be a VertexLayout')
        if layout not in self.layouts:
            self.layouts.append(layout)
            for name, fmt in layout.formats.items():
                self.attribute_formats.setdefault(name, set()).add(fmt)
        return layout

    def resolve_layout(self, vertex_layout: VertexLayout | None = None) -> VertexLayout | None:
        """Register or infer the geometry layout used with this storage."""
        if vertex_layout is None:
            if len(self.layouts) == 1:
                vertex_layout = self.layouts[0]
            elif len(self.layouts) > 1:
                raise ValueError('Specify vertex_layout when a VertexStorage supports multiple layouts.')
            else:
                return None
        if not isinstance(vertex_layout, VertexLayout):
            raise TypeError('vertex_layout must be a VertexLayout')
        self.add_layout(vertex_layout)
        return vertex_layout

    def get_vertex_layout(self, shader_layout: Any, vertex_layout: VertexLayout | None = None) -> Any:
        """Return ``shader_layout`` adapted to this storage's vertex layout.

        The shader owns attribute locations and component counts, whereas this
        storage owns the backing-buffer formats.  Keep that conversion at the
        storage boundary so domains are keyed by the resulting shader view.
        """
        layout = self.resolve_layout(vertex_layout)
        return shader_layout.get_vertex_view(layout) if layout is not None else shader_layout

    def attach_domain(self, domain: VertexDomain) -> None:
        """Attach a domain using this storage's selected sharing policy."""
        if self.sharing_policy == 'shared':
            assert self._vertex_stream_pool is not None
            self._vertex_stream_pool.attach_domain(domain)
        else:
            self._attach_separate_vertex_stream(domain)
        self._attach_index_stream(domain)

    def _attach_separate_vertex_stream(self, domain: VertexDomain) -> None:
        vertex_stream = domain.vertex_buffers
        self._vertex_streams.append(vertex_stream)
        domain.allocator = vertex_stream

    def _attach_index_stream(self, domain: VertexDomain) -> None:
        previous_index_stream = getattr(domain, 'index_stream', None)
        if previous_index_stream is None:
            return
        assert domain.index_type is not None
        if self.sharing_policy == 'separate':
            self._index_streams.append(previous_index_stream)
            domain.index_allocator = previous_index_stream
            return

        index_stream = self._shared_index_streams.setdefault(domain.index_type, previous_index_stream)
        if index_stream is previous_index_stream:
            self._index_streams.append(index_stream)
        if index_stream is not previous_index_stream:
            domain.index_stream = index_stream
            domain._streams = [index_stream if stream is previous_index_stream else stream for stream in domain._streams]
            domain.vao = domain._create_vao()
        domain.index_allocator = allocation.ChunkAllocator(
            self.chunk_size, index_stream.alloc, index_stream.allocator.dealloc,
        )
