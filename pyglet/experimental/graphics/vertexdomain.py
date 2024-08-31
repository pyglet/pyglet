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
from __future__ import annotations

import ctypes
from typing import TYPE_CHECKING, Any, Sequence, Type

from _ctypes import Array, _Pointer, _SimpleCData

from pyglet.gl.gl import (
    GL_BYTE,
    GL_DOUBLE,
    GL_FLOAT,
    GL_INT,
    GL_SHORT,
    GL_UNSIGNED_BYTE,
    GL_UNSIGNED_INT,
    GL_UNSIGNED_SHORT,
    GLint,
    GLintptr,
    GLsizei,
    GLvoid,
    glDrawArrays,
    glDrawElements,
    glMultiDrawArrays,
    glMultiDrawElements,
)
from pyglet.graphics import allocation, shader, vertexarray
from pyglet.graphics.vertexbuffer import AttributeBufferObject, IndexedBufferObject

CTypesDataType = Type[_SimpleCData]
CTypesPointer = _Pointer

if TYPE_CHECKING:
    from pyglet.graphics import Group
    from pyglet.graphics.allocation import Allocator
    from pyglet.graphics.shader import Attribute
    from pyglet.graphics.vertexarray import VertexArray


def _nearest_pow2(v: int) -> int:
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


def _make_attribute_property(name: str) -> property:
    def _attribute_getter(self: VertexList) -> Array[float | int]:
        buffer = self.domain.attrib_name_buffers[name]
        region = buffer.get_region(self.start, self.count)
        buffer.invalidate_region(self.start, self.count)
        return region

    def _attribute_setter(self: VertexList, data: Any) -> None:
        buffer = self.domain.attrib_name_buffers[name]
        buffer.set_region(self.start, self.count, data)

    return property(_attribute_getter, _attribute_setter)


class VertexList:
    """A list of vertices within a :py:class:`VertexDomain`.

    Use :py:meth:`VertexDomain.create` to construct this list.
    """
    count: int
    start: int
    domain: VertexDomain
    indexed: bool = False
    instanced: bool = False
    initial_attribs: dict

    def __init__(self, domain: VertexDomain, start: int, count: int) -> None:  # noqa: D107
        self.domain = domain
        self.start = start
        self.count = count
        self.initial_attribs = domain.attribute_meta

    def draw(self, mode: int) -> None:
        """Draw this vertex list in the given OpenGL mode.

        Args:
            mode:
                OpenGL drawing mode, e.g. ``GL_POINTS``, ``GL_LINES``, etc.
        """
        self.domain.draw_subset(mode, self)

    def resize(self, count: int, index_count: int | None = None) -> None:  # noqa: ARG002
        """Resize this group.

        Args:
            count:
                New number of vertices in the list.
            index_count:
                Ignored for non indexed VertexDomains

        """
        new_start = self.domain.safe_realloc(self.start, self.count, count)
        if new_start != self.start:
            # Copy contents to new location
            for buffer in self.domain.attrib_name_buffers.values():
                old_data = buffer.get_region(self.start, self.count)
                buffer.set_region(new_start, self.count, old_data)
        self.start = new_start
        self.count = count

    def delete(self) -> None:
        """Delete this group."""
        self.domain.allocator.dealloc(self.start, self.count)
        group = self.domain.group_vlists[self]
        self.domain.group_vertex_ranges[group].remove((self.start, self.count))
        del self.domain.group_vlists[self]
        # if not self.domain.group_vertex_ranges[group]:

    #     del self.domain.group_vertex_ranges[group]

    def update_group(self, group: Group):
        current_group = self.domain.group_vlists[self]
        assert current_group != group, "Changing group to same group."
        self.domain.group_vertex_ranges[current_group].remove((self.start, self.count))

        # Set new group
        self.domain.group_vlists[self] = group
        if group not in self.domain.group_vertex_ranges:
            self.domain.group_vertex_ranges[group] = []
        self.domain.group_vertex_ranges[group].append((self.start, self.count))

    def migrate(self, domain: VertexDomain) -> None:
        """Move this group from its current domain and add to the specified one.

        Attributes on domains must match.
        (In practice, used to change parent state of some vertices).

        Args:
            domain:
                Domain to migrate this vertex list to.

        """
        assert list(domain.attribute_names.keys()) == list(self.domain.attribute_names.keys()), \
            'Domain attributes must match.'

        new_start = domain.safe_alloc(self.count)
        for name, old_buffer in self.domain.attrib_name_buffers.items():
            new_buffer = domain.attrib_name_buffers[name]
            old_data = old_buffer.get_region(self.start, self.count)
            new_buffer.set_region(new_start, self.count, old_data)

        self.domain.allocator.dealloc(self.start, self.count)
        self.domain = domain
        self.start = new_start

    def set_attribute_data(self, name: str, data: Any) -> None:
        buffer = self.domain.attrib_name_buffers[name]
        count = self.count

        array_start = buffer.count * self.start
        array_end = buffer.count * count + array_start
        try:
            buffer.data[array_start:array_end] = data
            buffer.invalidate_region(self.start, count)
        except ValueError:
            msg = f"Invalid data size for '{name}'. Expected {array_end - array_start}, got {len(data)}."
            raise ValueError(msg) from None


class IndexedVertexList(VertexList):
    """A list of vertices within an :py:class:`IndexedVertexDomain` that are indexed.

    Use :py:meth:`IndexedVertexDomain.create` to construct this list.
    """
    domain: IndexedVertexDomain
    indexed: bool = True

    index_count: int
    index_start: int

    def __init__(self, domain: IndexedVertexDomain, start: int, count: int, index_start: int,  # noqa: D107
                 index_count: int) -> None:
        super().__init__(domain, start, count)
        self.index_start = index_start
        self.index_count = index_count

    def delete(self) -> None:
        """Delete this group."""
        group = self.domain.group_vlists[self]
        super().delete()
        self.domain.index_allocator.dealloc(self.index_start, self.index_count)

        self.domain.group_index_ranges[group].remove((self.index_start, self.index_count))

    def update_group(self, group: Group):
        current_group = self.domain.group_vlists[self]
        super().update_group(group)
        self.domain.group_index_ranges[current_group].remove((self.index_start, self.index_count))

        # Set new group
        self.domain.group_vlists[self] = group
        if group not in self.domain.group_index_ranges:
            self.domain.group_index_ranges[group] = []
        self.domain.group_index_ranges[group].append((self.index_start, self.index_count))

    def migrate(self, domain: IndexedVertexDomain) -> None:
        """Move this group from its current indexed domain and add to the specified one.

        Attributes on domains must match.  (In practice, used
        to change parent state of some vertices).

        Args:
            domain:
                Indexed domain to migrate this vertex list to.
        """
        if domain == self.domain:
            return

        old_start = self.start
        old_domain = self.domain
        super().migrate(domain)

        # Note: this code renumber the indices of the *original* domain
        # because the vertices are in a new position in the new domain
        if old_start != self.start:
            diff = self.start - old_start
            old_indices = old_domain.index_buffer.get_region(self.index_start, self.index_count)
            old_domain.index_buffer.set_region(self.index_start, self.index_count, [i + diff for i in old_indices])

        # copy indices to new domain
        old_array = old_domain.index_buffer.get_region(self.index_start, self.index_count)
        # must delloc before calling safe_index_alloc or else problems when same
        # batch is migrated to because index_start changes after dealloc
        old_domain.index_allocator.dealloc(self.index_start, self.index_count)

        new_start = self.domain.safe_index_alloc(self.index_count)
        self.domain.index_buffer.set_region(new_start, self.index_count, old_array)

        self.index_start = new_start

    @property
    def indices(self) -> list[int]:
        """Array of index data."""
        return self.domain.index_buffer.get_region(self.index_start, self.index_count)

    @indices.setter
    def indices(self, data: Sequence[int]) -> None:
        self.domain.index_buffer.set_region(self.index_start, self.index_count, data)


CULL_TIME = 10


class VertexDomain:
    """Management of a set of vertex lists.

    Construction of a vertex domain is usually done with the
    :py:func:`create_domain` function.
    """

    attribute_meta: dict[str, dict[str, Any]]
    allocator: Allocator
    buffer_attributes: list[tuple[AttributeBufferObject, Attribute]]
    vao: VertexArray
    attribute_names: dict[str, Attribute]
    attrib_name_buffers: dict[str, AttributeBufferObject]

    _property_dict: dict[str, property]
    _vertexlist_class: type

    _initial_count: int = 16
    _vertex_class: type[VertexList] = VertexList

    def __init__(self, attribute_meta: dict[str, dict[str, Any]]) -> None:  # noqa: D107
        self.attribute_meta = attribute_meta
        self.allocator = allocation.Allocator(self._initial_count)

        self.attribute_names = {}  # name: attribute
        self.buffer_attributes = []  # list of (buffer, attribute)
        self.attrib_name_buffers = {}  # dict of AttributeName: AttributeBufferObject (for VertexLists)

        # This maps groups to the specific start/size regions.
        self.group_vertex_ranges = {}  # New attribute to store vertex ranges by group
        self.group_vlists = {}

        self._property_dict = {}  # name: property(_getter, _setter)

        for name, meta in attribute_meta.items():
            assert meta['format'][0] in _gl_types, f"'{meta['format']}' is not a valid attribute format for '{name}'."
            location = meta['location']
            count = meta['count']
            gl_type = _gl_types[meta['format'][0]]
            normalize = 'n' in meta['format']
            instanced = meta['instance']

            self.attribute_names[name] = attribute = shader.Attribute(name, location, count, gl_type, normalize,
                                                                      instanced)

            # Create buffer:
            self.attrib_name_buffers[name] = buffer = AttributeBufferObject(attribute.stride * self.allocator.capacity,
                                                                            attribute)

            self.buffer_attributes.append((buffer, attribute))

            # Create custom property to be used in the VertexList:
            self._property_dict[attribute.name] = _make_attribute_property(name)

        # Make a custom VertexList class w/ properties for each attribute in the ShaderProgram:
        self._vertexlist_class = type(self._vertex_class.__name__, (self._vertex_class,), self._property_dict)

        self.vao = vertexarray.VertexArray()
        self.vao.bind()
        for buffer, attribute in self.buffer_attributes:
            buffer.bind()
            attribute.enable()
            attribute.set_pointer(buffer.ptr)
            if attribute.instance:
                attribute.set_divisor()
        self.vao.unbind()

    def safe_alloc(self, count: int) -> int:
        """Allocate vertices, resizing the buffers if necessary."""
        try:
            return self.allocator.alloc(count)
        except allocation.AllocatorMemoryException as e:
            capacity = _nearest_pow2(e.requested_capacity)
            for buffer, _ in self.buffer_attributes:
                buffer.resize(capacity * buffer.stride)
            self.allocator.set_capacity(capacity)
            return self.allocator.alloc(count)

    def safe_realloc(self, start: int, count: int, new_count: int) -> int:
        """Reallocate vertices, resizing the buffers if necessary."""
        try:
            return self.allocator.realloc(start, count, new_count)
        except allocation.AllocatorMemoryException as e:
            capacity = _nearest_pow2(e.requested_capacity)
            for buffer, _ in self.buffer_attributes:
                buffer.resize(capacity * buffer.stride)
            self.allocator.set_capacity(capacity)
            return self.allocator.realloc(start, count, new_count)

    def create(self, count: int, group: Group, index_count: int) -> VertexList:  # noqa: ARG002
        start = self.safe_alloc(count)
        vertex_list = self._vertexlist_class(self, start, count)
        if group not in self.group_vertex_ranges:
            self.group_vertex_ranges[group] = []
        self.group_vertex_ranges[group].append((start, count))
        self.group_vlists[vertex_list] = group
        return vertex_list

    def draw(self, mode: int) -> None:
        """Draw all vertices in the domain.

        All vertices in the domain are drawn at once. This is the
        most efficient way to render primitives.

        Args:
            mode:
                OpenGL drawing mode, e.g. ``GL_POINTS``, ``GL_LINES``, etc.

        """
        self.vao.bind()
        for buffer, _ in self.buffer_attributes:
            buffer.commit()

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

    def draw_groups(self, mode: int, groups: list[Group]) -> None:
        """Draw all vertices associated with the specified groups.

        Args:
            mode:
                OpenGL drawing mode, e.g., ``GL_POINTS``, ``GL_LINES``, etc.
            groups:
                The groups whose vertices should be drawn.
        """
        combined = []
        for group in groups:
            combined.extend(self.group_vertex_ranges[group])

        if not combined:
            return

        starts, sizes = zip(*combined)
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

    def draw_subset(self, mode: int, vertex_list: VertexList) -> None:
        """Draw a specific VertexList in the domain.

        The `vertex_list` parameter specifies a :py:class:`VertexList`
        to draw. Only primitives in that list will be drawn.

        Args:
            mode:
                OpenGL drawing mode, e.g. ``GL_POINTS``, ``GL_LINES``, etc.
            vertex_list:
                Vertex list to draw.

        """
        self.vao.bind()
        for buffer, _ in self.buffer_attributes:
            buffer.commit()

        glDrawArrays(mode, vertex_list.start, vertex_list.count)

    @property
    def is_empty(self) -> bool:
        return not self.allocator.starts and not self.group_vertex_ranges

    @property
    def has_vertices(self) -> bool:
        return all(not values for values in self.group_vertex_ranges.values())

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}@{id(self):x} {self.allocator}>'


class IndexedVertexDomain(VertexDomain):
    """Management of a set of indexed vertex lists.

    Construction of an indexed vertex domain is usually done with the
    :py:func:`create_domain` function.
    """
    index_allocator: Allocator
    index_gl_type: int
    index_c_type: CTypesDataType
    index_element_size: int
    index_buffer: IndexedBufferObject
    _initial_index_count = 16
    _vertex_class = IndexedVertexList

    def __init__(self, attribute_meta: dict[str, dict[str, Any]],  # noqa: D107
                 index_gl_type: int = GL_UNSIGNED_INT) -> None:
        super().__init__(attribute_meta)

        self.index_allocator = allocation.Allocator(self._initial_index_count)

        self.index_gl_type = index_gl_type
        self.index_c_type = shader._c_types[index_gl_type]  # noqa: SLF001
        self.index_element_size = ctypes.sizeof(self.index_c_type)
        self.index_buffer = IndexedBufferObject(self.index_allocator.capacity * self.index_element_size,
                                                shader._c_types[index_gl_type],
                                                self.index_element_size,
                                                1)

        self.vao.bind()
        self.index_buffer.bind_to_index_buffer()
        self.vao.unbind()

        # Make a custom VertexList class w/ properties for each attribute in the ShaderProgram:
        self._vertexlist_class = type(self._vertex_class.__name__, (self._vertex_class,),
                                      self._property_dict)
        # Dictionary to store index ranges by group
        self.group_index_ranges = {}

    def safe_index_alloc(self, count: int) -> int:
        """Allocate indices, resizing the buffers if necessary."""
        try:
            return self.index_allocator.alloc(count)
        except allocation.AllocatorMemoryException as e:
            capacity = _nearest_pow2(e.requested_capacity)
            self.index_buffer.resize(capacity * self.index_element_size)
            self.index_allocator.set_capacity(capacity)
            return self.index_allocator.alloc(count)

    def safe_index_realloc(self, start: int, count: int, new_count: int) -> int:
        """Reallocate indices, resizing the buffers if necessary."""
        try:
            return self.index_allocator.realloc(start, count, new_count)
        except allocation.AllocatorMemoryException as e:
            capacity = _nearest_pow2(e.requested_capacity)
            self.index_buffer.resize(capacity * self.index_element_size)
            self.index_allocator.set_capacity(capacity)
            return self.index_allocator.realloc(start, count, new_count)

    def create(self, count: int, group: Group, index_count: int) -> IndexedVertexList:
        """Create an :py:class:`IndexedVertexList` in this domain.

        Args:
            count:
                Number of vertices to create
            index_count:
                Number of indices to create
            group:
                The group to which this vertex list belongs
        """
        start = self.safe_alloc(count)
        index_start = self.safe_index_alloc(index_count)

        vertex_list = self._vertexlist_class(self, start, count, index_start, index_count)
        if group not in self.group_vertex_ranges:
            self.group_vertex_ranges[group] = []
        if group not in self.group_index_ranges:
            self.group_index_ranges[group] = []
        self.group_vertex_ranges[group].append((start, count))
        self.group_index_ranges[group].append((index_start, index_count))
        self.group_vlists[vertex_list] = group

        return vertex_list

    def draw(self, mode: int) -> None:
        """Draw all vertices in the domain.

        All vertices in the domain are drawn at once. This is the
        most efficient way to render primitives.

        Args:
            mode:
                OpenGL drawing mode, e.g. ``GL_POINTS``, ``GL_LINES``, etc.

        """
        self.vao.bind()
        for buffer, _ in self.buffer_attributes:
            buffer.commit()

        self.index_buffer.commit()

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

    def bind(self) -> None:
        """Bind the domain.

        This binds the VAO and all of its buffers.
        """
        self.vao.bind()

        for buffer, _ in self.buffer_attributes:
            buffer.commit()

        self.index_buffer.commit()

    def draw_groups(self, mode: int, groups: list[Group]) -> None:
        """Draw all vertices associated with the specified groups.

        This relies on the optimization of the batch call to set the state of the groups.

        Args:
            mode:
                OpenGL drawing mode, e.g., ``GL_POINTS``, ``GL_LINES``, etc.
            groups:
                The groups whose vertices should be drawn.
        """
        combined = []
        for group in groups:
            combined.extend(self.group_index_ranges[group])

        if not combined:
            return

        starts, sizes = zip(*combined)
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

    def draw_subset(self, mode: int, vertex_list: IndexedVertexList) -> None:
        """Draw a specific IndexedVertexList in the domain.

        The `vertex_list` parameter specifies a :py:class:`IndexedVertexList`
        to draw. Only primitives in that list will be drawn.

        Args:
            mode:
                OpenGL drawing mode, e.g. ``GL_POINTS``, ``GL_LINES``, etc.
            vertex_list:
                Vertex list to draw.
        """
        self.vao.bind()
        for buffer, _ in self.buffer_attributes:
            buffer.commit()

        self.index_buffer.commit()

        glDrawElements(mode, vertex_list.index_count, self.index_gl_type,
                       self.index_buffer.ptr +
                       vertex_list.index_start * self.index_element_size)

    @property
    def has_vertices(self) -> bool:
        return all(not values for values in self.group_index_ranges.values())
