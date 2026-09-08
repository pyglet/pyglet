from __future__ import annotations

from pyglet.graphics.api.webgl.buffer import WebGLBufferObject, WebGLIndexedBufferObject


def test_ctypes_backed_buffer_uploads_direct_memoryview(webgl_window):
    buffer = WebGLIndexedBufferObject(webgl_window.context, size=8, data_type="I", stride=4, count=1)
    try:
        buffer.set_region(0, 2, (5, 9))
        buffer.commit()
        assert WebGLBufferObject.get_bytes(buffer) == buffer.get_bytes()

        buffer.set_region(1, 1, (12,))
        buffer.commit()
        assert WebGLBufferObject.get_bytes(buffer) == buffer.get_bytes()
    finally:
        buffer.delete()
