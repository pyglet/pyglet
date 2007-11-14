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

def create(size, target=GL_ARRAY_BUFFER, usage=GL_DYNAMIC_DRAW, vbo=True):
    '''Create a buffer of vertex data.
    '''
    if vbo and gl_info.have_version(1, 5):
        return VertexBufferObject(size, target, usage)
    else:
        return VertexArray(size)


class AbstractBuffer(object):
    def bind(self):
        raise NotImplementedError('abstract')

    def unbind(self):
        raise NotImplementedError('abstract')

    def set_data(self, data):
        raise NotImplementedError('abstract')

    def set_data_region(self, data, start, length):
        raise NotImplementedError('abstract')

    def map(self, invalidate=False):
        raise NotImplementedError('abstract')

    def unmap(self):
        raise NotImplementedError('abstract')

    def delete(self):
        raise NotImplementedError('abstract')

class VertexBufferObject(AbstractBuffer):
    ptr = 0
    
    def __init__(self, size, target, usage):
        self.size = size
        self.target = target
        self.usage = usage

        id = GLuint()
        glGenBuffers(1, id)
        self.id = id.value
        glBindBuffer(target, self.id)
        glBufferData(target, self.size, None, self.usage)

    def bind(self):
        glBindBuffer(self.target, self.id)

    def unbind(self):
        glBindBuffer(self.target, 0)

    def set_data(self, data):
        glBufferData(self.target, self.size, data, self.usage)

    def set_data_region(self, data, start, length):
        glBufferSubData(self.target, start, length, data)

    def map(self, invalidate=False):
        if invalidate:
            glBufferData(self.target, self.size, None, self.usage)
        return ctypes.cast(glMapBuffer(self.target, GL_WRITE_ONLY),
                           ctypes.POINTER(ctypes.c_byte * self.size)).contents

    def unmap(self):
        glUnmapBuffer(self.target)

    def delete(self):
        id = gl.GLuint(self.id)
        glDeleteBuffers(1, id)

class VertexArray(AbstractBuffer):
    def __init__(self, size):
        self.size = size

        self.array = (ctypes.c_byte * size)()
        self.ptr = ctypes.cast(self.array, ctypes.c_void_p).value

    def bind(self):
        pass

    def unbind(self):
        pass
    
    def set_data(self, data):
        ctypes.memmove(self.ptr, data, self.size)

    def set_data_region(self, data, start, length):
        ctypes.memmove(self.ptr + start, data, length)

    def map(self, invalidate=False):
        return self.array

    def unmap(self):
        pass

    def delete(self):
        pass

def align(v, align):
    return ((v - 1) & ~(align - 1)) + align

def serialized(count, *formats):
    accessors = [Accessor.from_string(format) for format in formats]
    offset = 0
    for accessor in accessors:
        offset = align(offset, accessor.align)
        accessor.offset = offset
        offset += count * accessor.size
    return accessors

def interleaved(*formats):
    accessors = [Accessor.from_string(format) for format in formats]
    stride = 0
    for accessor in accessors:
        stride = align(stride, accessor.align)    
        accessor.offset = stride
        stride += accessor.size
    for accessor in accessors:
        accessor.stride = stride
    return accessors

class Accessor(object):
    _pointer_functions = {
        'c': (lambda self: lambda pointer:
                glColorPointer(self.count, self.gl_type, 
                               self.stride, self.offset + pointer)),
        'e': (lambda self: lambda pointer:
                glEdgeFlagPointer(self.stride, self.offset + pointer)),
        'f': (lambda self: lambda pointer:
                glFogCoordPointer(self.gl_type, self.stride, 
                                  self.offset + pointer)),
        'n': (lambda self: lambda pointer:
                glNormalPointer(self.gl_type, self.stride, 
                                self.offset + pointer)),
        's': (lambda self: lambda pointer:
                glSecondaryColorPointer(self.count, self.gl_type, 
                                        self.stride, self.offset + pointer)),
        't': (lambda self: lambda pointer:
                glTexCoordPointer(self.count, self.gl_type, self.stride, 
                                  self.offset + pointer)),
        'v': (lambda self: lambda pointer:
                glVertexPointer(self.count, self.gl_type, self.stride,
                                self.offset + pointer)),
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
           (?P<dest_index>[0-9]+)a)
        (?P<normalized>n?)
        (?P<count>[1234])
        (?P<type>[bBsSiIfd])
    ''', re.VERBOSE)
    
    def __init__(self, dest, count, gl_type, 
                 normalized=False, dest_index=None):
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
        
        if dest == 'a':
            self.set_pointer = \
                  (lambda pointer:
                     glVertexAttribPointer(dest_index, self.count, self.gl_type,
                                           normalized, self.stride, 
                                           pointer))
            self.enable = lambda: glEnableVertexAttribArray(dest_index)
        else:
            self.set_pointer = self._pointer_functions[dest](self)
            enable_bit = self._enable_bits[dest]
            self.enable = lambda: glEnableClientState(enable_bit)

        self.gl_type = gl_type
        self.c_type = _c_types[gl_type]
        self.count = count
        self.align = ctypes.sizeof(self.c_type)
        self.size = count * self.align

        # Defaults
        self.stride = self.size
        self.offset = 0

    @classmethod
    def from_string(cls, format):
        match = cls._format_re.match(format.lower())
        dest = match.group('dest')
        count = int(match.group('count'))
        gl_type = cls._gl_types[match.group('type')]
        normalized = match.group('normalized')
        dest_index = match.group('dest_index')
        if dest_index:
            dest_index = int(dest_index)
        return cls(dest, count, gl_type, normalized, dest_index)

    def to_array(self, array):
        '''Convert a Python sequence into a ctypes array.'''
        n = len(array)
        assert (n % self.count == 0,
            'Length of data array is not multiple of element count.')
        return (self.c_type * n)(*array)

    def set(self, buffer, data):
        data = self.to_array(data)
        if self.stride == self.size:
            buffer.set_data_region(data, self.offset, len(data) * self.align)
        else:
            c = self.count
            n = len(data)
            offset = self.offset // self.align
            stride = self.stride // self.align
            dest_n = n // self.count * stride 
            dest_bytes = buffer.map()
            dest_data = ctypes.cast(dest_bytes, 
                ctypes.POINTER(self.c_type * dest_n)).contents
            for i in range(n // c):
                s = offset + i * stride
                t = i * c
                for j in range(c):
                    dest_data[s + j] = data[t + j]
            buffer.unmap()

class ElementIndexAccessor(object):
    def __init__(self, gl_type):
        self.gl_type = gl_type
        self.c_type = _c_types[gl_type]
        self.size = ctypes.sizeof(self.c_type)
        self.offset = 0
        
    def set(self, buffer, data):
        data = (self.c_type * len(data))(*data)
        buffer.set_data_region(data, self.offset, len(data) * self.size)

    def draw(self, buffer, mode, start, count):
        glDrawElements(mode, count, self.gl_type, buffer.ptr +
                       self.offset + start)
