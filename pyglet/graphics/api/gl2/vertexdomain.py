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
from typing import TYPE_CHECKING, Any, Sequence

from ctypes import Array

from pyglet.graphics.api.gl import (
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
    GL_ARRAY_BUFFER, OpenGLSurfaceContext,

)
from pyglet.graphics.api.gl.enums import geometry_map
from pyglet.graphics.api.gl.shader import GLAttribute
from pyglet.graphics.api.gl2.buffer import AttributeBufferObject, IndexedBufferObject
from pyglet.graphics.vertexdomain import VertexStream, IndexStream, VertexArrayBinding, \
    VertexArrayProtocol

if TYPE_CHECKING:
    from pyglet.graphics.shader import AttributeView
    from pyglet.customtypes import CType, DataTypes
    from pyglet.graphics import GeometryMode
    from pyglet.graphics.shader import Attribute

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
    'h': GL_SHORT,
    'H': GL_UNSIGNED_SHORT,
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


class GLVertexArrayBinding(VertexArrayBinding):
    """GL2 doesn't have a real VAO. This just acts as a container."""
    def _create_vao(self) -> VertexArrayProtocol:
        return

    def _link(self) -> None:
        pass

    def bind(self) -> None:
        for stream in self.streams:
            stream.bind_into(self.vao)

    def unbind(self) -> None:
        for stream in self.streams:
            stream.unbind()

class InstancedVertexDomain:
    """Not available in OpenGL 2.0"""
    def __init__(self):
        raise NotImplementedError("InstancedVertexDomain is not available in OpenGL 2.0.")

class InstancedIndexedVertexDomain:
    """Not available in OpenGL 2.0"""
    def __init__(self):
        raise NotImplementedError("InstancedIndexedVertexDomain is not available in OpenGL 2.0.")

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

    def draw(self, mode: GeometryMode) -> None:
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
                Ignored for non-indexed VertexDomains

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
        self.domain.vertex_buffers.allocator.dealloc(self.start, self.count)

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
        # Copy data to new stream.
        self.domain.vertex_buffers.copy_data(new_start, domain.vertex_buffers, self.start, self.count)
        self.domain.vertex_buffers.allocator.dealloc(self.start, self.count)
        self.domain = domain
        self.start = new_start

    def set_attribute_data(self, name: str, data: Any) -> None:
        stream = self.domain.attrib_name_buffers[name]
        buffer = stream.attrib_name_buffers[name]

        array_start = buffer.element_count * self.start
        array_end = buffer.element_count * self.count + array_start
        buffer.data[array_start:array_end] = data
        buffer.invalidate_region(self.start, self.count)



class _RunningIndexSupport:
    """Used to mixin an IndexedVertexList class.

    Keeps an incrementing count for indices in the buffer.
    """
    __slots__: tuple[str, ...] = ()

    domain: IndexedVertexDomain | InstancedIndexedVertexDomain
    index_count: int
    index_start: int
    start: int

    supports_base_vertex: bool = False

    @property
    def indices(self) -> list[int]:
        stored = self.domain.index_stream.get_region(self.index_start, self.index_count)
        base = self.start
        return [i - base for i in stored]

    @indices.setter
    def indices(self, local: Sequence[int]) -> None:
        base: int = self.start
        stored: list[int] = [i + base for i in local]
        self.domain.index_stream.set_region(self.index_start, self.index_count, stored)

    def migrate(self, dst_domain: IndexedVertexDomain | InstancedIndexedVertexDomain) -> None:
        old_dom = self.domain
        old_start: int = self.start
        src_idx_start = self.index_start
        src_idx_count = self.index_count

        super().migrate(dst_domain)

        data = old_dom.index_stream.get_region(src_idx_start, src_idx_count)
        old_dom.index_stream.allocator.dealloc(src_idx_start, src_idx_count)

        delta: int = self.start - old_start
        if delta:
            data = [i + delta for i in data]

        new_idx_start = self.domain.safe_index_alloc(src_idx_count)
        self.domain.index_stream.set_region(new_idx_start, src_idx_count, data)
        self.index_start = new_idx_start

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
        self.domain.index_stream.dealloc(self.index_start, self.index_count)

    def migrate(self, domain: IndexedVertexDomain | InstancedIndexedVertexDomain) -> None:
        """Move this group from its current indexed domain and add to the specified one.

        Attributes on domains must match.  (In practice, used
        to change parent state of some vertices).

        Args:
            domain:
                Indexed domain to migrate this vertex list to.
        """
        # Handled by new mixins.
        raise NotImplementedError

    @property
    def indices(self) -> list[int]:
        """Array of index data."""
        return self.domain.index_stream.get_region(self.index_start, self.index_count)

    @indices.setter
    def indices(self, data: Sequence[int]) -> None:
        self.domain.index_stream.set_region(self.index_start, self.index_count, data)


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

class GLVertexStream(VertexStream):
    _ctx: OpenGLSurfaceContext

    def __init__(self, ctx: OpenGLSurfaceContext, initial_size: int, attrs: Sequence[Attribute], *, divisor: int = 0):
        super().__init__(ctx, initial_size, attrs, divisor=divisor)

    def get_graphics_attribute(self, attribute: Attribute, view: AttributeView) -> GLAttribute:
        return GLAttribute(attribute, view)

    def get_buffer(self, size: int, attribute) -> AttributeBufferObject:
        # TODO: use persistent buffer if we have GL support for it:
        # attribute.buffer = PersistentBufferObject(attribute.stride * self.allocator.capacity, attribute, self.vao)
        return AttributeBufferObject(self._ctx, size, attribute)

    def bind_into(self, vao) -> None:
        for attribute, buffer in zip(self.attribute_names.values(), self.buffers):
            buffer.bind()
            attribute.enable()
            attribute.set_pointer()
            attribute.set_divisor()

    def unbind(self) -> None:
        for attribute in self.attribute_names.values():
            attribute.disable()


class GLIndexStream(IndexStream):
    index_element_size: int
    index_c_type: CType
    gl_type: int

    def __init__(self, ctx: OpenGLSurfaceContext, data_type: DataTypes, initial_elems: int) -> None:
        self.gl_type = _gl_types[data_type]
        self.index_c_type = _c_types[self.gl_type]
        self.index_element_size = ctypes.sizeof(self.index_c_type)
        super().__init__(ctx, data_type, initial_elems)

    def _create_buffer(self) -> IndexedBufferObject:
        return IndexedBufferObject(self.ctx, self.allocator.capacity * self.index_element_size,
                                                self.index_c_type,
                                                self.index_element_size,
                                                1)

    def bind_into(self, vao: VertexArrayBinding) -> None:
        #self.buffer.bind_to_index_buffer()
        pass

    def unbind(self):
        self.buffer.unbind()


class VertexDomain:
    """Management of a set of vertex lists.

    Construction of a vertex domain is usually done with the
    :py:func:`create_domain` function.
    """
    streams: list[GLVertexStream | GLIndexStream]
    per_instance: list[Attribute]
    per_vertex: list[Attribute]

    attribute_meta: dict[str, Attribute]
    buffer_attributes: list[tuple[AttributeBufferObject, Attribute]]
    vao: GLVertexArrayBinding
    attribute_names: dict[str, Attribute]
    attrib_name_buffers: dict[str, GLVertexStream]
    _vertexlist_class: type

    _vertex_class: type[VertexList] = VertexList

    def __init__(self, context: OpenGLSurfaceContext, initial_count: int, attribute_meta: dict[str, Attribute]) -> None:
        self._context = context or pyglet.graphics.api.core.current_context
        self.attribute_meta = attribute_meta
        self.attrib_name_buffers = {}

        # Separate attributes.
        self.per_vertex: list[Attribute] = []
        self.per_instance: list[Attribute] = []
        for attrib in attribute_meta.values():
            if not attrib.fmt.is_instanced:
                self.per_vertex.append(attrib)
            else:
                self.per_instance.append(attrib)

        self._create_streams(initial_count)
        self._create_vao()

        for name, attrib in attribute_meta.items():
            if not attrib.fmt.is_instanced:
                self.attrib_name_buffers[name] = self.vertex_buffers

        # Make a custom VertexList class w/ properties for each attribute
        self._vertexlist_class = type(self._vertex_class.__name__, (self._vertex_class,), self.vertex_buffers._property_dict)

    def _create_vao(self) -> None:
        self.vao = GLVertexArrayBinding(self._context, self.streams)

    def _create_streams(self, size: int) -> None:
        self.vertex_buffers = GLVertexStream(self._context, size, self.per_vertex)
        self.streams = [self.vertex_buffers]

    def safe_alloc(self, count: int) -> int:
        """Allocate vertices, resizing the buffers if necessary."""
        return self.vertex_buffers.alloc(count)

    def safe_realloc(self, start: int, count: int, new_count: int) -> int:
        """Reallocate vertices, resizing the buffers if necessary."""
        return self.vertex_buffers.realloc(start, count, new_count)

    def create(self, count: int, indices: Sequence[int] | None = None) -> VertexList:  # noqa: ARG002
        """Create a :py:class:`VertexList` in this domain.

        Args:
            count:
                Number of vertices to create.
            indices:
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
        self.vertex_buffers.commit()
        # for buffer, attribute in self.buffer_attributes:
        #     buffer.commit()
        #     attribute.enable()
        #     attribute.set_pointer(0)

        starts, sizes = self.vertex_buffers.allocator.get_allocated_regions()
        primcount = len(starts)
        if primcount == 0:
            pass
        elif primcount == 1:
            # Common case
            self._context.glDrawArrays(mode, starts[0], sizes[0])
        else:
            starts = (GLint * primcount)(*starts)
            sizes = (GLsizei * primcount)(*sizes)
            self._context.glMultiDrawArrays(mode, starts, sizes, primcount)

        for _, attribute in self.vertex_buffers.attribute_names.items():
            attribute.disable()

    def draw_subset(self, mode: GeometryMode, vertex_list: VertexList) -> None:
        """Draw a specific VertexList in the domain.

        The `vertex_list` parameter specifies a :py:class:`VertexList`
        to draw. Only primitives in that list will be drawn.

        Args:
            mode:
                OpenGL drawing mode, e.g. ``GL_POINTS``, ``GL_LINES``, etc.
            vertex_list:
                Vertex list to draw.

        """
        for buffer, attribute in self.buffer_attributes:
            buffer.commit()
            attribute.enable()
            attribute.set_pointer(0)

        self._context.glDrawArrays(geometry_map[mode], vertex_list.start, vertex_list.count)

        for _, attribute in self.buffer_attributes:
            attribute.disable()

    @property
    def is_empty(self) -> bool:
        return not self.vertex_buffers.allocator.starts

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}@{id(self):x} {self.allocator}>'



class IndexedVertexDomain(VertexDomain):
    """Management of a set of indexed vertex lists.

    Construction of an indexed vertex domain is usually done with the
    :py:func:`create_domain` function.
    """
    _vertex_class = IndexedVertexList
    index_stream: GLIndexStream

    def __init__(self, context: OpenGLSurfaceContext, initial_count: int, attribute_meta: dict[str, Attribute],
                 index_type: DataTypes = "I") -> None:
        self.index_type = index_type
        super().__init__(context, initial_count, attribute_meta)
        # Make a custom VertexList class w/ properties for each attribute in the ShaderProgram:
        self._vertexlist_class = type(self._vertex_class.__name__, (_RunningIndexSupport, self._vertex_class),
                                      self.vertex_buffers._property_dict)

    def _create_streams(self, size: int) -> None:
        super()._create_streams(size)
        self.index_stream = GLIndexStream(self._context, self.index_type, size)
        self.streams.append(self.index_stream)

    def safe_index_alloc(self, count: int) -> int:
        """Allocate indices, resizing the buffers if necessary."""
        return self.index_stream.alloc(count)

    def safe_index_realloc(self, start: int, count: int, new_count: int) -> int:
        """Reallocate indices, resizing the buffers if necessary."""
        return self.index_stream.realloc(start, count, new_count)

    def create(self, count: int, indices: Sequence[int] | None) -> IndexedVertexList:
        """Create an :py:class:`IndexedVertexList` in this domain.

        Args:
            count:
                Number of vertices to create
            indices:
                Sequence of indices to create

        """
        index_count = len(indices)
        start = self.safe_alloc(count)
        index_start = self.safe_index_alloc(index_count)
        vertex_list = self._vertexlist_class(self, start, count, index_start, index_count)
        vertex_list.indices = indices  # Move into class at some point?
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
        self.vertex_buffers.commit()
        self.index_stream.commit()

        starts, sizes = self.index_stream.allocator.get_allocated_regions()
        primcount = len(starts)
        if primcount == 0:
            pass
        elif primcount == 1:
            # Common case
            self._context.glDrawElements(
                mode, sizes[0], self.index_stream.gl_type, starts[0] * self.index_stream.index_element_size,
            )
        else:
            starts = [s * self.index_stream.index_element_size for s in starts]
            starts = (ctypes.POINTER(GLvoid) * primcount)(*(GLintptr * primcount)(*starts))
            sizes = (GLsizei * primcount)(*sizes)
            self._context.glMultiDrawElements(mode, sizes, self.index_stream.gl_type, starts, primcount)

        self.vao.unbind()

        self._context.glBindBuffer(GL_ARRAY_BUFFER, 0)

    def draw_subset(self, mode: GeometryMode, vertex_list: IndexedVertexList) -> None:
        """Draw a specific IndexedVertexList in the domain.

        The `vertex_list` parameter specifies a :py:class:`IndexedVertexList`
        to draw. Only primitives in that list will be drawn.

        Args:
            mode:
                OpenGL drawing mode, e.g. ``GL_POINTS``, ``GL_LINES``, etc.
            vertex_list:
                Vertex list to draw.
        """
        for buffer, attribute in self.buffer_attributes:
            buffer.commit()
            attribute.enable()
            attribute.set_pointer(0)

        self.index_buffer.commit()

        self._context.glDrawElements(geometry_map[mode], vertex_list.index_count, self.index_gl_type,
                       vertex_list.index_start * self.index_element_size)

        for _, attribute in self.buffer_attributes:
            attribute.disable()

        self._context.glBindBuffer(GL_ARRAY_BUFFER, 0)
