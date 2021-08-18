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

"""Access byte arrays as arrays of vertex attributes.

Use :py:func:`create_attribute` to create an attribute accessor given a
simple format string.  Alternatively, the classes may be constructed directly.

Attribute format strings
========================

An attribute format string specifies the format of a vertex attribute.  Format
strings are accepted by the :py:func:`create_attribute` function as well as most
methods in the :py:mod:`pyglet.graphics` module.

Format strings have the following (BNF) syntax::

    attribute ::= name count type normalized

``name`` describes the vertex attribute, and can be any valid ascii characters.
The following single letter constants remain for backwards compatibility, but
are deprecated:

``v``
    'vertices' Shader attribute
``c``
    'color' Shader attribute
``t``
    'tex_coords' Shader attribute
``n``
    'normals' Shader attribute
``e``
    'edge_flags' Shader attribute
``f``
    'fog_coords' Shader attribute
``s``
    'secondary_colors' Shader attribute

``count`` gives the number of data components in the attribute.  For
example, a 3D vertex position has a count of 3.  Some attributes
constrain the possible counts that can be used; for example, a normal
vector must have a count of 3.

``type`` gives the data type of each component of the attribute.  The
following types can be used:

``b``
    ``GLbyte``
``B``
    ``GLubyte``
``s``
    ``GLshort``
``S``
    ``GLushort``
``i``
    ``GLint``
``I``
    ``GLuint``
``f``
    ``GLfloat``
``d``
    ``GLdouble``

``normalized`` indicates if the value should be normalized by OpenGL.

Some attributes constrain the possible data types; for example,
normal vectors must use one of the signed data types.  The use of
some data types, while not illegal, may have severe performance
concerns.  For example, the use of ``GLdouble`` is discouraged,
and colors should be specified with ``GLubyte``.

Whitespace is prohibited within the format string.

Some examples follow:

``vertices3f``
    3-float vertex position
``colors4bn``
    4-byte color, normalized
``colors3Bn``
    3-unsigned byte color, normalized
``tex_coords3f``
    3-float texture coordinate
"""

import re
import ctypes

from pyglet.gl import *
from pyglet.graphics import vertexbuffer

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

_gl_types = {
    'b': GL_BYTE,
    'B': GL_UNSIGNED_BYTE,
    's': GL_SHORT,
    'S': GL_UNSIGNED_SHORT,
    'i': GL_INT,
    'I': GL_UNSIGNED_INT,
    'f': GL_FLOAT,
    'd': GL_DOUBLE,
}


_attribute_format_re = re.compile(r"""
    (?P<name> .+?(?=[0-9]))
    (?P<count>[1234])
    (?P<type>[bBsSiIfd])
    (?P<normalize>n?)
""", re.VERBOSE)


def _align(v, align):
    return ((v - 1) & ~(align - 1)) + align


def interleave_attributes(attributes):
    """Interleave attribute offsets.

    Adjusts the offsets and strides of the given attributes so that
    they are interleaved.  Alignment constraints are respected.

    :Parameters:
        `attributes` : sequence of `VertexAttribute`
            Attributes to interleave in-place.

    """
    stride = 0
    max_size = 0
    for attribute in attributes:
        stride = _align(stride, attribute.align)
        attribute.offset = stride
        stride += attribute.size
        max_size = max(max_size, attribute.size)
    stride = _align(stride, max_size)
    for attribute in attributes:
        attribute.stride = stride


def serialize_attributes(count, attributes):
    """Serialize attribute offsets.
    
    Adjust the offsets of the given attributes so that they are
    packed serially against each other for `count` vertices.

    :Parameters:
        `count` : int
            Number of vertices.
        `attributes` : sequence of `VertexAttribute`
            Attributes to serialize in-place.

    """
    offset = 0
    for attribute in attributes:
        offset = _align(offset, attribute.align)
        attribute.offset = offset
        offset += count * attribute.stride


def create_attribute(shader_program, fmt):
    """Create a vertex attribute description from a format string.
    
    The initial stride and offset of the attribute will be 0.

    :Parameters:
        `shader_program_id` : int
            ID of the Shader Program that this attribute will belong to.
        `fmt` : str
            Attribute format string.  See the module summary for details.

    :rtype: `VertexAttribute`
    """

    match = _attribute_format_re.match(fmt)
    assert match, 'Invalid attribute format %r' % fmt

    name = match.group('name')
    count = int(match.group('count'))
    gl_type = _gl_types[match.group('type')]
    normalize = True if match.group('normalize') else False

    attribute_meta = shader_program.attributes.get(name, None)
    assert attribute_meta, f"No '{name}' attribute found in {shader_program}.\n"\
                           f"Valid attibutes are: {shader_program.attributes}."
    assert count == attribute_meta.count, f"Invalid count of '{count}' for {attribute_meta}."

    return VertexAttribute(name, attribute_meta.location, count, gl_type, normalize)


class VertexAttribute:
    """Abstract accessor for an attribute in a mapped buffer."""

    def __init__(self, name, location, count, gl_type, normalize):
        """Create the attribute accessor.

        :Parameters:
            `name` : str
                Name of the vertex attribute.
            `location` : int
                Location of the vertex attribute.
            `count` : int
                Number of components in the attribute.
            `gl_type` : int
                OpenGL type enumerant; for example, ``GL_FLOAT``
            `normalize`: bool
                True if OpenGL should normalize the values

        """
        assert count in (1, 2, 3, 4), 'Vertex attribute component count out of range'
        self.name = name
        self.location = location
        self.count = count

        self.gl_type = gl_type
        self.c_type = _c_types[gl_type]
        self.normalize = normalize

        self.align = ctypes.sizeof(self.c_type)
        self.size = count * self.align
        self.stride = self.size
        self.offset = 0

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
        glVertexAttribPointer(self.location, self.count, self.gl_type, self.normalize, self.stride, self.offset+pointer)

    def get_region(self, buffer, start, count):
        """Map a buffer region using this attribute as an accessor.

        The returned region can be modified as if the buffer was a contiguous
        array of this attribute (though it may actually be interleaved or
        otherwise non-contiguous).

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

        if self.stride == self.size or not array_count:
            # non-interleaved
            ptr_type = ctypes.POINTER(self.c_type * array_count)
            return buffer.get_region(byte_start, byte_size, ptr_type)
        else:
            # interleaved
            byte_start += self.offset
            byte_size -= self.offset
            elem_stride = self.stride // ctypes.sizeof(self.c_type)
            elem_offset = self.offset // ctypes.sizeof(self.c_type)
            ptr_type = ctypes.POINTER(self.c_type * (count * elem_stride - elem_offset))
            region = buffer.get_region(byte_start, byte_size, ptr_type)
            return vertexbuffer.IndirectArrayRegion(region, array_count, self.count, elem_stride)

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
        if self.stride == self.size:
            # non-interleaved
            byte_start = self.stride * start
            byte_size = self.stride * count
            array_count = self.count * count
            data = (self.c_type * array_count)(*data)
            buffer.set_data_region(data, byte_start, byte_size)
        else:
            # interleaved
            region = self.get_region(buffer, start, count)
            region[:] = data

    def __repr__(self):
        return f"VertexAttribute(name='{self.name}', location={self.location}, count={self.count})"
