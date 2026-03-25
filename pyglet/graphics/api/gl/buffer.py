"""OpenGL Buffer Objects."""

from __future__ import annotations

import ctypes
import sys
from functools import lru_cache
from typing import TYPE_CHECKING, Sequence

import pyglet
from pyglet.graphics.api.gl import (
    GL_ARRAY_BUFFER,
    GL_DRAW_INDIRECT_BUFFER,
    GL_DYNAMIC_DRAW,
    GL_ELEMENT_ARRAY_BUFFER,
    GL_READ_ONLY,
    GL_READ_WRITE,
    GL_MAP_COHERENT_BIT,
    GL_MAP_PERSISTENT_BIT,
    GL_MAP_READ_BIT,
    GL_MAP_WRITE_BIT,
    GL_PIXEL_PACK_BUFFER,
    GL_PIXEL_UNPACK_BUFFER,
    GL_TEXTURE_BUFFER,
    GL_TRANSFORM_FEEDBACK_BUFFER,
    GL_UNIFORM_BUFFER,
    GL_WRITE_ONLY,
    GLubyte,
    GLuint,
    OpenGLSurfaceContext,
)
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
    _data_type_to_ctype,
)

if TYPE_CHECKING:
    from pyglet.customtypes import CTypesPointer, DataTypes
    from pyglet.graphics.shader import GraphicsAttribute


class GLBufferObject(AbstractBuffer):
    """Lightweight OpenGL buffer object.

    This class intentionally treats data as bytes for GPU transfer.
    """

    id: int | None
    usage: int
    target: int
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

        buffer_id = GLuint()
        self._context.glGenBuffers(1, buffer_id)
        self.id = buffer_id.value

        self.bind()
        data = (GLubyte * self.size)()
        self._context.glBufferData(self.target, self.size, data, self.usage)

    def _validate_byte_range(self, offset: int, length: int) -> None:
        assert offset >= 0 and length >= 0, "Offset and length must be non-negative."  # noqa: PT018
        assert offset + length <= self.size, (
            f"Byte range [{offset}, {offset + length}) exceeds buffer size {self.size}."
        )

    def bind(self) -> None:
        self._context.glBindBuffer(self.target, self.id)

    def unbind(self) -> None:
        self._context.glBindBuffer(self.target, 0)

    def get_bytes(self) -> bytes:
        self.bind()
        ptr = self._context.glMapBufferRange(self.target, 0, self.size, GL_MAP_READ_BIT)
        data = ctypes.string_at(ptr, self.size)
        self._context.glUnmapBuffer(self.target)
        return data

    def get_bytes_region(self, offset: int, length: int) -> bytes:
        self._validate_byte_range(offset, length)
        self.bind()
        ptr = self._context.glMapBufferRange(self.target, offset, length, GL_MAP_READ_BIT)
        data = ctypes.string_at(ptr, length)
        self._context.glUnmapBuffer(self.target)
        return data

    def set_bytes(self, data: bytes | bytearray | memoryview) -> None:
        raw = bytes(data)
        assert len(raw) == self.size, f"Expected {self.size} bytes for full upload, got {len(raw)}."
        self.bind()
        self._context.glBufferData(self.target, self.size, raw, self.usage)

    def set_bytes_region(self, offset: int, data: bytes | bytearray | memoryview) -> None:
        # BufferObject updates are whole-buffer by design. Patch the local
        # bytes and re-upload the full content.
        raw = bytes(data)
        self._validate_byte_range(offset, len(raw))
        whole = bytearray(self.get_bytes())
        whole[offset:offset + len(raw)] = raw
        self.set_bytes(whole)

    def invalidate(self) -> None:
        self.bind()
        self._context.glBufferData(self.target, self.size, None, self.usage)

    def delete(self) -> None:
        if self.id is None:
            return
        self._context.glDeleteBuffers(1, GLuint(self.id))
        self.id = None

    def __del__(self) -> None:
        if self.id is not None:
            try:
                self._context.delete_buffer(self.id)
                self.id = None
            except (AttributeError, ImportError):
                pass  # Interpreter is shutting down

    def resize(self, size: int) -> None:
        assert size >= 0, "Size must be non-negative."
        copy_size = min(size, self.size)
        temp = (ctypes.c_byte * max(size, 1))()
        self.bind()
        if copy_size > 0:
            data = self._context.glMapBufferRange(self.target, 0, copy_size, GL_MAP_READ_BIT)
            ctypes.memmove(temp, data, copy_size)
            self._context.glUnmapBuffer(self.target)

        self.size = size
        self._context.glBufferData(self.target, self.size, temp if size > 0 else None, self.usage)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, size={self.size})"


class GLMappedBufferObject(GLBufferObject, BaseMappedBufferObject):
    """OpenGL buffer with map/unmap support."""

    def __init__(self, context: OpenGLSurfaceContext, size: int, target: int = GL_ARRAY_BUFFER,
                 usage: int = GL_DYNAMIC_DRAW) -> None:
        super().__init__(context, size, target, usage)
        # GLES3 only supports mapping a range.
        self._supports_range_only = self._context.get_info().get_opengl_api() == "gles"

    @staticmethod
    def _to_map_range_bits(bits: int) -> int:
        if bits == GL_WRITE_ONLY:
            return GL_MAP_WRITE_BIT
        if bits == GL_READ_ONLY:
            return GL_MAP_READ_BIT
        if bits == GL_READ_WRITE:
            return GL_MAP_READ_BIT | GL_MAP_WRITE_BIT
        return bits

    def map(self, bits: int = GL_WRITE_ONLY) -> CTypesPointer[ctypes.c_byte]:
        self.bind()
        if self._supports_range_only:
            range_bits = self._to_map_range_bits(bits)
            ptr = self._context.glMapBufferRange(self.target, 0, self.size, range_bits)
        else:
            ptr = self._context.glMapBuffer(self.target, bits)
        return ctypes.cast(ptr, ctypes.POINTER(ctypes.c_byte * self.size)).contents

    def map_range(
        self,
        start: int,
        size: int,
        ptr_type: type[CTypesPointer],
        bits: int = GL_MAP_WRITE_BIT,
    ) -> CTypesPointer:
        self.bind()
        return ctypes.cast(self._context.glMapBufferRange(self.target, start, size, bits), ptr_type).contents

    def unmap(self) -> None:
        self._context.glUnmapBuffer(self.target)


class GLBackedBufferObject(BaseBackedBufferObject, GLBufferObject):
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
        GLBufferObject.__init__(self, context, size, target=target, usage=usage)

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
        assert 0 <= offset <= self.size and offset + len(data) <= self.size, (
            f"Byte range [{offset}, {offset + len(data)}) exceeds buffer size {self.size}."
        )
        self.store.set_bytes(offset, data)
        self._mark_dirty_bytes(offset, offset + len(data))

    def commit(self) -> None:
        """Commits all saved changes to the underlying buffer before drawing.

        Allows submitting multiple changes at once, rather than having to call glBufferSubData for every change.
        """
        if not self._dirty:
            return

        self.bind()
        size = self._dirty_max - self._dirty_min
        if size > 0:
            if size == self.size:
                self._context.glBufferData(self.target, self.size, self.store.get_bytes(), self.usage)
            else:
                self._context.glBufferSubData(
                    self.target,
                    self._dirty_min,
                    size,
                    self.store.get_bytes(self._dirty_min, size),
                )

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


class GLAttributeBufferObject(GLBackedBufferObject):
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


class GLIndexedBufferObject(GLBackedBufferObject):
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
        self._context.glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.id)


class GLPixelBufferObject(GLBufferObject, PixelBuffer):
    """OpenGL pixel transfer buffer object (PBO)."""

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


class GLPixelPackBufferObject(GLPixelBufferObject, PixelPackBuffer):
    """OpenGL pixel pack buffer object (readback path)."""

    def __init__(self, context: OpenGLSurfaceContext, size: int, usage: int = GL_DYNAMIC_DRAW) -> None:
        super().__init__(context, size, pack=True, usage=usage)


class GLPixelUnpackBufferObject(GLPixelBufferObject, PixelUnpackBuffer):
    """OpenGL pixel unpack buffer object (upload path)."""

    def __init__(self, context: OpenGLSurfaceContext, size: int, usage: int = GL_DYNAMIC_DRAW) -> None:
        super().__init__(context, size, pack=False, usage=usage)


class GLTransformFeedbackBufferObject(GLBufferObject, TransformFeedbackBuffer):
    """OpenGL transform feedback buffer object."""

    def __init__(self, context: OpenGLSurfaceContext, size: int, usage: int = GL_DYNAMIC_DRAW) -> None:
        super().__init__(context, size, target=GL_TRANSFORM_FEEDBACK_BUFFER, usage=usage)

    def bind_base(self, index: int) -> None:
        self._context.glBindBufferBase(GL_TRANSFORM_FEEDBACK_BUFFER, index, self.id)

    def bind_range(self, index: int, offset: int, size: int) -> None:
        self._validate_byte_range(offset, size)
        self._context.glBindBufferRange(GL_TRANSFORM_FEEDBACK_BUFFER, index, self.id, offset, size)


class GLTextureBufferObject(GLBufferObject, TextureBuffer):
    """OpenGL texture buffer object (TBO)."""

    def __init__(self, context: OpenGLSurfaceContext, size: int, usage: int = GL_DYNAMIC_DRAW) -> None:
        super().__init__(context, size, target=GL_TEXTURE_BUFFER, usage=usage)


class GLDrawIndirectBufferObject(GLBufferObject, DrawIndirectBuffer):
    """OpenGL draw indirect buffer object."""

    def __init__(self, context: OpenGLSurfaceContext, size: int, usage: int = GL_DYNAMIC_DRAW) -> None:
        super().__init__(context, size, target=GL_DRAW_INDIRECT_BUFFER, usage=usage)


class GLUniformBufferObject(UniformBufferObject):
    """OpenGL Uniform Buffer Object wrapper."""

    buffer: GLBufferObject
    __slots__ = ()

    def _create_buffer(self, context: OpenGLSurfaceContext, buffer_size: int) -> GLBufferObject:
        return GLBufferObject(context, buffer_size, target=GL_UNIFORM_BUFFER)


class PersistentBufferObject(BaseMappedBufferObject):
    """A persistently mapped OpenGL buffer.

    Available in OpenGL 4.4+ contexts. The buffer is mapped once on creation
    and remains mapped for the buffer lifetime.
    """

    id: int | None
    target: int
    usage: int
    flags: int
    stride: int
    element_count: int
    data_type: DataTypes
    _ctype: type[object]
    _element_size: int
    _mapped: object | None
    _mapped_ptr: int
    _storage_size: int
    _context: OpenGLSurfaceContext

    def __init__(
        self,
        context: OpenGLSurfaceContext,
        size: int,
        graphics_attr: GraphicsAttribute,
        target: int = GL_ARRAY_BUFFER,
        usage: int = GL_DYNAMIC_DRAW,
    ) -> None:
        super().__init__(size)

        self.target = target
        self.usage = usage
        self._context = context
        self.stride = graphics_attr.view.stride
        self.element_count = graphics_attr.attribute.fmt.components
        self.data_type = graphics_attr.attribute.fmt.data_type
        self._ctype = _data_type_to_ctype(self.data_type)
        self._element_size = _data_type_size(self.data_type)
        self.flags = GL_MAP_READ_BIT | GL_MAP_WRITE_BIT | GL_MAP_PERSISTENT_BIT | GL_MAP_COHERENT_BIT

        self.id = None
        self._mapped = None
        self._mapped_ptr = 0
        self._storage_size = 0
        self._recreate(size)

    def _validate_byte_range(self, offset: int, length: int) -> None:
        assert offset >= 0 and length >= 0, "Offset and length must be non-negative."
        assert offset + length <= self.size, (
            f"Byte range [{offset}, {offset + length}) exceeds buffer size {self.size}."
        )

    def _create_storage(self, size: int) -> tuple[int, object, int, int]:
        storage_size = max(size, 1)
        buffer_id = GLuint()
        self._context.glGenBuffers(1, buffer_id)
        new_id = buffer_id.value

        self._context.glBindBuffer(self.target, new_id)
        data = (GLubyte * storage_size)()
        self._context.glBufferStorage(self.target, storage_size, data, self.flags)

        ptr_type = ctypes.POINTER(ctypes.c_byte * storage_size)
        mapped = ctypes.cast(self._context.glMapBufferRange(self.target, 0, storage_size, self.flags), ptr_type).contents
        mapped_ptr = ctypes.addressof(mapped)
        return new_id, mapped, mapped_ptr, storage_size

    def _recreate(self, size: int, preserve: bytes = b"") -> None:
        new_id, new_mapped, new_ptr, storage_size = self._create_storage(size)
        if preserve:
            ctypes.memmove(new_ptr, preserve, len(preserve))

        old_id = self.id
        self.id = new_id
        self.size = size
        self._mapped = new_mapped
        self._mapped_ptr = new_ptr
        self._storage_size = storage_size
        self.get_region.cache_clear()

        if old_id is not None:
            self._context.glDeleteBuffers(1, GLuint(old_id))

    def _require_mapped_ptr(self) -> int:
        assert self._mapped_ptr != 0, "PersistentBufferObject is not mapped."
        return self._mapped_ptr

    @property
    def element_size(self) -> int:
        return self._element_size

    def bind(self) -> None:
        self._context.glBindBuffer(self.target, self.id)

    def unbind(self) -> None:
        self._context.glBindBuffer(self.target, 0)

    def get_bytes(self) -> bytes:
        return ctypes.string_at(self._require_mapped_ptr(), self.size)

    def get_bytes_region(self, offset: int, length: int) -> bytes:
        self._validate_byte_range(offset, length)
        return ctypes.string_at(self._require_mapped_ptr() + offset, length)

    def set_bytes(self, data: bytes | bytearray | memoryview) -> None:
        raw = bytes(data)
        assert len(raw) == self.size, f"Expected {self.size} bytes for full upload, got {len(raw)}."
        ctypes.memmove(self._require_mapped_ptr(), raw, self.size)

    def set_bytes_region(self, offset: int, data: bytes | bytearray | memoryview) -> None:
        raw = bytes(data)
        self._validate_byte_range(offset, len(raw))
        ctypes.memmove(self._require_mapped_ptr() + offset, raw, len(raw))

    def map(self, bits: int = GL_WRITE_ONLY) -> CTypesPointer[ctypes.c_byte]:  # noqa: ARG002
        ptr_type = ctypes.POINTER(ctypes.c_byte * self.size)
        return ctypes.cast(self._require_mapped_ptr(), ptr_type).contents

    def map_range(
        self,
        start: int,
        size: int,
        ptr_type: type[CTypesPointer],
        bits: int = GL_MAP_WRITE_BIT,  # noqa: ARG002
    ) -> CTypesPointer:
        self._validate_byte_range(start, size)
        return ctypes.cast(self._require_mapped_ptr() + start, ptr_type).contents

    def unmap(self) -> None:
        # Persistent storage stays mapped for the buffer lifetime.
        return

    def delete(self) -> None:
        if self.id is None:
            return
        self._context.glDeleteBuffers(1, GLuint(self.id))
        self.id = None
        self._mapped = None
        self._mapped_ptr = 0
        self._storage_size = 0
        self.get_region.cache_clear()

    def __del__(self) -> None:
        if self.id is not None:
            try:
                self._context.delete_buffer(self.id)
                self.id = None
            except (AttributeError, ImportError):
                pass  # Interpreter is shutting down

    @lru_cache(maxsize=None)
    def get_region(self, start: int, count: int):
        assert start >= 0 and count >= 0, "Start and count must be non-negative."  # noqa: PT018
        byte_start = self.stride * start
        byte_size = self.stride * count
        self._validate_byte_range(byte_start, byte_size)

        array_count = self.element_count * count
        ptr_type = ctypes.POINTER(self._ctype * array_count)
        return ctypes.cast(self._require_mapped_ptr() + byte_start, ptr_type).contents

    def set_region(self, start: int, count: int, data: Sequence[float | int]) -> None:
        assert start >= 0 and count >= 0, "Start and count must be non-negative."  # noqa: PT018
        array_start = self.element_count * start
        array_end = self.element_count * count + array_start
        typed_count = self.size // self._element_size
        assert array_end <= typed_count, (
            f"Region [{array_start}, {array_end}) exceeds typed element count {typed_count}."
        )

        ptr_type = ctypes.POINTER(self._ctype * typed_count)
        typed = ctypes.cast(self._require_mapped_ptr(), ptr_type).contents
        typed[array_start:array_end] = data

    def resize(self, size: int) -> None:
        assert size >= 0, "Size must be non-negative."
        if size == self.size:
            return
        copy_size = min(self.size, size)
        preserved = self.get_bytes_region(0, copy_size) if copy_size > 0 else b""
        self._recreate(size, preserved)

    def commit(self) -> None:
        # Not needed for persistent mapping.
        return

    def invalidate(self) -> None:
        # Not needed for persistent mapping.
        return

    def invalidate_region(self, start: int, count: int) -> None:  # noqa: ARG002
        # Not needed for persistent mapping.
        return
