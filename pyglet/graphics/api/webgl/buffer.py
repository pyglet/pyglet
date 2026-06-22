"""WebGL Buffer Objects."""

from __future__ import annotations

import sys
from functools import lru_cache
from typing import TYPE_CHECKING, Sequence

import js
import pyodide.ffi

from pyglet.graphics.api.webgl.gl import (
    GL_ARRAY_BUFFER,
    GL_BUFFER_SIZE,
    GL_DRAW_INDIRECT_BUFFER,
    GL_DYNAMIC_DRAW,
    GL_ELEMENT_ARRAY_BUFFER,
    GL_PIXEL_PACK_BUFFER,
    GL_PIXEL_UNPACK_BUFFER,
    GL_TEXTURE_BUFFER,
    GL_TRANSFORM_FEEDBACK_BUFFER,
    GL_UNIFORM_BUFFER,
)
from pyglet.graphics import UnsupportedBackendError
from pyglet.graphics.buffer import (
    AbstractBuffer,
    BackedBufferObject as BaseBackedBufferObject,
    BufferDataStore,
    CTypeDataStore,
    DrawIndirectBuffer,
    MappedBufferObject as BaseMappedBufferObject,
    PixelBuffer,
    PixelPackBuffer,
    PixelUnpackBuffer,
    TextureBuffer,
    TransformFeedbackBuffer,
    UniformBufferObject,
    _data_type_size,
)

if TYPE_CHECKING:
    from pyglet.customtypes import DataTypes
    from pyglet.graphics.api.webgl import OpenGLSurfaceContext
    from pyglet.graphics.api.webgl.webgl_js import WebGLBuffer
    from pyglet.graphics.shader import GraphicsAttribute


def _to_js_uint8(data: bytes) -> js.Uint8Array:
    buffer = pyodide.ffi.to_js(memoryview(data))
    return js.Uint8Array.new(buffer)


class WebGLBufferObject(AbstractBuffer):
    """Lightweight WebGL buffer object.

    This class intentionally treats data as bytes for GPU transfer.
    """

    id: WebGLBuffer | None
    usage: int
    target: int

    # If the buffer data has been allocated yet.
    _allocated: bool

    # Even if it's allocated, there may be garbage in there. Mark when actual data exists.
    _data_uploaded: bool
    _context: OpenGLSurfaceContext

    def __init__(
        self,
        context: OpenGLSurfaceContext,
        size: int,
        target: int = GL_ARRAY_BUFFER,
        usage: int = GL_DYNAMIC_DRAW,
    ) -> None:
        super().__init__(size)
        self.usage = usage
        self.target = target
        self._context = context
        self._gl = context.gl

        self.id = self._gl.createBuffer()
        self._allocated = False
        self._data_uploaded = False

    def _validate_byte_range(self, offset: int, length: int) -> None:
        assert offset >= 0 and length >= 0, "Offset and length must be non-negative."
        assert offset + length <= self.size, (
            f"Byte range [{offset}, {offset + length}) exceeds buffer size {self.size}."
        )

    def bind(self) -> None:
        self._gl.bindBuffer(self.target, self.id)

    def unbind(self) -> None:
        self._gl.bindBuffer(self.target, None)

    def _ensure_allocated(self) -> None:
        if self._allocated:
            return
        self.bind()
        self._gl.bufferData(self.target, self.size, self.usage)
        self._allocated = True

    def _require_uploaded_data(self) -> None:
        assert self._data_uploaded, (
            "Buffer data has not been uploaded yet. "
            "Call set_bytes/set_bytes_region, commit, or write through a mapped pointer first."
        )

    def _set_data_uploaded(self) -> None:
        self._allocated = True
        self._data_uploaded = True

    def get_buffer_size(self) -> int:
        self.bind()
        return self._gl.getBufferParameter(self.target, GL_BUFFER_SIZE)

    def get_bytes(self) -> bytes:
        self._require_uploaded_data()
        self.bind()
        data = js.Uint8Array.new(self.size)
        self._gl.getBufferSubData(self.target, 0, data)
        return bytes(data.buffer.to_py(depth=1))

    def get_bytes_region(self, offset: int, length: int) -> bytes:
        self._require_uploaded_data()
        self._validate_byte_range(offset, length)
        self.bind()
        data = js.Uint8Array.new(length)
        self._gl.getBufferSubData(self.target, offset, data)
        return bytes(data.buffer.to_py(depth=1))

    def set_bytes(self, data: bytes | bytearray | memoryview) -> None:
        raw = bytes(data)
        assert len(raw) == self.size, f"Expected {self.size} bytes for full upload, got {len(raw)}."
        self.bind()
        self._gl.bufferData(self.target, _to_js_uint8(raw), self.usage)
        self._set_data_uploaded()

    def set_bytes_region(self, offset: int, data: bytes | bytearray | memoryview) -> None:
        # BufferObject updates are whole-buffer by design. Patch the local
        # bytes and re-upload the full content.
        raw = bytes(data)
        self._validate_byte_range(offset, len(raw))
        whole = bytearray(self.get_bytes()) if self._data_uploaded else bytearray(self.size)
        whole[offset:offset + len(raw)] = raw
        self.set_bytes(whole)

    def invalidate(self) -> None:
        self.bind()
        self._gl.bufferData(self.target, self.size, self.usage)
        self._allocated = True
        self._data_uploaded = False

    def delete(self) -> None:
        if self.id is None:
            return
        self._gl.deleteBuffer(self.id)
        self.id = None
        self._allocated = False
        self._data_uploaded = False

    def __del__(self) -> None:
        if self.id is not None:
            try:
                self._context.delete_buffer(self.id)
                self.id = None
            except (AttributeError, ImportError):
                pass  # Interpreter is shutting down

    def resize(self, size: int) -> None:
        if size == self.size:
            return
        if not self._allocated:
            self.size = size
            self._data_uploaded = False
            return

        # Copy data from old buffer into new buffer, then replace.
        old_id = self.id
        new_id = self._gl.createBuffer()
        copy_size = min(self.size, size) if self._data_uploaded else 0

        self._gl.bindBuffer(self._gl.COPY_READ_BUFFER, old_id)
        self._gl.bindBuffer(self._gl.COPY_WRITE_BUFFER, new_id)
        self._gl.bufferData(self._gl.COPY_WRITE_BUFFER, size, self._gl.DYNAMIC_DRAW)
        if copy_size > 0:
            self._gl.copyBufferSubData(
                self._gl.COPY_READ_BUFFER,
                self._gl.COPY_WRITE_BUFFER,
                0,
                0,
                copy_size,
            )
        self._gl.deleteBuffer(old_id)
        self.id = new_id
        self.size = size
        self._allocated = True
        self._data_uploaded = copy_size > 0

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, size={self.size})"


class WebGLMappedBufferObject(WebGLBufferObject, BaseMappedBufferObject):
    """Mapped WebGL buffers are not supported."""

    def map(self, bits: int = 0):
        raise UnsupportedBackendError("MappedBufferObject")

    def map_range(self, start: int, size: int, ptr_type, bits: int = 0):
        raise UnsupportedBackendError("MappedBufferObject")

    def unmap(self) -> None:
        raise UnsupportedBackendError("MappedBufferObject")


class WebGLBackedBufferObject(BaseBackedBufferObject, WebGLBufferObject):
    """Buffer with host-side mirrored store and deferred GPU commit."""

    data: object
    data_ptr: int | None
    _dirty_min: int
    _dirty_max: int
    _dirty: bool

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
        WebGLBufferObject.__init__(self, context, size, target=target, usage=usage)

        store = store or CTypeDataStore(size, data_type, stride, element_count)
        assert store.size == size and store.stride == stride and store.element_count == element_count, (
            "Store layout mismatch. "
            f"Expected size={size}, stride={stride}, element_count={element_count}; "
            f"got size={store.size}, stride={store.stride}, element_count={store.element_count}."
        )
        BaseBackedBufferObject.__init__(self, size, store)

        self._dirty_min = sys.maxsize
        self._dirty_max = 0
        self._dirty = False

    def _mark_dirty_bytes(self, byte_start: int, byte_end: int) -> None:
        if byte_start < self._dirty_min:
            self._dirty_min = byte_start
        if byte_end > self._dirty_max:
            self._dirty_max = byte_end
        self._dirty = True

    def set_bytes(self, data: bytes | bytearray | memoryview) -> None:
        raw = bytes(data)
        assert len(raw) == self.size, f"Expected {self.size} bytes for full upload, got {len(raw)}."
        self.store.set_bytes(0, raw)
        self._mark_dirty_bytes(0, self.size)

    def set_bytes_region(self, offset: int, data: bytes | bytearray | memoryview) -> None:
        raw = bytes(data)
        assert 0 <= offset <= self.size and offset + len(raw) <= self.size, (
            f"Byte range [{offset}, {offset + len(raw)}) exceeds buffer size {self.size}."
        )
        self.store.set_bytes(offset, raw)
        self._mark_dirty_bytes(offset, offset + len(raw))

    def commit(self) -> None:
        if not self._dirty:
            return

        self.bind()
        size = self._dirty_max - self._dirty_min
        if not self._allocated or not self._data_uploaded or size == self.size:
            self._gl.bufferData(self.target, _to_js_uint8(self.store.get_bytes()), self.usage)
        else:
            self._gl.bufferSubData(
                self.target,
                self._dirty_min,
                _to_js_uint8(self.store.get_bytes(self._dirty_min, size)),
            )
        self._set_data_uploaded()

        self._dirty_min = sys.maxsize
        self._dirty_max = 0
        self._dirty = False

    @lru_cache(maxsize=None)  # noqa: B019
    def get_region(self, start: int, count: int):
        return self.store.get_region(start, count)

    def set_region(self, start: int, count: int, data: Sequence[float | int]) -> None:
        self.store.set_region(start, count, data)
        self.invalidate_region(start, count)

    def copy_region(self, dst: int, src: int, count: int) -> None:
        self.store.copy_region(dst, src, count)
        self.invalidate_region(dst, count)

    def resize(self, size: int) -> None:
        self.resize_store(size)

        self._dirty_min = 0
        self._dirty_max = self.size
        self._dirty = True
        self.get_region.cache_clear()


class WebGLAttributeBufferObject(WebGLBackedBufferObject):
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


class WebGLIndexedBufferObject(WebGLBackedBufferObject):
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
            usage,
            target=GL_ELEMENT_ARRAY_BUFFER,
            store=store,
        )

    def bind_to_index_buffer(self) -> None:
        self._gl.bindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.id)


class WebGLPixelBufferObject(WebGLBufferObject, PixelBuffer):
    """WebGL pixel transfer buffer object (PBO)."""

    def __init__(
        self,
        context: OpenGLSurfaceContext,
        size: int,
        *,
        pack: bool = False,
        usage: int = GL_DYNAMIC_DRAW,
    ) -> None:
        target = GL_PIXEL_PACK_BUFFER if pack else GL_PIXEL_UNPACK_BUFFER
        super().__init__(context, size, target=target, usage=usage)


class WebGLPixelPackBufferObject(WebGLPixelBufferObject, PixelPackBuffer):
    """WebGL pixel pack buffer object (readback path)."""

    def __init__(self, context: OpenGLSurfaceContext, size: int, usage: int = GL_DYNAMIC_DRAW) -> None:
        super().__init__(context, size, pack=True, usage=usage)


class WebGLPixelUnpackBufferObject(WebGLPixelBufferObject, PixelUnpackBuffer):
    """WebGL pixel unpack buffer object (upload path)."""

    def __init__(self, context: OpenGLSurfaceContext, size: int, usage: int = GL_DYNAMIC_DRAW) -> None:
        super().__init__(context, size, pack=False, usage=usage)


class WebGLTransformFeedbackBufferObject(WebGLBufferObject, TransformFeedbackBuffer):
    """WebGL transform feedback buffer object."""

    def __init__(
        self,
        context: OpenGLSurfaceContext,
        size: int,
        usage: int = GL_DYNAMIC_DRAW,
        data_type: DataTypes = "b",
    ) -> None:
        """Create a WebGL transform feedback buffer.

        Args:
            context:
                Active WebGL surface context.
            size:
                Buffer size in bytes.
            usage:
                WebGL usage hint.
            data_type:
                Preferred scalar format for :meth:`get_data`. The helper always
                returns a ctypes array of this scalar type.
        """
        element_size = _data_type_size(data_type)
        assert size % element_size == 0, (
            f"Buffer size {size} is not aligned to element size {element_size} "
            f"for data type '{data_type}'."
        )
        super().__init__(context, size, target=GL_TRANSFORM_FEEDBACK_BUFFER, usage=usage)
        TransformFeedbackBuffer.__init__(self, size=size, data_type=data_type)

    def bind_base(self, index: int) -> None:
        self._ensure_allocated()
        self._gl.bindBufferBase(GL_TRANSFORM_FEEDBACK_BUFFER, index, self.id)
        self._data_uploaded = True

    def bind_range(self, index: int, offset: int, size: int) -> None:
        self._validate_byte_range(offset, size)
        self._ensure_allocated()
        self._gl.bindBufferRange(GL_TRANSFORM_FEEDBACK_BUFFER, index, self.id, offset, size)
        self._data_uploaded = True


class WebGLTextureBufferObject(WebGLBufferObject, TextureBuffer):
    """WebGL texture buffer object (TBO)."""

    def __init__(self, context: OpenGLSurfaceContext, size: int, usage: int = GL_DYNAMIC_DRAW) -> None:
        super().__init__(context, size, target=GL_TEXTURE_BUFFER, usage=usage)


class WebGLDrawIndirectBufferObject(WebGLBufferObject, DrawIndirectBuffer):
    """WebGL draw indirect buffer object."""

    def __init__(self, context: OpenGLSurfaceContext, size: int, usage: int = GL_DYNAMIC_DRAW) -> None:
        super().__init__(context, size, target=GL_DRAW_INDIRECT_BUFFER, usage=usage)


class WebGLUniformBufferObject(UniformBufferObject):
    """WebGL Uniform Buffer Object wrapper."""

    buffer: WebGLBufferObject
    minimum_alignment: int
    __slots__ = ("_gl", "minimum_alignment")

    def __init__(
        self,
        context: OpenGLSurfaceContext,
        view_class: type,
        buffer_size: int,
        binding: int,
        *,
        alignment: int | None = None,
        copies_per_resource: int = 3,
        strict: bool = False,
    ) -> None:
        self._context = context
        self._gl = context.gl
        self.minimum_alignment = max(1, context.info.MAX_UNIFORM_BUFFER_OFFSET_ALIGNMENT)
        requested_alignment = self.minimum_alignment if alignment is None else max(int(alignment), self.minimum_alignment)
        super().__init__(
            context,
            view_class,
            buffer_size,
            binding,
            alignment=requested_alignment,
            copies_per_resource=copies_per_resource,
            strict=strict,
        )

    def _create_buffer(self, context: OpenGLSurfaceContext, buffer_size: int) -> WebGLBufferObject:
        return WebGLBufferObject(context, buffer_size, target=GL_UNIFORM_BUFFER)

    def _bind_range(self, binding: int, offset: int, size: int) -> None:
        self._gl.bindBufferRange(GL_UNIFORM_BUFFER, binding, self.buffer.id, offset, size)


class WebGLPersistentBufferObject(BaseMappedBufferObject):
    """Persistently mapped buffers are not currently implemented."""

    def __init__(self, context, size, attribute, vao):  # noqa: ANN001
        raise UnsupportedBackendError("PersistentBufferObject")
