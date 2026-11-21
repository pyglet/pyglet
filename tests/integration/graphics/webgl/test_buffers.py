from __future__ import annotations

from unittest.mock import Mock

import pyglet

from pyglet.graphics.api.webgl.buffer import WebGLBufferObject, WebGLIndexedBufferObject


def test_buffer_finalizer_deletes_handle(webgl_window) -> None:
    buffer = WebGLBufferObject(webgl_window.context, size=8)
    handle = buffer.handle
    buffer._ensure_allocated()
    assert webgl_window.context.gl.isBuffer(handle)

    buffer.__del__()

    assert buffer.handle is None
    assert not webgl_window.context.gl.isBuffer(handle)


def test_buffer_region_write_allocates_once_and_updates_in_place(webgl_window, monkeypatch) -> None:
    buffer = WebGLBufferObject(webgl_window.context, size=8)
    try:
        gl = Mock(wraps=webgl_window.context.gl)
        with monkeypatch.context() as patch:
            patch.setattr(buffer, "_gl", gl)
            buffer.set_bytes_region(2, b"abcd")
            buffer.set_bytes_region(3, memoryview(b"XY"))

            gl.bufferData.assert_called_once_with(buffer.target, buffer.size, buffer.usage)
            assert [call.args[:2] for call in gl.bufferSubData.call_args_list] == [
                (buffer.target, 2), (buffer.target, 3),
            ]
            gl.getBufferSubData.assert_not_called()
        assert buffer.get_bytes_region(2, 4) == b"aXYd"
    finally:
        buffer.delete()


def test_ctypes_backed_buffer_uploads_direct_memoryview(webgl_window):
    buffer = WebGLIndexedBufferObject(webgl_window.context, size=8, data_type="I", stride=4, count=1)
    try:
        buffer.set_region(0, 2, (5, 9))
        buffer.commit()
        assert WebGLBufferObject.get_bytes(buffer) == buffer.get_bytes()

        buffer.set_region(1, 1, (12,))
        buffer.commit()
        assert WebGLBufferObject.get_bytes(buffer) == buffer.get_bytes()

        buffer.resize(16)
        buffer.set_region(2, 2, (20, 21))
        buffer.set_region(0, 1, (3,))
        buffer.commit()
        assert WebGLBufferObject.get_bytes(buffer) == buffer.get_bytes()
        buffer.set_region(1, 1, (7,))
        buffer.commit()
        assert WebGLBufferObject.get_bytes(buffer) == buffer.get_bytes()
    finally:
        buffer.delete()


def test_uniform_buffer_custom_alignment_preserves_driver_alignment(webgl_window) -> None:
    ctx = webgl_window.context
    driver_alignment = ctx.info.MAX_UNIFORM_BUFFER_OFFSET_ALIGNMENT
    requested_alignment = driver_alignment + 1
    program = pyglet.graphics.get_default_shader()
    block = program.uniform_blocks["WindowBlock"]
    ubo = block.create_ubo(alignment=requested_alignment, copies_per_resource=1, strict=True)
    try:
        binding = ubo.upload_to_available_binding(ubo.get_data_structure())
        assert binding.offset % driver_alignment == 0
        assert binding.offset % requested_alignment == 0
        ubo.bind_slice(binding)
    finally:
        ubo.delete()
