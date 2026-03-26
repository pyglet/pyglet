import ctypes

import pyglet
import pytest
from pyglet.graphics.buffer import CTypeDataStore
from pyglet.graphics.shader import Attribute
from tests.annotations import GraphicsAPI, require_graphics_api

if pyglet.options.backend in GraphicsAPI.GL3:
    from pyglet.graphics.api.gl.buffer import GLBufferObject, GLIndexedBufferObject, GLMappedBufferObject
elif pyglet.options.backend in GraphicsAPI.GL2:
    from pyglet.graphics.api.gl2.buffer import (
        GL2BufferObject as GLBufferObject,
        GL2IndexedBufferObject as GLIndexedBufferObject,
        GL2MappedBufferObject as GLMappedBufferObject
    )
else:
    pytest.skip(f"Unsupported graphics backend for buffer tests: {pyglet.options.backend}", allow_module_level=True)




def test_ctype_data_store_assertions():
    with pytest.raises(AssertionError):
        CTypeDataStore(size=3, data_type="I", stride=4, element_count=1)

    store = CTypeDataStore(size=8, data_type="I", stride=4, element_count=1)
    with pytest.raises(AssertionError):
        store.set_bytes(7, b"\x00\x01")


def test_buffer_object_create_resize_and_delete(gl3_context):
    gl3_context.switch_to()
    ctx = gl3_context.context

    buffer = GLBufferObject(ctx, 16)
    assert buffer.size == 16
    assert len(buffer.get_bytes()) == 16

    payload = bytes(range(16))
    buffer.set_bytes(payload)
    assert buffer.get_bytes() == payload

    buffer.set_bytes_region(4, b"\xaa\xbb\xcc\xdd")
    expected = bytearray(payload)
    expected[4:8] = b"\xaa\xbb\xcc\xdd"
    assert buffer.get_bytes() == bytes(expected)

    buffer.resize(24)
    resized = buffer.get_bytes()
    assert buffer.size == 24
    assert resized[:16] == bytes(expected)

    buffer.resize(8)
    assert buffer.get_bytes() == bytes(expected[:8])

    buffer.delete()
    assert buffer.id is None
    buffer.delete()


def test_buffer_object_assertions(gl3_context):
    gl3_context.switch_to()
    ctx = gl3_context.context
    buffer = GLBufferObject(ctx, 8)

    with pytest.raises(AssertionError):
        buffer.set_bytes(b"\x00")
    with pytest.raises(AssertionError):
        buffer.get_bytes_region(-1, 1)
    with pytest.raises(AssertionError):
        buffer.set_bytes_region(7, b"\x00\x01")

    buffer.delete()

@require_graphics_api(GraphicsAPI.GL3)
def test_mapped_buffer_region_updates(gl3_context):
    # Mapped buffers aren't supported by GLES2.
    gl3_context.switch_to()
    ctx = gl3_context.context

    buffer = GLMappedBufferObject(ctx, 16)

    whole = buffer.map()
    whole[:] = b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f"
    buffer.unmap()
    assert buffer.get_bytes() == bytes(range(16))

    ptr_type = ctypes.POINTER(ctypes.c_ubyte * 4)
    region = buffer.map_range(6, 4, ptr_type)
    region[:] = (ctypes.c_ubyte * 4)(90, 91, 92, 93)
    buffer.unmap()

    expected = bytearray(range(16))
    expected[6:10] = bytes((90, 91, 92, 93))
    assert buffer.get_bytes() == bytes(expected)

    buffer.delete()
    assert buffer.id is None


def test_backed_index_buffer_commit_resize_and_delete(gl3_context):
    gl3_context.switch_to()
    ctx = gl3_context.context

    buffer = GLIndexedBufferObject(ctx, size=8, data_type="I", stride=4, count=1)

    buffer.set_region(0, 2, [5, 9])
    buffer.commit()

    cpu_data = buffer.get_bytes()
    gpu_data = GLBufferObject.get_bytes(buffer)
    assert gpu_data == cpu_data

    values = (ctypes.c_uint32 * 2).from_buffer_copy(gpu_data)
    assert tuple(values) == (5, 9)

    buffer.resize(16)
    buffer.set_region(2, 2, [12, 13])
    buffer.commit()

    cpu_data_resized = buffer.get_bytes()
    gpu_data_resized = GLBufferObject.get_bytes(buffer)
    assert gpu_data_resized == cpu_data_resized

    values_resized = (ctypes.c_uint32 * 4).from_buffer_copy(gpu_data_resized)
    assert tuple(values_resized[:2]) == (5, 9)
    assert tuple(values_resized[2:4]) == (12, 13)

    buffer.delete()
    assert buffer.id is None
    buffer.delete()


def test_backed_index_buffer_set_data_with_ctypes_array(gl3_context):
    gl3_context.switch_to()
    ctx = gl3_context.context

    buffer = GLIndexedBufferObject(ctx, size=16, data_type="I", stride=4, count=1)

    initial_values = (ctypes.c_uint32 * 4)(11, 22, 33, 44)
    buffer.set_data(initial_values)
    buffer.commit()

    gpu_data = GLBufferObject.get_bytes(buffer)
    typed_gpu = (ctypes.c_uint32 * 4).from_buffer_copy(gpu_data)
    assert tuple(typed_gpu) == (11, 22, 33, 44)

    buffer.delete()


def test_backed_index_buffer_set_data_with_python_list(gl3_context):
    gl3_context.switch_to()
    ctx = gl3_context.context

    buffer = GLIndexedBufferObject(ctx, size=16, data_type="I", stride=4, count=1)

    buffer.set_data([11, 22, 33, 44])
    buffer.commit()

    gpu_data = GLBufferObject.get_bytes(buffer)
    typed_gpu = (ctypes.c_uint32 * 4).from_buffer_copy(gpu_data)
    assert tuple(typed_gpu) == (11, 22, 33, 44)

    buffer.delete()


def test_backed_index_buffer_set_data_region_with_python_list(gl3_context):
    gl3_context.switch_to()
    ctx = gl3_context.context

    buffer = GLIndexedBufferObject(ctx, size=16, data_type="I", stride=4, count=1)

    initial_values = (ctypes.c_uint32 * 4)(11, 22, 33, 44)
    buffer.set_data(initial_values)
    buffer.commit()

    buffer.set_data_region([99, 100], start=8, length=8)
    buffer.commit()

    gpu_data = GLBufferObject.get_bytes(buffer)
    typed_gpu = (ctypes.c_uint32 * 4).from_buffer_copy(gpu_data)
    assert tuple(typed_gpu) == (11, 22, 99, 100)

    buffer.delete()


def test_backed_index_buffer_set_data_ptr_with_ctypes_pointer(gl3_context):
    gl3_context.switch_to()
    ctx = gl3_context.context

    buffer = GLIndexedBufferObject(ctx, size=16, data_type="I", stride=4, count=1)

    initial_values = (ctypes.c_uint32 * 4)(11, 22, 33, 44)
    buffer.set_data(initial_values)
    buffer.commit()

    ptr_values = (ctypes.c_uint32 * 2)(7, 8)
    ptr = ctypes.cast(ptr_values, ctypes.POINTER(ctypes.c_ubyte))
    buffer.set_data_ptr(0, 8, ptr)
    buffer.commit()

    gpu_data = GLBufferObject.get_bytes(buffer)
    typed_gpu = (ctypes.c_uint32 * 4).from_buffer_copy(gpu_data)
    assert tuple(typed_gpu) == (7, 8, 33, 44)

    buffer.delete()

@require_graphics_api(GraphicsAPI.DESKTOP_GL)
def test_gl_vertex_stream_persistent_resize_rebinds_vao(gl3_context):
    from pyglet.graphics.api.gl import GL_VERTEX_ATTRIB_ARRAY_BUFFER_BINDING, GLint
    from pyglet.graphics.api.gl.buffer import PersistentBufferObject
    from pyglet.graphics.api.gl.vertexdomain import GLVertexArrayBinding, GLVertexStream

    gl3_context.switch_to()
    ctx = gl3_context.context
    info = ctx.get_info()

    if info.get_opengl_api() != "gl":
        pytest.skip("Persistent buffers are only integrated for desktop OpenGL contexts.")
    if not (info.have_version(4, 4) or info.have_extension("GL_ARB_buffer_storage")):
        pytest.skip("Persistent buffers require OpenGL 4.4 or GL_ARB_buffer_storage.")

    previous_option = pyglet.options.opengl_persistent_buffers
    stream = None
    vao_binding = None
    pyglet.options.opengl_persistent_buffers = True
    try:
        stream = GLVertexStream(ctx, initial_size=2, attrs=[Attribute("position", 0, 2, "f")])
        buffer = stream.buffers[0]
        assert isinstance(buffer, PersistentBufferObject)

        vao_binding = GLVertexArrayBinding(ctx, [stream])

        buffer.set_region(0, 2, [1.0, 2.0, 3.0, 4.0])
        old_id = buffer.id
        stream.resize(4)

        assert buffer.id != old_id
        assert list(buffer.get_region(0, 2)) == [1.0, 2.0, 3.0, 4.0]

        vao_binding.bind()
        bound_buffer = GLint()
        ctx.glGetVertexAttribiv(0, GL_VERTEX_ATTRIB_ARRAY_BUFFER_BINDING, bound_buffer)
        vao_binding.unbind()
        assert bound_buffer.value == buffer.id
    finally:
        pyglet.options.opengl_persistent_buffers = previous_option
        if vao_binding is not None:
            vao_binding.vao.delete()
        if stream is not None:
            for buf in stream.buffers:
                buf.delete()
