from __future__ import annotations

import pyglet
import pytest
from pyglet.image import ImageData
from tests.annotations import GraphicsAPIGroups, require_graphics_api


pytestmark = require_graphics_api(GraphicsAPIGroups.GL3)


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


@pytest.mark.parametrize("layout", ["region", "padded", "negative_pitch", "argb"])
def test_texture_streamer_upload_image_layouts(test_window, layout):
    test_window.switch_to()
    ctx = test_window.context
    expected = bytes((1, 2, 3, 255, 4, 5, 6, 255, 7, 8, 9, 255, 10, 11, 12, 255))
    if layout == "region":
        parent = ImageData(3, 3, "RGBA", bytes(range(36)))
        source = parent.get_region(1, 1, 2, 2)
        expected = bytes(range(16, 24)) + bytes(range(28, 36))
    elif layout == "padded":
        source = ImageData(2, 2, "RGBA", expected[:8] + b"pad!" + expected[8:] + b"pad!", pitch=12)
    elif layout == "negative_pitch":
        source = ImageData(2, 2, "RGBA", expected[8:] + expected[:8], pitch=-8)
    else:
        source = ImageData(2, 2, "ARGB", b"".join(expected[i + 3:i + 4] + expected[i:i + 3]
                                                 for i in range(0, len(expected), 4)))
    texture = pyglet.graphics.Texture.create(2, 2, context=ctx)
    streamer = pyglet.graphics.TextureStreamer(ctx)
    try:
        job = streamer.queue_upload(texture, source)
        streamer.submit()
        assert job.pbos[0].size == len(expected)
        _finish_submitted_streamer(ctx, streamer, job)
        assert bytes(texture.fetch().get_bytes("RGBA", 8)) == expected
    finally:
        streamer.delete()
        texture.delete()


def test_texture_streamer_download_restores_client_readbacks(test_window):
    test_window.switch_to()
    ctx = test_window.context
    texture = pyglet.graphics.Texture.create(2, 2, context=ctx)
    streamer = pyglet.graphics.TextureStreamer(ctx)
    try:
        expected = bytes((21, 43, 65, 255)) * 4
        texture.upload(ImageData(2, 2, "RGBA", expected), 0, 0, 0)
        job = streamer.queue_download(texture)
        _finish_streamer(ctx, streamer, job)
        assert bytes(texture.fetch().get_bytes("RGBA", 8)) == expected
    finally:
        streamer.delete()
        texture.delete()


@pytest.mark.parametrize("use_region", [False, True])
def test_texture_streamer_mipmap_upload_and_download(test_window, use_region):
    test_window.switch_to()
    ctx = test_window.context
    texture = pyglet.graphics.Texture.create(8, 4, context=ctx)
    texture.init_mipmaps()
    target = texture.get_region(4, 0, 4, 4) if use_region else texture
    streamer = pyglet.graphics.TextureStreamer(ctx)
    try:
        expected = bytes((31, 63, 95, 255)) * 4
        upload = streamer.queue_upload(target, ImageData(2, 2, "RGBA", expected), level=1)
        _finish_streamer(ctx, streamer, upload)
        download = streamer.queue_download(target, width=2, height=2, level=1)
        _finish_streamer(ctx, streamer, download)
        assert (download.image_data.width, download.image_data.height) == (2, 2)
        assert bytes(download.image_data.get_bytes("RGBA", 8)) == expected
        assert bytes(texture.fetch(level=1).get_region(2 if use_region else 0, 0, 2, 2).get_bytes("RGBA", 8)) == expected
        whole = streamer.queue_download(target, level=1)
        _finish_streamer(ctx, streamer, whole)
        assert (whole.image_data.width, whole.image_data.height) == (2 if use_region else 4, 2)
    finally:
        streamer.delete()
        texture.delete()


@pytest.mark.parametrize("texture_class", ["Texture3D", "TextureArray"])
def test_texture_streamer_nonzero_layer(test_window, texture_class):
    test_window.switch_to()
    ctx = test_window.context
    texture = getattr(pyglet.graphics, texture_class).create_for_images(
        [_image(4, 4, (0, 0, 0, 255)) for _ in range(4)], context=ctx,
    )
    texture.init_mipmaps()
    streamer = pyglet.graphics.TextureStreamer(ctx)
    try:
        expected = bytes((12, 34, 56, 255)) * 4
        upload = streamer.queue_upload(texture, ImageData(2, 2, "RGBA", expected), z=1, level=1)
        _finish_streamer(ctx, streamer, upload)
        download = streamer.queue_download(texture, z=1, level=1)
        _finish_streamer(ctx, streamer, download)
        assert (download.image_data.width, download.image_data.height) == (2, 2)
        assert bytes(download.image_data.get_bytes("RGBA", 8)) == expected
        assert bytes(texture.fetch(z=0, level=1).get_bytes("RGBA", 8)) == bytes(16)
    finally:
        streamer.delete()
        texture.delete()


@pytest.mark.parametrize("use_region", [False, True])
@pytest.mark.parametrize("bounds", [
    dict(x=-1), dict(y=-1), dict(x=2), dict(y=2), dict(z=-1), dict(z=1),
    dict(level=-1), dict(level=1),
])
def test_texture_streamer_rejects_invalid_bounds_before_queuing(test_window, use_region, bounds):
    from pyglet.image.base import ImageException

    test_window.switch_to()
    texture = pyglet.graphics.Texture.create(4, 4, context=test_window.context)
    target = texture.get_region(1, 1, 2, 2) if use_region else texture
    streamer = pyglet.graphics.TextureStreamer(test_window.context)
    try:
        # A 3x3 upload at x=2 or y=2 overflows even the root texture.
        source = _image(2 if use_region else 3, 2 if use_region else 3, (1, 2, 3, 255))
        with pytest.raises(ImageException):
            streamer.queue_upload(target, source, **bounds)
        download_bounds = dict(width=3, height=3, **bounds) if not use_region else dict(width=2, height=2, **bounds)
        with pytest.raises(ImageException):
            streamer.queue_download(target, **download_bounds)
        assert not streamer._queued_uploads
        assert not streamer._queued_downloads
    finally:
        streamer.delete()
        texture.delete()


def test_texture_streamer_default_download_bounds(test_window):
    test_window.switch_to()
    texture = pyglet.graphics.Texture.create(4, 2, context=test_window.context)
    streamer = pyglet.graphics.TextureStreamer(test_window.context)
    try:
        job = streamer.queue_download(texture, x=1, y=1)
        _finish_streamer(test_window.context, streamer, job)
        assert (job.image_data.width, job.image_data.height) == (3, 1)
    finally:
        streamer.delete()
        texture.delete()
