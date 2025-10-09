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

from pyglet.graphics.api.webgl import vertexarray
from pyglet.graphics.api.webgl.gl import (
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
)
from pyglet.graphics.api.webgl.enums import geometry_map
from pyglet.graphics.api.webgl.shader import GLAttribute
from pyglet.graphics.api.webgl.buffer import AttributeBufferObject, IndexedBufferObject
from pyglet.graphics.instance import InstanceBucket, BaseInstanceDomain, VertexInstanceBase
from pyglet.graphics.vertexdomain import (
    VertexArrayBinding,
    VertexArrayProtocol,
    InstanceStream,
    VertexStream,
    IndexStream,
    _RunningIndexSupport,
)

if TYPE_CHECKING:
    from pyglet.graphics.shader import AttributeView
    from pyglet.customtypes import CType, DataTypes
    from pyglet.graphics import GeometryMode
    from pyglet.graphics.shader import Attribute
    from pyglet.graphics.api.webgl.context import OpenGLSurfaceContext

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
    def _attribute_getter(self: VertexList) -> ctypes.Array[float | int]:
        buffer = self.domain.attrib_name_buffers[name]
        region = buffer.get_region(self.start, self.count)
        buffer.invalidate_region(self.start, self.count)
        return region

    def _attribute_setter(self: VertexList, data: Any) -> None:
        buffer = self.domain.attrib_name_buffers[name]
        buffer.set_region(self.start, self.count, data)

    return property(_attribute_getter, _attribute_setter)


class _GLVertexStreamMix(VertexStream):
    _ctx: OpenGLSurfaceContext
    attrib_name_buffers: dict[str, AttributeBufferObject]

    def __init__(self, ctx: OpenGLSurfaceContext, initial_size: int, attrs: Sequence[Attribute], *, divisor: int = 0):
        super().__init__(ctx, initial_size, attrs, divisor=divisor)

    def get_graphics_attribute(self, attribute: Attribute, view: AttributeView) -> GLAttribute:
        return GLAttribute(attribute, view)

    def get_buffer(self, size: int, attribute) -> AttributeBufferObject:
        return AttributeBufferObject(self._ctx, size, attribute)

    def bind_into(self, vao) -> None:
        for attribute, buffer in zip(self.attribute_names.values(), self.buffers):
            buffer.bind()
            attribute.enable()
            attribute.set_pointer()
            attribute.set_divisor()

class GLVertexStream(_GLVertexStreamMix, VertexStream):  # noqa: D101
    def __init__(self, ctx: OpenGLSurfaceContext, initial_size: int, attrs: Sequence[Attribute]) -> None:
        """Contains data for vertex stream.

        Args:
            ctx:
                The core context that owns this stream.
            initial_size:
                Initial buffer size.
            attrs:
                Attributes that will be used.
        """
        super().__init__(ctx, initial_size, attrs)

class GLInstanceStream(_GLVertexStreamMix, InstanceStream):  # noqa: D101
    _ctx: OpenGLSurfaceContext

    def __init__(self, ctx: OpenGLSurfaceContext, initial_size: int, attrs: Sequence[Attribute],  # noqa: D107
                 *, divisor: int = 0) -> None:
        super().__init__(ctx, initial_size, attrs, divisor=divisor)

class GLVertexArrayBinding(VertexArrayBinding):  # noqa: D101

    def _create_vao(self) -> VertexArrayProtocol:
        return vertexarray.VertexArray(self._ctx)

    def _link(self) -> None:
        self.vao.bind()
        for stream in self.streams:
            stream.bind_into(self.vao)
        self.vao.unbind()

    def bind(self) -> None:
        self.vao.bind()

    def unbind(self) -> None:
        self.vao.unbind()


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


class InstanceVertexList(VertexList):
    """A list of vertices within an :py:class:`InstancedVertexDomain` that are not indexed."""
    instanced: bool = True

    def __init__(self, domain: VertexDomain, start: int, count: int, bucket: InstanceBucket) -> None:  # noqa: D107
        super().__init__(domain, start, count)
        self.bucket = bucket
        self.bucket.create_instance()

    def create_instance(self, **attributes: Any) -> VertexInstanceBase:
        return self.bucket.create_instance(**attributes)

    def set_attribute_data(self, name: str, data: Any) -> None:
        if self.initial_attribs[name].fmt.is_instanced:
            stream = self.bucket.stream
            count = 1
            start = 0
        else:
            stream = self.domain.attrib_name_buffers[name]
            count = self.count
            start = self.start
        buffer = stream.attrib_name_buffers[name]

        array_start = buffer.element_count * start
        array_end = buffer.element_count * count + array_start
        try:
            buffer.data[array_start:array_end] = data
            buffer.invalidate_region(start, count)
        except ValueError:
            msg = f"Invalid data size for '{buffer}'. Expected {array_end - array_start}, got {len(data)}."
            raise ValueError(msg) from None



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


class InstanceIndexedVertexList(VertexList):
    """A list of vertices within an :py:class:`IndexedVertexDomain` that are indexed.

    Use :py:meth:`IndexedVertexDomain.create` to construct this list.
    """
    domain: IndexedVertexDomain | InstancedIndexedVertexDomain
    indexed: bool = True
    instanced: bool = True

    index_count: int
    index_start: int

    bucket: InstanceBucket

    def __init__(self, domain: IndexedVertexDomain, start: int, count: int, index_start: int,
                 index_count: int, bucket: InstanceBucket) -> None:
        super().__init__(domain, start, count)
        self.index_start = index_start
        self.index_count = index_count
        self.bucket = bucket
        self.bucket.create_instance()

    def delete(self) -> None:
        """Delete this group."""
        raise Exception
        super().delete()
        self.domain.index_allocator.dealloc(self.index_start, self.index_count)

    def migrate(self, domain: InstancedIndexedVertexDomain) -> None:
        old_domain = self.domain

        # Moved vertex data here.
        super().migrate(domain)

        # Remove from bucket and enter into new bucket.
        new_bucket = domain.instance_domain.get_elements_bucket(mode=0,
                                                    first_index=self.index_start,
                                                   index_count=self.index_count,
                                                   index_type="I")

        # Move instance data.
        old_domain.instance_domain.move_all(self.bucket, new_bucket)

    def create_instance(self, **attributes: Any) -> None:
        return self.bucket.create_instance(**attributes)

    def set_attribute_data(self, name: str, data: Any) -> None:
        if self.initial_attribs[name].fmt.is_instanced:
            stream = self.bucket.stream
            count = 1
            start = 0
        else:
            stream = self.domain.attrib_name_buffers[name]
            count = self.count
            start = self.start
        buffer = stream.attrib_name_buffers[name]

        array_start = buffer.element_count * start
        array_end = buffer.element_count * count + array_start
        try:
            buffer.data[array_start:array_end] = data
            buffer.invalidate_region(start, count)
        except ValueError:
            msg = f"Invalid data size for '{buffer}'. Expected {array_end - array_start}, got {len(data)}."
            raise ValueError(msg) from None


class GLIndexStream(IndexStream):  # noqa: D101
    index_element_size: int
    index_c_type: CType
    gl_type: int

    def __init__(self, ctx: OpenGLSurfaceContext, data_type: DataTypes, initial_elems: int) -> None:  # noqa: D107
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
        self.buffer.bind_to_index_buffer()


class VertexDomain:
    """Management of a set of vertex lists.

    Construction of a vertex domain is usually done with the
    :py:func:`create_domain` function.
    """
    streams: list[GLVertexStream | GLInstanceStream | GLIndexStream]
    per_instance: list[Attribute]
    per_vertex: list[Attribute]

    attribute_meta: dict[str, Attribute]
    buffer_attributes: list[tuple[AttributeBufferObject, Attribute]]
    vao: GLVertexArrayBinding
    attribute_names: dict[str, Attribute]
    attrib_name_buffers: dict[str, GLVertexStream]
    _vertexlist_class: type

    _vertex_class: type[VertexList] = VertexList

    def __init__(self, context: OpenGLSurfaceContext, initial_count: int, attribute_meta: dict[str, Attribute]) -> None:  # noqa: D107
        self._context = context
        self._gl = self._context.gl

        ext = self._gl.getExtension("WEBGL_multi_draw")
        if ext:
            self._multi_draw_array = ext.multiDrawArraysWEBGL
            self._multi_draw_elements = ext.multiDrawElementsWEBGL
        else:
            self._multi_draw_array = None
            self._multi_draw_elements = None

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
        self._vertexlist_class = type(self._vertex_class.__name__, (self._vertex_class,),
                                      self.vertex_buffers._property_dict)  # noqa: SLF001

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

        starts, sizes = self.vertex_buffers.allocator.get_allocated_regions()
        primcount = len(starts)
        if primcount == 0:
            pass
        elif primcount == 1:
            # Common case
            self._gl.drawArrays(mode, starts[0], sizes[0])
        else:
            if self._multi_draw_array:
                starts = (GLint * primcount)(*starts)
                sizes = (GLsizei * primcount)(*sizes)
                self._multi_draw_array(starts[:], 0, sizes[:], 0, primcount)
            else:
                # If not available, draw separately.
                for start, size in zip(starts, sizes):
                    self._gl.drawArrays(mode, start, size)

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
        self.vao.bind()
        self.vertex_buffers.commit()
        self._gl.drawArrays(geometry_map[mode], vertex_list.start, vertex_list.count)

    @property
    def is_empty(self) -> bool:
        return not self.vertex_buffers.allocator.starts

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}@{id(self):x} vertex_alloc={self.vertex_buffers.allocator}>'


class GLInstanceDomainArrays(BaseInstanceDomain):  # noqa: D101
    def __init__(self, domain: Any, initial_instances: int) -> None:
        super().__init__(domain, initial_instances)
        self._ctx = domain._context  # noqa: SLF001
        self._gl = domain._context.gl  # noqa: SLF001

    def _create_bucket_arrays(self) -> InstanceBucket:
        istream = GLInstanceStream(self._ctx, self._initial, self._domain.per_instance, divisor=1)
        vao = GLVertexArrayBinding(self._ctx, [self._domain.vertex_buffers, istream])
        return InstanceBucket(istream, vao)

    def _create_bucket_elements(self) -> InstanceBucket:
        raise NotImplementedError("Use GLInstanceDomainElements for indexed draws")

    def draw(self, mode: int) -> None:
        for key, bucket in self._buckets.items():
            if bucket.instance_count <= 0:
                continue
            first_vertex, vertex_count = self._geom[bucket]
            bucket.vao.bind()
            bucket.stream.commit()
            self._gl.drawArraysInstanced(mode, first_vertex, vertex_count, bucket.instance_count)

    def draw_subset(self, mode: int, vertex_list: InstanceVertexList):
        """Draw a specific VertexList in the domain."""
        bucket = vertex_list.bucket
        bucket.vao.bind()
        bucket.stream.commit()
        self._gl.drawArraysInstanced(mode, vertex_list.start, vertex_list.count, bucket.instance_count)

class GLInstanceDomainElements(BaseInstanceDomain):  # noqa: D101
    _ctx: OpenGLSurfaceContext

    def __init__(self, domain: Any, initial_instances: int, index_stream: GLIndexStream) -> None:
        super().__init__(domain, initial_instances)
        self._ctx = domain._context  # noqa: SLF001
        self._gl = domain._context.gl  # noqa: SLF001
        self._index_stream = index_stream
        self._index_gl_type = self._index_stream.gl_type
        self._elem_size = index_stream.index_element_size

    def _create_bucket_elements(self) -> InstanceBucket:
        istream = GLInstanceStream(self._ctx, self._initial, self._domain.per_instance, divisor=1)
        vao = GLVertexArrayBinding(self._ctx, [self._domain.vertex_buffers, istream, self._index_stream])
        return InstanceBucket(istream, vao)

    def _create_bucket_arrays(self) -> InstanceBucket:
        raise NotImplementedError("Use GLInstanceDomainArrays for non-indexed draws")

    def draw_subset(self, mode: GeometryMode, vertex_list: InstanceIndexedVertexList) -> None:
        """Draw a specific VertexList in the domain."""
        byte_offset = vertex_list.index_start * self._elem_size
        self._gl.drawElementsInstanced(
            mode, vertex_list.index_count, self._index_gl_type, byte_offset,
            vertex_list.bucket.instance_count,
        )

    def draw(self, mode: int) -> None:
        for key, bucket in self._buckets.items():
            if bucket.instance_count <= 0:
                continue
            first_index, index_count, _, _ = self._geom[bucket]
            byte_offset = first_index * self._elem_size
            bucket.vao.bind()
            bucket.stream.commit()
            self._gl.drawElementsInstanced(
                mode, index_count, self._index_gl_type, byte_offset,
                bucket.instance_count,
            )


class InstancedVertexDomain(VertexDomain):  # noqa: D101
    _instances: int
    _instance_properties: dict[str, property]
    _vertexinstance_class: type
    _vertex_class = InstanceVertexList

    def __init__(self, context: OpenGLSurfaceContext, initial_count: int,  # noqa: D107
                 attribute_meta: dict[str, Attribute]) -> None:
        super().__init__(context, initial_count, attribute_meta)
        self.instance_buckets = GLInstanceDomainArrays(self, initial_count)
        self._initial_size = initial_count

    def _create_vao(self) -> None:
        """Handled by buckets."""

    def create(self, count: int, indices: Sequence[int] | None = None) -> VertexList:  # noqa: ARG002
        start = self.safe_alloc(count)
        bucket = self.instance_buckets.get_arrays_bucket(mode=0, first_vertex=start, vertex_count=count)
        return self._vertexlist_class(self, start, count, bucket)

    def draw(self, mode: int) -> None:
        """Draw all vertices in the domain.

        All vertices in the domain are drawn at once. This is the
        most efficient way to render primitives.

        Args:
            mode:
                OpenGL drawing mode, e.g. ``GL_POINTS``, ``GL_LINES``, etc.

        """
        self.vertex_buffers.commit()
        self.instance_buckets.draw(mode)

    def draw_subset(self, mode: GeometryMode, vertex_list: InstanceVertexList) -> None:
        """Draw a specific VertexList in the domain.

        The `vertex_list` parameter specifies a :py:class:`VertexList`
        to draw. Only primitives in that list will be drawn.

        Args:
            mode:
                OpenGL drawing mode, e.g. ``GL_POINTS``, ``GL_LINES``, etc.
            vertex_list:
                Vertex list to draw.
        """
        self.vertex_buffers.commit()
        self.instance_buckets.draw_subset(geometry_map[mode], vertex_list)



class IndexedVertexDomain(VertexDomain):
    """Management of a set of indexed vertex lists.

    Construction of an indexed vertex domain is usually done with the
    :py:func:`create_domain` function.
    """
    _vertex_class = IndexedVertexList
    _supports_base_vertex: bool = False

    def __init__(self, context: OpenGLSurfaceContext, initial_count: int, attribute_meta: dict[str, Attribute],
                 index_type: DataTypes = "I") -> None:
        self.index_type = index_type
        super().__init__(context, initial_count, attribute_meta)
        # Make a custom VertexList class w/ properties for each attribute in the ShaderProgram:
        self._vertexlist_class = type(self._vertex_class.__name__, (_RunningIndexSupport, self._vertex_class),
                                      self.vertex_buffers._property_dict)  # noqa: SLF001

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
                The indices used for this vertex list.

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
        self.index_stream.buffer.commit()

        starts, sizes = self.index_stream.allocator.get_allocated_regions()
        primcount = len(starts)
        if primcount == 0:
            pass
        elif primcount == 1:
            # Common case
            self._gl.drawElements(mode, sizes[0], self.index_stream.gl_type, starts[0] * self.index_stream.index_element_size)
        else:
            if self._multi_draw_elements:
                starts = [s * self.index_stream.index_element_size for s in starts]
                starts = (ctypes.POINTER(GLvoid) * primcount)(*(GLintptr * primcount)(*starts))
                sizes = (GLsizei * primcount)(*sizes)
                self._multi_draw_elements(mode, sizes[:], 0, self.index_stream.gl_type, starts[:], 0, primcount)
            else:
                for start, size in zip(starts, sizes):
                    self._gl.drawElements(mode, size, self.index_stream.gl_type,
                                          start * self.index_stream.index_element_size)

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
        self.vao.bind()
        self.vertex_buffers.commit()
        self.index_stream.buffer.commit()

        self._gl.drawElements(geometry_map[mode], vertex_list.index_count, self.index_stream.gl_type,
                       vertex_list.index_start * self.index_stream.index_element_size)



class InstancedIndexedVertexDomain(IndexedVertexDomain):
    """Management of a set of indexed vertex lists.

    Construction of an indexed vertex domain is usually done with the
    :py:func:`create_domain` function.
    """
    _initial_index_count: int = 16
    _vertex_class = InstanceIndexedVertexList

    def __init__(self, context: OpenGLSurfaceContext, initial_count: int, attribute_meta: dict[str, dict[str, Any]],
                 index_type: DataTypes = "I") -> None:
        super().__init__(context, initial_count, attribute_meta, index_type)
        self.instance_domain = GLInstanceDomainElements(self, initial_count, index_stream=self.index_stream)

    def _create_vao(self) -> None:
        """Handled by buckets."""

    def create(self, count: int, indices: Sequence[int] | None) -> IndexedVertexList:
        """Create an :py:class:`IndexedVertexList` in this domain.

        Args:
            count:
                Number of vertices to create
            indices:
                Indices used for this vertex list.

        """
        index_count = len(indices)
        start = self.safe_alloc(count)
        index_start = self.safe_index_alloc(index_count)
        bucket = self.instance_domain.get_elements_bucket(
            mode=0,  # Separate Mode from draw call into bucket at some point?
            first_index=index_start,
            index_count=index_count,
            index_type=self.index_type,
            base_vertex=0,
        )
        vertex_list = self._vertexlist_class(self, start, count, index_start, index_count, bucket)
        vertex_list.indices = indices
        return vertex_list

    def draw(self, mode: int) -> None:
        """Draw all vertices in the domain.

        All vertices in the domain are drawn at once. This is the
        most efficient way to render primitives.

        Args:
            mode:
                OpenGL drawing mode, e.g. ``GL_POINTS``, ``GL_LINES``, etc.

        """
        self.vertex_buffers.commit()
        self.index_stream.commit()
        self.instance_domain.draw(mode)

    def draw_subset(self, mode: GeometryMode, vertex_list: InstanceIndexedVertexList) -> None:
        """Draw a specific IndexedVertexList in the domain.

        The ``vertex_list`` parameter specifies a :py:class:`IndexedVertexList`
        to draw. Only primitives in that list will be drawn.

        Args:
            mode:
                OpenGL drawing mode, e.g. ``GL_POINTS``, ``GL_LINES``, etc.
            vertex_list:
                Vertex list to draw.

        """
        self.vertex_buffers.commit()
        self.index_stream.commit()
        self.instance_domain.draw_subset(geometry_map[mode], vertex_list)
