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
from typing import TYPE_CHECKING, Mapping, Sequence

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
    OpenGLSurfaceContext,

)
from pyglet.graphics import UnsupportedBackendError
from pyglet.graphics.api.gl.enums import geometry_map
from pyglet.graphics.api.gl.shader import GLAttribute
from pyglet.graphics.api.gl2.buffer import GL2AttributeBufferObject, GL2IndexedBufferObject
from pyglet.graphics.buffer import _data_type_size
from pyglet.graphics.vertexstorage import VertexStream, IndexStream, VertexArrayBinding, VertexArrayProtocol
from pyglet.graphics.vertexdomain import (
    VertexDomain as BaseVertexDomain,
    VertexList as BaseVertexList,
    IndexedVertexDomain as BaseIndexedVertexDomain,
    IndexedVertexList as BaseIndexedVertexList,
    VertexGroupBucket,
    _RunningIndexSupport,
)

if TYPE_CHECKING:
    from pyglet.graphics.attributes import Attribute, AttributeFormat, AttributeView
    from pyglet.graphics.shader import ShaderProgram
    from pyglet.customtypes import DataTypes
    from pyglet.enums import GeometryMode

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

class GLVertexArrayBinding(VertexArrayBinding):
    streams: list[GLVertexStream | GLIndexStream]

    def __init__(self, ctx: OpenGLSurfaceContext, streams: list[VertexStream | IndexStream],
                 attributes: Mapping[str, Attribute] | None = None) -> None:
        self.shader_attributes = attributes or {}
        super().__init__(ctx, streams)

    """GL2 doesn't have a real VAO. This just acts as a container."""
    def _create_vao(self) -> VertexArrayProtocol | None:
        return None

    def _link(self) -> None:
        pass

    def bind(self) -> None:
        for stream in self.streams:
            stream.bind_into(self)

    def unbind(self) -> None:
        for stream in self.streams:
            if isinstance(stream, GLVertexStream):
                stream.unbind(self)
            else:
                stream.unbind()


class InstancedVertexDomain:
    """Not available in OpenGL 2.0"""
    def __init__(self, *args, **kwargs):
        raise UnsupportedBackendError("InstancedVertexDomain")


class InstancedIndexedVertexDomain:
    """Not available in OpenGL 2.0"""
    def __init__(self, *args, **kwargs):
        raise UnsupportedBackendError("InstancedIndexedVertexDomain")


class VertexList(BaseVertexList):
    ...


class IndexedVertexList(BaseIndexedVertexList):
    ...


class GLVertexStream(VertexStream):
    _ctx: OpenGLSurfaceContext

    def __init__(self, ctx: OpenGLSurfaceContext, initial_size: int, attrs: Sequence[AttributeFormat],
                 *, divisor: int = 0):
        super().__init__(ctx, initial_size, attrs, divisor=divisor)

    def get_attribute_layout(self, attribute: AttributeFormat, view: AttributeView) -> GLAttribute:
        return GLAttribute(attribute, view)

    def get_buffer(self, size: int, attribute) -> GL2AttributeBufferObject:
        return GL2AttributeBufferObject(self._ctx, size, attribute)

    def _enable_attribute(self, location: int) -> None:
        """Enable a shader input at ``location``."""
        self._ctx.glEnableVertexAttribArray(location)

    def _disable_attribute(self, location: int) -> None:
        """Disable a shader input at ``location``."""
        self._ctx.glDisableVertexAttribArray(location)

    def _set_attribute_pointer(self, shader_attribute: Attribute, graphics_attribute: GLAttribute) -> None:
        """Bind geometry storage to a shader input."""
        location = shader_attribute.location
        geometry_format = graphics_attribute.fmt
        if shader_attribute.is_integer:
            self._ctx.glVertexAttribIPointer(
                location, geometry_format.components, graphics_attribute.gl_type,
                graphics_attribute.view.stride, ctypes.c_void_p(graphics_attribute.view.offset),
            )
        else:
            self._ctx.glVertexAttribPointer(
                location, geometry_format.components, graphics_attribute.gl_type,
                geometry_format.normalized, graphics_attribute.view.stride,
                ctypes.c_void_p(graphics_attribute.view.offset),
            )

    def bind_into(self, binding: GLVertexArrayBinding) -> None:
        for name, graphics_attribute in self.attribute_layouts.items():
            shader_attribute = binding.shader_attributes.get(name)
            if shader_attribute is None:
                continue
            buffer = self.attrib_name_buffers[name]
            # Enforce bind even if buffer is not dirty.
            buffer.bind()
            buffer.commit()
            location = shader_attribute.location
            self._enable_attribute(location)
            self._set_attribute_pointer(shader_attribute, graphics_attribute)

    def unbind(self, binding: GLVertexArrayBinding) -> None:
        for shader_attribute in binding.shader_attributes.values():
            self._disable_attribute(shader_attribute.location)


class GLIndexStream(IndexStream):
    index_element_size: int
    gl_type: int

    def __init__(self, ctx: OpenGLSurfaceContext, data_type: DataTypes, initial_elems: int) -> None:
        self.gl_type = _gl_types[data_type]
        super().__init__(ctx, data_type, initial_elems)
        self.index_element_size = self.buffer.element_size

    def _create_buffer(self) -> GL2IndexedBufferObject:
        index_element_size = _data_type_size(self.data_type)
        return GL2IndexedBufferObject(
            self.ctx,
            self.allocator.capacity * index_element_size,
            self.data_type,
            index_element_size,
            1,
        )

    def bind_into(self, _vao: VertexArrayBinding) -> None:
        # Indexed draw offsets are interpreted relative to the currently bound element buffer.
        self.buffer.bind_to_index_buffer()
        self.buffer.commit()

    def unbind(self):
        self.buffer.unbind()


class VertexDomain(BaseVertexDomain):
    """Management of a set of vertex lists.

    Construction of a vertex domain is usually done with the
    :py:func:`create_domain` function.
    """
    def _has_multi_draw_extension(self, ctx: OpenGLSurfaceContext) -> bool:
        return ctx.info.have_extension("GL_EXT_multi_draw_arrays")

    def _create_vertex_class(self) -> type:
        return type(self._vertex_class.__name__, (self._vertex_class,), self.vertex_buffers._property_dict)

    def _create_vao(self) -> GLVertexArrayBinding:
        return GLVertexArrayBinding(self._context, self._streams, self.shader_attributes)

    def get_vertex_input_binding(self, program: ShaderProgram) -> GLVertexArrayBinding:
        super().get_vertex_input_binding(program)
        if program.attributes == self.shader_attributes:
            return self.vao
        try:
            return self._vertex_input_bindings[program.key]
        except AttributeError:
            self._vertex_input_bindings = {}
        except KeyError:
            pass
        binding = GLVertexArrayBinding(self._context, self._streams, program.attributes)
        self._vertex_input_bindings[program.key] = binding
        return binding

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
                A :class:`~pyglet.enums.GeometryMode` value, such as
                :attr:`~pyglet.enums.GeometryMode.POINTS` or
                :attr:`~pyglet.enums.GeometryMode.LINES`.

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

        self.vao.unbind()

    def draw_subset(self, mode: GeometryMode, vertex_list: VertexList) -> None:
        """Draw a specific VertexList in the domain.

        The `vertex_list` parameter specifies a :py:class:`VertexList`
        to draw. Only primitives in that list will be drawn.

        Args:
            mode:
                A :class:`~pyglet.enums.GeometryMode` value, such as
                :attr:`~pyglet.enums.GeometryMode.POINTS` or
                :attr:`~pyglet.enums.GeometryMode.LINES`.
            vertex_list:
                Vertex list to draw.

        """
        self.vertex_buffers.commit()
        self._context.glDrawArrays(geometry_map[mode], vertex_list.start, vertex_list.count)

    @property
    def is_empty(self) -> bool:
        return not self.vertex_buffers.allocator.starts

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}@{id(self):x} {self.allocator}>'



class IndexedVertexDomain(BaseIndexedVertexDomain):
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
        return ctx.info.have_extension("GL_EXT_multi_draw_arrays")

    def _create_vao(self) -> GLVertexArrayBinding:
        return GLVertexArrayBinding(self._context, self._streams, self.shader_attributes)

    def get_vertex_input_binding(self, program: ShaderProgram) -> GLVertexArrayBinding:
        super().get_vertex_input_binding(program)
        if program.attributes == self.shader_attributes:
            return self.vao
        try:
            return self._vertex_input_bindings[program.key]
        except AttributeError:
            self._vertex_input_bindings = {}
        except KeyError:
            pass
        binding = GLVertexArrayBinding(self._context, self._streams, program.attributes)
        self._vertex_input_bindings[program.key] = binding
        return binding

    def _create_streams(self, size: int) -> list[VertexStream | IndexStream]:
        self.vertex_buffers = GLVertexStream(self._context, size, self.per_vertex)
        self.index_stream = GLIndexStream(self._context, self.index_type, size)
        return [self.vertex_buffers, self.index_stream]

    def draw_buckets(self, mode: int, buckets: list[VertexGroupBucket]) -> None:
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

    def draw_subset(self, mode: GeometryMode, vertex_list: IndexedVertexList) -> None:
        """Draw a specific IndexedVertexList in the domain.

        The `vertex_list` parameter specifies a :py:class:`IndexedVertexList`
        to draw. Only primitives in that list will be drawn.

        Args:
            mode:
                A :class:`~pyglet.enums.GeometryMode` value, such as
                :attr:`~pyglet.enums.GeometryMode.POINTS` or
                :attr:`~pyglet.enums.GeometryMode.LINES`.
            vertex_list:
                Vertex list to draw.
        """
        self.vertex_buffers.commit()
        self.index_stream.commit()
        self._context.glDrawElements(
            geometry_map[mode],
            vertex_list.index_count,
            self.index_stream.gl_type,
            vertex_list.index_start * self.index_stream.index_element_size,
        )
