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

def create_buffer(size, target=GL_ARRAY_BUFFER, usage=GL_DYNAMIC_DRAW, 
                  vbo=True, backed=False):
    '''Create a buffer of vertex data.

    :Parameters:
        `size` : int
            Size of the buffer, in bytes
        `target` : int
            OpenGL target buffer
        `usage` : int
            OpenGL usage constant
        `vbo` : bool
            True if a `VertexBufferObject` should be created if the driver
            supports it; otherwise only a `VertexArray` is created.
        `backed` : bool
            True if a VBO should be backed by a system store using
            `BackedVertexBufferObject`.

    :rtype: `AbstractBuffer`
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

    def get_region(self, start, size, ptr_type):
        '''Map a region of the buffer into a ctypes array of the desired
        type.  This region does not need to be unmapped, but will become
        invalid if the buffer is resized.
        '''
        raise NotImplementedError('abstract')

    def delete(self):
        raise NotImplementedError('abstract')

class AbstractBufferRegion(object):
    array = None
    
    def invalidate(self):
        '''Mark this region as changed.'''
        pass

class VertexBufferObjectRegion(AbstractBufferRegion):
    def __init__(self, buffer, start, end, array):
        self.buffer = buffer
        self.start = start
        self.end = end
        self.array = array

    def invalidate(self):
        buffer = self.buffer
        buffer._dirty_min = min(buffer._dirty_min, self.start)
        buffer._dirty_max = max(buffer._dirty_max, self.end)

class VertexArrayRegion(AbstractBufferRegion):
    def __init__(self, array):
        self.array = array

class IndirectArrayRegion(AbstractBufferRegion):
    def __init__(self, region, size, component_count, component_stride):
        self.region = region
        self.size = size
        self.count = component_count
        self.stride = component_stride
        self.array = self

    def __getitem__(self, index):
        if not isinstance(index, slice):
            elem = index // self.count
            j = index % self.count
            return self.region.array[elem * self.stride + j]

        start = index.start or 0
        stop = index.stop
        step = index.step or 1
        if stop is None:
            stop = self.size

        # ctypes does not support stepped slicing, so do the work in a list
        # and copy it back.
        data = self.region.array[:]
        value = [0] * ((stop - start) // step)
        stride = self.stride
        count = self.count
        for i in range(self.count):
            value[start + i:stop + i:count * step] = \
                data[start * stride + i:stop * stride + i:stride * step]
        return value

    def __setitem__(self, index, value):
        if not isinstance(index, slice):
            elem = index // self.count
            j = index % self.count
            self.region.array[elem * self.stride + j] = value
            return

        start = index.start or 0
        stop = index.stop
        step = index.step or 1
        if stop is None:
            stop = self.size

        # ctypes does not support stepped slicing, so do the work in a list
        # and copy it back.
        data = self.region.array[:]
        stride = self.stride
        count = self.count
        for i in range(self.count):
            data[start * stride + i:stop * stride + i:stride * step] = \
                value[start + i:stop + i:count * step]
        self.region.array[:] = data

    def invalidate(self):
        self.region.invalidate()
        
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
        ptr = ctypes.cast(glMapBuffer(self.target, GL_WRITE_ONLY),
                          ctypes.POINTER(ctypes.c_byte * self.size)).contents
        glPopClientAttrib()
        return ptr

    def unmap(self):
        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        glUnmapBuffer(self.target)
        glPopClientAttrib()

    def get_region(self, start, size, ptr_type):
        raise NotImplementedError('Not supported, use BackedVertexBufferObject')

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

    def get_region(self, start, size, ptr_type):
        array = ctypes.cast(self.data_ptr + start, ptr_type).contents
        return VertexBufferObjectRegion(self, start, start + size, array)

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

    def get_region(self, start, size, ptr_type):
        array = ctypes.cast(self.ptr + start, ptr_type).contents
        return VertexArrayRegion(array)

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

def interleave_attributes(attributes):
    '''Adjust the offsets and strides of the given attributes so that
    they are interleaved.  Alignment constraints are respected.
    '''
    stride = 0
    max_size = 0
    for attribute in attributes:
        stride = align(stride, attribute.align)    
        attribute.offset = stride
        stride += attribute.size
        max_size = max(max_size, attribute.size)
    stride = align(stride, max_size)
    for attribute in attributes:
        attribute.stride = stride

def serialize_attributes(count, attributes):
    '''Adjust the offsets of the given attributes so that they are
    packed serially against each other for `count` vertices.
    '''
    offset = 0
    for attribute in attributes:
        offset = align(offset, attribute.align)
        attribute.offset = offset
        offset += count * attribute.stride

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
    _fixed_count = None
    
    def __init__(self, count, gl_type):
        assert count in (1, 2, 3, 4), 'Component count out of range'
        self.gl_type = gl_type
        self.c_type = _c_types[gl_type]
        self.count = count
        self.align = ctypes.sizeof(self.c_type)
        self.size = count * self.align
        self.stride = self.size
        self.offset = 0

    def enable(self):
        raise NotImplementedError('abstract')

    def set_pointer(self, offset):
        raise NotImplementedError('abstract')

    def get_region(self, buffer, start, count):
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
            return IndirectArrayRegion(region, array_count, self.count, elem_stride)

    def to_array(self, array):
        '''Convert a Python sequence into a ctypes array.'''
        n = len(array)
        assert n % self.count == 0, \
            'Length of data array is not multiple of element count.'
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

class ColorAttribute(AbstractAttribute):
    plural = 'colors'
    
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

_attribute_classes = {
    'c': ColorAttribute,
    'e': EdgeFlagAttribute,
    'f': FogCoordAttribute,
    'n': NormalAttribute,
    's': SecondaryColorAttribute,
    't': TexCoordAttribute,
    'v': VertexAttribute,
}

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

_usage_format_re = re.compile(r'''
    (?P<attribute>[^/]*)
    (/ (?P<usage> static|dynamic|stream))?
''', re.VERBOSE)

_gl_usages = {
    'static': GL_STATIC_DRAW,
    'dynamic': GL_DYNAMIC_DRAW,
    'stream': GL_STREAM_DRAW,
}

def create_attribute_usage(format):
    '''Create an attribute and usage pair from a format string.  The
    format string is the same as that used for `create_attribute`, with
    the addition of an optional usage component::

        usage ::= attribute ( '/' ('static' | 'dynamic' | 'stream') )?

    If the usage is not given it defaults to 'dynamic'.
    
    Some examples:

    ``v3f/stream``
        3D vertex position using floats, for stream usage
    ``c4b/static``
        4-byte color attribute, for static usage

    :return: attribute, usage  
    '''
    match = _usage_format_re.match(format)
    attribute_format = match.group('attribute')
    attribute = create_attribute(attribute_format)
    usage = match.group('usage')
    if usage:
        usage = _gl_usages[usage]
    else:
        usage = GL_DYNAMIC_DRAW

    return (attribute, usage)

def create_domain(*attribute_usage_formats):
    '''Create a vertex domain covering the given attribute usage formats.
    See documentation for `create_attribute_usage` and `create_attribute` for
    the grammar of these format strings.

    :rtype: `VertexDomain`
    '''
    attribute_usages = [create_attribute_usage(f) \
                        for f in attribute_usage_formats]
    return VertexDomain(attribute_usages)

def create_indexed_domain(*attribute_usage_formats):
    attribute_usages = [create_attribute_usage(f) \
                        for f in attribute_usage_formats]
    return IndexedVertexDomain(attribute_usages)


class VertexDomain(object):
    _version = 0
    _initial_count = 16

    def __init__(self, attribute_usages):
        self.count = 0
        self.max_count = self._initial_count

        static_attributes = []
        attributes = []
        self.buffer_attributes = []   # list of (buffer, attributes)
        for attribute, usage in attribute_usages:
            if usage == GL_STATIC_DRAW:
                # Group attributes for interleaved buffer
                static_attributes.append(attribute)
            else:
                # Create non-interleaved buffer
                attributes.append(attribute)
                attribute.buffer = create_buffer(
                    attribute.stride * self.max_count, usage=usage, backed=True)
                attribute.buffer.element_size = attribute.stride
                attribute.buffer.attributes = (attribute,)
                self.buffer_attributes.append(
                    (attribute.buffer, (attribute,)))

        # Create buffer for interleaved data
        if static_attributes:
            interleave_attributes(static_attributes)
            stride = static_attributes[0].stride
            buffer = create_buffer(
                stride * self.max_count, usage=GL_STATIC_DRAW, backed=True)
            buffer.element_size = stride
            self.buffer_attributes.append(
                (buffer, static_attributes))

            attributes.extend(static_attributes)
            for attribute in static_attributes:
                attribute.buffer = buffer

        # Create named attributes for each attribute
        self.attributes = {}
        for attribute in attributes:
            if isinstance(attribute, GenericAttribute):
                index = attribute.index
                if 'generic' not in self.attributes:
                    self.attributes['generic'] = {}
                assert index not in self.attributes['generic'], \
                    'More than one generic attribute with index %d' % index
                self.attributes['generic'][index] = attribute
            else:
                name = attribute.plural
                assert name not in self.attributes, \
                    'More than one "%s" attribute given' % name
                self.attributes[name] = attribute

    def add(self, **data):
        '''Create vertices in this domain and initialise them with
        given attribute data.'''

    def create_group(self, count):
        '''Create a `VertexGroup` in this domain of size `count`.

        :rtype: `VertexGroup`
        '''
        index = self.count

        if index + count >= self.max_count:
            # Reallocate the buffers
            while self.max_count < index + count:
                self.max_count *= 2
            self._version += 1
            for buffer, _ in self.buffer_attributes:
                buffer.resize(self.max_count * buffer.element_size)
        
        self.count += count

        return VertexGroup(self, index, count)

    def draw(self, mode):
        '''Draw all vertices currently allocated without indexing.

        All vertices are drawn using the given `mode`, e.g. ``GL_QUADS``.
        '''
        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        for buffer, attributes in self.buffer_attributes:
            buffer.bind()
            for attribute in attributes:
                attribute.enable()
                attribute.set_pointer(attribute.buffer.ptr)

        # TODO free lists
        glDrawArrays(mode, 0, self.count)
        
        for buffer, _ in self.buffer_attributes:
            buffer.unbind()
        glPopClientAttrib()

class IndexedVertexDomain(VertexDomain):
    _initial_index_count = 16

    def __init__(self, attribute_usages, index_gl_type=GL_UNSIGNED_INT):
        super(IndexedVertexDomain, self).__init__(attribute_usages)

        self.index_count = 0
        self.max_index_count = self._initial_index_count
        
        self.index_gl_type = index_gl_type
        self.index_c_type = _c_types[index_gl_type]
        self.index_element_size = ctypes.sizeof(self.index_c_type)
        self.index_buffer = create_buffer(
            self.max_index_count * self.index_element_size, 
            target=GL_ELEMENT_ARRAY_BUFFER, backed=True)

    def create_group(self, count, index_count):
        index = self.count
        if index + count >= self.max_count:
            # Reallocate the buffers
            while self.max_count < index + count:
                self.max_count *= 2
            self._version += 1
            for buffer, _ in self.buffer_attributes:
                buffer.resize(self.max_count * buffer.element_size)
        self.count += count

        index_start = self.index_count
        if index_start + index_count > self.max_index_count:
            # Reallocate index buffer
            while self.max_index_count < index_start + index_count:
                self.max_index_count *= 2
            self._version += 1
            self.index_buffer.resize(
                self.max_index_count * self.index_element_size)
        self.index_count += index_count

        return IndexedVertexGroup(self, index, count, index_start, index_count) 

    def get_index_region(self, start, count):
        byte_start = self.index_element_size * start
        byte_count = self.index_element_size * count
        ptr_type = ctypes.POINTER(self.index_c_type * count)
        return self.index_buffer.get_region(byte_start, byte_count, ptr_type)

    def draw(self, mode):
        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        for buffer, attributes in self.buffer_attributes:
            buffer.bind()
            for attribute in attributes:
                attribute.enable()
                attribute.set_pointer(attribute.buffer.ptr)

        # TODO free lists
        self.index_buffer.bind()
        glDrawElements(mode, self.index_count, self.index_gl_type,
            self.index_buffer.ptr)
        
        self.index_buffer.unbind()
        for buffer, _ in self.buffer_attributes:
            buffer.unbind()
        glPopClientAttrib()


class VertexGroup(object):
    '''Small region of the buffers managed by a `VertexDomain`.  Create
    with `VertexDomain.create`.
    '''
    
    def __init__(self, domain, start, count):
        self.domain = domain
        self.start = start
        self.count = count

    def resize(self, count):
        '''Resize this group.'''

    def delete(self):
        '''Delete this group.'''

    _vertices_cache = None
    _vertices_cache_version = None

    def _get_vertices(self):
        if (self._vertices_cache_version != self.domain._version):
            domain = self.domain
            attribute = domain.attributes['vertices']
            self._vertices_cache = attribute.get_region(
                attribute.buffer, self.start, self.count)
            self._vertices_cache_version = domain._version

        region = self._vertices_cache
        region.invalidate()
        return region.array

    def _set_vertices(self, data):
        self._get_vertices()[:] = data
    
    vertices = property(_get_vertices, _set_vertices)

    _normals_cache = None
    _normals_cache_version = None

    def _get_normals(self):
        if (self._normals_cache_version != self.domain._version):
            domain = self.domain
            attribute = domain.attributes['normals']
            self._normals_cache = attribute.get_region(
                attribute.buffer, self.start, self.count)
            self._normals_cache_version = domain._version

        region = self._normals_cache
        region.invalidate()
        return region.array

    def _set_normals(self, data):
        self._get_normals()[:] = data

    normals = property(_get_normals, _set_normals)

    _tex_coords_cache = None
    _tex_coords_cache_version = None

    def _get_tex_coords(self):
        if (self._tex_coords_cache_version != self.domain._version):
            domain = self.domain
            attribute = domain.attributes['tex_coords']
            self._tex_coords_cache = attribute.get_region(
                attribute.buffer, self.start, self.count)
            self._tex_coords_cache_version = domain._version

        region = self._tex_coords_cache
        region.invalidate()
        return region.array

    def _set_tex_coords(self, data):
        self._get_tex_coords()[:] = data

    tex_coords = property(_get_tex_coords, _set_tex_coords)

class IndexedVertexGroup(VertexGroup):
    def __init__(self, domain, start, count, index_start, index_count):
        super(IndexedVertexGroup, self).__init__(domain, start, count)

        self.index_start = index_start
        self.index_count = index_count

    _indices_cache = None
    _indices_cache_version = None

    def _get_indices(self):
        if self._indices_cache_version != self.domain._version:
            domain = self.domain
            self._indices_cache = domain.get_index_region(
                self.index_start, self.index_count)
            self._indices_cache_version = domain._version

        region = self._indices_cache
        region.invalidate()
        return region.array

    def _set_indices(self, data):
        self._get_indices()[:] = data

    indices = property(_get_indices, _set_indices)
