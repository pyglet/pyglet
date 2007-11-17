#!/usr/bin/python
# $Id:$

import ctypes
import re
import sys

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

def create(size, target=GL_ARRAY_BUFFER, usage=GL_DYNAMIC_DRAW, 
           vbo=True, backed=False):
    '''Create a buffer of vertex data.
    '''
    if vbo and gl_info.have_version(1, 5):
        if backed:
            return BackedVertexBufferObject(size, target, usage)
        else:
            return VertexBufferObject(size, target, usage)
    else:
        return VertexArray(size)


class AbstractBuffer(object):
    #: Memory offset of buffer needed by glVertexPointer etc.
    ptr = 0
    #: Size of buffer, in bytes.
    size = 0

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
    def __init__(self, size, target, usage):
        self.size = size
        self.target = target
        self.usage = usage

        id = GLuint()
        glGenBuffers(1, id)
        self.id = id.value
        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        glBindBuffer(target, self.id)
        glBufferData(target, self.size, None, self.usage)
        glPopClientAttrib()

    def bind(self):
        glBindBuffer(self.target, self.id)

    def unbind(self):
        glBindBuffer(self.target, 0)

    def set_data(self, data):
        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        glBindBuffer(self.target, self.id)
        glBufferData(self.target, self.size, data, self.usage)
        glPopClientAttrib()

    def set_data_region(self, data, start, length):
        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        glBindBuffer(self.target, self.id)
        glBufferSubData(self.target, start, length, data)
        glPopClientAttrib()

    def map(self, invalidate=False):
        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        glBindBuffer(self.target, self.id)
        if invalidate:
            glBufferData(self.target, self.size, None, self.usage)
        glPopClientAttrib()
        return ctypes.cast(glMapBuffer(self.target, GL_WRITE_ONLY),
                           ctypes.POINTER(ctypes.c_byte * self.size)).contents

    def unmap(self):
        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        glUnmapBuffer(self.target)
        glPopClientAttrib()

    def delete(self):
        id = gl.GLuint(self.id)
        glDeleteBuffers(1, id)

    def resize(self, size):
        # Map, create a copy, then reinitialize.
        temp = (ctypes.c_byte * size)()

        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        glBindBuffer(self.target, self.id)
        data = glMapBuffer(self.target, GL_READ_ONLY)
        ctypes.memmove(temp, data, min(size, self.size))
        glUnmapBuffer(self.target)

        self.size = size
        glBufferData(self.target, self.size, temp, self.usage)
        glPopClientAttrib()

class BackedVertexBufferObject(VertexBufferObject):
    '''A VBO with system-memory backed store.
    
    Updates to the data via `set_data`, `set_data_region` and `map` will be
    held in local memory until `bind` is called.  The advantage is that fewer
    OpenGL calls are needed, increasing performance.  
    
    There may also be less performance penalty for resizing this buffer.

    Updates to data via `map` are committed immediately.
    '''
    def __init__(self, size, target, usage):
        super(BackedVertexBufferObject, self).__init__(size, target, usage)
        self.data = (ctypes.c_byte * size)()
        self.data_ptr = ctypes.cast(self.data, ctypes.c_void_p).value
        self._dirty_min = sys.maxint
        self._dirty_max = 0

    def bind(self):
        # Commit pending data
        super(BackedVertexBufferObject, self).bind()
        size = self._dirty_max - self._dirty_min
        if size > 0:
            if size == self.size:
                glBufferData(self.target, self.size, self.data, self.usage)
            else:
                glBufferSubData(self.target, self._dirty_min, size,
                    self.data_ptr + self._dirty_min)
            self._dirty_min = sys.maxint
            self._dirty_max = 0

    def set_data(self, data):
        super(VertexBufferObject, self).set_data(data)
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

    def resize(self, size):
        data = (ctypes.c_byte * size)()
        ctypes.memmove(data, self.data, min(size, self.size))
        self.data = data
        self.data_ptr = ctypes.cast(self.data, ctypes.c_void_p).value
        
        self.size = size
        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        glBindBuffer(self.target, self.id)
        glBufferData(self.target, self.size, self.data, self.usage)
        glPopClientAttrib()

        self._dirty_min = sys.maxint
        self._dirty_max = 0

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

    def resize(self, size):
        array = (ctypes.c_byte * size)()
        ctypes.memmove(array, self.array, min(size, self.size))
        self.size = size
        self.array = array
        self.ptr = ctypes.cast(self.array, ctypes.c_void_p).value

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
            self.dest_index = dest_index
        else:
            self.set_pointer = self._pointer_functions[dest](self)
            enable_bit = self._enable_bits[dest]
            self.enable = lambda: glEnableClientState(enable_bit)

        self.dest = dest # used by allocator
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
        '''Create an accessor given a format description such as "V3F".
        The initial stride and offset of the accessor will be 0.

        Format strings have the following syntax::

            destination count type

        ``destination`` gives the type of vertex attribute this accessor
        describes.  A number followed by ``A`` specifies a generic vertex
        attribute.  For example, ``3A`` is generic vertex attribute with
        index 3.  The predefined vertex attributes are specified as follows:

        ``C``
            Vertex color
        ``E``
            Edge flag
        ``F``
            Fog coordinate
        ``N``
            Normal vector
        ``S``
            Secondary color
        ``T``
            Texture coordinate
        ``V``
            Vertex coordinate

        ``count`` gives the number of data items in the attribute.  For
        example, a 3D vertex position has a count of 3.  Some destinations
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

        Some destinations constrain the possible data types; for example,
        normal vectors must use one of the signed data types.  The use of
        some data types, while not illegal, may have severe performance
        concerns.  For example, the use of ``GLdouble`` is discouraged,
        and colours should be specified with ``GLubyte``.

        The format string is case-insensitive and whitespace is prohibited.

        Some examples follow:

        ``V3F``
            3-float vertex position
        ``C4B``
            4-byte colour
        ``1Eb``
            Edge flag
        ``0A3F``
            3-float generic vertex attribute 0
        ``1A1I``
            Integer generic vertex attribute 1

        '''
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

    def set(self, buffer, data, start=0):
        data = self.to_array(data)
        if self.stride == self.size:
            buffer.set_data_region(data, 
                                   self.offset + start * self.stride, 
                                   len(data) * self.align)
        else:
            c = self.count
            n = len(data)
            offset = (self.offset + start * self.stride) // self.align
            stride = self.stride // self.align
            dest_n =  (n // self.count + start) * stride 
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

class Allocator(object):
    _accessor_names = {
        'c': 'colors',
        'e': 'edge_flags',
        'f': 'fog_coords',
        'n': 'normals',
        's': 'secondary_colors',
        't': 'tex_coords',
        'v': 'vertices'
    }

    _gl_usage = {
        'static': GL_STATIC_DRAW,
        'dynamic': GL_DYNAMIC_DRAW,
        'stream': GL_STREAM_DRAW,
    }

    _initial_count = 16

    def __init__(self, *formats):
        self.count = 0
        self.max_count = self._initial_count

        interleaved_formats = []
        accessors = []
        self.buffer_accessors = []   # list of (buffer, accessors)
        for format in formats:
            if '/' in format:
                format, usage = format.split('/', 1)
                assert usage in self._gl_usage, 'Invalid usage "%s"' % usage
                usage = self._gl_usage[usage]
            else:
                usage = GL_DYNAMIC_DRAW

            if usage == GL_STATIC_DRAW:
                # Group static usages into an interleaved buffer
                interleaved_formats.append(format)
            else:
                # Create non-interlaved buffer
                accessor = Accessor.from_string(format)
                accessors.append(accessor)
                accessor.buffer = create(accessor.stride * self.max_count,
                                         usage=usage,
                                         backed=True)
                accessor.buffer.element_size = accessor.stride
                accessor.buffer.accessors = (accessor,)
                self.buffer_accessors.append(
                    (accessor.buffer, (accessor,)))

        # Create buffer for interleaved data
        if interleaved_formats:
            interleaved_accessors = interleaved(*interleaved_formats)
            buffer = create(interleaved_accessors[0].stride * self.max_count,
                            usage=GL_STATIC_DRAW,
                            backed=False)
            buffer.element_size = interleaved_accessors[0].stride
            self.buffer_accessors.append(
                (buffer, interleaved_accessors))

            accessors.extend(interleaved_accessors)
            for accessor in interleaved_accessors:
                accessor.buffer = buffer

        # Create named attributes for each accessor
        self.accessors = {}
        for accessor in accessors:
            if accessor.dest == 'a':
                index = attribute.dest_index
                if 'generic' not in self.accessors:
                    self.accessors['generic'] = {}
                assert (index not in self.accessors['generic'],
                    'More than one generic attribute with index %d' % index)
                self.accessors['generic'][index] = accessor
            else:
                name = self._accessor_names[accessor.dest]
                assert (name not in self.accessors,
                    'More than one "%s" attribute given' % name)
                self.accessors[name] = accessor

    def alloc(self, count):
        '''Allocate `count` vertices.

        :rtype: AllocatorRegion
        '''
        index = self.count

        if index + self.count >= self.max_count:
            # Reallocate the buffers
            self.max_count *= 2
            for buffer, _ in self.buffer_accessors:
                buffer.resize(self.max_count * buffer.element_size)
        
        self.count += count

        return AllocatorRegion(self, index, count)

    def draw(self, mode):
        '''Draw all vertices currently allocated without indexing.

        All vertices are drawn using the given `mode`, e.g. ``GL_QUADS``.
        '''
        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        for buffer, accessors in self.buffer_accessors:
            buffer.bind()
            for accessor in accessors:
                accessor.enable()
                accessor.set_pointer(accessor.buffer.ptr)

        # TODO free lists
        glDrawArrays(mode, 0, self.count)
        
        for buffer, _ in self.buffer_accessors:
            buffer.unbind()
        glPopClientAttrib()

class AllocatorRegion(object):
    '''Small region of the buffers managed by an `Allocator`.  Create
    with `Allocator.alloc`.
    '''
    
    # This object must be small and fast to initialise, as it should be
    # suitable for individual sprites and text strings.
    __slots__ = ('allocator', 'start', 'count')
    
    def __init__(self, allocator, start, count):
        self.allocator = allocator
        self.start = start
        self.count = count

    def set_vertices(self, data):
        accessor = self.allocator.accessors['vertices']
        accessor.set(accessor.buffer, data, self.start)
    
    vertices = property(None, set_vertices)

    def set_tex_coords(self, data):
        accessor = self.allocator.accessors['tex_coords']
        accessor.set(accessor.buffer, data, self.start)

    tex_coords = property(None, set_tex_coords)
