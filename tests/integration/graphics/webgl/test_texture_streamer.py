"""Texture streamer packing and rectangle readback on a real WebGL2 context."""
from __future__ import annotations

import asyncio

import pyglet
import pytest
from pyglet.enums import ComponentFormat


@pytest.fixture
def finish_texture_streamer():
    """Poll across browser event-loop turns, rather than hiding waits with finish()."""
    from pyodide.ffi import can_run_sync, run_sync

    if not can_run_sync():
        pytest.skip("Synchronous browser tests need JSPI to await GPU fences.")

    async def finish(streamer, job):
        for _ in range(200):
            streamer.poll()
            if job.completed:
                return
            await asyncio.sleep(0.005)
        pytest.fail("Texture transfer did not complete after yielding to the browser.")

    return lambda streamer, job: run_sync(finish(streamer, job))


def _image(color: tuple[int, int, int, int]) -> pyglet.image.ImageData:
    return pyglet.image.ImageData(1, 1, "RGBA", bytes(color))


@pytest.mark.parametrize("persistent", [False, True])
@pytest.mark.parametrize("block_size,expected_blocks", [(1, 5), (12, 3), (1024, 1)])
@pytest.mark.parametrize("texture_format", [ComponentFormat.RGB, ComponentFormat.RGBA])
def test_packed_uploads_and_pool_reuse(webgl_window, finish_texture_streamer, persistent, block_size,
                                     expected_blocks, texture_format):
    gl = webgl_window.context.gl
    texture = pyglet.graphics.Texture.create(5, 1, internal_format=texture_format,
                                             blank_data=True, context=webgl_window.context)
    streamer = pyglet.graphics.TextureStreamer(webgl_window, persistent_uploads=persistent,
                                                upload_buffer_size=block_size)
    try:
        first_handles = None
        for generation in range(2):
            colors = [(index * 10, generation * 40, 30, 255) for index in range(5)]
            # Exercise both RGB storage and CPU expansion to opaque RGBA.
            # Either payload size requires padding between PBO byte offsets.
            uploads = [(pyglet.image.ImageData(1, 1, "RGB", bytes(color[:3])), index, 0)
                       for index, color in enumerate(colors)]
            job = streamer.queue_uploads(texture, uploads)
            streamer.submit()
            assert len(job.pbos) == expected_blocks
            handles = [pbo.handle for pbo in job.pbos]
            if first_handles is None:
                first_handles = handles
            else:
                assert all(any(gl.isBuffer(handle) and handle == previous for previous in first_handles)
                           for handle in handles)
            finish_texture_streamer(streamer, job)
            assert bytes(texture.fetch().get_bytes("RGBA", 20)) == b"".join(map(bytes, colors))
            assert not gl.getParameter(gl.PIXEL_UNPACK_BUFFER_BINDING)
    finally:
        streamer.delete()
        texture.delete()


def test_partial_batch_limits_and_completion(webgl_window, finish_texture_streamer, monkeypatch):
    context = webgl_window.context
    texture = pyglet.graphics.Texture.create(5, 1, context=context)
    streamer = pyglet.graphics.TextureStreamer(webgl_window)
    fences, events = [], []
    create_fence = context.create_frame_fence

    def record_fence():
        fence = create_fence()
        fences.append(fence)
        return fence

    monkeypatch.setattr(context, "create_frame_fence", record_fence)
    streamer.push_handlers(on_upload_complete=events.append)
    try:
        colors = [(index * 10, 20, 30, 255) for index in range(5)]
        job = streamer.queue_uploads(texture, [(_image(color), index, 0) for index, color in enumerate(colors)])
        streamer.submit(max_uploads=2)
        assert job._next_upload == 2
        assert len(job.pbos) == 1
        context.gl.finish()
        streamer.poll()
        assert not job.completed and not events and not fences
        streamer.process(max_bytes=8)
        assert job._next_upload == 4
        assert not job.submitted and not fences
        streamer.process(max_uploads=2)
        assert job.submitted and len(fences) == 1
        fence = job.fence
        assert fence is not None and context.gl.isSync(fence)
        streamer.poll()
        assert not job.completed and not events
        finish_texture_streamer(streamer, job)
        assert not context.gl.isSync(fence)
        streamer.poll()
        assert events == [job]
        assert bytes(texture.fetch().get_bytes("RGBA", 20)) == b"".join(map(bytes, colors))
    finally:
        streamer.delete()
        texture.delete()


@pytest.mark.parametrize("texture_class", ["Texture", "Texture3D", "TextureArray"])
def test_packed_mip_regions_and_layers(webgl_window, finish_texture_streamer, texture_class):
    cls = getattr(pyglet.graphics, texture_class)
    if texture_class == "Texture":
        texture = cls.create(8, 4, context=webgl_window.context)
        z = 0
    else:
        texture = cls.create_for_images([pyglet.image.ImageData(8, 4, "RGBA", bytes(128)) for _ in range(4)],
                                        context=webgl_window.context)
        z = 1
    texture.generate_mipmaps()
    region = texture.get_region(4, 0, 4, 4) if z == 0 else texture
    streamer = pyglet.graphics.TextureStreamer(webgl_window)
    try:
        colors = [(10, 20, 30, 255), (40, 50, 60, 255)]
        job = streamer.queue_uploads(region, [(_image(color), index, 0, z, 1)
                                               for index, color in enumerate(colors)])
        streamer.submit()
        assert len(job.pbos) == 1
        finish_texture_streamer(streamer, job)
        download = streamer.queue_download(region, width=2, height=1, z=z, level=1)
        streamer.submit()
        assert download.pbo.size == 8
        finish_texture_streamer(streamer, download)
        assert bytes(download.image_data.get_bytes("RGBA", 8)) == b"".join(map(bytes, colors))
    finally:
        streamer.delete()
        texture.delete()


def test_rectangle_readback_restores_pack_state(webgl_window, finish_texture_streamer):
    gl = webgl_window.context.gl
    texture = pyglet.graphics.Texture.create_from_image(_image((10, 20, 30, 255)), context=webgl_window.context)
    streamer = pyglet.graphics.TextureStreamer(webgl_window)
    fields = (gl.PACK_ALIGNMENT, gl.PACK_ROW_LENGTH, gl.PACK_SKIP_PIXELS, gl.PACK_SKIP_ROWS)
    previous = [gl.getParameter(field) for field in fields]
    values = (8, 9, 2, 1)
    try:
        for field, value in zip(fields, values):
            gl.pixelStorei(field, value)
        job = streamer.queue_download(texture, width=1, height=1)
        streamer.submit()
        assert job.pbo.size == 4
        assert gl.isSync(job.fence)
        streamer.poll()
        assert not job.completed and job.destination is None
        finish_texture_streamer(streamer, job)
        assert bytes(job.image_data.get_bytes("RGBA", 4)) == bytes((10, 20, 30, 255))
        assert [gl.getParameter(field) for field in fields] == list(values)
        assert not gl.getParameter(gl.PIXEL_PACK_BUFFER_BINDING)
    finally:
        for field, value in zip(fields, previous):
            gl.pixelStorei(field, value)
        streamer.delete()
        texture.delete()


@pytest.mark.parametrize("layout", ["region", "padded", "negative_pitch", "bgra"])
def test_texture_streamer_upload_layouts(webgl_window, finish_texture_streamer, layout):
    expected = bytes((1, 2, 3, 255, 4, 5, 6, 255, 7, 8, 9, 255, 10, 11, 12, 255))
    if layout == "region":
        source = pyglet.image.ImageData(3, 3, "RGBA", bytes(range(36))).get_region(1, 1, 2, 2)
        expected = bytes(range(16, 24)) + bytes(range(28, 36))
    elif layout == "padded":
        source = pyglet.image.ImageData(2, 2, "RGBA", expected[:8] + b"pad!" + expected[8:] + b"pad!", pitch=12)
    elif layout == "negative_pitch":
        source = pyglet.image.ImageData(2, 2, "RGBA", expected[8:] + expected[:8], pitch=-8)
    else:
        source = pyglet.image.ImageData(2, 2, "BGRA", b"".join(expected[i:i + 4][2::-1] + expected[i + 3:i + 4]
                                                               for i in range(0, len(expected), 4)))
    texture = pyglet.graphics.Texture.create(2, 2, context=webgl_window.context)
    streamer = pyglet.graphics.TextureStreamer(webgl_window)
    try:
        upload = streamer.queue_upload(texture, source)
        streamer.submit()
        finish_texture_streamer(streamer, upload)
        assert upload.completed
        assert bytes(texture.fetch().get_bytes("RGBA", 8)) == expected
        download = streamer.queue_download(texture)
        streamer.submit()
        finish_texture_streamer(streamer, download)
        assert download.completed
        assert bytes(download.image_data.get_bytes("RGBA", 8)) == expected
        assert not webgl_window.context.gl.getParameter(webgl_window.context.gl.PIXEL_PACK_BUFFER_BINDING)
    finally:
        streamer.delete()
        texture.delete()


@pytest.mark.parametrize("texture_class", ["Texture", "Texture3D", "TextureArray"])
def test_texture_streamer_mipmap_and_layer_bounds(webgl_window, finish_texture_streamer, texture_class):
    from pyglet.image.base import ImageException

    cls = getattr(pyglet.graphics, texture_class)
    if texture_class == "Texture":
        texture = cls.create(4, 4, context=webgl_window.context)
        z = 0
    else:
        images = [pyglet.image.ImageData(4, 4, "RGBA", bytes(64)) for _ in range(4)]
        texture = cls.create_for_images(images, context=webgl_window.context)
        z = 1
    texture.generate_mipmaps()
    streamer = pyglet.graphics.TextureStreamer(webgl_window)
    try:
        with pytest.raises(ImageException):
            streamer.queue_download(texture, width=3, level=1)
        with pytest.raises(ImageException):
            streamer.queue_upload(texture, pyglet.image.ImageData(3, 3, "RGBA", bytes(36)), level=1)
        expected = bytes((12, 34, 56, 255)) * 4
        upload = streamer.queue_upload(texture, pyglet.image.ImageData(2, 2, "RGBA", expected), z=z, level=1)
        streamer.submit()
        finish_texture_streamer(streamer, upload)
        assert upload.completed
        download = streamer.queue_download(texture, z=z, level=1)
        streamer.submit()
        finish_texture_streamer(streamer, download)
        assert (download.image_data.width, download.image_data.height) == (2, 2)
        assert bytes(download.image_data.get_bytes("RGBA", 8)) == expected
    finally:
        streamer.delete()
        texture.delete()
