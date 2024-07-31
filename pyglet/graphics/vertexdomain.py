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
from typing import TYPE_CHECKING, Any, NoReturn, Sequence, Type

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
    glDrawArraysInstanced,
    glDrawElements,
    glDrawElementsInstanced,
    glMultiDrawArrays,
    glMultiDrawElements,
)
from pyglet.graphics import allocation, shader, vertexarray
from pyglet.graphics.vertexbuffer import AttributeBufferObject, IndexedBufferObject

CTypesDataType = Type[_SimpleCData]
CTypesPointer = _Pointer

if TYPE_CHECKING:
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
    domain: VertexDomain | InstancedVertexDomain
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

    def set_instance_source(self, domain: InstancedVertexDomain, instance_attributes: Sequence[str]) -> None:
        assert self.instanced is False, "Vertex list is already an instance."
        assert list(domain.attribute_names.keys()) == list(self.domain.attribute_names.keys()), \
            'Domain attributes must match.'

        new_start = domain.safe_alloc(self.count)
        for key, current_buffer in self.domain.attrib_name_buffers.items():
            new_buffer = domain.attrib_name_buffers[key]
            old_data = current_buffer.get_region(self.start, self.count)
            if key in instance_attributes:
                attrib = domain.attribute_names[key]
                count = 1
                old_data = old_data[:attrib.count]
            else:
                count = self.count
            new_buffer.set_region(new_start, count, old_data)

        self.domain.allocator.dealloc(self.start, self.count)
        self.domain = domain
        self.start = new_start
        self.instanced = True

    def migrate(self, domain: VertexDomain | InstancedVertexDomain) -> None:
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

    def add_instance(self, **kwargs: Any) -> VertexInstance:
        assert self.instanced
        self.domain._instances += 1  # noqa: SLF001

        instance_id = self.domain._instances  # noqa: SLF001

        start = self.domain.safe_alloc_instance(3)

        for buffer, attribute in self.domain.buffer_attributes:
            if attribute.instance:
                assert attribute.name in kwargs, (f"{attribute.name} is defined as an instance attribute, "
                                                  f"keyword argument not found.")
                buffer.set_region(instance_id - 1, 1, kwargs[attribute.name])

        return self.domain._vertexinstance_class(self, instance_id, start)  # noqa: SLF001

    def delete_instance(self, instance: VertexInstance) -> None:
        assert self.instanced
        if instance.id != self.domain._instances:  # noqa: SLF001
            msg = "Only the last instance added can be removed."
            raise Exception(msg)

        self.domain._instances -= 1  # noqa: SLF001

        self.domain.instance_allocator.dealloc(instance.start, 3)


class IndexedVertexList(VertexList):
    """A list of vertices within an :py:class:`IndexedVertexDomain` that are indexed.

    Use :py:meth:`IndexedVertexDomain.create` to construct this list.
    """
    domain: IndexedVertexDomain | InstancedIndexedVertexDomain
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
        super().delete()
        self.domain.index_allocator.dealloc(self.index_start, self.index_count)

    def migrate(self, domain: IndexedVertexDomain | InstancedIndexedVertexDomain) -> None:
        """Move this group from its current indexed domain and add to the specified one.

        Attributes on domains must match.  (In practice, used
        to change parent state of some vertices).

        Args:
            domain:
                Indexed domain to migrate this vertex list to.
        """
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

    def set_instance_source(self, domain: IndexedVertexDomain | InstancedIndexedVertexDomain,
                            instance_attributes: Sequence[str]) -> None:
        assert self.instanced is False, "IndexedVertexList is already an instance."
        old_start = self.start
        old_domain = self.domain
        super().set_instance_source(domain, instance_attributes)

        assert list(domain.attribute_names.keys()) == list(self.domain.attribute_names.keys()), \
            'Domain attributes must match.'

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


class VertexInstance:
    id: int
    start: int
    _vertex_list: VertexList | IndexedVertexList

    def __init__(self, vertex_list: VertexList | IndexedVertexList, instance_id: int, start: int) -> None:
        self.id = instance_id
        self.start = start
        self._vertex_list = vertex_list

    @property
    def domain(self) -> InstancedVertexDomain | InstancedIndexedVertexDomain:
        return self._vertex_list.domain

    def delete(self) -> None:
        self._vertex_list.delete_instance(self)
        self._vertex_list = None


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

    def create(self, count: int, index_count: int | None = None) -> VertexList:  # noqa: ARG002
        """Create a :py:class:`VertexList` in this domain.

        Args:
            count:
                Number of vertices to create.
            index_count:
                Ignored for non indexed VertexDomains
        """
        start = self.safe_alloc(count)
        return self._vertexlist_class(self, start, count)

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
        return not self.allocator.starts

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}@{id(self):x} {self.allocator}>'


def _make_instance_attribute_property(name: str) -> property:
    def _attribute_getter(self: VertexInstance) -> Array[CTypesDataType]:
        buffer = self.domain.attrib_name_buffers[name]
        region = buffer.get_region(self.id - 1, 1)
        buffer.invalidate_region(self.id - 1, 1)
        return region

    def _attribute_setter(self: VertexInstance, data: Any) -> None:
        buffer = self.domain.attrib_name_buffers[name]
        buffer.set_region(self.id - 1, 1, data)

    return property(_attribute_getter, _attribute_setter)


def _make_restricted_instance_attribute_property(name: str) -> property:
    def _attribute_getter(self: VertexInstance) -> Array[CTypesDataType]:
        buffer = self.domain.attrib_name_buffers[name]
        return buffer.get_region(self.id - 1, 1)

    def _attribute_setter(_self: VertexInstance, _data: Any) -> NoReturn:
        msg = f"Attribute '{name}' is not an instanced attribute."
        raise Exception(msg)

    return property(_attribute_getter, _attribute_setter)


class InstancedVertexDomain(VertexDomain):  # noqa: D101
    instance_allocator: Allocator
    _instances: int
    _instance_properties: dict[str, property]
    _vertexinstance_class: type

    def __init__(self, attribute_meta: dict[str, dict[str, Any]]) -> None:
        super().__init__(attribute_meta)
        self._instances = 1
        self.instance_allocator = allocation.Allocator(self._initial_count)

        self._instance_properties = {}
        for name, attribute in self.attribute_names.items():
            if attribute.instance:
                self._instance_properties[name] = _make_instance_attribute_property(name)
            else:
                self._instance_properties[name] = _make_restricted_instance_attribute_property(name)

        self._vertexinstance_class = type('VertexInstance', (VertexInstance,), self._instance_properties)

    def safe_alloc_instance(self, count: int) -> int:
        try:
            return self.instance_allocator.alloc(count)
        except allocation.AllocatorMemoryException as e:
            capacity = _nearest_pow2(e.requested_capacity)
            for buffer, attribute in self.buffer_attributes:
                if attribute.instance:
                    buffer.resize(capacity * buffer.stride)
            self.instance_allocator.set_capacity(capacity)
            return self.instance_allocator.alloc(count)

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
        glDrawArraysInstanced(mode, starts[0], sizes[0], self._instances)

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

        glDrawArraysInstanced(mode, vertex_list.start, vertex_list.count, self._instances)

    @property
    def is_empty(self) -> bool:
        return not self.allocator.starts


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

    def create(self, count: int, index_count: int) -> IndexedVertexList:
        """Create an :py:class:`IndexedVertexList` in this domain.

        Args:
            count:
                Number of vertices to create
            index_count:
                Number of indices to create

        """
        start = self.safe_alloc(count)
        index_start = self.safe_index_alloc(index_count)
        return self._vertexlist_class(self, start, count, index_start, index_count)

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


class InstancedIndexedVertexDomain(IndexedVertexDomain, InstancedVertexDomain):
    """Management of a set of indexed vertex lists.

    Construction of an indexed vertex domain is usually done with the
    :py:func:`create_domain` function.
    """
    _initial_index_count: int = 16

    def __init__(self, attribute_meta: dict[str, dict[str, Any]],  # noqa: D107
                 index_gl_type: int = GL_UNSIGNED_INT) -> None:
        super().__init__(attribute_meta, index_gl_type)

    def safe_index_alloc(self, count: int) -> int:
        """Allocate indices, resizing the buffers if necessary.

        Returns:
            The starting index of the allocated region.
        """
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

    def create(self, count: int, index_count: int) -> IndexedVertexList:
        """Create an :py:class:`IndexedVertexList` in this domain.

        Args:
            count:
                Number of vertices to create
            index_count:
                Number of indices to create

        """
        start = self.safe_alloc(count)
        index_start = self.safe_index_alloc(index_count)
        return self._vertexlist_class(self, start, count, index_start, index_count)

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

        starts, sizes = self.index_allocator.get_allocated_regions()
        glDrawElementsInstanced(mode, sizes[0], self.index_gl_type,
                                self.index_buffer.ptr + starts[0] * self.index_element_size, self._instances)

    def draw_subset(self, mode: int, vertex_list: IndexedVertexList) -> None:
        """Draw a specific IndexedVertexList in the domain.

        The ``vertex_list`` parameter specifies a :py:class:`IndexedVertexList`
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

        glDrawElementsInstanced(mode, vertex_list.index_count, self.index_gl_type,
                                self.index_buffer.ptr +
                                vertex_list.index_start * self.index_element_size, self._instances)
