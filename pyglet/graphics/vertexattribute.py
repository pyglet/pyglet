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

import ctypes

from pyglet.gl import *


_c_types = {
    GL_BYTE: ctypes.c_byte,
    GL_UNSIGNED_BYTE: ctypes.c_ubyte,
    GL_SHORT: ctypes.c_short,
    GL_UNSIGNED_SHORT: ctypes.c_ushort,
    GL_INT: ctypes.c_int,
    GL_UNSIGNED_INT: ctypes.c_uint,
    GL_FLOAT: ctypes.c_float,
    GL_DOUBLE: ctypes.c_double,
}


class VertexAttribute:
    """Abstract accessor for an attribute in a mapped buffer."""

    def __init__(self, name, location, count, gl_type, normalize):
        """Create the attribute accessor.

        :Parameters:
            `name` : str
                Name of the vertex attribute.
            `location` : int
                Location (index) of the vertex attribute.
            `count` : int
                Number of components in the attribute.
            `gl_type` : int
                OpenGL type enumerant; for example, ``GL_FLOAT``
            `normalize`: bool
                True if OpenGL should normalize the values

        """
        self.name = name
        self.location = location
        self.count = count

        self.gl_type = gl_type
        self.c_type = _c_types[gl_type]
        self.normalize = normalize

        self.align = ctypes.sizeof(self.c_type)
        self.size = count * self.align
        self.stride = self.size

    def enable(self):
        """Enable the attribute."""
        glEnableVertexAttribArray(self.location)

    def set_pointer(self, pointer):
        """Setup this attribute to point to the currently bound buffer at
        the given offset.

        ``offset`` should be based on the currently bound buffer's ``ptr``
        member.

        :Parameters:
            `offset` : int
                Pointer offset to the currently bound buffer for this
                attribute.

        """
        glVertexAttribPointer(self.location, self.count, self.gl_type, self.normalize, self.stride, pointer)

    def get_region(self, buffer, start, count):
        """Map a buffer region using this attribute as an accessor.

        The returned region consists of a contiguous array of component
        data elements.  For example, if this attribute uses 3 floats per
        vertex, and the `count` parameter is 4, the number of floats mapped
        will be ``3 * 4 = 12``.

        :Parameters:
            `buffer` : `AbstractMappable`
                The buffer to map.
            `start` : int
                Offset of the first vertex to map.
            `count` : int
                Number of vertices to map

        :rtype: `AbstractBufferRegion`
        """
        byte_start = self.stride * start
        byte_size = self.stride * count
        array_count = self.count * count
        ptr_type = ctypes.POINTER(self.c_type * array_count)
        return buffer.get_region(byte_start, byte_size, ptr_type)

    def set_region(self, buffer, start, count, data):
        """Set the data over a region of the buffer.

        :Parameters:
            `buffer` : AbstractMappable`
                The buffer to modify.
            `start` : int
                Offset of the first vertex to set.
            `count` : int
                Number of vertices to set.
            `data` : sequence
                Sequence of data components.

        """
        byte_start = self.stride * start
        byte_size = self.stride * count
        array_count = self.count * count
        data = (self.c_type * array_count)(*data)
        buffer.set_data_region(data, byte_start, byte_size)

    def __repr__(self):
        return f"VertexAttribute(name='{self.name}', location={self.location}, count={self.count})"
