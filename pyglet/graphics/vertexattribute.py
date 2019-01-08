# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2018 Alex Holkner
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
# $Id:$

"""Access byte arrays as arrays of vertex attributes.

Use :py:func:`create_attribute` to create an attribute accessor given a
simple format string.  Alternatively, the classes may be constructed directly.

Attribute format strings
========================

An attribute format string specifies the format of a vertex attribute.  Format
strings are accepted by the :py:func:`create_attribute` function as well as most
methods in the :py:mod:`pyglet.graphics` module.

Format strings have the following (BNF) syntax::

    attribute ::= ( name | texture 't' ) count type

``name`` describes the vertex attribute, and can be any valid ascii characters.
You can also use one of the following constants for the predefined attributes:

``c``
    Vertex color
``e``
    Edge flag
``f``
    Fog coordinate
``n``
    Normal vector
``s``
    Secondary color
``t``
    Texture coordinate
``v``
    Vertex coordinate

Texture coordinates for multiple texture units can be specified with the
texture number before the constant 't'.  For example, ``1t`` gives the
texture coordinate attribute for texture unit 1.

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

Some attributes constrain the possible data types; for example,
normal vectors must use one of the signed data types.  The use of
some data types, while not illegal, may have severe performance
concerns.  For example, the use of ``GLdouble`` is discouraged,
and colours should be specified with ``GLubyte``.

Whitespace is prohibited within the format string.

Some examples follow:

``v3f``
    3-float vertex position
``c4b``
    4-byte colour
``1eb``
    Edge flag
``0g3f``
    3-float generic vertex attribute 0
``1gn1i``
    Integer generic vertex attribute 1, normalized to [-1, 1]
``2gn4B``
    4-byte generic vertex attribute 2, normalized to [0, 1] (because
    the type is unsigned)
``3t2f``
    2-float texture coordinate for texture unit 3.

"""

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import ctypes
import re

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


# TODO: validate this for texcoord_texture matches:
_attribute_format_re = re.compile(r"""
    (?P<name> .+?(?=[0-9]) |
    (?P<texcoord_texture>[0-9]+) t)
    (?P<count>[1234])
    (?P<type>[bBsSiIfd])
""", re.VERBOSE)


_attribute_cache = {}


def _align(v, align):
    return ((v - 1) & ~(align - 1)) + align


def interleave_attributes(attributes):
    """Interleave attribute offsets.

    Adjusts the offsets and strides of the given attributes so that
    they are interleaved.  Alignment constraints are respected.

    :Parameters:
        `attributes` : sequence of `AbstractAttribute`
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
        `attributes` : sequence of `AbstractAttribute`
            Attributes to serialize in-place.

    """
    offset = 0
    for attribute in attributes:
        offset = _align(offset, attribute.align)
        attribute.offset = offset
        offset += count * attribute.stride


def create_attribute(shader_program_id, fmt):
    """Create a vertex attribute description from a format string.
    
    The initial stride and offset of the attribute will be 0.

    :Parameters:
        `shader_program_id` : int
            ID of the Shader Program that this attribute will belong to.
        `fmt` : str
            Attribute format string.  See the module summary for details.

    :rtype: `AbstractAttribute`
    """
    try:
        cls, args = _attribute_cache[fmt]
        return cls(*args)
    except KeyError:
        pass

    match = _attribute_format_re.match(fmt)
    assert match, 'Invalid attribute format %r' % fmt

    name = match.group('name')
    count = int(match.group('count'))
    gl_type = _gl_types[match.group('type')]
    texcoord_texture = match.group('texcoord_texture')

    # TODO: update documentation to remove cruft.

    if texcoord_texture:
        attr_class = MultiTexCoordAttribute
        args = shader_program_id, int(texcoord_texture), count, gl_type
    elif name in _attribute_classes:
        attr_class = _attribute_classes[name]
        if attr_class._fixed_count:
            assert count == attr_class._fixed_count, \
                'Attributes named "%s" must have count of %d' % (name, attr_class._fixed_count)
            args = (shader_program_id, gl_type)
        else:
            args = (shader_program_id, count, gl_type)
    else:
        attr_class = GenericAttribute
        args = shader_program_id, name, count, gl_type

    _attribute_cache[fmt] = attr_class, args
    return attr_class(*args)


class AbstractAttribute:
    """Abstract accessor for an attribute in a mapped buffer.
    """
    name = None
    _fixed_count = None

    def __init__(self, shader_program_id, count, gl_type):
        """Create the attribute accessor.

        :Parameters:
            `shader_program_id` : int
                ID of the Shader Program that this attribute will belong to.
            `count` : int
                Number of components in the attribute.
            `gl_type` : int
                OpenGL type enumerant; for example, ``GL_FLOAT``

        """
        assert count in (1, 2, 3, 4), 'Component count out of range'
        self.shader_program_id = shader_program_id
        self.gl_type = gl_type
        self.c_type = _c_types[gl_type]
        self.count = count
        self.align = ctypes.sizeof(self.c_type)
        self.size = count * self.align
        self.stride = self.size
        self.offset = 0
        attr_name = ctypes.create_string_buffer(self.name.encode('utf8'))
        self.location = glGetAttribLocation(shader_program_id, attr_name)
        assert self.location != -1, "'{0}' attribute not found in Shader".format(self.name)

        self._size_cache = {}
        self._pointer_cache = {}

    def enable(self):
        """Enable the attribute using ``glEnableVertexAttribArray``."""
        glEnableVertexAttribArray(self.location)

    def set_pointer(self, offset):
        """Setup this attribute to point to the currently bound buffer at
        the given offset.

        ``offset`` should be based on the currently bound buffer's ``ptr``
        member.

        :Parameters:
            `offset` : int
                Pointer offset to the currently bound buffer for this
                attribute.

        """
        raise NotImplementedError('abstract')

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

        try:
            byte_start, byte_size, array_count = self._size_cache[count]
        except KeyError:
            byte_start = self.stride * start
            byte_size = self.stride * count
            array_count = self.count * count
            self._size_cache[count] = byte_start, byte_size, array_count

        if self.stride == self.size or not array_count:
            # non-interleaved
            try:
                ptr_type = self._pointer_cache[self.c_type * array_count]
            except KeyError:
                ptr_type = ctypes.POINTER(self.c_type * array_count)
                self._pointer_cache[self.c_type * array_count] = ptr_type
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
        return "Attribute(name='{0}', count={1})".format(self.name, self.count)


class VertexAttribute(AbstractAttribute):
    """Vertex coordinate attribute."""

    name = 'vertices'

    def __init__(self, shader_program_id, count, gl_type):
        assert count > 1, 'Vertex attribute must have count of 2, 3 or 4'
        assert gl_type in (GL_SHORT, GL_INT, GL_INT, GL_FLOAT, GL_DOUBLE),\
            'Vertex attribute must have signed type larger than byte'
        super(VertexAttribute, self).__init__(shader_program_id, count, gl_type)

    def set_pointer(self, pointer):
        glVertexAttribPointer(self.location, self.count, self.gl_type,
                              False, self.stride, self.offset + pointer)


class ColorAttribute(AbstractAttribute):
    """Color vertex attribute."""

    name = 'colors'

    def __init__(self, shader_program_id, count, gl_type):
        assert count in (3, 4), 'Color attributes must have count of 3 or 4'
        super(ColorAttribute, self).__init__(shader_program_id, count, gl_type)

    def set_pointer(self, pointer):
        glVertexAttribPointer(self.location, self.count, self.gl_type,
                              True, self.stride, self.offset + pointer)


# TODO: test this
class EdgeFlagAttribute(AbstractAttribute):
    """Edge flag attribute."""

    name = 'edge_flags'
    _fixed_count = 1

    def __init__(self, shader_program_id, gl_type):
        assert gl_type in (GL_BYTE, GL_UNSIGNED_BYTE, GL_BOOL),\
            'Edge flag attribute must have boolean type'
        super(EdgeFlagAttribute, self).__init__(shader_program_id, 1, gl_type)

    def set_pointer(self, pointer):
        glVertexAttribPointer(self.location, self.count, self.gl_type,
                              True, self.stride, self.offset + pointer)     # Normalized?


# TODO: test this
class FogCoordAttribute(AbstractAttribute):
    """Fog coordinate attribute."""

    name = 'fog_coords'

    def __init__(self, shader_program_id, count, gl_type):
        super(FogCoordAttribute, self).__init__(shader_program_id, count, gl_type)

    def set_pointer(self, pointer):
        glVertexAttribPointer(self.location, self.count, self.gl_type,
                              False, self.stride, self.offset + pointer)     # Normalized?


# TODO: test this
class NormalAttribute(AbstractAttribute):
    """Normal vector attribute."""

    name = 'normals'
    _fixed_count = 3

    def __init__(self, shader_program_id, gl_type):
        assert gl_type in (GL_BYTE, GL_SHORT, GL_INT, GL_FLOAT, GL_DOUBLE), \
            'Normal attribute must have signed type'
        super(NormalAttribute, self).__init__(shader_program_id, 3, gl_type)

    def set_pointer(self, pointer):
        glVertexAttribPointer(self.location, self.count, self.gl_type,
                              False, self.stride, self.offset + pointer)


# TODO: test this
class SecondaryColorAttribute(AbstractAttribute):
    """Secondary color attribute."""

    name = 'secondary_colors'
    _fixed_count = 3

    def __init__(self, shader_program_id, gl_type):
        super(SecondaryColorAttribute, self).__init__(shader_program_id, 3, gl_type)

    def set_pointer(self, pointer):
        glVertexAttribPointer(self.location, self.count, self.gl_type,
                              True, self.stride, self.offset + pointer)


class TexCoordAttribute(AbstractAttribute):
    """Texture coordinate attribute."""

    name = 'tex_coords'

    def __init__(self, shader_program_id, count, gl_type):
        assert gl_type in (GL_SHORT, GL_INT, GL_INT, GL_FLOAT, GL_DOUBLE), \
            'Texture coord attribute must have non-byte signed type'
        super(TexCoordAttribute, self).__init__(shader_program_id, count, gl_type)

    def set_pointer(self, pointer):
        glVertexAttribPointer(self.location, self.count, self.gl_type,
                              False, self.stride, self.offset + pointer)

    def convert_to_multi_tex_coord_attribute(self):
        """Changes the class of the attribute to `MultiTexCoordAttribute`.
        """
        self.__class__ = MultiTexCoordAttribute
        self.texture = 0


# TODO: test this
class MultiTexCoordAttribute(AbstractAttribute):
    """Texture coordinate attribute."""

    def __init__(self, shader_program_id, texture, count, gl_type):
        assert gl_type in (GL_SHORT, GL_INT, GL_INT, GL_FLOAT, GL_DOUBLE), \
            'Texture coord attribute must have non-byte signed type'
        self.texture = texture
        super(MultiTexCoordAttribute, self).__init__(shader_program_id, count, gl_type)

    def set_pointer(self, pointer):
        glVertexAttribPointer(self.location, self.count, self.gl_type,
                              False, self.stride, self.offset + pointer)


class GenericAttribute(AbstractAttribute):
    """Generic vertex attribute, used by shader programs."""

    def __init__(self, shader_program_id, name, count, gl_type):
        self.name = name
        super(GenericAttribute, self).__init__(shader_program_id, count, gl_type)

    def set_pointer(self, pointer):
        glVertexAttribPointer(self.location, self.count, self.gl_type,
                              False, self.stride, self.offset + pointer)


_attribute_classes = {
    'c': ColorAttribute,
    'e': EdgeFlagAttribute,
    'f': FogCoordAttribute,
    'n': NormalAttribute,
    's': SecondaryColorAttribute,
    't': TexCoordAttribute,
    'v': VertexAttribute,
}
