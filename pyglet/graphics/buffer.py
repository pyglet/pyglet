"""Shared GPU buffer abstractions.

`AbstractBuffer` models a GPU byte buffer. It intentionally has no knowledge
of ctypes element formats or shader attribute data types.

Typed host-side data is provided by `BufferDataStore` implementations. The
default store is `CTypeDataStore`, but other stores can be created later such
as JS for WebGL or even Numpy.
"""

from __future__ import annotations

import abc
import ctypes
import struct
import warnings
from ctypes import Array
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Sequence, Union

if TYPE_CHECKING:
    from pyglet.customtypes import CType, CTypesPointer, DataTypes


ByteSource = Union[bytes, bytearray, memoryview]
DataSource = Union[Sequence[Union[float, int]], Array[Any]]

_DATA_TYPE_TO_CTYPE: dict[str, type[Any]] = {
    "?": ctypes.c_bool,
    "b": ctypes.c_byte,
    "B": ctypes.c_ubyte,
    "h": ctypes.c_short,
    "H": ctypes.c_ushort,
    "i": ctypes.c_int,
    "I": ctypes.c_uint,
    "q": ctypes.c_longlong,
    "Q": ctypes.c_ulonglong,
    "f": ctypes.c_float,
    "d": ctypes.c_double,
}


def _data_type_to_ctype(data_type: DataTypes) -> CType:
    c_type = _DATA_TYPE_TO_CTYPE.get(data_type)
    if c_type is None:
        msg = f"Unsupported data type '{data_type}'."
        raise Exception(msg)
    return c_type


def _data_type_size(data_type: DataTypes) -> int:
    try:
        return struct.calcsize(data_type)
    except struct.error as exc:
        msg = f"Unsupported data type '{data_type}'."
        raise AssertionError(msg) from exc


def _to_bytes(data: ByteSource | Sequence[int] | CTypesPointer) -> bytes:
    """Convert supported host-side inputs into raw bytes."""
    if hasattr(data, "contents"):
        return ctypes.string_at(data, ctypes.sizeof(data.contents))

    try:
        return bytes(data)
    except TypeError as exc:
        msg = (
            f"Unsupported data type: {type(data)!r}. "
            "Use bytes-like objects, ctypes arrays, ctypes pointers, or integer sequences."
        )
        raise AssertionError(msg) from exc


def _align_to(value: int, alignment: int) -> int:
    """Align ``value`` to the next ``alignment`` boundary."""
    assert value >= 0, "Value must be non-negative."
    assert alignment > 0, "Alignment must be greater than zero."
    return (value + alignment - 1) // alignment * alignment


class AbstractBuffer(abc.ABC):
    """A backend GPU buffer represented as bytes."""

    size: int

    def __init__(self, size: int) -> None:
        self.size = size

    @abc.abstractmethod
    def bind(self) -> None:
        """Bind this buffer for updates/reads."""

    @abc.abstractmethod
    def unbind(self) -> None:
        """Unbind this buffer."""

    @abc.abstractmethod
    def get_bytes(self) -> bytes:
        """Read the entire buffer contents as bytes."""

    @abc.abstractmethod
    def get_bytes_region(self, offset: int, length: int) -> bytes:
        """Read a byte-range from the buffer."""

    @abc.abstractmethod
    def set_bytes(self, data: ByteSource) -> None:
        """Replace the entire buffer contents from bytes."""

    @abc.abstractmethod
    def set_bytes_region(self, offset: int, data: ByteSource) -> None:
        """Write bytes into a sub-range of the buffer."""

    @abc.abstractmethod
    def resize(self, size: int) -> None:
        """Resize the buffer."""

    @abc.abstractmethod
    def delete(self) -> None:
        """Free backend resources used by this buffer."""

    def get_data(self) -> bytes:
        """Compatibility helper for callers that expect `get_data`."""
        return self.get_bytes()

    def get_data_region(self, start: int, length: int) -> bytes:
        """Compatibility helper for callers that expect `get_data_region`."""
        return self.get_bytes_region(start, length)

    def set_data(self, data: Sequence[int] | CTypesPointer | ByteSource) -> None:
        """Compatibility helper for callers that expect `set_data`."""
        self.set_bytes(_to_bytes(data))

    def set_data_region(self, data: Sequence[int] | CTypesPointer | ByteSource, start: int, length: int) -> None:
        """Compatibility helper for callers that expect `set_data_region`."""
        if hasattr(data, "contents"):
            self.set_bytes_region(start, ctypes.string_at(data, length))
            return

        raw = _to_bytes(data)
        assert len(raw) >= length, f"Insufficient data length. Expected at least {length} bytes, got {len(raw)}."
        self.set_bytes_region(start, raw[:length])

    def set_data_ptr(self, offset: int, length: int, ptr: CTypesPointer) -> None:
        """Compatibility helper for callers that pass a ctypes pointer."""
        self.set_bytes_region(offset, ctypes.string_at(ptr, length))


@dataclass(frozen=True)
class BufferBindingSlice:
    offset: int
    size: int


@dataclass
class BufferRange:
    offset: int
    size: int
    in_use: bool = False
    frame_use_count: int = 0

class RingBuffer:
    """Generic ring allocator.

    Range lifetime is tracked by owners such as ``FrameResourceManager`` by
    setting ``BufferRange.in_use``. This allocator only selects writable ranges.
    """

    strict: bool
    alignment: int
    range_size: int
    range_stride: int
    copies_per_resource: int
    _planned_size: int
    _next_offset: int
    _ranges: list[BufferRange]
    _next_range_index: int
    _current_slice: BufferBindingSlice | None

    def __init__(
        self,
        *,
        range_size: int,
        alignment: int = 1,
        copies_per_resource: int = 3,
        strict: bool = False,
        start_offset: int = 0,
    ) -> None:
        assert range_size > 0, "Range size must be greater than zero."
        self.strict = bool(strict)
        self.alignment = max(1, int(alignment))
        self.range_size = int(range_size)
        self.range_stride = _align_to(self.range_size, self.alignment)
        self.copies_per_resource = max(1, int(copies_per_resource))
        self._next_offset = _align_to(max(0, int(start_offset)), self.alignment)
        self._planned_size = self._next_offset
        self._ranges = []
        self._next_range_index = 0
        self._current_slice = None

    @property
    def planned_size(self) -> int:
        return self._planned_size

    def reserve_resource_range(
        self,
        copies_per_resource: int | None = None,
    ) -> list[BufferRange]:
        count = self.copies_per_resource if copies_per_resource is None else max(1, int(copies_per_resource))
        assert count is not None
        assert count > 0
        start = len(self._ranges)
        for _ in range(count):
            self._ranges.append(self._allocate_range())
        return self._ranges[start:]

    def acquire_writable_slice(self) -> tuple[BufferBindingSlice, BufferRange]:
        if not self._ranges:
            self.reserve_resource_range()

        range_ = self._ranges[self._next_range_index]
        self._next_range_index = (self._next_range_index + 1) % len(self._ranges)

        # If not in use, allocate.
        if not range_.in_use:
            binding = BufferBindingSlice(offset=range_.offset, size=range_.size)
            self._current_slice = binding
            return binding, range_

        if self.strict:
            raise RuntimeError(
                "RingBuffer has no writable range. All reserved ranges are still in use. "
                "Increase initial buffer size or copies_per_resource."
            )
        warnings.warn("RingBuffer wrapped while full. Consider growing range capacity to avoid more stalls.")
        new_range = self._allocate_range()
        self._ranges.append(new_range)
        self._on_non_strict_expand(new_range)
        binding = BufferBindingSlice(offset=new_range.offset, size=new_range.size)
        self._current_slice = binding
        return binding, new_range

    def acquire_writable_slice_from_ranges(
        self,
        ranges: list[BufferRange],
        next_range_index: int,
    ) -> tuple[BufferBindingSlice, BufferRange, int]:
        if not ranges:
            ranges.extend(self.reserve_resource_range())

        range_index = next_range_index % len(ranges)
        for _ in range(len(ranges)):
            range_ = ranges[range_index]
            range_index = (range_index + 1) % len(ranges)
            if not range_.in_use:
                binding = BufferBindingSlice(offset=range_.offset, size=range_.size)
                self._current_slice = binding
                return binding, range_, range_index

        if self.strict:
            raise RuntimeError(
                "RingBuffer has no writable range. All reserved ranges are still in use. "
                "Increase initial buffer size or copies_per_resource."
            )
        warnings.warn("RingBuffer wrapped while full. Consider growing range capacity to avoid more stalls.")
        new_range = self._allocate_range()
        self._ranges.append(new_range)
        ranges.append(new_range)
        self._on_non_strict_expand(new_range)
        binding = BufferBindingSlice(offset=new_range.offset, size=new_range.size)
        self._current_slice = binding
        return binding, new_range, 0

    def delete(self) -> None:
        for range_ in self._ranges:
            range_.in_use = False
            range_.frame_use_count = 0
        self._ranges.clear()
        self._current_slice = None
        self._next_range_index = 0

    def _allocate_range(self) -> BufferRange:
        offset = _align_to(self._next_offset, self.alignment)
        self._next_offset = offset + self.range_stride
        self._planned_size = max(self._planned_size, self._next_offset)
        return BufferRange(offset=offset, size=self.range_size)

    def _find_range_for_binding(self, binding: BufferBindingSlice) -> BufferRange:
        for range_ in self._ranges:
            if range_.offset == binding.offset and range_.size == binding.size:
                return range_
        msg = (
            f"Could not resolve ring range for binding offset={binding.offset}, size={binding.size}. "
            "The binding may not belong to this resource."
        )
        raise RuntimeError(msg)

    def _on_non_strict_expand(self, _new_range: BufferRange) -> None:
        """Hook for subclasses when strict=False expansion occurs."""



class UniformBufferObject(RingBuffer):
    """Backend-agnostic Uniform Buffer Object wrapper."""

    buffer: AbstractBuffer
    view_class: type[ctypes.Structure]
    view: ctypes.Structure
    _view_ptr: Any
    _context: Any
    binding: int
    _storage_committed: bool
    __slots__ = ("_context", "_storage_committed", "_view_ptr", "binding", "buffer", "view", "view_class")

    def __init__(
        self,
        context: Any,
        view_class: type[ctypes.Structure],
        buffer_size: int,
        binding: int,
        *,
        alignment: int = 1,
        copies_per_resource: int = 3,
        strict: bool = False,
    ) -> None:
        self._context = context
        self.buffer = self._create_buffer(context, buffer_size)
        self.view_class = view_class
        self.view = view_class()
        self._view_ptr = ctypes.pointer(self.view)
        self.binding = binding
        self._storage_committed = False
        super().__init__(
            range_size=buffer_size,
            alignment=alignment,
            copies_per_resource=copies_per_resource,
            strict=strict,
            # Keep [0, range_size) for legacy ``with ubo as block:`` uploads.
            start_offset=buffer_size,
        )

    @property
    def id(self) -> int:
        return self.buffer.id

    @property
    def size(self) -> int:
        return self.buffer.size

    @property
    def slice_size(self) -> int:
        return self.range_size

    @property
    def slice_stride(self) -> int:
        return self.range_stride

    def read(self) -> bytes:
        return self.buffer.get_data()

    def __enter__(self) -> ctypes.Structure:
        return self.view

    def __exit__(self, _exc_type, _exc_val, _exc_tb) -> None:  # noqa: ANN001
        self._ensure_storage_for_commit(self.range_size)
        view_size = ctypes.sizeof(self.view)
        self.buffer.set_data_region(self._view_ptr, 0, view_size)
        self._storage_committed = True

    def get_data_structure(self) -> ctypes.Structure:
        return self.view_class()

    def upload_to_available_binding(
        self,
        resource_data: ctypes.Structure,
    ) -> BufferBindingSlice:
        binding, range_ = self.acquire_writable_slice()
        self._commit_data(range_, resource_data)
        self._context.frame_resources.allocate_ubo(range_)
        return binding

    def upload_to_available_binding_from_ranges(
        self,
        resource_data: ctypes.Structure,
        ranges: list[BufferRange],
        next_range_index: int,
    ) -> tuple[BufferBindingSlice, BufferRange, int]:
        binding, range_, next_range_index = self.acquire_writable_slice_from_ranges(ranges, next_range_index)
        self._commit_data(range_, resource_data)
        self._context.frame_resources.allocate_ubo(range_)
        return binding, range_, next_range_index

    def bind_slice(self, binding: BufferBindingSlice, *, binding_index: int | None = None) -> None:
        index = self.binding if binding_index is None else binding_index
        assert index >= 0, "Binding index must be non-negative."
        assert binding.offset >= 0 and binding.size >= 0, "Offset and size must be non-negative."  # noqa: PT018
        assert binding.offset + binding.size <= self.size, (
            f"Slice [{binding.offset}, {binding.offset + binding.size}) exceeds UBO size {self.size}."
        )
        self._bind_range(index, binding.offset, binding.size)

    def use_range(self, range_: BufferRange) -> None:
        self._context.frame_resources.use_ubo(range_)

    def delete(self) -> None:
        super().delete()
        self.buffer.delete()

    @abc.abstractmethod
    def _create_buffer(self, context: Any, buffer_size: int) -> AbstractBuffer:
        raise NotImplementedError

    @abc.abstractmethod
    def _bind_range(self, binding: int, offset: int, size: int) -> None:
        raise NotImplementedError

    def _on_non_strict_expand(self, _new_range: BufferRange) -> None:
        self._ensure_storage_for_commit(self.planned_size, force_double=True)

    def _commit_data(self, range_: BufferRange, resource_data: ctypes.Structure) -> None:
        if range_.in_use and self._context.frame_active:
            msg = "Cannot modify a UBO range while it is in use by the active frame."
            raise RuntimeError(msg)

        data_size = ctypes.sizeof(resource_data)
        assert data_size <= range_.size, (
            f"Resource data size {data_size} exceeds reserved range size {range_.size}."
        )
        self._ensure_storage_for_commit(range_.offset + range_.size)
        data_ptr = ctypes.pointer(resource_data)
        self.buffer.set_data_region(data_ptr, range_.offset, data_size)
        self._storage_committed = True

    def _ensure_storage_for_commit(self, required_end: int, *, force_double: bool = False) -> None:
        required_size = max(required_end, self.planned_size)
        if required_size <= self.size and not force_double:
            return

        if not self._storage_committed:
            self.buffer.resize(required_size)
            return

        if self.strict and required_size > self.size:
            raise RuntimeError(
                f"UniformBufferObject backing store full at {self.size} bytes while ranges are in use "
                "by submitted frames. "
                "Increase initial buffer size or copies_per_resource."
            )

        current_size = max(1, self.size)
        new_size = current_size * 2 if force_double else current_size
        while new_size < required_size:
            new_size *= 2

        if new_size != self.size:
            msg = f"Growing UniformBufferObject({self.id}) storage from {self.size} to {new_size} bytes."
            warnings.warn(msg)
            self.buffer.resize(new_size)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.buffer.id}, binding={self.binding}, size={self.size}, "
            f"range_size={self.range_size}, range_stride={self.range_stride}, ranges={len(self._ranges)}, "
            f"strict={self.strict})"
        )


class UniformBufferRegion:
    """UBO region that uploads through a ring-buffered ``UniformBufferObject``.

    The region owns one CPU-side data structure and a set of GPU ranges.

    General practice is to update the data structure, mark it dirty, and then commit when you are done updating
    for that frame.

    .. warning:: Do not make the CPU-side data dirty after binding/committing during the same frame (for example,
                 during the ``on_draw`` call), or GPU stalls may occur.

    .. versionadded:: 3.0
    """

    __slots__ = (
        "_current_binding",
        "_current_range",
        "_dirty",
        "_next_range_index",
        "_ranges",
        "_ubo",
        "data",
    )

    def __init__(
        self,
        ubo: UniformBufferObject,
        *,
        copies_per_resource: int | None = None,
    ) -> None:
        self._ubo = ubo
        self.data = ubo.get_data_structure()
        self._current_binding: BufferBindingSlice | None = None
        self._current_range: BufferRange | None = None
        self._ranges = ubo.reserve_resource_range(copies_per_resource=copies_per_resource)
        self._next_range_index = 0
        self._dirty = True

    @property
    def ubo(self) -> UniformBufferObject:
        """The underlying ``UniformBufferObject``."""
        return self._ubo

    @property
    def dirty(self) -> bool:
        """Whether the CPU-side data needs to be uploaded before drawing."""
        return self._dirty

    def __enter__(self) -> ctypes.Structure:
        return self.data

    def __exit__(self, _exc_type: Any, _exc_val: Any, _exc_tb: Any) -> None:
        self.mark_dirty()

    def mark_dirty(self) -> None:
        """Mark the CPU-side data for upload on the next ``bind`` call."""
        self._dirty = True

    def commit(self) -> None:
        """Upload dirty CPU-side data to the next writable GPU range."""
        if not self._dirty:
            return

        self._current_binding, self._current_range, self._next_range_index = (
            self._ubo.upload_to_available_binding_from_ranges(
                self.data,
                self._ranges,
                self._next_range_index,
            )
        )
        self._dirty = False

    def bind(self, *, binding_index: int | None = None) -> None:
        """Upload dirty data if needed, then bind the current GPU range."""
        self.commit()

        if self._current_binding is None or self._current_range is None:
            return

        self._ubo.use_range(self._current_range)
        self._ubo.bind_slice(self._current_binding, binding_index=binding_index)


class MappedBufferObject(AbstractBuffer):
    """A GPU buffer that supports map/unmap and range mapping."""

    @abc.abstractmethod
    def map(self, bits: int = 0) -> Any:
        """Map the entire buffer."""

    @abc.abstractmethod
    def map_range(self, start: int, size: int, ptr_type: type[CTypesPointer], bits: int = 0) -> Any:
        """Map a range of the buffer."""

    @abc.abstractmethod
    def unmap(self) -> None:
        """Unmap a previously mapped buffer."""


class BufferDataStore(abc.ABC):
    """Host-side data store used by `BackedBufferObject`."""

    size: int
    stride: int
    element_count: int

    @property
    @abc.abstractmethod
    def data(self) -> Any:
        """Store-specific data object."""

    @property
    @abc.abstractmethod
    def data_ptr(self) -> int | None:
        """Optional integer pointer/address to the store memory."""

    @property
    @abc.abstractmethod
    def element_size(self) -> int:
        """Size in bytes of one store element."""

    @abc.abstractmethod
    def get_bytes(self, offset: int = 0, length: int | None = None) -> bytes:
        """Get raw bytes from the store."""

    @abc.abstractmethod
    def set_bytes(self, offset: int, data: ByteSource) -> None:
        """Write raw bytes into the store."""

    @abc.abstractmethod
    def get_region(self, start: int, count: int) -> Any:
        """Return a typed region view."""

    @abc.abstractmethod
    def set_region(self, start: int, count: int, data: Sequence[float | int]) -> None:
        """Write typed region data."""

    @abc.abstractmethod
    def copy_region(self, dst: int, src: int, count: int) -> None:
        """Copy a typed region inside the store."""

    @abc.abstractmethod
    def resize(self, size: int) -> None:
        """Resize the store."""


class CTypeDataStore(BufferDataStore):
    """ctypes-based `BufferDataStore`.

    This is the default host-side data store and keeps data in a ctypes array.
    """

    data_type: DataTypes
    _ctype: CType
    _element_size: int
    _data: Any
    _data_ptr: int
    _owns_memory: bool

    def __init__(
        self,
        size: int,
        data_type: DataTypes,
        stride: int,
        element_count: int,
        data_ptr: int | None = None,
    ) -> None:
        """Create a ctypes-backed typed data store.

        Args:
            size:
                Total byte size for the store.
            data_type:
                Struct-format data type code (for example ``"f"`` or ``"I"``)
                used to determine the underlying ctypes type and element size.
            stride:
                Byte stride for one logical element in this buffer layout.
            element_count:
                Number of scalar values per logical element.
            data_ptr:
                Optional pointer to externally owned memory. When provided, this
                store binds to that memory instead of allocating its own ctypes
                array.

        Note:
            The ``_owns_memory`` flag indicates whether this store allocated its
            own backing array (``True``) or is bound to external memory
            (``False``). This is used to protect ``resize``: externally backed
            stores cannot reallocate memory and must be rebound with
            ``rebind_external``.
        """
        self.data_type = data_type
        self._ctype = _data_type_to_ctype(data_type)
        self._element_size = _data_type_size(data_type)
        self.stride = stride
        self.element_count = element_count
        self.size = size
        self._owns_memory = data_ptr is None
        if data_ptr is None:
            self._allocate(size)
        else:
            self._bind_external_memory(data_ptr)

    @property
    def data(self) -> Array[Any]:
        return self._data

    @property
    def data_ptr(self) -> int:
        return self._data_ptr

    @property
    def element_size(self) -> int:
        return self._element_size

    def _allocate(self, size: int) -> None:
        assert size % self._element_size == 0, (
            f"Buffer size {size} is not aligned to element size {self._element_size} "
            f"for data type '{self.data_type}'."
        )

        count = size // self._element_size
        self._data = (self._ctype * count)()
        self._data_ptr = ctypes.addressof(self._data)

    def _bind_external_memory(self, data_ptr: int) -> None:
        """Bind this store to an external memory region.

        The region is assumed to stay valid for the lifetime of the binding.
        The store creates a typed ctypes view over that pointer so normal
        ``get/set_region`` and ``get/set_bytes`` operations work without copying.

        Args:
            data_ptr:
                Integer pointer address for the externally managed memory block.
                The block must be large enough for ``self.size`` bytes.
        """
        assert data_ptr != 0, "External data pointer must be non-zero."
        assert self.size % self._element_size == 0, (
            f"Buffer size {self.size} is not aligned to element size {self._element_size} "
            f"for data type '{self.data_type}'."
        )

        self._data_ptr = data_ptr
        count = self.size // self._element_size
        if count > 0:
            self._data = (self._ctype * count).from_address(data_ptr)
        else:
            self._data = (self._ctype * 0)()

    def rebind_external(self, size: int, data_ptr: int) -> None:
        """Rebind this store to a new externally-owned memory region."""
        self.size = size
        self._owns_memory = False
        self._bind_external_memory(data_ptr)

    def _validate_byte_range(self, offset: int, length: int) -> None:
        assert offset >= 0 and length >= 0, "Offset and length must be non-negative."  # noqa: PT018
        assert offset + length <= self.size, (
            f"Byte range [{offset}, {offset + length}) exceeds store size {self.size}."
        )

    def get_bytes(self, offset: int = 0, length: int | None = None) -> bytes:
        if length is None:
            length = self.size - offset
        self._validate_byte_range(offset, length)
        return ctypes.string_at(self._data_ptr + offset, length)

    def set_bytes(self, offset: int, data: ByteSource) -> None:
        raw = bytes(data)
        self._validate_byte_range(offset, len(raw))
        ctypes.memmove(self._data_ptr + offset, raw, len(raw))

    def get_region(self, start: int, count: int) -> Array[Any]:
        byte_start = self.stride * start
        array_count = self.element_count * count
        ptr_type = ctypes.POINTER(self._ctype * array_count)
        return ctypes.cast(self._data_ptr + byte_start, ptr_type).contents

    def set_region(self, start: int, count: int, data: Sequence[float | int]) -> None:
        array_start = self.element_count * start
        array_end = self.element_count * count + array_start
        self._data[array_start:array_end] = data

    def copy_region(self, dst: int, src: int, count: int) -> None:
        if count <= 0 or dst == src:
            return
        byte_src = src * self.stride
        byte_dst = dst * self.stride
        byte_size = count * self.stride
        self._validate_byte_range(byte_src, byte_size)
        self._validate_byte_range(byte_dst, byte_size)
        ctypes.memmove(self._data_ptr + byte_dst, self._data_ptr + byte_src, byte_size)

    def resize(self, size: int) -> None:
        assert self._owns_memory, "Cannot resize an externally backed store. Use rebind_external instead."
        old_data = self._data
        old_size = self.size
        self.size = size
        self._allocate(size)
        ctypes.memmove(self._data, old_data, min(old_size, size))


class BackedBufferObject(AbstractBuffer):
    """A GPU buffer that keeps data on the host."""

    store: BufferDataStore
    stride: int
    element_count: int
    _data_element_size: int

    def __init__(self, size: int, store: BufferDataStore) -> None:
        # Initialize AbstractBuffer directly to avoid MRO conflicts with
        # backend classes that also derive from AbstractBuffer.
        AbstractBuffer.__init__(self, size)
        self.store = store
        self.stride = store.stride
        self.element_count = store.element_count
        self._data_element_size = store.element_size

    @property
    def data(self) -> Any:
        return self.store.data

    @property
    def data_ptr(self) -> int | None:
        return self.store.data_ptr

    @property
    def element_size(self) -> int:
        return self.store.element_size

    @abc.abstractmethod
    def commit(self) -> None:
        """Commits all saved changes to the underlying GPU buffer before drawing.

        Allows submitting multiple changes at once, rather than having to call glBufferSubData for every change.
        """

    @abc.abstractmethod
    def _mark_dirty_bytes(self, byte_start: int, byte_end: int) -> None:
        """Mark an absolute byte range as dirty in backend-specific tracking."""

    def get_bytes(self) -> bytes:
        return self.store.get_bytes()

    def get_bytes_region(self, offset: int, length: int) -> bytes:
        return self.store.get_bytes(offset, length)

    def set_bytes(self, data: ByteSource) -> None:
        raw = bytes(data)
        self.store.set_bytes(0, raw)
        self._mark_dirty_bytes(0, len(raw))

    def set_bytes_region(self, offset: int, data: ByteSource) -> None:
        raw = bytes(data)
        self.store.set_bytes(offset, raw)
        self._mark_dirty_bytes(offset, offset + len(raw))

    def get_region(self, start: int, count: int) -> Any:
        return self.store.get_region(start, count)

    def set_region(self, start: int, count: int, data: Sequence[float | int]) -> None:
        self.store.set_region(start, count, data)
        self.invalidate_region(start, count)

    def copy_region(self, dst: int, src: int, count: int) -> None:
        self.store.copy_region(dst, src, count)
        self.invalidate_region(dst, count)

    def resize_store(self, size: int) -> None:
        self.store.resize(size)
        self.size = size

    def set_data(self, data: DataSource) -> None:
        self.data[:] = data
        self._mark_dirty_bytes(0, self.size)

    def set_data_region(self, data: DataSource, start: int, length: int) -> None:
        array_start = start // self._data_element_size
        array_end = (start + length) // self._data_element_size
        self.data[array_start:array_end] = data
        self._mark_dirty_bytes(start, start + length)

    def set_data_ptr(self, offset: int, length: int, ptr: CTypesPointer) -> None:
        dst_ptr = self.store.data_ptr
        if dst_ptr is not None:
            ctypes.memmove(dst_ptr + offset, ptr, length)
            self._mark_dirty_bytes(offset, offset + length)
            return
        self.set_bytes_region(offset, ctypes.string_at(ptr, length))

    def invalidate(self) -> None:
        """Mark the entire store as dirty."""
        self._mark_dirty_bytes(0, self.size)

    def invalidate_region(self, start: int, count: int) -> None:
        """Mark a typed region as dirty."""
        byte_start = self.stride * start
        byte_end = byte_start + self.stride * count
        self._mark_dirty_bytes(byte_start, byte_end)


class AttributeBufferObject(BackedBufferObject):
    """A backed buffer used for shader attributes."""


class IndexedBufferObject(BackedBufferObject):
    """A backed buffer used for indices."""


class PersistentBufferObject(MappedBufferObject):
    """A persistently mapped GPU buffer.

    Available in OpenGL 4.3+ contexts. Persistently mapped buffers
    are mapped one time on creation, and can be updated at any time
    without the need to map or unmap.
    """


class IndexedBindingBuffer(AbstractBuffer):
    """Backend-agnostic role for buffers that support indexed binding points."""

    @abc.abstractmethod
    def bind_base(self, index: int) -> None:
        """Bind this buffer object to an indexed binding point."""

    @abc.abstractmethod
    def bind_range(self, index: int, offset: int, size: int) -> None:
        """Bind a byte range of this buffer object to an indexed binding point."""


class ShaderStorageBuffer(IndexedBindingBuffer):
    """Backend-agnostic shader storage buffer."""


class PixelBuffer(AbstractBuffer):
    """Backend-agnostic pixel transfer buffer."""


class PixelPackBuffer(PixelBuffer):
    """Backend-agnostic pixel pack buffer."""


class PixelUnpackBuffer(PixelBuffer):
    """Backend-agnostic pixel unpack buffer."""


class TransformFeedbackBuffer(IndexedBindingBuffer):
    """Backend-agnostic transform feedback buffer."""
    _data_type: DataTypes

    def __init__(self, size: int, *, data_type: DataTypes = "b") -> None:
        """Create a transform feedback buffer view.

        Args:
            size:
                The buffer size in bytes.
            data_type:
                Preferred format used by helper method :meth:`get_data`, defaults
                to ``"b"`` for bytes.
        """
        super().__init__(size)
        self._data_type = data_type

    def get_data(self) -> Array[Any]:
        """Read transform feedback data as the initialized ctypes array."""
        element_size = _data_type_size(self._data_type)
        assert self.size % element_size == 0, (
            f"Buffer size {self.size} is not aligned to element size {element_size} "
            f"for data type '{self._data_type}'."
        )

        c_type = _data_type_to_ctype(self._data_type)
        count = self.size // element_size
        raw = self.get_bytes()
        return (c_type * count).from_buffer_copy(raw)


class TextureBuffer(AbstractBuffer):
    """Backend-agnostic texture buffer."""


class DrawIndirectBuffer(AbstractBuffer):
    """Backend-agnostic draw indirect buffer."""
