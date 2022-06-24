# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# Copyright (c) 2008-2022 pyglet contributors
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

"""Byte abstractions of OpenGL Buffer Objects.

Use `create_buffer` to create a Buffer Object.

Buffers can optionally be created "mappable" (incorporating the
`AbstractMappable` mix-in).  In this case the buffer provides a ``get_region``
method which provides the most efficient path for updating partial data within
the buffer.
"""

import sys
import ctypes

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


class AbstractMappable:
    def get_region(self, start, size, ptr_type):
        """Map a region of the buffer into a ctypes array of the desired
        type.  This region does not need to be unmapped, but will become
        invalid if the buffer is resized.

        Note that although a pointer type is required, an array is mapped.
        For example::

            get_region(0, ctypes.sizeof(c_int) * 20, ctypes.POINTER(c_int * 20))

        will map bytes 0 to 80 of the buffer to an array of 20 ints.

        Changes to the array may not be recognised until the region's
        :py:meth:`AbstractBufferRegion.invalidate` method is called.

        :Parameters:
            `start` : int
                Offset into the buffer to map from, in bytes
            `size` : int
                Size of the buffer region to map, in bytes
            `ptr_type` : ctypes pointer type
                Pointer type describing the array format to create

        :rtype: :py:class:`AbstractBufferRegion`
        """
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
        ptr = ctypes.cast(glMapBuffer(GL_ARRAY_BUFFER, GL_WRITE_ONLY), ctypes.POINTER(ctypes.c_byte * self.size)).contents
        return ptr

    def map_range(self, start, size, ptr_type):
        glBindBuffer(GL_ARRAY_BUFFER, self.id)
        ptr = ctypes.cast(glMapBufferRange(GL_ARRAY_BUFFER, start, size, GL_MAP_WRITE_BIT), ptr_type).contents
        return ptr

    def unmap(self):
        glUnmapBuffer(GL_ARRAY_BUFFER)

    def __del__(self):
        try:
            if self.id is not None:
                self._context.delete_buffer(self.id)
        except:
            pass

    def delete(self):
        buffer_id = GLuint(self.id)
        try:
            glDeleteBuffers(1, buffer_id)
        except Exception:
            pass
        self.id = None

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


class MappableBufferObject(BufferObject, AbstractMappable):
    """A buffer with system-memory backed store.

    Updates to the data via `set_data`, `set_data_region` and `map` will be
    held in local memory until `bind` is called.  The advantage is that fewer
    OpenGL calls are needed, increasing performance.

    There may also be less performance penalty for resizing this buffer.

    Updates to data via :py:meth:`map` are committed immediately.
    """
    def __init__(self, size, usage=GL_DYNAMIC_DRAW):
        super(MappableBufferObject, self).__init__(size, usage)
        self.data = (ctypes.c_byte * size)()
        self.data_ptr = ctypes.addressof(self.data)
        self._dirty_min = sys.maxsize
        self._dirty_max = 0

    def bind(self):
        # Commit pending data
        super(MappableBufferObject, self).bind()
        size = self._dirty_max - self._dirty_min
        if size > 0:
            if size == self.size:
                glBufferData(GL_ARRAY_BUFFER, self.size, self.data, self.usage)
            else:
                glBufferSubData(GL_ARRAY_BUFFER, self._dirty_min, size, self.data_ptr + self._dirty_min)
            self._dirty_min = sys.maxsize
            self._dirty_max = 0

    def set_data(self, data):
        super(MappableBufferObject, self).set_data(data)
        ctypes.memmove(self.data, data, self.size)
        self._dirty_min = 0
        self._dirty_max = self.size

    def set_data_region(self, data, start, length):
        ctypes.memmove(self.data_ptr + start, data, length)
        self._dirty_min = min(start, self._dirty_min)
        self._dirty_max = max(start + length, self._dirty_max)

    def map(self, invalidate=False):
        self._dirty_min = 0
        self._dirty_max = self.size
        return self.data

    def unmap(self):
        pass

    def get_region(self, start, size, ptr_type):
        array = ctypes.cast(self.data_ptr + start, ptr_type).contents
        return BufferObjectRegion(self, start, start + size, array)

    def resize(self, size):
        data = (ctypes.c_byte * size)()
        ctypes.memmove(data, self.data, min(size, self.size))
        self.data = data
        self.data_ptr = ctypes.addressof(self.data)

        self.size = size

        glBindBuffer(GL_ARRAY_BUFFER, self.id)
        glBufferData(GL_ARRAY_BUFFER, self.size, self.data, self.usage)

        self._dirty_min = sys.maxsize
        self._dirty_max = 0


class BufferObjectRegion:
    """A mapped region of a MappableBufferObject."""

    __slots__ = 'buffer', 'start', 'end', 'array'

    def __init__(self, buffer, start, end, array):
        self.buffer = buffer
        self.start = start
        self.end = end
        self.array = array

    def invalidate(self):
        """Mark this region as changed.

        The buffer may not be updated with the latest contents of the
        array until this method is called.  (However, it may not be updated
        until the next time the buffer is used, for efficiency).
        """
        buffer = self.buffer
        buffer._dirty_min = min(buffer._dirty_min, self.start)
        buffer._dirty_max = max(buffer._dirty_max, self.end)
