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
from pyglet.graphics.vertexdomain import (
    VertexStream,
    IndexStream,
    VertexArrayBinding,
    VertexArrayProtocol,
    VertexDomainBase,
    VertexListBase,
    IndexedVertexDomainBase,
    IndexedVertexListBase,
    VertexGroupBucket,
    _RunningIndexSupport,
)

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
    streams: list[GLVertexStream | GLIndexStream]

    """GL2 doesn't have a real VAO. This just acts as a container."""
    def _create_vao(self) -> VertexArrayProtocol | None:
        return None

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
    def __init__(self, *args, **kwargs):
        raise NotImplementedError("InstancedVertexDomain is not available in OpenGL 2.0.")


class InstancedIndexedVertexDomain:
    """Not available in OpenGL 2.0"""
    def __init__(self, *args, **kwargs):
        raise NotImplementedError("InstancedIndexedVertexDomain is not available in OpenGL 2.0.")


class VertexList(VertexListBase):
    ...


class IndexedVertexList(IndexedVertexListBase):
    ...


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

    def bind_into(self, _vao: None) -> None:
        for attribute, buffer in zip(self.attribute_names.values(), self.buffers):
            buffer.commit()
            attribute.enable()
            attribute.set_pointer()

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


class VertexDomain(VertexDomainBase):
    """Management of a set of vertex lists.

    Construction of a vertex domain is usually done with the
    :py:func:`create_domain` function.
    """
    def _has_multi_draw_extension(self, ctx: OpenGLSurfaceContext) -> bool:
        return ctx.get_info().have_extension("GL_EXT_multi_draw_arrays")

    def _create_vertex_class(self) -> type:
        return type(self._vertex_class.__name__, (self._vertex_class,), self.vertex_buffers._property_dict)

    def _create_vao(self) -> GLVertexArrayBinding:
        return GLVertexArrayBinding(self._context, self._streams)

    def _create_streams(self, size: int) -> list[VertexStream | IndexStream]:
        self.vertex_buffers = GLVertexStream(self._context, size, self.per_vertex)
        return [self.vertex_buffers]

    def draw_buckets(self, mode: int, buckets: list[VertexGroupBucket]) -> None:
        regions = []
        for bucket in buckets:
            regions.extend(bucket.merged_ranges)

        start_list = [region[0] for region in regions]
        size_list = [region[1] for region in regions]

        if self._supports_multi_draw:
            primcount = len(regions)
            starts = (GLint * primcount)(*start_list)
            sizes = (GLsizei * primcount)(*size_list)
            self._context.glMultiDrawArrays(mode, starts, sizes, primcount)
        else:
            for start, size in zip(start_list, size_list):
                self._context.glDrawArrays(mode, start, size)

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



class IndexedVertexDomain(IndexedVertexDomainBase):
    """Management of a set of indexed vertex lists.

    Construction of an indexed vertex domain is usually done with the
    :py:func:`create_domain` function.
    """

    _vertex_class = IndexedVertexList
    index_stream: GLIndexStream

    def _create_vertex_class(self) -> type:
        # Make a custom VertexList class w/ properties for each attribute in the ShaderProgram:
        return type(self._vertex_class.__name__, (_RunningIndexSupport, self._vertex_class),
                                      self.vertex_buffers._property_dict)  # noqa: SLF001

    def _has_multi_draw_extension(self, ctx: OpenGLSurfaceContext) -> bool:
        return ctx.get_info().have_extension("GL_EXT_multi_draw_arrays")

    def _create_vao(self) -> GLVertexArrayBinding:
        return GLVertexArrayBinding(self._context, self._streams)

    def _create_streams(self, size: int) -> list[VertexStream | IndexStream]:
        self.vertex_buffers = GLVertexStream(self._context, size, self.per_vertex)
        self.index_stream = GLIndexStream(self._context, self.index_type, size)
        return [self.vertex_buffers, self.index_stream]

    def draw_buckets(self, mode: int, buckets: list[VertexGroupBucket]) -> None:
        self.vao.bind()
        regions = []
        for bucket in buckets:
            regions.extend(bucket.merged_ranges)

        start_list = [region[0] for region in regions]
        size_list = [region[1] for region in regions]
        primcount = len(regions)

        if self._supports_multi_draw:
            starts = [s * self.index_stream.index_element_size for s in start_list]
            starts = (ctypes.POINTER(GLvoid) * primcount)(*(GLintptr * primcount)(*starts))
            sizes = (GLsizei * primcount)(*size_list)
            self._context.glMultiDrawElements(mode, sizes, self.index_stream.gl_type, starts, primcount)
        else:
            for start, size in zip(start_list, size_list):
                self._context.glDrawElements(
                    mode, size, self.index_stream.gl_type, start * self.index_stream.index_element_size)

        self.vao.unbind()

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
