"""Manage related vertex attributes within a single vertex domain.

A vertex "domain" consists of a set of attribute descriptions that together
describe the layout of one or more vertex buffers which are used together to
specify the vertices in a primitive.  Additionally, the domain manages the
buffers used to store the data and will resize them as necessary to accommodate
new vertices.

Domains can optionally be indexed, in which case they also manage a buffer
containing vertex indices.  This buffer is grown separately and has no size
relation to the attribute buffers.

Applications can create vertices (and optionally, indices) within a domain
with the :py:meth:`VertexDomain.create` method.  This returns a
:py:class:`VertexList` representing the list of vertices created.  The vertex
attribute data within the group can be modified, and the changes will be made
to the underlying buffers automatically.

The entire domain can be efficiently drawn in one step with the
:py:meth:`VertexDomain.draw` method, assuming all the vertices comprise
primitives of the same OpenGL primitive mode.
"""

import ctypes

import pyglet

from pyglet.gl import *
from pyglet.graphics import allocation, shader, vertexarray
from pyglet.graphics.vertexbuffer import BufferObject, MappableBufferObject


def _nearest_pow2(v):
    # From http://graphics.stanford.edu/~seander/bithacks.html#RoundUpPowerOf2
    # Credit: Sean Anderson
    v -= 1
    v |= v >> 1
    v |= v >> 2
    v |= v >> 4
    v |= v >> 8
    v |= v >> 16
    return v + 1


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


class VertexDomain:
    """Management of a set of vertex lists.

    Construction of a vertex domain is usually done with the
    :py:func:`create_domain` function.
    """
    version = 0
    _initial_count = 16

    def __init__(self, program, attribute_meta):
        self.program = program
        self.attribute_meta = attribute_meta
        self.allocator = allocation.Allocator(self._initial_count)
        self.vao = vertexarray.VertexArray()

        self.attributes = []
        self.buffer_attributes = []  # list of (buffer, attributes)

        for name, meta in attribute_meta.items():
            assert meta['format'][0] in _gl_types, f"'{meta['format']}' is not a valid atrribute format for '{name}'."
            location = meta['location']
            count = meta['count']
            gl_type = _gl_types[meta['format'][0]]
            normalize = 'n' in meta['format']
            attribute = shader.Attribute(name, location, count, gl_type, normalize)
            self.attributes.append(attribute)

            # Create buffer:
            attribute.buffer = MappableBufferObject(attribute.stride * self.allocator.capacity)
            attribute.buffer.element_size = attribute.stride
            attribute.buffer.attributes = (attribute,)
            self.buffer_attributes.append((attribute.buffer, (attribute,)))

        # Create named attributes for each attribute
        self.attribute_names = {}
        for attribute in self.attributes:
            self.attribute_names[attribute.name] = attribute

    def __del__(self):
        # Break circular refs that Python GC seems to miss even when forced
        # collection.
        for attribute in self.attributes:
            try:
                del attribute.buffer
            except AttributeError:
                pass

    def safe_alloc(self, count):
        """Allocate vertices, resizing the buffers if necessary."""
        try:
            return self.allocator.alloc(count)
        except allocation.AllocatorMemoryException as e:
            capacity = _nearest_pow2(e.requested_capacity)
            self.version += 1
            for buffer, _ in self.buffer_attributes:
                buffer.resize(capacity * buffer.element_size)
            self.allocator.set_capacity(capacity)
            return self.allocator.alloc(count)

    def safe_realloc(self, start, count, new_count):
        """Reallocate vertices, resizing the buffers if necessary."""
        try:
            return self.allocator.realloc(start, count, new_count)
        except allocation.AllocatorMemoryException as e:
            capacity = _nearest_pow2(e.requested_capacity)
            self.version += 1
            for buffer, _ in self.buffer_attributes:
                buffer.resize(capacity * buffer.element_size)
            self.allocator.set_capacity(capacity)
            return self.allocator.realloc(start, count, new_count)

    def create(self, count, index_count=None):
        """Create a :py:class:`VertexList` in this domain.

        :Parameters:
            `count` : int
                Number of vertices to create.
            `index_count`: None
                Ignored for non indexed VertexDomains

        :rtype: :py:class:`VertexList`
        """
        start = self.safe_alloc(count)
        return VertexList(self, start, count)

    def draw(self, mode):
        """Draw all vertices in the domain.

        All vertices in the domain are drawn at once. This is the
        most efficient way to render primitives.

        :Parameters:
            `mode` : int
                OpenGL drawing mode, e.g. ``GL_POINTS``, ``GL_LINES``, etc.

        """
        self.vao.bind()

        for buffer, attributes in self.buffer_attributes:
            buffer.bind()
            for attribute in attributes:
                attribute.enable()
                attribute.set_pointer(attribute.buffer.ptr)

        starts, sizes = self.allocator.get_allocated_regions()
        primcount = len(starts)
        if primcount == 0:
            pass
        elif primcount == 1:
            # Common case
            glDrawArrays(mode, starts[0], sizes[0])
        else:
            starts = (GLint * primcount)(*starts)
            sizes = (GLsizei * primcount)(*sizes)
            glMultiDrawArrays(mode, starts, sizes, primcount)

        for buffer, _ in self.buffer_attributes:
            buffer.unbind()

    def draw_subset(self, mode, vertex_list):
        """Draw a specific VertexList in the domain.

        The `vertex_list` parameter specifies a :py:class:`VertexList`
        to draw. Only primitives in that list will be drawn.

        :Parameters:
            `mode` : int
                OpenGL drawing mode, e.g. ``GL_POINTS``, ``GL_LINES``, etc.
            `vertex_list` : `VertexList`
                Vertex list to draw.

        """
        self.vao.bind()

        for buffer, attributes in self.buffer_attributes:
            buffer.bind()
            for attribute in attributes:
                attribute.enable()
                attribute.set_pointer(attribute.buffer.ptr)

        glDrawArrays(mode, vertex_list.start, vertex_list.count)

        for buffer, _ in self.buffer_attributes:
            buffer.unbind()

    @property
    def is_empty(self):
        return not self.allocator.starts

    def __repr__(self):
        return '<%s@%x %s>' % (self.__class__.__name__, id(self), self.allocator)


class VertexList:
    """A list of vertices within a :py:class:`VertexDomain`.  Use
    :py:meth:`VertexDomain.create` to construct this list.
    """
    def __init__(self, domain, start, count):
        self.domain = domain
        self.start = start
        self.count = count
        self._caches = {}
        self._cache_versions = {}

    def draw(self, mode):
        """Draw this vertex list in the given OpenGL mode.

        :Parameters:
            `mode` : int
                OpenGL drawing mode, e.g. ``GL_POINTS``, ``GL_LINES``, etc.

        """
        self.domain.draw_subset(mode, self)

    def resize(self, count, index_count=None):
        """Resize this group.

        :Parameters:
            `count` : int
                New number of vertices in the list.
            `index_count`: None
                Ignored for non indexed VertexDomains

        """
        new_start = self.domain.safe_realloc(self.start, self.count, count)
        if new_start != self.start:
            # Copy contents to new location
            for attribute in self.domain.attributes:
                old = attribute.get_region(attribute.buffer, self.start, self.count)
                new = attribute.get_region(attribute.buffer, new_start, self.count)
                new.array[:] = old.array[:]
                new.invalidate()
        self.start = new_start
        self.count = count

        for version in self._cache_versions:
            self._cache_versions[version] = None

    def delete(self):
        """Delete this group."""
        self.domain.allocator.dealloc(self.start, self.count)

    def migrate(self, domain):
        """Move this group from its current domain and add to the specified
        one.  Attributes on domains must match.  (In practice, used to change
        parent state of some vertices).

        :Parameters:
            `domain` : `VertexDomain`
                Domain to migrate this vertex list to.

        """
        assert list(domain.attribute_names.keys()) == list(self.domain.attribute_names.keys()),\
            'Domain attributes must match.'

        new_start = domain.safe_alloc(self.count)
        for key, old_attribute in self.domain.attribute_names.items():
            old = old_attribute.get_region(old_attribute.buffer, self.start, self.count)
            new_attribute = domain.attribute_names[key]
            new = new_attribute.get_region(new_attribute.buffer, new_start, self.count)
            new.array[:] = old.array[:]
            new.invalidate()

        self.domain.allocator.dealloc(self.start, self.count)
        self.domain = domain
        self.start = new_start

        for version in self._cache_versions:
            self._cache_versions[version] = None

    def set_attribute_data(self, name, data):
        attribute = self.domain.attribute_names[name]
        attribute.set_region(attribute.buffer, self.start, self.count, data)

    def __getattr__(self, name):
        """dynamic access to vertex attributes, for backwards compatibility.
        """
        domain = self.domain
        if self._cache_versions.get(name, None) != domain.version:
            attribute = domain.attribute_names[name]
            self._caches[name] = attribute.get_region(attribute.buffer, self.start, self.count)
            self._cache_versions[name] = domain.version

        region = self._caches[name]
        region.invalidate()
        return region.array

    def __setattr__(self, name, value):
        # Allow setting vertex attributes directly without overwriting them:
        if 'domain' in self.__dict__ and name in self.__dict__['domain'].attribute_names:
            getattr(self, name)[:] = value
            return
        super().__setattr__(name, value)


class IndexedVertexDomain(VertexDomain):
    """Management of a set of indexed vertex lists.

    Construction of an indexed vertex domain is usually done with the
    :py:func:`create_domain` function.
    """
    _initial_index_count = 16

    def __init__(self, program, attribute_meta, index_gl_type=GL_UNSIGNED_INT):
        super(IndexedVertexDomain, self).__init__(program, attribute_meta)

        self.index_allocator = allocation.Allocator(self._initial_index_count)

        self.index_gl_type = index_gl_type
        self.index_c_type = shader._c_types[index_gl_type]
        self.index_element_size = ctypes.sizeof(self.index_c_type)
        self.index_buffer = BufferObject(self.index_allocator.capacity * self.index_element_size)

    def safe_index_alloc(self, count):
        """Allocate indices, resizing the buffers if necessary."""
        try:
            return self.index_allocator.alloc(count)
        except allocation.AllocatorMemoryException as e:
            capacity = _nearest_pow2(e.requested_capacity)
            self.version += 1
            self.index_buffer.resize(capacity * self.index_element_size)
            self.index_allocator.set_capacity(capacity)
            return self.index_allocator.alloc(count)

    def safe_index_realloc(self, start, count, new_count):
        """Reallocate indices, resizing the buffers if necessary."""
        try:
            return self.index_allocator.realloc(start, count, new_count)
        except allocation.AllocatorMemoryException as e:
            capacity = _nearest_pow2(e.requested_capacity)
            self.version += 1
            self.index_buffer.resize(capacity * self.index_element_size)
            self.index_allocator.set_capacity(capacity)
            return self.index_allocator.realloc(start, count, new_count)

    def create(self, count, index_count):
        """Create an :py:class:`IndexedVertexList` in this domain.

        :Parameters:
            `count` : int
                Number of vertices to create
            `index_count`
                Number of indices to create

        """
        start = self.safe_alloc(count)
        index_start = self.safe_index_alloc(index_count)
        return IndexedVertexList(self, start, count, index_start, index_count)

    def get_index_region(self, start, count):
        """Get a data from a region of the index buffer.

        :Parameters:
            `start` : int
                Start of the region to map.
            `count` : int
                Number of indices to map.

        :rtype: Array of int
        """
        byte_start = self.index_element_size * start
        byte_count = self.index_element_size * count
        ptr_type = ctypes.POINTER(self.index_c_type * count)
        map_ptr = self.index_buffer.map_range(byte_start, byte_count, ptr_type)
        data = map_ptr[:]
        self.index_buffer.unmap()
        return data

    def set_index_region(self, start, count, data):
        byte_start = self.index_element_size * start
        byte_count = self.index_element_size * count
        ptr_type = ctypes.POINTER(self.index_c_type * count)
        map_ptr = self.index_buffer.map_range(byte_start, byte_count, ptr_type)
        map_ptr[:] = data
        self.index_buffer.unmap()

    def draw(self, mode):
        """Draw all vertices in the domain.

        All vertices in the domain are drawn at once. This is the
        most efficient way to render primitives.

        :Parameters:
            `mode` : int
                OpenGL drawing mode, e.g. ``GL_POINTS``, ``GL_LINES``, etc.

        """
        self.vao.bind()

        for buffer, attributes in self.buffer_attributes:
            buffer.bind()
            for attribute in attributes:
                attribute.enable()
                attribute.set_pointer(attribute.buffer.ptr)
        self.index_buffer.bind_to_index_buffer()

        starts, sizes = self.index_allocator.get_allocated_regions()
        primcount = len(starts)
        if primcount == 0:
            pass
        elif primcount == 1:
            # Common case
            glDrawElements(mode, sizes[0], self.index_gl_type,
                           self.index_buffer.ptr + starts[0] * self.index_element_size)
        else:
            starts = [s * self.index_element_size + self.index_buffer.ptr for s in starts]
            starts = (ctypes.POINTER(GLvoid) * primcount)(*(GLintptr * primcount)(*starts))
            sizes = (GLsizei * primcount)(*sizes)
            glMultiDrawElements(mode, sizes, self.index_gl_type, starts, primcount)

        self.index_buffer.unbind()
        for buffer, _ in self.buffer_attributes:
            buffer.unbind()

    def draw_subset(self, mode, vertex_list):
        """Draw a specific IndexedVertexList in the domain.

        The `vertex_list` parameter specifies a :py:class:`IndexedVertexList`
        to draw. Only primitives in that list will be drawn.

        :Parameters:
            `mode` : int
                OpenGL drawing mode, e.g. ``GL_POINTS``, ``GL_LINES``, etc.
            `vertex_list` : `IndexedVertexList`
                Vertex list to draw.

        """
        self.vao.bind()

        for buffer, attributes in self.buffer_attributes:
            buffer.bind()
            for attribute in attributes:
                attribute.enable()
                attribute.set_pointer(attribute.buffer.ptr)
        self.index_buffer.bind_to_index_buffer()

        glDrawElements(mode, vertex_list.index_count, self.index_gl_type,
                       self.index_buffer.ptr +
                       vertex_list.index_start * self.index_element_size)

        self.index_buffer.unbind()
        for buffer, _ in self.buffer_attributes:
            buffer.unbind()


class IndexedVertexList(VertexList):
    """A list of vertices within an :py:class:`IndexedVertexDomain` that are
    indexed. Use :py:meth:`IndexedVertexDomain.create` to construct this list.
    """
    _indices_cache = None
    _indices_cache_version = None

    def __init__(self, domain, start, count, index_start, index_count):
        super().__init__(domain, start, count)
        self.index_start = index_start
        self.index_count = index_count

    def resize(self, count, index_count):
        """Resize this group.

        :Parameters:
            `count` : int
                New number of vertices in the list.
            `index_count` : int
                New number of indices in the list.

        """
        old_start = self.start
        super().resize(count)

        # Change indices (because vertices moved)
        if old_start != self.start:
            diff = self.start - old_start
            self.indices[:] = [i + diff for i in self.indices]

        # Resize indices
        new_start = self.domain.safe_index_realloc(self.index_start, self.index_count, index_count)
        if new_start != self.index_start:
            old = self.domain.get_index_region(self.index_start, self.index_count)
            new = self.domain.get_index_region(self.index_start, self.index_count)
            new.array[:] = old.array[:]
            new.invalidate()

        self.index_start = new_start
        self.index_count = index_count
        self._indices_cache_version = None

    def delete(self):
        """Delete this group."""
        super().delete()
        self.domain.index_allocator.dealloc(self.index_start, self.index_count)

    def migrate(self, domain):
        """Move this group from its current indexed domain and add to the
        specified one.  Attributes on domains must match.  (In practice, used 
        to change parent state of some vertices).

        :Parameters:
            `domain` : `IndexedVertexDomain`
                Indexed domain to migrate this vertex list to.

        """
        old_start = self.start
        old_domain = self.domain
        super().migrate(domain)

        # Note: this code renumber the indices of the *original* domain
        # because the vertices are in a new position in the new domain
        if old_start != self.start:
            diff = self.start - old_start
            old_indices = old_domain.get_index_region(self.index_start, self.index_count)
            old_domain.set_index_region(self.index_start, self.index_count, [i + diff for i in old_indices])

        # copy indices to new domain
        old_array = old_domain.get_index_region(self.index_start, self.index_count)
        # must delloc before calling safe_index_alloc or else problems when same
        # batch is migrated to because index_start changes after dealloc
        old_domain.index_allocator.dealloc(self.index_start, self.index_count)

        new_start = self.domain.safe_index_alloc(self.index_count)
        self.domain.set_index_region(new_start, self.index_count, old_array)

        self.index_start = new_start
        self._indices_cache_version = None

    @property
    def indices(self):
        """Array of index data."""
        if self._indices_cache_version != self.domain.version:
            domain = self.domain
            self._indices_cache = domain.get_index_region(self.index_start, self.index_count)
            self._indices_cache_version = domain.version

        return self._indices_cache

    @indices.setter
    def indices(self, data):
        self.domain.set_index_region(self.index_start, self.index_count, data)
