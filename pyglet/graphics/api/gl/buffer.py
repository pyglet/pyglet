"""OpenGL Buffer Objects.

:py:class:`~BufferObject` and a :py:class:`~BackedBufferObject` are provided.
The first is a lightweight abstraction over an OpenGL buffer, as created
with ``glGenBuffers``. The backed buffer object is similar, but provides a
full mirror of the data in CPU memory. This allows for delayed uploading of
changes to GPU memory, which can improve performance is some cases.
"""
from __future__ import annotations

import ctypes
import sys
from functools import lru_cache
from typing import TYPE_CHECKING, Sequence


from pyglet.graphics.api.gl import (
    GL_ARRAY_BUFFER,
    GL_DYNAMIC_DRAW,
    GL_ELEMENT_ARRAY_BUFFER,
    GL_MAP_COHERENT_BIT,
    GL_MAP_PERSISTENT_BIT,
    GL_MAP_READ_BIT,
    GL_MAP_WRITE_BIT,
    GL_WRITE_ONLY,
    GLubyte,
    GLuint,
    OpenGLSurfaceContext,
)
from pyglet.graphics.buffer import AbstractBuffer

if TYPE_CHECKING:
    from pyglet.customtypes import CType, CTypesPointer
    from pyglet.graphics.shader import Attribute, GraphicsAttribute
    from ctypes import Array, _SimpleCData

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
    usage: int
    target: int
    _context: OpenGLSurfaceContext | None

    def __init__(self, context: OpenGLSurfaceContext, size: int, target = GL_ARRAY_BUFFER, usage: int = GL_DYNAMIC_DRAW) -> None:
        """Initialize the BufferObject with the given size and draw usage.

        Buffer data is cleared on creation.
        """
        super().__init__('b', size)
        self.usage = usage
        self.target = target
        self._context = context

        buffer_id = GLuint()
        self._context.glGenBuffers(1, buffer_id)
        self.id = buffer_id.value

        self._context.glBindBuffer(self.target, self.id)
        data = (GLubyte * self.size)()
        self._context.glBufferData(self.target, self.size, data, self.usage)

    def get_bytes(self) -> bytes:
        self._context.glBindBuffer(self.target, self.id)
        ptr = self._context.glMapBufferRange(self.target, 0, self.size, GL_MAP_READ_BIT)
        data = ctypes.string_at(ptr, size=self.size)
        self._context.glUnmapBuffer(self.target)
        return data

    def get_bytes_region(self, offset: int, length: int) -> bytes:
        ...

    def get_data(self) -> ctypes.Array[CType]:
        self._context.glBindBuffer(self.target, self.id)
        ptr = self._context.glMapBufferRange(self.target, 0, self.size, GL_MAP_READ_BIT)
        data = ctypes.string_at(ptr, size=self.size)
        self._context.glUnmapBuffer(self.target)
        return data

    def get_data_region(self, start: int, length: int) -> ctypes.Array[CType]:
        ...

    def set_bytes(self, data: bytes) -> None:
        ...

    def set_bytes_region(self, start: int, length: int) -> None:
        ...

    def set_data_ptr(self, offset: int, length: int, ptr: CTypesPointer) -> None:
        ...

    def invalidate(self) -> None:
        self._context.glBufferData(self.target, self.size, None, self.usage)

    def bind(self) -> None:
        self._context.glBindBuffer(self.target, self.id)

    def unbind(self) -> None:
        self._context.glBindBuffer(self.target, 0)

    def set_data(self, data: Sequence[int] | CTypesPointer) -> None:
        self._context.glBindBuffer(self.target, self.id)
        self._context.glBufferData(self.target, self.size, data, self.usage)

    def set_data_region(self, data: Sequence[int] | CTypesPointer, start: int, length: int) -> None:
        self._context.glBindBuffer(self.target, self.id)
        self._context.glBufferSubData(self.target, start, length, data)

    def map(self, bits=GL_WRITE_ONLY) -> CTypesPointer[ctypes.c_byte]:
        self._context.glBindBuffer(self.target, self.id)
        return ctypes.cast(self._context.glMapBuffer(self.target, bits),
                           ctypes.POINTER(ctypes.c_byte * self.size)).contents

    def map_range(self, start: int, size: int, ptr_type: type[CTypesPointer], bits=GL_MAP_WRITE_BIT) -> CTypesPointer:
        self._context.glBindBuffer(self.target, self.id)
        return ctypes.cast(self._context.glMapBufferRange(self.target, start, size, bits), ptr_type).contents

    def unmap(self) -> None:
        self._context.glUnmapBuffer(self.target)

    def delete(self) -> None:
        self._context.glDeleteBuffers(1, GLuint(self.id))
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

        self._context.glBindBuffer(self.target, self.id)
        data = self._context.glMapBufferRange(self.target, 0, self.size, GL_MAP_READ_BIT)
        ctypes.memmove(temp, data, min(size, self.size))
        self._context.glUnmapBuffer(self.target)

        self.size = size
        self._context.glBufferData(self.target, self.size, temp, self.usage)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, data_type={self.data_type}, size={self.size})"


class BackedBufferObject(BufferObject):
    """A buffer with system-memory backed store.

    Updates to the data via ``set_data`` and ``set_data_region`` will be held
    in system memory until ``commit`` is called.  The advantage is that fewer
    OpenGL calls are needed, which can increase performance at the expense of
    system memory.
    """
    data: Array[CType] | Array[_SimpleCData]
    data_ptr: int
    _dirty_min: int
    _dirty_max: int
    _dirty: bool
    stride: int
    element_count: int
    ctype: CType

    def __init__(self, context: OpenGLSurfaceContext, size: int, c_type: CType, stride: int, element_count: int,
                 usage: int = GL_DYNAMIC_DRAW) -> None:
        super().__init__(context, size, GL_ARRAY_BUFFER, usage)

        self.c_type = c_type
        self._ctypes_size = ctypes.sizeof(c_type)
        number = size // self._ctypes_size
        self.data = (c_type * number)()
        self.data_ptr = ctypes.addressof(self.data)

        self._dirty_min = sys.maxsize
        self._dirty_max = 0
        self._dirty = False

        self.stride = stride
        self.element_count = element_count

    def commit(self) -> None:
        """Commits all saved changes to the underlying buffer before drawing.

        Allows submitting multiple changes at once, rather than having to call glBufferSubData for every change.
        """
        if not self._dirty:
            return

        self._context.glBindBuffer(self.target, self.id)
        size = self._dirty_max - self._dirty_min
        if size > 0:
            if size == self.size:
                self._context.glBufferData(self.target, self.size, self.data, self.usage)
            else:
                self._context.glBufferSubData(self.target, self._dirty_min, size, self.data_ptr + self._dirty_min)

            self._dirty_min = sys.maxsize
            self._dirty_max = 0
            self._dirty = False

    @lru_cache(maxsize=None)  # noqa: B019
    def get_region(self, start: int, count: int) -> Array[CType]:
        byte_start = self.stride * start  # byte offset
        array_count = self.element_count * count  # number of values
        ptr_type = ctypes.POINTER(self.c_type * array_count)
        return ctypes.cast(self.data_ptr + byte_start, ptr_type).contents

    def set_region(self, start: int, count: int, data: Sequence[float]) -> None:
        array_start = self.element_count * start
        array_end = self.element_count * count + array_start

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

    def __init__(self, context: OpenGLSurfaceContext, size: int, graphics_attr: GraphicsAttribute) -> None:
        # size is the allocator size * attribute.stride (buffer size)
        super().__init__(context, size, graphics_attr.attribute.c_type,
                         graphics_attr.view.stride,
                         graphics_attr.attribute.fmt.components)


class IndexedBufferObject(BackedBufferObject):
    """A backed buffer used for indices."""

    def __init__(self, context: OpenGLSurfaceContext, size: int, c_type: CType, stride: int, count: int,
                 usage: int = GL_DYNAMIC_DRAW) -> None:
        super().__init__(context, size, c_type, stride, count, usage)

    def bind_to_index_buffer(self) -> None:
        """Binds this buffer as an index buffer on the active vertex array."""
        self._context.glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.id)


class PersistentBufferObject(AbstractBuffer):
    """A persistently mapped buffer.

    Available in OpenGL 4.3+ contexts. Persistently mapped buffers
    are mapped one time on creation, and can be updated at any time
    without the need to map or unmap.
    """

    def __init__(self, context, size, attribute, vao):
        # TODO: Persistent buffers cannot be resized. A new buffer is created, and the
        #       data is copied over. Therefore, unlike other buffers, they currently
        #       require s reference to an attribute so the attribute pointer can be reset
        #       on resize calls. This can be reevaluated for a better solution.

        self.size = size
        self.attribute = attribute
        self.attribute_stride = attribute.stride
        self.attribute_count = attribute.element_count
        self.attribute_ctype = attribute.c_type
        self.vao = vao

        self._context = context

        buffer_id = GLuint()
        self._context.glGenBuffers(1, buffer_id)
        self.id = buffer_id.value
        self._context.glBindBuffer(GL_ARRAY_BUFFER, self.id)

        self.flags = GL_MAP_WRITE_BIT | GL_MAP_PERSISTENT_BIT | GL_MAP_COHERENT_BIT
        data = (GLubyte * size)()
        self._context.glBufferStorage(GL_ARRAY_BUFFER, size, data, self.flags)

        # size is the allocator size * attribute.stride
        number = size // attribute.element_size
        ptr = ctypes.POINTER(attribute.c_type * number)
        self.data = ctypes.cast(self._context.glMapBufferRange(GL_ARRAY_BUFFER, 0, size, self.flags), ptr).contents

    def set_data(self, data: Sequence[int] | CTypesPointer) -> None:
        raise NotImplementedError("Not yet implemented")

    def set_data_region(self, data: Sequence[int] | CTypesPointer, start: int, length: int) -> None:
        raise NotImplementedError("Not yet implemented")

    def bind(self, target=GL_ARRAY_BUFFER):
        self._context.glBindBuffer(target, self.id)

    def unbind(self):
        self._context.glBindBuffer(GL_ARRAY_BUFFER, 0)

    def map(self) -> CTypesPointer[ctypes.c_ubyte]:
        raise NotImplementedError("PersistentBufferObjects are always mapped.")

    def map_range(self, start, size, ptr_type, flags=GL_MAP_WRITE_BIT):
        raise NotImplementedError("PersistentBufferObjects are always mapped.")

    def unmap(self) -> None:
        raise NotImplementedError("PersistentBufferObjects cannot be unmapped.")

    def delete(self) -> None:
        self._context.glDeleteBuffers(1, GLuint(self.id))
        self.id = None

    @lru_cache(maxsize=None)
    def get_region(self, start, count):
        byte_start = self.attribute_stride * start  # byte offset
        array_count = self.attribute_count * count  # number of values

        ptr_type = ctypes.POINTER(self.attribute_ctype * array_count)
        return ctypes.cast(ctypes.addressof(self.data) + byte_start, ptr_type).contents

    def set_region(self, start, count, data):
        array_start = self.attribute_count * start
        array_end = self.attribute_count * count + array_start
        self.data[array_start:array_end] = data

    def resize(self, size):
        # Create temporary copy of current data
        temp = (GLubyte * size)()
        ctypes.memmove(temp, self.data, min(size, self.size))
        self._context.glDeleteBuffers(1, GLuint(self.id))

        # Generate new buffer
        buffer_id = GLuint()
        self._context.glGenBuffers(1, buffer_id)
        self.id = buffer_id.value

        # Link attributes to new buffer:
        self.vao.bind()
        self.bind()
        self.attribute.enable()
        self.attribute.set_pointer(self.ptr)

        # Initialize the new buffer with the old data, and map it:
        self._context.glBufferStorage(GL_ARRAY_BUFFER, size, temp, self.flags)

        ptr_type = self.attribute.c_type * (size // self.attribute.element_size)
        self.data = self.map_range(0, size, ctypes.POINTER(ptr_type), self.flags)

        self.size = size
        self.get_region.cache_clear()

    def sub_data(self):
        # Not necessary with persistent mapping
        pass

    def invalidate(self):
        # Not necessary with persistent mapping
        pass

    def invalidate_region(self, start, count):
        # Not necessary with persistent mapping
        pass
