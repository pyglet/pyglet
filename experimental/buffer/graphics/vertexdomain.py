#!/usr/bin/python
# $Id:$

'''Manage related vertex attributes within a single vertex domain.

A vertex "domain" consists of a set of attribute descriptions that together
describe the layout of one or more vertex buffers which are used together to
specify the vertices in a primitive.  Additionally, the domain manages the
buffers used to store the data and will resize them as necessary to accomodate
new vertices.

Domains can optionally be indexed, in which case they also manage a buffer
containing vertex indices.  This buffer is grown separately and has no size
relation to the attribute buffers.

Applications can create vertices (and optionally, indices) within a domain
with the `VertexDomain.create` method.  This returns a `VertexList`
representing the list of vertices created.  The vertex attribute data within
the group can be modified, and the changes will be made to the underlying
buffers automatically.

The entire domain can be efficiently drawn in one step with the
`VertexDomain.draw` method, assuming all the vertices comprise primitives of
the same OpenGL primitive mode.
'''

import ctypes
import re

from pyglet.gl import *

# Local imports
import vertexattribute
import vertexbuffer

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
    attribute = vertexattribute.create_attribute(attribute_format)
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
    '''Create an indexed vertex domain covering the given attribute usage
    formats.  See documentation for `create_attribute_usage` and
    `create_attribute` for the grammar of these format strings.

    :rtype: `VertexDomain`
    '''
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
                attribute.buffer = vertexbuffer.create_mappable_buffer(
                    attribute.stride * self.max_count, usage=usage)
                attribute.buffer.element_size = attribute.stride
                attribute.buffer.attributes = (attribute,)
                self.buffer_attributes.append(
                    (attribute.buffer, (attribute,)))

        # Create buffer for interleaved data
        if static_attributes:
            vertexattribute.interleave_attributes(static_attributes)
            stride = static_attributes[0].stride
            buffer = vertexbuffer.create_mappable_buffer(
                stride * self.max_count, usage=GL_STATIC_DRAW)
            buffer.element_size = stride
            self.buffer_attributes.append(
                (buffer, static_attributes))

            attributes.extend(static_attributes)
            for attribute in static_attributes:
                attribute.buffer = buffer

        # Create named attributes for each attribute
        self.attributes = attributes
        self.attribute_names = {}
        for attribute in attributes:
            if isinstance(attribute, vertexattribute.GenericAttribute):
                index = attribute.index
                if 'generic' not in self.attributes:
                    self.attributes['generic'] = {}
                assert index not in self.attributes['generic'], \
                    'More than one generic attribute with index %d' % index
                self.attribute_names['generic'][index] = attribute
            else:
                name = attribute.plural
                assert name not in self.attributes, \
                    'More than one "%s" attribute given' % name
                self.attribute_names[name] = attribute

    def add(self, **data):
        '''Create vertices in this domain and initialise them with
        given attribute data.'''

    def create(self, count):
        '''Create a `VertexList` in this domain.

        :Parameters:
            `count` : int
                Number of vertices to create.

        :rtype: `VertexList`
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

        return VertexList(self, index, count)

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

class VertexList(object):
    '''A list of vertices within a `VertexDomain`.  Use
    `VertexDomain.create` to construct this list.
    '''
    
    def __init__(self, domain, start, count):
        self.domain = domain
        self.start = start
        self.count = count

    def resize(self, count):
        '''Resize this group.'''

    def delete(self):
        '''Delete this group.'''

    def set_attribute_data(self, i, data):
        attribute = self.domain.attributes[i]
        # TODO without region
        region = attribute.get_region(attribute.buffer, self.start, self.count)
        region.array[:] = data
        region.invalidate()

    _vertices_cache = None
    _vertices_cache_version = None

    def _get_vertices(self):
        if (self._vertices_cache_version != self.domain._version):
            domain = self.domain
            attribute = domain.attribute_names['vertices']
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
            attribute = domain.attribute_names['normals']
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
            attribute = domain.attribute_names['tex_coords']
            self._tex_coords_cache = attribute.get_region(
                attribute.buffer, self.start, self.count)
            self._tex_coords_cache_version = domain._version

        region = self._tex_coords_cache
        region.invalidate()
        return region.array

    def _set_tex_coords(self, data):
        self._get_tex_coords()[:] = data

    tex_coords = property(_get_tex_coords, _set_tex_coords)


class IndexedVertexDomain(VertexDomain):
    _initial_index_count = 16

    def __init__(self, attribute_usages, index_gl_type=GL_UNSIGNED_INT):
        super(IndexedVertexDomain, self).__init__(attribute_usages)

        self.index_count = 0
        self.max_index_count = self._initial_index_count
        
        self.index_gl_type = index_gl_type
        self.index_c_type = vertexattribute._c_types[index_gl_type]
        self.index_element_size = ctypes.sizeof(self.index_c_type)
        self.index_buffer = vertexbuffer.create_mappable_buffer(
            self.max_index_count * self.index_element_size, 
            target=GL_ELEMENT_ARRAY_BUFFER)

    def create(self, count, index_count):
        '''Create an `IndexedVertexList` in this domain.

        :Parameters:
            `count` : int
                Number of vertices to create
            `index_count`
                Number of indices to create

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

        index_start = self.index_count
        if index_start + index_count > self.max_index_count:
            # Reallocate index buffer
            while self.max_index_count < index_start + index_count:
                self.max_index_count *= 2
            self._version += 1
            self.index_buffer.resize(
                self.max_index_count * self.index_element_size)
        self.index_count += index_count

        return IndexedVertexList(self, index, count, index_start, index_count) 

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

class IndexedVertexList(VertexList):
    '''A list of vertices within an `IndexedVertexDomain` that are indexed.
    Use `IndexedVertexDomain.create` to construct this list.
    '''
    def __init__(self, domain, start, count, index_start, index_count):
        super(IndexedVertexList, self).__init__(domain, start, count)

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
