from __future__ import annotations

import pyglet
from pyglet.image import ImageData
from tests.annotations import GraphicsAPIGroups, require_graphics_api


def _image(width: int, height: int, color: tuple[int, int, int, int]) -> ImageData:
    return ImageData(width, height, "RGBA", bytes(color) * (width * height))


def _finish_streamer(ctx, streamer, *jobs) -> None:
    streamer.submit()
    _finish_submitted_streamer(ctx, streamer, *jobs)


def _finish_submitted_streamer(ctx, streamer, *jobs) -> None:
    for _ in range(20):
        streamer.process()
        if all(job.completed for job in jobs):
            return
        ctx.glFinish()
    incomplete = [job for job in jobs if not job.completed]
    msg = f"TextureStreamer jobs did not complete: {incomplete!r}"
    raise AssertionError(msg)


@require_graphics_api(GraphicsAPIGroups.GL3)
def test_texture_streamer_upload_dispatches_completion(test_window):
    test_window.switch_to()
    ctx = test_window.context
    texture = pyglet.graphics.Texture.create(2, 2, blank_data=True, context=ctx)
    streamer = pyglet.graphics.TextureStreamer(ctx)
    upload_events = []
    job_events = []

    streamer.push_handlers(
        on_upload_complete=lambda job: upload_events.append(job),
        on_job_complete=lambda job: job_events.append(job),
    )

    try:
        expected = bytes((25, 50, 75, 255)) * 4
        job = streamer.queue_upload(texture, ImageData(2, 2, "RGBA", expected))
        assert job.texture is texture
        assert job.region is not None
        assert job.region.owner is texture
        assert job.regions == [job.region]

        _finish_streamer(ctx, streamer, job)

        fetched = bytes(texture.get_image_data().get_bytes("RGBA", 8))
        assert fetched == expected
        assert upload_events == [job]
        assert job_events == [job]
    finally:
        streamer.delete()
        texture.delete()


@require_graphics_api(GraphicsAPIGroups.GL3)
def test_texture_streamer_process_only_polls_submitted_jobs(test_window):
    test_window.switch_to()
    ctx = test_window.context
    texture = pyglet.graphics.Texture.create(1, 1, blank_data=True, context=ctx)
    streamer = pyglet.graphics.TextureStreamer(ctx)

    try:
        job = streamer.queue_upload(texture, ImageData(1, 1, "RGBA", bytes((90, 80, 70, 255))))
        streamer.process()
        ctx.glFinish()
        streamer.process()

        assert not job.submitted
        assert not job.completed

        _finish_streamer(ctx, streamer, job)
        fetched = bytes(texture.get_image_data().get_bytes("RGBA", 4))
        assert fetched == bytes((90, 80, 70, 255))
    finally:
        streamer.delete()
        texture.delete()


@require_graphics_api(GraphicsAPIGroups.GL3)
def test_texture_streamer_upload_binds_destination_texture(test_window):
    test_window.switch_to()
    ctx = test_window.context
    texture = pyglet.graphics.Texture.create(1, 1, blank_data=True, context=ctx)
    decoy = pyglet.graphics.Texture.create(1, 1, blank_data=True, context=ctx)
    streamer = pyglet.graphics.TextureStreamer(ctx)

    try:
        expected = bytes((12, 34, 56, 255))
        job = streamer.queue_upload(texture, ImageData(1, 1, "RGBA", expected))
        decoy.bind()

        _finish_streamer(ctx, streamer, job)

        fetched = bytes(texture.get_image_data().get_bytes("RGBA", 4))
        decoy_fetched = bytes(decoy.get_image_data().get_bytes("RGBA", 4))
        assert fetched == expected
        assert decoy_fetched == bytes((0, 0, 0, 0))
    finally:
        streamer.delete()
        texture.delete()
        decoy.delete()


@require_graphics_api(GraphicsAPIGroups.GL3)
def test_texture_streamer_upload_uses_pixel_unpack_buffer(test_window):
    from pyglet.graphics.api.gl.buffer import GLPixelUnpackBufferObject

    test_window.switch_to()
    ctx = test_window.context
    texture = pyglet.graphics.Texture.create(1, 1, blank_data=True, context=ctx)
    streamer = pyglet.graphics.TextureStreamer(ctx)

    try:
        job = streamer.queue_upload(texture, ImageData(1, 1, "RGBA", bytes((1, 2, 3, 255))))
        streamer.submit()

        assert len(job.pbos) == 1
        assert isinstance(job.pbos[0], GLPixelUnpackBufferObject)
        pbo = job.pbos[0]

        _finish_submitted_streamer(ctx, streamer, job)

        assert job.pbos == []
        assert streamer._upload_pbo_pool == [pbo]
        assert bytes(texture.get_image_data().get_bytes("RGBA", 4)) == bytes((1, 2, 3, 255))

        job = streamer.queue_upload(texture, ImageData(1, 1, "RGBA", bytes((4, 5, 6, 255))))
        streamer.submit()
        assert job.pbos == [pbo]
        _finish_submitted_streamer(ctx, streamer, job)
    finally:
        streamer.delete()
        texture.delete()


@require_graphics_api(GraphicsAPIGroups.GL3)
def test_texture_streamer_uploads_multiple_regions(test_window):
    test_window.switch_to()
    ctx = test_window.context
    texture = pyglet.graphics.Texture.create(4, 2, blank_data=True, context=ctx)
    streamer = pyglet.graphics.TextureStreamer(ctx, upload_pool_size=1)

    try:
        red = _image(2, 2, (200, 0, 0, 255))
        blue = _image(2, 2, (0, 0, 180, 255))
        job = streamer.queue_uploads(texture, [(red, 0, 0), (blue, 2, 0)])
        assert job.region is None
        assert len(job.regions) == 2
        assert [(region.x, region.y, region.width, region.height) for region in job.regions] == [
            (0, 0, 2, 2),
            (2, 0, 2, 2),
        ]

        _finish_streamer(ctx, streamer, job)

        fetched = bytes(texture.get_image_data().get_bytes("RGBA", 16))
        expected_row = bytes((200, 0, 0, 255)) * 2 + bytes((0, 0, 180, 255)) * 2
        assert fetched == expected_row * 2
    finally:
        streamer.delete()
        texture.delete()


@require_graphics_api(GraphicsAPIGroups.GL3)
def test_texture_streamer_download_returns_image_data(test_window):
    test_window.switch_to()
    ctx = test_window.context
    texture = pyglet.graphics.Texture.create(2, 2, blank_data=True, context=ctx)
    streamer = pyglet.graphics.TextureStreamer(ctx)
    download_events = []

    streamer.push_handlers(on_download_complete=lambda job: download_events.append(job))

    try:
        expected = bytes((10, 20, 30, 255)) * 4
        texture.upload(ImageData(2, 2, "RGBA", expected), 0, 0, 0)

        job = streamer.queue_download(texture)
        _finish_streamer(ctx, streamer, job)

        assert job.destination is not None
        assert bytes(job.destination.get_bytes("RGBA", 8)) == expected
        assert job.image_data is job.destination
        assert download_events == [job]
    finally:
        streamer.delete()
        texture.delete()


@require_graphics_api(GraphicsAPIGroups.GL3)
def test_texture_streamer_download_uses_pixel_pack_buffer_until_polled(test_window):
    from pyglet.graphics.api.gl.buffer import GLPixelPackBufferObject

    test_window.switch_to()
    ctx = test_window.context
    texture = pyglet.graphics.Texture.create(1, 1, blank_data=True, context=ctx)
    streamer = pyglet.graphics.TextureStreamer(ctx)

    try:
        expected = bytes((40, 50, 60, 255))
        texture.upload(ImageData(1, 1, "RGBA", expected), 0, 0, 0)
        job = streamer.queue_download(texture)
        streamer.submit()

        assert isinstance(job.pbo, GLPixelPackBufferObject)
        pbo = job.pbo
        assert job.destination is None

        _finish_submitted_streamer(ctx, streamer, job)

        assert job.pbo is None
        assert streamer._download_pbo_pool == [pbo]
        assert job.destination is not None
        assert bytes(job.destination.get_bytes("RGBA", 4)) == expected

        job = streamer.queue_download(texture)
        streamer.submit()
        assert job.pbo is pbo
        _finish_submitted_streamer(ctx, streamer, job)
    finally:
        streamer.delete()
        texture.delete()


@require_graphics_api(GraphicsAPIGroups.GL3)
def test_texture_streamer_download_region(test_window):
    test_window.switch_to()
    ctx = test_window.context
    texture = pyglet.graphics.Texture.create(2, 2, blank_data=True, context=ctx)
    streamer = pyglet.graphics.TextureStreamer(ctx)

    try:
        pixels = bytes((
            1, 2, 3, 255,
            4, 5, 6, 255,
            7, 8, 9, 255,
            10, 11, 12, 255,
        ))
        texture.upload(ImageData(2, 2, "RGBA", pixels), 0, 0, 0)

        job = streamer.queue_download(texture, x=1, y=1, width=1, height=1)
        _finish_streamer(ctx, streamer, job)

        assert job.destination is not None
        assert bytes(job.destination.get_bytes("RGBA", 4)) == bytes((10, 11, 12, 255))
    finally:
        streamer.delete()
        texture.delete()
