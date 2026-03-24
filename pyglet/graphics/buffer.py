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
from ctypes import Array
from typing import TYPE_CHECKING, Any, Sequence, Union

import pyglet

if TYPE_CHECKING:
    from pyglet.customtypes import CType, CTypesPointer


ByteSource = Union[bytes, bytearray, memoryview]
DataSource = Union[Sequence[Union[float, int]], Array[Any]]


def _to_bytes(data: ByteSource | Sequence[int] | CTypesPointer, length: int | None = None) -> bytes:
    """Convert supported host-side inputs into raw bytes."""
    if isinstance(data, (bytes, bytearray, memoryview)):
        raw = bytes(data)
        if length is None:
            return raw
        assert len(raw) >= length, f"Insufficient data length. Expected at least {length} bytes, got {len(raw)}."
        return raw[:length]

    if isinstance(data, ctypes.Array):
        raw = bytes(data)
        if length is None:
            return raw
        assert len(raw) >= length, f"Insufficient data length. Expected at least {length} bytes, got {len(raw)}."
        return raw[:length]

    # ctypes pointer-like objects (e.g. pointer(struct), POINTER(c_ubyte), etc.)
    if hasattr(data, "contents"):
        size = length if length is not None else ctypes.sizeof(data.contents)
        return ctypes.string_at(data, size)

    try:
        raw = bytes(data)
    except TypeError as exc:
        msg = (
            f"Unsupported data type: {type(data)!r}. "
            "Use bytes-like objects, ctypes arrays, ctypes pointers, or integer sequences."
        )
        raise AssertionError(msg) from exc

    if length is None:
        return raw
    assert len(raw) >= length, f"Insufficient data length. Expected at least {length} bytes, got {len(raw)}."
    return raw[:length]


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
        self.set_bytes_region(start, _to_bytes(data, length))

    def set_data_ptr(self, offset: int, length: int, ptr: CTypesPointer) -> None:
        """Compatibility helper for callers that pass a ctypes pointer."""
        self.set_bytes_region(offset, ctypes.string_at(ptr, length))


class UniformBufferObject:
    """Backend-agnostic Uniform Buffer Object wrapper."""

    buffer: AbstractBuffer
    view: ctypes.Structure
    _view_ptr: Any
    binding: int
    __slots__ = "_view_ptr", "binding", "buffer", "view"

    def __init__(self, context: Any, view_class: type[ctypes.Structure], buffer_size: int, binding: int) -> None:
        self.buffer = self._create_buffer(context, buffer_size)
        self.view = view_class()
        self._view_ptr = ctypes.pointer(self.view)
        self.binding = binding

    @property
    def id(self) -> int:
        """The buffer ID associated with this UBO."""
        return self.buffer.id

    def read(self) -> bytes:
        """Read the byte contents of the buffer."""
        return self.buffer.get_data()

    def __enter__(self) -> ctypes.Structure:
        return self.view

    def __exit__(self, _exc_type, _exc_val, _exc_tb) -> None:  # noqa: ANN001
        self.buffer.set_data(self._view_ptr)

    @abc.abstractmethod
    def _create_buffer(self, context: Any, buffer_size: int) -> AbstractBuffer:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.buffer.id}, binding={self.binding})"


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

    c_type: CType
    _ctypes_size: int
    _data: Any
    _data_ptr: int

    def __init__(self, size: int, c_type: CType, stride: int, element_count: int) -> None:
        self.c_type = c_type
        self._ctypes_size = ctypes.sizeof(c_type)
        self.stride = stride
        self.element_count = element_count
        self.size = size
        self._allocate(size)

    @property
    def data(self) -> Array[Any]:
        return self._data

    @property
    def data_ptr(self) -> int:
        return self._data_ptr

    @property
    def element_size(self) -> int:
        return self._ctypes_size

    def _allocate(self, size: int) -> None:
        assert size % self._ctypes_size == 0, (
            f"Buffer size {size} is not aligned to ctype size {self._ctypes_size} "
            f"for {self.c_type}."
        )

        count = size // self._ctypes_size
        self._data = (self.c_type * count)()
        self._data_ptr = ctypes.addressof(self._data)

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
        ptr_type = ctypes.POINTER(self.c_type * array_count)
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


class TextureBuffer(AbstractBuffer):
    """Backend-agnostic texture buffer."""


class DrawIndirectBuffer(AbstractBuffer):
    """Backend-agnostic draw indirect buffer."""
