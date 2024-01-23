"""Byte abstractions of OpenGL Buffer Objects.

Use `create_buffer` to create a Buffer Object.

Buffers can optionally be created "mappable" (incorporating the
`AbstractMappable` mix-in).  In this case the buffer provides a ``get_region``
method which provides the most efficient path for updating partial data within
the buffer.
"""

import sys
import ctypes

from functools import lru_cache

import pyglet
from pyglet.gl import *


class AbstractBuffer:
    """Abstract buffer of byte data.

    :Ivariables:
        `size` : int
            Size of buffer, in bytes
        `ptr` : int
            Memory offset of the buffer, as used by the ``glVertexPointer``
            family of functions
        `usage` : int
            OpenGL buffer usage, for example ``GL_DYNAMIC_DRAW``

    """

    ptr = 0
    size = 0

    def bind(self, target=GL_ARRAY_BUFFER):
        """Bind this buffer to an OpenGL target."""
        raise NotImplementedError('abstract')

    def unbind(self):
        """Reset the buffer's OpenGL target."""
        raise NotImplementedError('abstract')

    def set_data(self, data):
        """Set the entire contents of the buffer.

        :Parameters:
            `data` : sequence of int or ctypes pointer
                The byte array to set.

        """
        raise NotImplementedError('abstract')

    def set_data_region(self, data, start, length):
        """Set part of the buffer contents.

        :Parameters:
            `data` : sequence of int or ctypes pointer
                The byte array of data to set
            `start` : int
                Offset to start replacing data
            `length` : int
                Length of region to replace

        """
        raise NotImplementedError('abstract')

    def map(self):
        """Map the entire buffer into system memory.

        The mapped region must be subsequently unmapped with `unmap` before
        performing any other operations on the buffer.

        :Parameters:
            `invalidate` : bool
                If True, the initial contents of the mapped block need not
                reflect the actual contents of the buffer.

        :rtype: ``POINTER(ctypes.c_ubyte)``
        :return: Pointer to the mapped block in memory
        """
        raise NotImplementedError('abstract')

    def unmap(self):
        """Unmap a previously mapped memory block."""
        raise NotImplementedError('abstract')

    def resize(self, size):
        """Resize the buffer to a new size.

        :Parameters:
            `size` : int
                New size of the buffer, in bytes

        """

    def delete(self):
        """Delete this buffer, reducing system resource usage."""
        raise NotImplementedError('abstract')


class BufferObject(AbstractBuffer):
    """Lightweight representation of an OpenGL Buffer Object.

    The data in the buffer is not replicated in any system memory (unless it
    is done so by the video driver).  While this can improve memory usage and
    possibly performance, updates to the buffer are relatively slow.
    The target of the buffer is ``GL_ARRAY_BUFFER`` internally to avoid
    accidentally overriding other states when altering the buffer contents.
    The intended target can be set when binding the buffer.

    This class does not implement :py:class:`AbstractMappable`, and so has no
    :py:meth:`~AbstractMappable.get_region` method.  See 
    :py:class:`MappableVertexBufferObject` for a Buffer class
    that does implement :py:meth:`~AbstractMappable.get_region`.
    """

    def __init__(self, size, usage=GL_DYNAMIC_DRAW):
        self.size = size
        self.usage = usage
        self._context = pyglet.gl.current_context

        buffer_id = GLuint()
        glGenBuffers(1, buffer_id)
        self.id = buffer_id.value

        glBindBuffer(GL_ARRAY_BUFFER, self.id)
        data = (GLubyte * self.size)()
        glBufferData(GL_ARRAY_BUFFER, self.size, data, self.usage)

    def invalidate(self):
        glBufferData(GL_ARRAY_BUFFER, self.size, None, self.usage)

    def bind(self, target=GL_ARRAY_BUFFER):
        glBindBuffer(target, self.id)

    def unbind(self):
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def bind_to_index_buffer(self):
        """Binds this buffer as an index buffer on the active vertex array."""
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.id)

    def set_data(self, data):
        glBindBuffer(GL_ARRAY_BUFFER, self.id)
        glBufferData(GL_ARRAY_BUFFER, self.size, data, self.usage)

    def set_data_region(self, data, start, length):
        glBindBuffer(GL_ARRAY_BUFFER, self.id)
        glBufferSubData(GL_ARRAY_BUFFER, start, length, data)

    def map(self):
        glBindBuffer(GL_ARRAY_BUFFER, self.id)
        ptr = ctypes.cast(glMapBuffer(GL_ARRAY_BUFFER, GL_WRITE_ONLY),
                          ctypes.POINTER(ctypes.c_byte * self.size)).contents
        return ptr

    def map_range(self, start, size, ptr_type):
        glBindBuffer(GL_ARRAY_BUFFER, self.id)
        ptr = ctypes.cast(glMapBufferRange(GL_ARRAY_BUFFER, start, size, GL_MAP_WRITE_BIT), ptr_type).contents
        return ptr

    def unmap(self):
        glUnmapBuffer(GL_ARRAY_BUFFER)

    def delete(self):
        glDeleteBuffers(1, GLuint(self.id))
        self.id = None

    def __del__(self):
        if self.id is not None:
            try:
                self._context.delete_buffer(self.id)
                self.id = None
            except (AttributeError, ImportError):
                pass  # Interpreter is shutting down

    def resize(self, size):
        # Map, create a copy, then reinitialize.
        temp = (ctypes.c_byte * size)()

        glBindBuffer(GL_ARRAY_BUFFER, self.id)
        data = glMapBufferRange(GL_ARRAY_BUFFER, 0, self.size, GL_MAP_READ_BIT)
        ctypes.memmove(temp, data, min(size, self.size))
        glUnmapBuffer(GL_ARRAY_BUFFER)

        self.size = size
        glBufferData(GL_ARRAY_BUFFER, self.size, temp, self.usage)

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, size={self.size})"


class AttributeBufferObject(BufferObject):
    """A buffer with system-memory backed store.

    Updates to the data via `set_data` and `set_data_region` will be held
    in local memory until `buffer_data` is called.  The advantage is that
    fewer OpenGL calls are needed, which can increasing performance at the
    expense of system memory.
    """

    def __init__(self, size, attribute, usage=GL_DYNAMIC_DRAW):
        # size is the allocator size * attribute.stride
        super().__init__(size, usage)
        number = size // attribute.element_size
        self.data = (attribute.c_type * number)()
        self.data_ptr = ctypes.addressof(self.data)

        self._dirty_min = sys.maxsize
        self._dirty_max = 0
        self._dirty = False

        self.attribute_stride = attribute.stride
        self.attribute_count = attribute.count
        self.attribute_ctype = attribute.c_type

    def sub_data(self):
        """Updates the buffer if any data has been changed or invalidated. Allows submitting multiple changes at once,
        rather than having to call glBufferSubData for every change."""
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

    @lru_cache(maxsize=None)
    def get_region(self, start, count):
        byte_start = self.attribute_stride * start  # byte offset
        array_count = self.attribute_count * count  # number of values
        ptr_type = ctypes.POINTER(self.attribute_ctype * array_count)
        return ctypes.cast(self.data_ptr + byte_start, ptr_type).contents

    def set_region(self, start, count, data):
        array_start = self.attribute_count * start
        array_end = self.attribute_count * count + array_start

        self.data[array_start:array_end] = data

        # replicated from self.invalidate_region
        byte_start = self.attribute_stride * start
        byte_end = byte_start + self.attribute_stride * count
        # As of Python 3.11, this is faster than min/max:
        if byte_start < self._dirty_min:
            self._dirty_min = byte_start
        if byte_end > self._dirty_max:
            self._dirty_max = byte_end
        self._dirty = True

    def resize(self, size):
        # size is the allocator size * attribute.stride
        number = size // ctypes.sizeof(self.attribute_ctype)
        data = (self.attribute_ctype * number)()
        ctypes.memmove(data, self.data, min(size, self.size))
        self.data = data
        self.data_ptr = ctypes.addressof(data)
        self.size = size

        glBindBuffer(GL_ARRAY_BUFFER, self.id)
        glBufferData(GL_ARRAY_BUFFER, self.size, self.data, self.usage)

        self._dirty_min = sys.maxsize
        self._dirty_max = 0
        self._dirty = False

        self.get_region.cache_clear()

    def invalidate(self):
        super().invalidate()
        self._dirty = True

    def invalidate_region(self, start, count):
        byte_start = self.attribute_stride * start
        byte_end = byte_start + self.attribute_stride * count
        # As of Python 3.11, this is faster than min/max:
        if byte_start < self._dirty_min:
            self._dirty_min = byte_start
        if byte_end > self._dirty_max:
            self._dirty_max = byte_end
        self._dirty = True
