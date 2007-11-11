#!/usr/bin/python
# $Id:$

import ctypes
import re

from pyglet.gl import *
from pyglet.gl import gl_info

def create(count, *attribute_formats, **kwargs):
    '''Create a buffer of vertex data.

    Example::

        create(120, 'v:3f', 'c:2b', 't:2f', 'a0:n2H', 'a2:f')

    Creates a buffer of 120 vertices, with each vertex containing:

    * 3 vertex position floats
    * 2 color bytes
    * 2 texture coordinate floats
    * 2 normalized unsigned ints for generic vertex attribute 0
    * 2 floats for generic vertex attribute 2

    :rtype: AbstractBufferAccessor
    '''
    interleaved = kwargs.get('interleaved')
    attributes = [Attribute.from_string(format) \
                  for format in attribute_formats]

    stride = sum(attribute.size for attribute in attributes)
    size = stride * count
    offset = 0
    if interleaved:
        for attribute in attributes:
            attribute.set_pointer = attribute.set_pointer(stride, offset)
            attribute.offset = offset
            offset += attribute.size
    else:
        for attribute in attributes:
            attribute.set_pointer = attribute.set_pointer(0, offset)
            attribute.offset = offset
            offset += attribute.size * count
        stride = 0

    have_vbo = gl_info.have_version(1, 5)
    
    if have_vbo:
        buffer = VertexBufferObject(attributes, stride, size)
    else:
        buffer = VertexArray(attributes, stride, size)

    return buffer

class Attribute(object):
    _pointer_functions = {
        'c': (lambda count, gl_type:
               (lambda stride, offset:
                 (lambda pointer:
                    glColorPointer(count, gl_type, stride, pointer + offset)
             ))),
        'e': (lambda count, gl_type: 
               (lambda stride, offset:
                 (lambda pointer:
                    glEdgeFlagPointer(stride, pointer + offset)
             ))),
        'f': (lambda count, gl_type:
               (lambda stride, offset:
                 (lambda pointer:
                    glFogCoordPointer(gl_type, stride, pointer + offset)
             ))),
        'n': (lambda count, gl_type:
               (lambda stride, offset:
                 (lambda pointer:
                    glNormalPointer(gl_type, stride, pointer + offset)
             ))),
        's': (lambda count, gl_type:
               (lambda stride, offset:
                 (lambda pointer:
                    glSecondaryColorPointer(count, gl_type, stride, 
                                            pointer + offset)
             ))),
        't': (lambda count, gl_type:
               (lambda stride, offset:
                 (lambda pointer:
                    glTexCoordPointer(count, gl_type, stride, pointer + offset)
             ))),
        'v': (lambda count, gl_type:
               (lambda stride, offset:
                 (lambda pointer:
                    glVertexPointer(count, gl_type, stride, pointer + offset)
             ))),
    }

    _enable_bits = {
        'c': GL_COLOR_ARRAY,
        'e': GL_EDGE_FLAG_ARRAY,
        'f': GL_FOG_COORD_ARRAY,
        'n': GL_NORMAL_ARRAY,
        's': GL_SECONDARY_COLOR_ARRAY,
        't': GL_TEXTURE_COORD_ARRAY,
        'v': GL_VERTEX_ARRAY,
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
    
    _gl_type_sizes = {
        GL_BYTE: 1,
        GL_UNSIGNED_BYTE: 1,
        GL_SHORT: 2,
        GL_UNSIGNED_SHORT: 2,
        GL_INT: 4,
        GL_UNSIGNED_INT: 4,
        GL_FLOAT: 4,
        GL_DOUBLE: 8,
    }

    _format_re = re.compile(r'''
        (?P<dest>
           [cefnstv] | 
           a(?P<dest_index>[0-9]+))
        : (?P<normalized>n?)
          (?P<count>[1234])
          (?P<type>[bBsSiIfd])
    ''', re.VERBOSE)
    
    def __init__(self, dest, count, gl_type, normalized=False,
                 dest_index=None):
        assert (count in (1, 2, 3, 4),
            'Element count out of range')
        assert (dest == 'a' or not normalized,
            'Only generic vertex attributes can be normalized')
        assert (dest == 'a' or dest_index is None,
            'Dest index was specified for non-generic vertex attribute')
        assert (dest != 'c' or count in (3, 4),
            'Color attributes must have count of 3 or 4')
        assert (dest != 'e' or count == 1,
            'Edge flag attribute must have count of 1')
        assert (dest != 'e' or gl_type in (
            GL_BYTE, GL_UNSIGNED_BYTE, GL_BOOLEAN),
            'Edge flag attribute must have boolean type')
        assert (dest != 'n' or count == 3,
            'Normal attribute must have count of 3')
        assert (dest != 'n' or gl_type in (
            GL_BYTE, GL_SHORT, GL_INT, GL_FLOAT, GL_DOUBLE),
            'Normal attribute must have signed type')
        assert (dest != 's' or count == 3,
            'Secondary color must have count of 3')
        assert (dest != 't' or gl_type in (
            GL_SHORT, GL_INT, GL_INT, GL_DOUBLE),
            'Texture coord attribute must have signed type larger than byte')
        assert (dest != 'v' or count in (2, 3, 4),
            'Vertex attribute must have count of 2, 3 or 4')
        assert (dest != 'v' or gl_type in (
            GL_SHORT, GL_INT, GL_INT, GL_DOUBLE),
            'Vertex attribute must have signed type larger than byte')
        
        self.dest = dest
        if dest == 'a':
            self.dest_index = dest_index
            self.set_pointer = \
                (lambda stride, offset: 
                  (lambda pointer:
                     glVertexAttribPointer(dest_index, count, gl_type,
                                           normalized, stride, 
                                           pointer + offset)
                 ))
            self.enable = lambda: glEnableVertexAttribArray(dest_index)
        else:
            self.set_pointer = self._pointer_functions[dest](count, gl_type)
            enable_bit = self._enable_bits[dest]
            self.enable = lambda: glEnableClientState(enable_bit)

        self.c_type = self._c_types[gl_type]
        self.size = count * ctypes.sizeof(self.c_type)
        self.count = count

    @classmethod
    def from_string(cls, format):
        match = cls._format_re.match(format)
        dest = match.group('dest')
        count = int(match.group('count'))
        gl_type = cls._gl_types[match.group('type')]
        normalized = match.group('normalized')
        dest_index = match.group('dest_index')
        if dest_index:
            dest_index = int(dest_index)
        return cls(dest, count, gl_type, normalized, dest_index)

    def to_array(self, array):
        '''Convert a Python sequence into a ctypes byte array.'''
        n = len(array)
        assert (n % self.count == 0,
            'Length of data array is not multiple of element count.')
        return (self.c_type * n)(*array)

    def set_pointer(self, stride, offset):
        '''Access this attribute at the given stride and offset.  Calls
        gl*Pointer with the appropriate arguments.'''
        # Actually set on the instance during __init__.

    def enable(self):
        '''Enable this attribute.'''
        # Actually set on the instance during __init__.

class AbstractBuffer(object):
    attribute_map = None
    generic_attribute_map = None

    def __init__(self, attributes, stride):
        self.stride = stride
        self.attribute_map = {}
        for attribute in attributes:
            if attribute.dest == 'a':
                if not self.generic_attribute_map:
                    self.generic_attribute_map = {}
                self.generic_attribute_map[attribute.dest_index] = attribute
            else:
                assert (attribute.dest not in self.attribute_map,
                    'Attribute %s given more than once' % attribute.dest)
                self.attribute_map[attribute.dest] = attribute

    def set_vertex_data(self, data):
        assert self.stride == 0
        attribute = self.attribute_map['v']
        data = attribute.to_array(data)
        length = len(data) * ctypes.sizeof(attribute.c_type)
        self._bind_buffer()
        self._set_data_region(data, attribute.offset, length)
        self._unbind_buffer()

    def set_normal_data(self, data):
        assert self.stride == 0
        attribute = self.attribute_map['n']
        data = attribute.to_array(data)
        length = len(data) * ctypes.sizeof(attribute.c_type)
        self._bind_buffer()
        self._set_data_region(data, attribute.offset, length)
        self._unbind_buffer()

    def _bind_buffer(self):
        raise NotImplementedError('abstract')

    def _set_data(self, data):
        raise NotImplementedError('abstract')

    def _set_data_region(self, data, start, length):
        raise NotImplementedError('abstract')

    def _map(self):
        raise NotImplementedError('abstract')

    def _unmap(self):
        raise NotImplementedError('abstract')

class VertexBufferObject(AbstractBuffer):
    def __init__(self, attributes, stride, size):
        super(VertexBufferObject, self).__init__(attributes, stride)
        self.size = size
        self.attributes = attributes

        id = GLuint()
        glGenBuffers(1, id)
        self.id = id.value
        glBindBuffer(GL_ARRAY_BUFFER, self.id)
        glBufferData(GL_ARRAY_BUFFER, self.size, None, GL_DYNAMIC_DRAW)
        for attribute in self.attributes:
            attribute.enable()
            attribute.set_pointer(0)

    def _bind_buffer(self):
        glBindBuffer(GL_ARRAY_BUFFER, self.id)

    def _unbind_buffer(self):
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def _set_data(self, data):
        glBufferData(GL_ARRAY_BUFFER, self.size, data, GL_DYNAMIC_DRAW)

    def _set_data_region(self, data, start, length):
        glBufferSubData(GL_ARRAY_BUFFER, start, length, data)

    def _map(self):
        return ctypes.cast(glMapBuffer(GL_ARRAY_BUFFER, GL_WRITE_ONLY),
                           ctypes.c_byte * self.size)

    def _unmap(self):
        glUnmapBuffer(GL_ARRAY_BUFFER)

class VertexArray(AbstractBuffer):
    def __init__(self, attributes, stride, size):
        super(VertexArray, self).__init__(attributes, stride)
        self.size = size
        self.attributes = attributes

        self.array = (ctypes.c_byte * size)()
        self.ptr = ctypes.cast(self.array, ctypes.c_void_p).value

    def _bind_buffer(self):
        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        for attribute in self.attributes:
            attribute.enable()
            attribute.set_pointer(self.ptr)

    def _unbind_buffer(self):
        glPopClientAttrib()
    
    def _set_data(self, data):
        ctypes.memmove(self.ptr, data)

    def _set_data_region(self, data, start, length):
        ctypes.memmove(self.ptr + start, data, length)

    def _map(self):
        return self.array

    def _unmap(self):
        pass

