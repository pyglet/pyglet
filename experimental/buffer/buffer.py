#!/usr/bin/python
# $Id:$

import ctypes
import re

from pyglet.gl import *
from pyglet.gl import gl_info

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

def create(count, *attribute_formats, **kwargs):
    '''Create a buffer of vertex data.

    Example::

        create(120, 'v:3f', 'c:4b', 't:2f', 'a0:n2H', 'a2:f')

    Creates a buffer of 120 vertices, with each vertex containing:

    * 3 vertex position floats
    * 4 color bytes
    * 2 texture coordinate floats
    * 2 normalized unsigned ints for generic vertex attribute 0
    * 2 floats for generic vertex attribute 2

    :rtype: AbstractBufferAccessor
    '''
    interleaved = kwargs.get('interleaved')
    attributes = [VertexAttribute.from_string(format) \
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
        buffer = VertexBufferObject(size)
    else:
        buffer = VertexArray(size)

    return VertexAttributeAccessor(buffer, attributes, stride)

def create_index(count, gl_type=GL_UNSIGNED_INT):
    '''Create an element index array.
    '''
    have_vbo = gl_info.have_version(1, 5)
    size = ctypes.sizeof(_c_types[gl_type]) * count
    
    if have_vbo:
        buffer = VertexBufferObject(size, target=GL_ELEMENT_ARRAY_BUFFER)
    else:
        buffer = VertexArray(size)

    return ElementIndexAccessor(buffer, gl_type, count)


class Attribute(object):


    c_type = None
    size = 0
    count = 0
   
    def set_pointer(self, stride, offset):
        '''Access this attribute at the given stride and offset.  Calls
        gl*Pointer with the appropriate arguments.'''
        raise NotImplementedError('abstract')

    def enable(self):
        '''Enable this attribute.'''
        raise NotImplementedError('abstract')

class VertexAttribute(Attribute):
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

        self.c_type = _c_types[gl_type]
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

class AbstractBuffer(object):
    one_time_configure = False
    
    def configure(self, attributes):
        raise NotImplementedError('abstract')
    
    def bind(self):
        raise NotImplementedError('abstract')

    def unbind(self):
        raise NotImplementedError('abstract')

    def set_data(self, data):
        raise NotImplementedError('abstract')

    def set_data_region(self, data, start, length):
        raise NotImplementedError('abstract')

    def map(self):
        raise NotImplementedError('abstract')

    def unmap(self):
        raise NotImplementedError('abstract')

class VertexBufferObject(AbstractBuffer):
    configured = False
    ptr = 0
    
    def __init__(self, size, target=GL_ARRAY_BUFFER):
        self.size = size
        self.target = target

        id = GLuint()
        glGenBuffers(1, id)
        self.id = id.value
        glBindBuffer(GL_ARRAY_BUFFER, self.id)
        glBufferData(GL_ARRAY_BUFFER, self.size, None, GL_DYNAMIC_DRAW)

    def configure(self, attributes):
        # nvidia driver does not require config every bind; once per VBO is
        # enough (is this in spec?)
        if not self.configured:
            for attribute in attributes:
                attribute.enable()
                attribute.set_pointer(0)
            configured = True

    def bind(self):
        glBindBuffer(self.target, self.id)

    def unbind(self):
        glBindBuffer(self.target, 0)

    def set_data(self, data):
        glBufferData(self.target, self.size, data, GL_DYNAMIC_DRAW)

    def set_data_region(self, data, start, length):
        glBufferSubData(self.target, start, length, data)

    def map(self):
        return ctypes.cast(glMapBuffer(self.target, GL_WRITE_ONLY),
                           ctypes.c_byte * self.size)

    def unmap(self):
        glUnmapBuffer(self.target)

class VertexArray(AbstractBuffer):
    def __init__(self, size):
        self.size = size

        self.array = (ctypes.c_byte * size)()
        self.ptr = ctypes.cast(self.array, ctypes.c_void_p).value

    def configure(self, attributes):
        for attribute in attributes:
            attribute.enable()
            attribute.set_pointer(self.ptr)

    def bind(self):
        pass

    def unbind(self):
        pass
    
    def set_data(self, data):
        ctypes.memmove(self.ptr, data, self.size)

    def set_data_region(self, data, start, length):
        ctypes.memmove(self.ptr + start, data, length)

    def map(self):
        return self.array

    def unmap(self):
        pass

class VertexAttributeAccessor(object):
    attributes = None
    attribute_map = None
    generic_attribute_map = None

    def __init__(self, buffer, attributes, stride):
        self.buffer = buffer
        self.stride = stride
        self.attributes = attributes
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

    def set_data(self, *data):
        blergh

    def set_vertex_data(self, data):
        assert self.stride == 0
        attribute = self.attribute_map['v']
        data = attribute.to_array(data)
        length = len(data) * ctypes.sizeof(attribute.c_type)
        self.buffer.bind()
        self.buffer.set_data_region(data, attribute.offset, length)
        self.buffer.unbind()

    def set_normal_data(self, data):
        assert self.stride == 0
        attribute = self.attribute_map['n']
        data = attribute.to_array(data)
        length = len(data) * ctypes.sizeof(attribute.c_type)
        self.buffer.bind()
        self.buffer.set_data_region(data, attribute.offset, length)
        self.buffer.unbind()

class ElementIndexAccessor(object):
    def __init__(self, buffer, gl_type, count):
        self.buffer = buffer
        self.gl_type = gl_type
        self.c_type = _c_types[gl_type]
        self.count = count
        
    def set_data(self, data):
        data = (self.c_type * self.count)(*data)
        self.buffer.bind()
        self.buffer.set_data(data)
        self.buffer.unbind()

    def draw(self, mode, vertices, start=0, count=None):
        if count is None:
            count = self.count - start
        
        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        vertices.buffer.bind()
        vertices.buffer.configure(vertices.attributes)
        self.buffer.bind()
        glDrawElements(mode, count, self.gl_type, self.buffer.ptr + start)
        self.buffer.unbind()
        vertices.buffer.unbind()
        glPopClientAttrib()
