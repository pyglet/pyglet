from __future__ import annotations

import ctypes

import pyglet
import pytest
from pyglet.enums import GeometryMode
from pyglet.graphics.api.gl import GL_ELEMENT_ARRAY_BUFFER_BINDING, GLint
from pyglet.graphics.api.gl2.buffer import GL2BufferObject, GL2IndexedBufferObject
from pyglet.graphics.buffer import CTypeDataStore

from tests.annotations import GraphicsAPIGroups, require_graphics_api


pytestmark = require_graphics_api(GraphicsAPIGroups.GL2)


def test_ctype_data_store_assertions():
    with pytest.raises(AssertionError):
        CTypeDataStore(size=3, data_type="I", stride=4, element_count=1)

    store = CTypeDataStore(size=8, data_type="I", stride=4, element_count=1)
    with pytest.raises(AssertionError):
        store.set_bytes(7, b"\x00\x01")


def test_buffer_object_create_resize_and_delete(test_window):
    test_window.switch_to()
    buffer = GL2BufferObject(test_window.context, 16)

    assert buffer.size == 16
    with pytest.raises(AssertionError):
        buffer.get_bytes()

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


def test_buffer_object_assertions(test_window):
    test_window.switch_to()
    buffer = GL2BufferObject(test_window.context, 8)

    with pytest.raises(AssertionError):
        buffer.set_bytes(b"\x00")
    with pytest.raises(AssertionError):
        buffer.get_bytes()
    with pytest.raises(AssertionError):
        buffer.get_bytes_region(-1, 1)
    with pytest.raises(AssertionError):
        buffer.set_bytes_region(7, b"\x00\x01")

    buffer.delete()


def test_backed_index_buffer_commit_resize_and_delete(test_window):
    test_window.switch_to()
    buffer = GL2IndexedBufferObject(test_window.context, size=8, data_type="I", stride=4, count=1)

    buffer.set_region(0, 2, [5, 9])
    buffer.commit()

    cpu_data = buffer.get_bytes()
    gpu_data = GL2BufferObject.get_bytes(buffer)
    assert gpu_data == cpu_data

    values = (ctypes.c_uint32 * 2).from_buffer_copy(gpu_data)
    assert tuple(values) == (5, 9)

    buffer.resize(16)
    buffer.set_region(2, 2, [12, 13])
    buffer.commit()

    cpu_data_resized = buffer.get_bytes()
    gpu_data_resized = GL2BufferObject.get_bytes(buffer)
    assert gpu_data_resized == cpu_data_resized

    values_resized = (ctypes.c_uint32 * 4).from_buffer_copy(gpu_data_resized)
    assert tuple(values_resized[:2]) == (5, 9)
    assert tuple(values_resized[2:4]) == (12, 13)

    buffer.delete()
    assert buffer.id is None
    buffer.delete()


def test_backed_index_buffer_first_partial_commit_allocates_and_uploads(test_window):
    test_window.switch_to()
    buffer = GL2IndexedBufferObject(test_window.context, size=16, data_type="I", stride=4, count=1)

    buffer.set_data_region([7], start=0, length=4)
    buffer.commit()

    gpu_data = GL2BufferObject.get_bytes(buffer)
    typed_gpu = (ctypes.c_uint32 * 4).from_buffer_copy(gpu_data)
    assert tuple(typed_gpu) == (7, 0, 0, 0)

    buffer.delete()


def test_backed_index_buffer_set_data_with_ctypes_array(test_window):
    test_window.switch_to()
    buffer = GL2IndexedBufferObject(test_window.context, size=16, data_type="I", stride=4, count=1)

    initial_values = (ctypes.c_uint32 * 4)(11, 22, 33, 44)
    buffer.set_data(initial_values)
    buffer.commit()

    gpu_data = GL2BufferObject.get_bytes(buffer)
    typed_gpu = (ctypes.c_uint32 * 4).from_buffer_copy(gpu_data)
    assert tuple(typed_gpu) == (11, 22, 33, 44)

    buffer.delete()


def test_backed_index_buffer_set_data_with_python_list(test_window):
    test_window.switch_to()
    buffer = GL2IndexedBufferObject(test_window.context, size=16, data_type="I", stride=4, count=1)

    buffer.set_data([11, 22, 33, 44])
    buffer.commit()

    gpu_data = GL2BufferObject.get_bytes(buffer)
    typed_gpu = (ctypes.c_uint32 * 4).from_buffer_copy(gpu_data)
    assert tuple(typed_gpu) == (11, 22, 33, 44)

    buffer.delete()


def test_backed_index_buffer_set_data_region_with_python_list(test_window):
    test_window.switch_to()
    buffer = GL2IndexedBufferObject(test_window.context, size=16, data_type="I", stride=4, count=1)

    initial_values = (ctypes.c_uint32 * 4)(11, 22, 33, 44)
    buffer.set_data(initial_values)
    buffer.commit()

    buffer.set_data_region([99, 100], start=8, length=8)
    buffer.commit()

    gpu_data = GL2BufferObject.get_bytes(buffer)
    typed_gpu = (ctypes.c_uint32 * 4).from_buffer_copy(gpu_data)
    assert tuple(typed_gpu) == (11, 22, 99, 100)

    buffer.delete()


def test_backed_index_buffer_set_data_ptr_with_ctypes_pointer(test_window):
    test_window.switch_to()
    buffer = GL2IndexedBufferObject(test_window.context, size=16, data_type="I", stride=4, count=1)

    initial_values = (ctypes.c_uint32 * 4)(11, 22, 33, 44)
    buffer.set_data(initial_values)
    buffer.commit()

    ptr_values = (ctypes.c_uint32 * 2)(7, 8)
    ptr = ctypes.cast(ptr_values, ctypes.POINTER(ctypes.c_ubyte))
    buffer.set_data_ptr(0, 8, ptr)
    buffer.commit()

    gpu_data = GL2BufferObject.get_bytes(buffer)
    typed_gpu = (ctypes.c_uint32 * 4).from_buffer_copy(gpu_data)
    assert tuple(typed_gpu) == (7, 8, 33, 44)

    buffer.delete()


def _create_quad_vertices(x: float, y: float, z: float, width: float, height: float) -> tuple[float, ...]:
    return (
        x, y, z,
        x + width, y, z,
        x + width, y + height, z,
        x, y + height, z,
    )


def test_gl2_indexed_batch_draw_keeps_element_buffer_bound(test_window) -> None:
    """Ensure GL2 indexed draws bind EBO every draw, even when index buffer is not dirty."""
    test_window.switch_to()
    ctx = test_window.context
    program = pyglet.graphics.api.get_default_shader()
    batch = pyglet.graphics.Batch()

    vertices = _create_quad_vertices(0, 0, 0, 50, 50)
    colors = (1, 0.5, 0.2, 1) * 4
    indices = [0, 1, 2, 0, 2, 3]

    program.vertex_list_indexed(
        4,
        GeometryMode.TRIANGLES,
        indices,
        batch=batch,
        group=None,
        position=vertices,
        colors=colors,
    )

    original_draw_elements = ctx.glDrawElements
    original_multi_draw_elements = ctx.glMultiDrawElements
    observed_bindings: list[int] = []

    def checked_draw_elements(mode, count, gl_type, offset):  # noqa: ANN001
        binding = GLint()
        ctx.glGetIntegerv(GL_ELEMENT_ARRAY_BUFFER_BINDING, binding)
        observed_bindings.append(binding.value)
        assert binding.value != 0, "GL_ELEMENT_ARRAY_BUFFER was not bound during glDrawElements."
        return original_draw_elements(mode, count, gl_type, offset)

    def checked_multi_draw_elements(mode, counts, gl_type, offsets, primcount):  # noqa: ANN001
        binding = GLint()
        ctx.glGetIntegerv(GL_ELEMENT_ARRAY_BUFFER_BINDING, binding)
        observed_bindings.append(binding.value)
        assert binding.value != 0, "GL_ELEMENT_ARRAY_BUFFER was not bound during glMultiDrawElements."
        return original_multi_draw_elements(mode, counts, gl_type, offsets, primcount)

    ctx.glDrawElements = checked_draw_elements
    ctx.glMultiDrawElements = checked_multi_draw_elements
    try:
        # First draw commits new buffers. Second draw is the regression case: no dirty index data.
        batch.draw()
        batch.draw()
    finally:
        ctx.glDrawElements = original_draw_elements
        ctx.glMultiDrawElements = original_multi_draw_elements

    assert len(observed_bindings) >= 2
