"""Byte abstractions of OpenGL Buffer Objects.

Use `create_buffer` to create a Buffer Object.

Buffers can optionally be created "mappable" (incorporating the
`AbstractMappable` mix-in).  In this case the buffer provides a ``get_region``
method which provides the most efficient path for updating partial data within
the buffer.
"""

from __future__ import annotations

import abc
import ctypes
from abc import abstractmethod
from functools import lru_cache
from typing import Sequence, TYPE_CHECKING
from pyglet.graphics.shader import _data_type_to_ctype, GraphicsAttribute

if TYPE_CHECKING:
    from pyglet.customtypes import DataTypes, CType, CTypesPointer
    from pyglet.graphics.shader import Attribute


class AbstractBuffer(abc.ABC):
    c_type_size: int
    data_type: DataTypes
    c_type: CType
    size: int

    def __init__(self, data_type: DataTypes, size: int) -> None:
        """Create a buffer with the intended data type.

        Args:
            data_type:
                Data types.
            size:
                Array size of the buffer, based on the data_type.
        """
        self.data_type = data_type
        self.size = size

        self.c_type = _data_type_to_ctype[data_type]
        self.c_type_size = ctypes.sizeof(self.c_type)

    @classmethod
    def from_byte_size(cls, data_type: DataTypes, size: int) -> AbstractBuffer:
        c_type = _data_type_to_ctype[data_type]
        return cls(data_type, size // ctypes.sizeof(c_type))

    @abstractmethod
    def set_data_ptr(self, offset: int, length: int, ptr: CTypesPointer) -> None:
        """Copy data from ptr into the data_ptr at offset."""

    @abstractmethod
    def get_data(self) -> ctypes.Array[CType]:
        """Get the entire buffer contents."""

    @abstractmethod
    def get_data_region(self, start: int, length: int) -> ctypes.Array[CType]:
        """Get a range in the current buffer."""

    @abstractmethod
    def set_data(self, data: Sequence) -> None:
        """Set the entire buffer contents."""

    @abstractmethod
    def set_data_region(self, start: int, data: Sequence[float | int]) -> None:
        """Set part of the buffer contents."""

    @abstractmethod
    def get_bytes(self) -> bytes:
        """Return the entire buffer contents in bytes."""

    @abstractmethod
    def get_bytes_region(self, offset: int, length: int) -> bytes:
        """Return a region of the buffer contents based on bytes."""

    @abstractmethod
    def set_bytes(self, data: bytes) -> None:
        """Set the entire buffer data using bytes."""

    @abstractmethod
    def set_bytes_region(self, offset: int, data: bytes) -> None:
        """Set bytes at an offset in the buffer."""

    @abstractmethod
    def resize(self, size: int) -> None:
        """Resize the buffer to a new size."""

    @abstractmethod
    def delete(self) -> None:
        """Free memory or resources with the underlying buffer.

        The buffer should be unusable after this.
        """


class MappedBufferObjectBase(AbstractBuffer):
    """A buffer that requires being mapped before writing or reading data."""

    def get_region(self, start: int, count: int) -> ctypes.Array[CType]:
        ...

    @abc.abstractmethod
    def map(self) -> CTypesPointer[ctypes.c_ubyte]:
        """Map the entire buffer into system memory.

        The mapped region must be subsequently unmapped with `unmap` before
        performing any other operations on the buffer.

        Returns:
            Pointer to the mapped block in memory
        """

    @abc.abstractmethod
    def unmap(self) -> None:
        """Unmap a previously mapped memory block."""

    # @abc.abstractmethod
    # def map_region(self, start: int, size: int) -> CTypesPointer[ctypes.c_byte]:
    #     """Map the entire buffer into system memory.
    #
    #     The mapped region must be subsequently unmapped with `unmap` before
    #     performing any other operations on the buffer.
    #
    #     Returns:
    #         Pointer to the mapped block in memory
    #     """
    #
    # @abc.abstractmethod
    # def map_byte_region(self, offset: int, size: int) -> CTypesPointer[ctypes.c_byte]:
    #     """Map the entire buffer into system memory.
    #
    #     The mapped region must be subsequently unmapped with `unmap` before
    #     performing any other operations on the buffer.
    #
    #     Returns:
    #         Pointer to the mapped block in memory
    #     """

class BackedBufferObjectBase(AbstractBuffer):
    """A buffer with system-memory backed store.

    Updates to the data via `set_data` and `set_data_region` will be held
    in local memory until `buffer_data` is called.  The advantage is that
    fewer OpenGL calls are needed, which can increasing performance at the
    expense of system memory.
    """
    # A ctypes array of the specified data_type
    data: ctypes.Array[CType]

    # Memory address pointing to the CTypes data.
    data_ptr: int

    def __init__(self, data_type: DataTypes, size: int) -> None:
        super().__init__(data_type, size)
        self.data = (self.c_type * size)()
        self.data_ptr = ctypes.addressof(self.data)

    @abstractmethod
    def commit(self) -> None:
        """Commits all saved changes to the underlying buffer before drawing.

        Allows submitting multiple changes at once, rather than having to call glBufferSubData for every change.
        """

    def invalidate(self) -> None:
        ...

    def invalidate_region(self, start: int, count: int) -> None:
        ...


class AttributeBufferObject(BackedBufferObjectBase):
    """A backed buffer used for Shader Program attributes."""

    def __init__(self, size: int, shader_attr: GraphicsAttribute) -> None:  # noqa: D107
        # size is the allocator size * attribute.stride (buffer size)
        super().__init__(size, shader_attr.attribute.c_type, shader_attr.view.stride, shader_attr.attribute.fmt.components)


class IndexedBufferObject(BackedBufferObjectBase):
    """A backed buffer used for indices."""

    def __init__(self, size: int, c_type: CType, stride: int, count: int) -> None:
        super().__init__(size, c_type, stride, count)


class PersistentBufferObject(BackedBufferObjectBase):
    """A persistently mapped buffer.

    Available in OpenGL 4.3+ contexts. Persistently mapped buffers
    are mapped one time on creation, and can be updated at any time
    without the need to map or unmap.
    """

    def __init__(self, size, attribute, vao):
        ...

    def set_data(self, data: Sequence[int] | CTypesPointer) -> None:
        raise NotImplementedError("Not yet implemented")

    def set_data_region(self, data: Sequence[int] | CTypesPointer, start: int, length: int) -> None:
        raise NotImplementedError("Not yet implemented")

    def bind(self, target=None):
        ...

    def unbind(self):
        ...

    def map(self) -> CTypesPointer[ctypes.c_ubyte]:
        raise NotImplementedError("PersistentBufferObjects are always mapped.")

    def map_range(self, start, size, ptr_type, flags):
        raise NotImplementedError("PersistentBufferObjects are always mapped.")

    def unmap(self) -> None:
        raise NotImplementedError("PersistentBufferObjects cannot be unmapped.")

    def delete(self) -> None:
        ...

    @lru_cache(maxsize=None)
    def get_region(self, start, count):
        ...

    def set_region(self, start, count, data):
        ...

    def resize(self, size):
        ...

    def sub_data(self):
        # Not necessary with persistent mapping
        pass

    def invalidate(self):
        # Not necessary with persistent mapping
        pass

    def invalidate_region(self, start, count):
        # Not necessary with persistent mapping
        pass
