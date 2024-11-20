"""OpenGL Buffer Objects.

:py:class:`~BufferObject` and a :py:class:`~BackedBufferObject` are provied.
The first is a lightweight abstraction over an OpenGL buffer, as created
with ``glGenBuffers``. The backed buffer object is similar, but provides a
full mirror of the data in CPU memory. This allows for delayed uploading of
changes to GPU memory, which can improve performance is some cases.
"""
from __future__ import annotations

import abc
import ctypes
import sys
from functools import lru_cache
from typing import TYPE_CHECKING, Sequence, Type

from _ctypes import Array, _Pointer, _SimpleCData

import pyglet
from pyglet.gl.gl import (
    GL_ARRAY_BUFFER,
    GL_DYNAMIC_DRAW,
    GL_ELEMENT_ARRAY_BUFFER,
    GL_MAP_READ_BIT,
    GL_MAP_WRITE_BIT,
    GL_WRITE_ONLY,
    GLubyte,
    GLuint,
    glBindBuffer,
    glBufferData,
    glBufferSubData,
    glDeleteBuffers,
    glGenBuffers,
    glMapBuffer,
    glMapBufferRange,
    glUnmapBuffer,
)

if TYPE_CHECKING:
    from pyglet.gl import Context
    from pyglet.graphics.shader import Attribute

CTypesDataType = Type[_SimpleCData]
CTypesPointer = _Pointer


class AbstractBuffer:
    """Abstract buffer of byte data.

    Attributes:
        size:
            Size of buffer, in bytes
        ptr:
            Memory offset of the buffer, as used by the ``glVertexPointer`` family of functions
    """

    ptr: int = 0
    size: int = 0

    @abc.abstractmethod
    def bind(self, target: int = GL_ARRAY_BUFFER) -> None:
        """Bind this buffer to an OpenGL target."""

    @abc.abstractmethod
    def unbind(self) -> None:
        """Reset the buffer's OpenGL target."""

    @abc.abstractmethod
    def set_data(self, data: Sequence[int] | CTypesPointer) -> None:
        """Set the entire contents of the buffer.

        Args:
            data:
                The byte array to set.

        """

    @abc.abstractmethod
    def set_data_region(self, data: Sequence[int] | CTypesPointer, start: int, length: int) -> None:
        """Set part of the buffer contents.

        Args:
            data:
                The byte array of data to set
            start:
                Offset to start replacing data
            length:
                Length of region to replace

        """

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

    def resize(self, size: int) -> None:
        """Resize the buffer to a new size.

        Args:
            size:
                New size of the buffer, in bytes

        """

    @abc.abstractmethod
    def delete(self) -> None:
        """Delete this buffer, reducing system resource usage."""


class BufferObject(AbstractBuffer):
    """Lightweight representation of an OpenGL Buffer Object.

    The data in the buffer is not replicated in any system memory (unless it
    is done so by the video driver).  While this can reduce system memory usage,
    performing multiple small updates to the buffer can be relatively slow.
    The target of the buffer is ``GL_ARRAY_BUFFER`` internally to avoid
    accidentally overriding other states when altering the buffer contents.
    The intended target can be set when binding the buffer.
    """

    id: int
    size: int
    usage: int
    _context: Context | None

    def __init__(self, size: int, usage: int = GL_DYNAMIC_DRAW) -> None:
        """Initialize the BufferObject with the given size and draw usage.

        Buffer data is cleared on creation.
        """
        self.size = size
        self.usage = usage
        self._context = pyglet.gl.current_context

        buffer_id = GLuint()
        glGenBuffers(1, buffer_id)
        self.id = buffer_id.value

        glBindBuffer(GL_ARRAY_BUFFER, self.id)
        data = (GLubyte * self.size)()
        glBufferData(GL_ARRAY_BUFFER, self.size, data, self.usage)

    def invalidate(self) -> None:
        glBufferData(GL_ARRAY_BUFFER, self.size, None, self.usage)

    def bind(self, target: int = GL_ARRAY_BUFFER) -> None:
        glBindBuffer(target, self.id)

    def unbind(self) -> None:
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def bind_to_index_buffer(self) -> None:
        """Binds this buffer as an index buffer on the active vertex array."""
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.id)

    def set_data(self, data: Sequence[int] | CTypesPointer) -> None:
        glBindBuffer(GL_ARRAY_BUFFER, self.id)
        glBufferData(GL_ARRAY_BUFFER, self.size, data, self.usage)

    def set_data_region(self, data: Sequence[int] | CTypesPointer, start: int, length: int) -> None:
        glBindBuffer(GL_ARRAY_BUFFER, self.id)
        glBufferSubData(GL_ARRAY_BUFFER, start, length, data)

    def map(self) -> CTypesPointer[ctypes.c_byte]:
        glBindBuffer(GL_ARRAY_BUFFER, self.id)
        return ctypes.cast(glMapBuffer(GL_ARRAY_BUFFER, GL_WRITE_ONLY),
                           ctypes.POINTER(ctypes.c_byte * self.size)).contents

    def map_range(self, start: int, size: int, ptr_type: type[CTypesPointer]) -> CTypesPointer:
        glBindBuffer(GL_ARRAY_BUFFER, self.id)
        return ctypes.cast(glMapBufferRange(GL_ARRAY_BUFFER, start, size, GL_MAP_WRITE_BIT), ptr_type).contents

    def unmap(self) -> None:
        glUnmapBuffer(GL_ARRAY_BUFFER)

    def delete(self) -> None:
        glDeleteBuffers(1, GLuint(self.id))
        self.id = None

    def __del__(self) -> None:
        if self.id is not None:
            try:
                self._context.delete_buffer(self.id)
                self.id = None
            except (AttributeError, ImportError):
                pass  # Interpreter is shutting down

    def resize(self, size: int) -> None:
        # Map, create a copy, then reinitialize.
        temp = (ctypes.c_byte * size)()

        glBindBuffer(GL_ARRAY_BUFFER, self.id)
        data = glMapBufferRange(GL_ARRAY_BUFFER, 0, self.size, GL_MAP_READ_BIT)
        ctypes.memmove(temp, data, min(size, self.size))
        glUnmapBuffer(GL_ARRAY_BUFFER)

        self.size = size
        glBufferData(GL_ARRAY_BUFFER, self.size, temp, self.usage)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, size={self.size})"


class BackedBufferObject(BufferObject):
    """A buffer with system-memory backed store.

    Updates to the data via ``set_data`` and ``set_data_region`` will be held
    in system memory until ``commit`` is called.  The advantage is that fewer
    OpenGL calls are needed, which can increase performance at the expense of
    system memory.
    """
    data: CTypesDataType
    data_ptr: int
    _dirty_min: int
    _dirty_max: int
    _dirty: bool
    stride: int
    count: int
    ctype: CTypesDataType

    def __init__(self, size: int, c_type: CTypesDataType, stride: int, count: int,  # noqa: D107
                 usage: int = GL_DYNAMIC_DRAW) -> None:
        super().__init__(size, usage)

        self.c_type = c_type
        self._ctypes_size = ctypes.sizeof(c_type)
        number = size // self._ctypes_size
        self.data = (c_type * number)()
        self.data_ptr = ctypes.addressof(self.data)

        self._dirty_min = sys.maxsize
        self._dirty_max = 0
        self._dirty = False

        self.stride = stride
        self.count = count

    def commit(self) -> None:
        """Commits all saved changes to the underlying buffer before drawing.

        Allows submitting multiple changes at once, rather than having to call glBufferSubData for every change.
        """
        if not self._dirty:
            return

        glBindBuffer(GL_ARRAY_BUFFER, self.id)
        size = self._dirty_max - self._dirty_min
        if size > 0:
            if size == self.size:
                glBufferData(GL_ARRAY_BUFFER, self.size, self.data, self.usage)
            else:
                glBufferSubData(GL_ARRAY_BUFFER, self._dirty_min, size, self.data_ptr + self._dirty_min)

            self._dirty_min = sys.maxsize
            self._dirty_max = 0
            self._dirty = False

    @lru_cache(maxsize=None)  # noqa: B019
    def get_region(self, start: int, count: int) -> Array[CTypesDataType]:
        byte_start = self.stride * start  # byte offset
        array_count = self.count * count  # number of values
        ptr_type = ctypes.POINTER(self.c_type * array_count)
        return ctypes.cast(self.data_ptr + byte_start, ptr_type).contents

    def set_region(self, start: int, count: int, data: Sequence[float]) -> None:
        array_start = self.count * start
        array_end = self.count * count + array_start

        self.data[array_start:array_end] = data

        # replicated from self.invalidate_region
        byte_start = self.stride * start
        byte_end = byte_start + self.stride * count
        # As of Python 3.11, this is faster than min/max:
        if byte_start < self._dirty_min:
            self._dirty_min = byte_start
        if byte_end > self._dirty_max:
            self._dirty_max = byte_end
        self._dirty = True

    def resize(self, size: int) -> None:
        # size is the allocator size * attribute.stride
        number = size // ctypes.sizeof(self.c_type)
        data = (self.c_type * number)()
        ctypes.memmove(data, self.data, min(size, self.size))
        self.data = data
        self.data_ptr = ctypes.addressof(data)
        self.size = size

        # Set the dirty range to be the entire buffer.
        self._dirty_min = 0
        self._dirty_max = self.size
        self._dirty = True

        self.get_region.cache_clear()

    def invalidate(self) -> None:
        super().invalidate()
        self._dirty = True

    def invalidate_region(self, start: int, count: int) -> None:
        byte_start = self.stride * start
        byte_end = byte_start + self.stride * count
        # As of Python 3.11, this is faster than min/max:
        if byte_start < self._dirty_min:
            self._dirty_min = byte_start
        if byte_end > self._dirty_max:
            self._dirty_max = byte_end
        self._dirty = True


class AttributeBufferObject(BackedBufferObject):
    """A backed buffer used for Shader Program attributes."""

    def __init__(self, size: int, attribute: Attribute) -> None:  # noqa: D107
        # size is the allocator size * attribute.stride (buffer size)
        super().__init__(size, attribute.c_type, attribute.stride, attribute.count)


class IndexedBufferObject(BackedBufferObject):
    """A backed buffer used for indices."""

    def __init__(self, size: int, c_type: CTypesDataType, stride: int, count: int,  # noqa: D107
                 usage: int = GL_DYNAMIC_DRAW) -> None:
        super().__init__(size, c_type, stride, count, usage)
