#!/usr/bin/python
# $Id:$

'''Classes for manipulating buffer data as specific vertex attributes.

Use `create_attribute` to create an attribute accessor given a simple format
string.  Alternatively, the classes may be constructed directly.
'''

import ctypes
import re

from pyglet.gl import *

# Local imports
import vertexbuffer

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

_attribute_format_re = re.compile(r'''
    (?P<name>
       [cefnstv] | 
       (?P<generic_index>[0-9]+) g
       (?P<generic_normalized>n?))
    (?P<count>[1234])
    (?P<type>[bBsSiIfd])
''', re.VERBOSE)

def _align(v, align):
    return ((v - 1) & ~(align - 1)) + align

def interleave_attributes(attributes):
    '''Adjust the offsets and strides of the given attributes so that
    they are interleaved.  Alignment constraints are respected.
    '''
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
    '''Adjust the offsets of the given attributes so that they are
    packed serially against each other for `count` vertices.
    '''
    offset = 0
    for attribute in attributes:
        offset = _align(offset, attribute.align)
        attribute.offset = offset
        offset += count * attribute.stride

def create_attribute(format):
    '''Create a vertex attribute description given a format string such as
    "v3f".  The initial stride and offset of the attribute will be 0.

    Format strings have the following syntax::

        attribute ::= ( name | index 'g' 'n'? ) count type

    ``name`` describes the vertex attribute, and is one of the following
    constants for the predefined attributes:

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

    You can alternatively create a generic indexed vertex attribute by
    specifying its index in decimal followed by the constant ``g``.  For
    example, ``0g`` specifies the generic vertex attribute with index 0.
    If the optional constant ``n`` is present after the ``g``, the
    attribute is normalised to the range ``[0, 1]`` or ``[-1, 1]`` within
    the range of the data type.

    ``count`` gives the number of data components in the attribute.  For
    example, a 3D vertex position has a count of 3.  Some attributes
    constrain the possible counts that can be used; for example, a normal
    vector must have a count of 3.

    ``type`` gives the data type of each component of the attribute.  The
    following types can be used:

    ``b``
        GLbyte
    ``B``
        GLubyte
    ``s``
        GLshort
    ``S``
        GLushort
    ``i``
        GLint
    ``I``
        GLuint
    ``f``
        GLfloat
    ``d``
        GLdouble

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

    '''

    match = _attribute_format_re.match(format)
    assert match, 'Invalid attribute format %r' % format
    count = int(match.group('count'))
    gl_type = _gl_types[match.group('type')]
    generic_index = match.group('generic_index')
    if generic_index:
        normalized = match.group('generic_normalized')
        return GenericAttribute(
            int(generic_index), normalized, count, gl_type)
    else:
        name = match.group('name')
        attr_class = _attribute_classes[name]
        if attr_class._fixed_count:
            assert count == attr_class._fixed_count, \
                'Attributes named "%s" must have count of %d' % (
                    name, attr_class._fixed_count)
            return attr_class(gl_type)
        else:
            return attr_class(count, gl_type)

class AbstractAttribute(object):
    '''Abstract accessor for an attribute in a mapped buffer.
    '''
    
    _fixed_count = None
    _component_names = ['x', 'y', 'z', 'w']
    
    def __init__(self, count, gl_type):
        assert count in (1, 2, 3, 4), 'Component count out of range'
        self.gl_type = gl_type
        self.c_type = _c_types[gl_type]
        self.count = count
        self.align = ctypes.sizeof(self.c_type)
        self.size = count * self.align
        self.stride = self.size
        self.offset = 0

        class struct_type(ctypes.Structure):
            _slots_ = self._component_names[:self.count]
            _fields_ = [ \
                (self._component_names[i], self.c_type) \
                for i in range(count) \
            ]
        self.struct_type = struct_type

    def enable(self):
        '''Enable the attribute using ``glEnableClientState``.'''
        raise NotImplementedError('abstract')

    def set_pointer(self, offset):
        '''Setup this attribute to point to the currently bound buffer at
        the given offset.

        ``offset`` should be based on the currently bound buffer's ``ptr``
        member.

        :Parameters:
            `offset` : int
                Pointer offset to the currently bound buffer for this
                attribute.

        '''
        raise NotImplementedError('abstract')

    def get_region(self, buffer, start, count):
        '''Map a buffer region using this attribute as an accessor.

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
        '''
        byte_start = self.stride * start
        byte_size = self.stride * count
        if self.stride == self.size:
            # non-interleaved
            array_count = self.count * count
            ptr_type = ctypes.POINTER(self.c_type * array_count)
            return buffer.get_region(byte_start, byte_size, ptr_type)
        else:
            # interleaved
            byte_start += self.offset
            elem_stride = self.stride // ctypes.sizeof(self.c_type)
            array_count = elem_stride * count
            ptr_type = ctypes.POINTER(self.c_type * array_count)
            region = buffer.get_region(byte_start, byte_size, ptr_type)
            return vertexbuffer.IndirectArrayRegion(
                region, array_count, self.count, elem_stride)

    def get_struct_region(self, buffer, start, count):
        byte_start = self.stride * start
        byte_size = self.stride * count
        assert self.stride == self.size
        
        ptr_type = ctypes.POINTER(self.struct_type * count)
        return buffer.get_region(byte_start, byte_size, ptr_type)


class ColorAttribute(AbstractAttribute):
    plural = 'colors'
    _component_names = ['r', 'g', 'b', 'a']
    
    def __init__(self, count, gl_type):
        assert count in (3, 4), 'Color attributes must have count of 3 or 4'
        super(ColorAttribute, self).__init__(count, gl_type)

    def enable(self):
        glEnableClientState(GL_COLOR_ARRAY)
    
    def set_pointer(self, pointer):
        glColorPointer(self.count, self.gl_type, self.stride,
                       self.offset + pointer)

class EdgeFlagAttribute(AbstractAttribute):
    plural = 'edge_flags'
    _fixed_count = 1
    
    def __init__(self, gl_type):
        assert gl_type in (GL_BYTE, GL_UNSIGNED_BYTE, GL_BOOL), \
            'Edge flag attribute must have boolean type'
        super(EdgeFlagAttribute, self).__init__(1, gl_type)

    def enable(self):
        glEnableClientState(GL_EDGE_FLAG_ARRAY)
    
    def set_pointer(self, pointer):
        glEdgeFlagPointer(self.stride, self.offset + pointer)

class FogCoordAttribute(AbstractAttribute):
    plural = 'fog_coords'
    
    def __init__(self, count, gl_type):
        super(FogCoordAttribute, self).__init__(count, gl_type)

    def enable(self):
        glEnableClientState(GL_FOG_COORD_ARRAY)
    
    def set_pointer(self, pointer):
        glFogCoordPointer(self.count, self.gl_type, self.stride,
                          self.offset + pointer)

class NormalAttribute(AbstractAttribute):
    plural = 'normals'
    _fixed_count = 3

    def __init__(self, gl_type):
        assert gl_type in (GL_BYTE, GL_SHORT, GL_INT, GL_FLOAT, GL_DOUBLE), \
            'Normal attribute must have signed type'
        super(NormalAttribute, self).__init__(3, gl_type)

    def enable(self):
        glEnableClientState(GL_NORMAL_ARRAY)
    
    def set_pointer(self, pointer):
        glNormalPointer(self.gl_type, self.stride, self.offset + pointer)

class SecondaryColorAttribute(AbstractAttribute):
    plural = 'secondary_colors'
    _fixed_count = 3

    def __init__(self, gl_type):
        super(SecondaryColorAttribute, self).__init__(3, gl_type)

    def enable(self):
        glEnableClientState(GL_SECONDARY_COLOR_ARRAY)
    
    def set_pointer(self, pointer):
        glSecondaryColorPointer(3, self.gl_type, self.stride,
                                self.offset + pointer)

class TexCoordAttribute(AbstractAttribute):
    plural = 'tex_coords'

    def __init__(self, count, gl_type):
        assert gl_type in (GL_SHORT, GL_INT, GL_INT, GL_FLOAT, GL_DOUBLE), \
            'Texture coord attribute must have non-byte signed type'
        super(TexCoordAttribute, self).__init__(count, gl_type)

    def enable(self):
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)
    
    def set_pointer(self, pointer):
        glTexCoordPointer(self.count, self.gl_type, self.stride,
                       self.offset + pointer)

class VertexAttribute(AbstractAttribute):
    _component_names = ['x', 'y', 'z', 'w']
    plural = 'vertices'

    def __init__(self, count, gl_type):
        assert count > 1, \
            'Vertex attribute must have count of 2, 3 or 4'
        assert gl_type in (GL_SHORT, GL_INT, GL_INT, GL_FLOAT, GL_DOUBLE), \
            'Vertex attribute must have signed type larger than byte'
        super(VertexAttribute, self).__init__(count, gl_type)

    def enable(self):
        glEnableClientState(GL_VERTEX_ARRAY)

    def set_pointer(self, pointer):
        glVertexPointer(self.count, self.gl_type, self.stride,
                        self.offset + pointer)

class GenericAttribute(AbstractAttribute):
    def __init__(self, index, normalized, count, gl_type):
        self.normalized = normalized
        self.index = index
        super(GenericAttribute, self).__init__(count, gl_type)

    def enable(self):
        glEnableVertexAttribArray(self.generic_index)

    def set_pointer(self, pointer):
        glVertexAttribPointer(self.index, self.count, self.gl_type,
                              self.normalized, self.stride, 
                              self.offset + pointer)

_attribute_classes = {
    'c': ColorAttribute,
    'e': EdgeFlagAttribute,
    'f': FogCoordAttribute,
    'n': NormalAttribute,
    's': SecondaryColorAttribute,
    't': TexCoordAttribute,
    'v': VertexAttribute,
}
