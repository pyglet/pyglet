"""OpenGL 2.0 buffer objects built on top of the shared GL implementation."""

from __future__ import annotations

from ctypes import Structure
from typing import TYPE_CHECKING

from pyglet.graphics.api.gl import GL_ARRAY_BUFFER, GL_DYNAMIC_DRAW, GL_ELEMENT_ARRAY_BUFFER, OpenGLSurfaceContext
from pyglet.graphics.api.gl.buffer import GLBackedBufferObject, GLBufferObject, GLMappedBufferObject
from pyglet.graphics.buffer import BufferDataStore, MappedBufferObject as BaseMappedBufferObject

if TYPE_CHECKING:
    from pyglet.customtypes import DataTypes
    from pyglet.graphics.shader import GraphicsAttribute


class GL2BufferObject(GLBufferObject):
    """OpenGL 2.0 buffer object wrapper using shared GL buffer behavior."""

    def __init__(
        self,
        context: OpenGLSurfaceContext,
        size: int,
        usage: int = GL_DYNAMIC_DRAW,
        target: int = GL_ARRAY_BUFFER,
    ) -> None:
        super().__init__(context, size, target=target, usage=usage)

    def bind_to_index_buffer(self) -> None:
        self._context.glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.id)


class GL2MappedBufferObject(GLMappedBufferObject):
    """OpenGL 2.0 mapped buffer wrapper.

    Not supported in GLES 2.0.
    """

    def __init__(
        self,
        context: OpenGLSurfaceContext,
        size: int,
        usage: int = GL_DYNAMIC_DRAW,
        target: int = GL_ARRAY_BUFFER,
    ) -> None:
        super().__init__(context, size, target=target, usage=usage)


class GL2BackedBufferObject(GLBackedBufferObject):
    """OpenGL 2.0 backed buffer wrapper."""

    def __init__(
        self,
        context: OpenGLSurfaceContext,
        size: int,
        data_type: DataTypes,
        stride: int,
        element_count: int,
        usage: int = GL_DYNAMIC_DRAW,
        target: int = GL_ARRAY_BUFFER,
        store: BufferDataStore | None = None,
    ) -> None:
        super().__init__(
            context,
            size,
            data_type,
            stride,
            element_count,
            usage=usage,
            target=target,
            store=store,
        )


class GL2AttributeBufferObject(GL2BackedBufferObject):
    """A backed buffer used for shader attributes."""

    def __init__(
        self,
        context: OpenGLSurfaceContext,
        size: int,
        graphics_attr: GraphicsAttribute,
        store: BufferDataStore | None = None,
    ) -> None:
        super().__init__(
            context,
            size,
            graphics_attr.attribute.fmt.data_type,
            graphics_attr.view.stride,
            graphics_attr.attribute.fmt.components,
            store=store,
        )


class GL2IndexedBufferObject(GL2BackedBufferObject):
    """A backed buffer used for indices."""

    def __init__(
        self,
        context: OpenGLSurfaceContext,
        size: int,
        data_type: DataTypes,
        stride: int,
        count: int,
        usage: int = GL_DYNAMIC_DRAW,
        store: BufferDataStore | None = None,
    ) -> None:
        super().__init__(
            context,
            size,
            data_type,
            stride,
            count,
            usage=usage,
            target=GL_ELEMENT_ARRAY_BUFFER,
            store=store,
        )

    def bind_to_index_buffer(self) -> None:
        self._context.glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.id)


class GL2UniformBufferObject:
    """Uniform buffers are unsupported in OpenGL 2.0."""

    def __init__(self, view_class: type[Structure], buffer_size: int, binding: int) -> None:
        msg = "UniformBufferObject is not available in OpenGL 2.0."
        raise NotImplementedError(msg)


UniformBufferObject = GL2UniformBufferObject


class GL2PersistentBufferObject(BaseMappedBufferObject):
    """Persistent mapped buffers are unsupported in OpenGL 2.0."""

    def __init__(self, context, size, attribute, vao):  # noqa: ANN001
        msg = "PersistentBufferObject is not available in OpenGL 2.0."
        raise NotImplementedError(msg)
