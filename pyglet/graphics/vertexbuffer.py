# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# Copyright (c) 2008-2021 pyglet contributors
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


def create_buffer(size, target=GL_ARRAY_BUFFER, usage=GL_DYNAMIC_DRAW, mappable=True):
    """Create a buffer object for vertex or other data.

    :Parameters:
        `size` : int
            Size of the buffer, in bytes
        `target` : int
            OpenGL target buffer (defaults to GL_ARRAY_BUFFER)
        `usage` : int
            OpenGL usage constant (defaults to GL_DYNAMIC_DRAW)
        `mappable` : bool
            True to create a mappable buffer (defaults to True)

    :rtype: `AbstractBuffer` or `AbstractBuffer` with `AbstractMappable`
    """
    if mappable:
        return MappableBufferObject(size, target, usage)
    else:
        return BufferObject(size, target, usage)


class AbstractBuffer:
    """Abstract buffer of byte data.

    :Ivariables:
        `size` : int
            Size of buffer, in bytes
        `ptr` : int
            Memory offset of the buffer, as used by the ``glVertexPointer``
            family of functions
        `target` : int
            OpenGL buffer target, for example ``GL_ARRAY_BUFFER``
        `usage` : int
            OpenGL buffer usage, for example ``GL_DYNAMIC_DRAW``

    """

    ptr = 0
    size = 0

    def bind(self):
        """Bind this buffer to its OpenGL target."""
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

    def map(self, invalidate=False):
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

    This class does not implement :py:class:`AbstractMappable`, and so has no
    :py:meth:`~AbstractMappable.get_region` method.  See 
    :py:class:`MappableVertexBufferObject` for a Buffer class
    that does implement :py:meth:`~AbstractMappable.get_region`.
    """

    def __init__(self, size, target, usage):
        self.size = size
        self.target = target
        self.usage = usage
        self._context = pyglet.gl.current_context

        buffer_id = GLuint()
        glGenBuffers(1, buffer_id)
        self.id = buffer_id.value

        glBindBuffer(target, self.id)
        glBufferData(target, self.size, None, self.usage)

    def bind(self):
        glBindBuffer(self.target, self.id)

    def unbind(self):
        glBindBuffer(self.target, 0)

    def set_data(self, data):
        glBindBuffer(self.target, self.id)
        glBufferData(self.target, self.size, data, self.usage)

    def set_data_region(self, data, start, length):
        glBindBuffer(self.target, self.id)
        glBufferSubData(self.target, start, length, data)

    def map(self, invalidate=False):
        glBindBuffer(self.target, self.id)
        if invalidate:
            glBufferData(self.target, self.size, None, self.usage)
        ptr = ctypes.cast(glMapBuffer(self.target, GL_WRITE_ONLY), ctypes.POINTER(ctypes.c_byte * self.size)).contents
        return ptr

    def map_range(self, start, size, ptr_type):
        glBindBuffer(self.target, self.id)
        ptr = ctypes.cast(glMapBufferRange(self.target, start, size, GL_MAP_WRITE_BIT), ptr_type).contents
        glUnmapBuffer(self.target)
        return ptr

    def unmap(self):
        glUnmapBuffer(self.target)

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

        glBindBuffer(self.target, self.id)
        data = glMapBuffer(self.target, GL_READ_ONLY)
        ctypes.memmove(temp, data, min(size, self.size))
        glUnmapBuffer(self.target)

        self.size = size
        glBufferData(self.target, self.size, temp, self.usage)


class MappableBufferObject(BufferObject, AbstractMappable):
    """A buffer with system-memory backed store.

    Updates to the data via `set_data`, `set_data_region` and `map` will be
    held in local memory until `bind` is called.  The advantage is that fewer
    OpenGL calls are needed, increasing performance.

    There may also be less performance penalty for resizing this buffer.

    Updates to data via :py:meth:`map` are committed immediately.
    """
    def __init__(self, size, target, usage):
        super(MappableBufferObject, self).__init__(size, target, usage)
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
                glBufferData(self.target, self.size, self.data, self.usage)
            else:
                glBufferSubData(self.target, self._dirty_min, size, self.data_ptr + self._dirty_min)
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

        glBindBuffer(self.target, self.id)
        glBufferData(self.target, self.size, self.data, self.usage)

        self._dirty_min = sys.maxsize
        self._dirty_max = 0


class AbstractBufferRegion:
    """A mapped region of a buffer.

    Buffer regions are obtained using :py:meth:`~AbstractMappable.get_region`.

    :Ivariables:
        `array` : ctypes array
            Array of data, of the type and count requested by
            :py:meth:`~AbstractMappable.get_region`.

    """
    def invalidate(self):
        """Mark this region as changed.

        The buffer may not be updated with the latest contents of the
        array until this method is called.  (However, it may not be updated
        until the next time the buffer is used, for efficiency).
        """
        pass


class BufferObjectRegion(AbstractBufferRegion):
    """A mapped region of a BufferObject."""

    __slots__ = 'buffer', 'start', 'end', 'array'

    def __init__(self, buffer, start, end, array):
        self.buffer = buffer
        self.start = start
        self.end = end
        self.array = array

    def invalidate(self):
        buffer = self.buffer
        buffer._dirty_min = min(buffer._dirty_min, self.start)
        buffer._dirty_max = max(buffer._dirty_max, self.end)


class IndirectArrayRegion(AbstractBufferRegion):
    """A mapped region in which data elements are not necessarily contiguous.

    This region class is used to wrap buffer regions in which the data
    must be accessed with some stride.  For example, in an interleaved buffer
    this region can be used to access a single interleaved component as if the
    data was contiguous.
    """

    def __init__(self, region, size, component_count, component_stride):
        """Wrap a buffer region.

        Use the `component_count` and `component_stride` parameters to specify
        the data layout of the encapsulated region.  For example, if RGBA
        data is to be accessed as if it were packed RGB, ``component_count``
        would be set to 3 and ``component_stride`` to 4.  If the region
        contains 10 RGBA tuples, the ``size`` parameter is ``3 * 10 = 30``.

        :Parameters:
            `region` : `AbstractBufferRegion`
                The region with interleaved data
            `size` : int
                The number of elements that this region will provide access to.
            `component_count` : int
                The number of elements that are contiguous before some must
                be skipped.
            `component_stride` : int
                The number of elements of interleaved data separating
                the contiguous sections.

        """
        self.region = region
        self.size = size
        self.count = component_count
        self.stride = component_stride
        self.array = self

    def __repr__(self):
        return 'IndirectArrayRegion(size=%d, count=%d, stride=%d)' % (
            self.size, self.count, self.stride)

    def __getitem__(self, index):
        count = self.count
        if not isinstance(index, slice):
            elem = index // count
            j = index % count
            return self.region.array[elem * self.stride + j]

        start = index.start or 0
        stop = index.stop
        step = index.step or 1
        if start < 0:
            start = self.size + start
        if stop is None:
            stop = self.size
        elif stop < 0:
            stop = self.size + stop

        assert step == 1 or step % count == 0, 'Step must be multiple of component count'

        data_start = (start // count) * self.stride + start % count
        data_stop = (stop // count) * self.stride + stop % count
        data_step = step * self.stride

        #  TODO stepped getitem is probably wrong, see setitem for correct.
        value_step = step * count

        value = [0] * ((stop - start) // step)
        stride = self.stride
        for i in range(count):
            value[i::value_step] = self.region.array[data_start + i:data_stop + i:data_step]
        return value

    def __setitem__(self, index, value):
        count = self.count
        if not isinstance(index, slice):
            elem = index // count
            j = index % count
            self.region.array[elem * self.stride + j] = value
            return

        start = index.start or 0
        stop = index.stop
        step = index.step or 1
        if start < 0:
            start = self.size + start
        if stop is None:
            stop = self.size
        elif stop < 0:
            stop = self.size + stop

        assert step == 1 or step % count == 0, 'Step must be multiple of component count'

        data_start = (start // count) * self.stride + start % count
        data_stop = (stop // count) * self.stride + stop % count

        if step == 1:
            data_step = self.stride
            value_step = count
            for i in range(count):
                self.region.array[data_start + i:data_stop + i:data_step] = value[i::value_step]
        else:
            data_step = (step // count) * self.stride
            self.region.array[data_start:data_stop:data_step] = value

    def invalidate(self):
        self.region.invalidate()
