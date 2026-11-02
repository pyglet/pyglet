from ctypes import byref
from pathlib import Path
from unittest.mock import Mock

import pyglet
import pytest

from pyglet.graphics.api.gl import gl
from pyglet.graphics import Texture
from pyglet.graphics.api.gl.texture import GLCompressedTexture
from pyglet.image import CompressedImageData, CompressedImageDecoder, ImageData, ImageException
from pyglet.graphics import TextureError, TextureFormatError, UnsupportedCompressedTextureError
from pyglet.image.base import CompressionFormat
from tests.annotations import GraphicsAPIGroups, require_graphics_api


FORMAT = CompressionFormat(b"DXT1", alpha=True)

_image_path = Path(__file__).parents[3] / "data" / "images"


def _level_dimensions(context, texture, level: int) -> tuple[int, int]:
    width = gl.GLint()
    height = gl.GLint()
    context.glGetTexLevelParameteriv(texture.target, level, gl.GL_TEXTURE_WIDTH, byref(width))
    context.glGetTexLevelParameteriv(texture.target, level, gl.GL_TEXTURE_HEIGHT, byref(height))
    return width.value, height.value


@require_graphics_api(GraphicsAPIGroups.MODERN_DESKTOP_GL)
def test_compressed_texture_uploads_dds_mip_chain(test_window):
    test_window.switch_to()
    context = test_window.context
    if not context.core.have_extension("GL_ARB_texture_compression_bptc"):
        pytest.skip("BPTC texture compression is not supported.")

    image = pyglet.image.load(_image_path / "rgba_bc7.dds")
    texture = image.get_texture()

    assert texture.mipmap_count == len(image.mipmap_data) + 1
    for level in range(texture.mipmap_count):
        assert _level_dimensions(context, texture, level) == (
            max(1, image.width >> level),
            max(1, image.height >> level),
        )


@require_graphics_api(GraphicsAPIGroups.MODERN_DESKTOP_GL)
def test_compressed_texture_generates_mip_chain(test_window):
    test_window.switch_to()
    context = test_window.context
    if not (
        context.core.have_extension("GL_EXT_texture_compression_s3tc")
        or context.core.have_extension("GL_EXT_texture_compression_dxt1")
    ):
        pytest.skip("S3TC texture compression is not supported.")

    image = pyglet.image.load(_image_path / "rgba_dxt1.dds")
    texture = image.get_texture()
    texture.generate_mipmaps()

    assert texture.mipmap_count == image.width.bit_length()
    assert _level_dimensions(context, texture, texture.mipmap_count - 1) == (1, 1)


@pytest.fixture
def unsupported(monkeypatch):
    monkeypatch.setattr(GLCompressedTexture, "supports_format", Mock(return_value=False))
    create = Mock(side_effect=AssertionError("Compressed creation must not run"))
    monkeypatch.setattr(GLCompressedTexture, "create_from_image", create)
    return create


def decode_color(data: bytes, width: int, height: int) -> ImageData:
    return ImageData(width, height, "RGBA", data[:4] * (width * height))


@require_graphics_api(GraphicsAPIGroups.GL3)
def test_supplied_decoder_uploads_pixels_and_caches_texture(test_window, unsupported):
    """Upload software-decoded pixels once and reuse the cached texture."""
    test_window.switch_to()
    decoder = Mock(side_effect=decode_color)
    image = CompressedImageData(4, 4, FORMAT, b"\x11\x22\x33\xff", decoder=decoder)
    texture = image.get_texture()
    try:
        assert isinstance(texture, Texture)
        assert bytes(texture.fetch().get_bytes("RGBA", 16)) == b"\x11\x22\x33\xff" * 16
        assert image.get_texture() is texture
        decoder.assert_called_once_with(image.data, 4, 4)
        unsupported.assert_not_called()
    finally:
        texture.delete()


@require_graphics_api(GraphicsAPIGroups.GL3)
def test_callable_object_implements_decoder_protocol(test_window, unsupported):
    """Accept a callable decoder object and forward the selected context."""
    class Decoder:
        def __call__(self, payload: bytes, w: int, h: int) -> ImageData:
            return decode_color(payload, w, h)

    decoder: CompressedImageDecoder = Decoder()
    image = CompressedImageData(1, 1, FORMAT, b"\x11\x22\x33\xff", decoder=decoder)
    texture = image.create_texture(GLCompressedTexture, context=test_window.context)
    texture.delete()
    GLCompressedTexture.supports_format.assert_called_once_with(FORMAT, context=test_window.context)


@require_graphics_api(GraphicsAPIGroups.GL3)
def test_fallback_preserves_authored_mipmap_pixels(test_window, unsupported):
    """Decode and upload each authored mipmap level with its original pixels."""
    test_window.switch_to()
    colors = [b"\x10\x20\x30\xff", b"\x40\x50\x60\xff", b"\x70\x80\x90\xff"]
    decoder = Mock(side_effect=decode_color)
    image = CompressedImageData(4, 4, FORMAT, colors[0], decoder=decoder)
    image.set_mipmap_data(1, colors[1])
    image.set_mipmap_data(2, colors[2])
    texture = image.get_texture()
    try:
        assert texture.mipmap_count == 3
        assert texture.valid_mipmaps == (0, 1, 2)
        for level, color in enumerate(colors):
            size = max(1, 4 >> level)
            assert bytes(texture.fetch(level=level).get_bytes("RGBA", size * 4)) == color * (size * size)
        assert [call.args[1:] for call in decoder.call_args_list] == [(4, 4), (2, 2), (1, 1)]
    finally:
        texture.delete()


@require_graphics_api(GraphicsAPIGroups.GL3)
def test_no_decoder_reports_unsupported_format(unsupported):
    """Raise the specific unsupported-format error when no fallback is supplied."""
    image = CompressedImageData(4, 4, FORMAT, bytes(8))
    with pytest.raises(UnsupportedCompressedTextureError, match="no software decoder supplied") as error:
        image.get_texture()
    assert isinstance(error.value, TextureError)
    assert isinstance(error.value, TextureFormatError)
    assert not isinstance(error.value, ImageException)
    unsupported.assert_not_called()


@require_graphics_api(GraphicsAPIGroups.GL3)
def test_unmapped_format_can_use_application_decoder(test_window):
    """Allow application decoders to handle formats unknown to the backend."""
    test_window.switch_to()
    decoder = Mock(side_effect=decode_color)
    image = CompressedImageData(1, 1, CompressionFormat(b"APP!", alpha=True), bytes(4), decoder=decoder)
    texture = image.get_texture()
    try:
        assert isinstance(texture, Texture)
        decoder.assert_called_once_with(bytes(4), 1, 1)
    finally:
        texture.delete()


@pytest.mark.parametrize("result", [None, bytes(16), ImageData(1, 1, "RGBA", bytes(4))])
@require_graphics_api(GraphicsAPIGroups.GL3)
def test_invalid_decoded_image_fails_before_allocation(unsupported, result, monkeypatch):
    """Reject incorrect decoder return types and dimensions before allocating a texture."""
    create = Mock(side_effect=AssertionError("GPU allocation must not run"))
    monkeypatch.setattr(Texture, "create_from_image", create)
    image = CompressedImageData(4, 4, FORMAT, bytes(8), decoder=Mock(return_value=result))
    with pytest.raises(ImageException, match="must return ImageData of size 4x4") as error:
        image.get_texture()
    assert not isinstance(error.value, TextureError)
    create.assert_not_called()


@require_graphics_api(GraphicsAPIGroups.GL3)
def test_decoder_exception_propagates_without_caching(unsupported):
    """Propagate decoder failures without caching an incomplete texture."""
    decoder = Mock(side_effect=ValueError("corrupt block"))
    image = CompressedImageData(4, 4, FORMAT, bytes(8), decoder=decoder)
    with pytest.raises(ValueError, match="corrupt block"):
        image.get_texture()
    assert image._current_texture is None


@require_graphics_api(GraphicsAPIGroups.GL3)
def test_incomplete_mip_chain_fails_before_allocation(unsupported, monkeypatch):
    """Reject missing mipmap data before allocating a fallback texture."""
    create = Mock()
    monkeypatch.setattr(Texture, "create_from_image", create)
    image = CompressedImageData(4, 4, FORMAT, bytes(8), decoder=decode_color)
    image.set_mipmap_data(2, bytes(8))
    with pytest.raises(ImageException, match="mipmap level 1 has no data"):
        image.get_texture()
    create.assert_not_called()


@require_graphics_api(GraphicsAPIGroups.GL3)
def test_supported_format_skips_decoder_and_propagates_upload_errors(monkeypatch):
    """Keep native upload errors visible without attempting software decoding."""
    monkeypatch.setattr(GLCompressedTexture, "supports_format", Mock(return_value=True))
    decoder = Mock(side_effect=AssertionError("Software decoding must not run"))
    create = Mock(side_effect=RuntimeError("upload failed"))
    monkeypatch.setattr(GLCompressedTexture, "create_from_image", create)
    image = CompressedImageData(4, 4, FORMAT, bytes(8), decoder=decoder)
    with pytest.raises(RuntimeError, match="upload failed"):
        image.get_texture()
    create.assert_called_once_with(image, context=None)
    decoder.assert_not_called()


@require_graphics_api(GraphicsAPIGroups.GL3)
def test_fallback_upload_failure_releases_texture(unsupported, monkeypatch):
    """Delete the fallback texture if a mipmap upload fails."""
    texture = Mock()
    texture.upload.side_effect = RuntimeError("mipmap upload failed")
    monkeypatch.setattr(Texture, "create_from_image", Mock(return_value=texture))
    image = CompressedImageData(4, 4, FORMAT, bytes(8), decoder=decode_color)
    image.set_mipmap_data(1, bytes(8))
    with pytest.raises(RuntimeError, match="mipmap upload failed"):
        image.get_texture()
    texture.delete.assert_called_once()
    assert image._current_texture is None


@require_graphics_api(GraphicsAPIGroups.GL3)
def test_direct_compressed_creation_checks_support_before_gl_allocation(monkeypatch):
    """Reject unsupported direct uploads before creating an OpenGL texture handle."""
    context = Mock()
    monkeypatch.setattr(GLCompressedTexture, "supports_format", Mock(return_value=False))
    image = CompressedImageData(4, 4, FORMAT, bytes(8))
    with pytest.raises(UnsupportedCompressedTextureError, match="Unsupported compressed texture format"):
        GLCompressedTexture.create_from_image(image, context=context)
    context.glGenTextures.assert_not_called()


@require_graphics_api(GraphicsAPIGroups.GL3)
def test_dxt1_only_extension_does_not_claim_dxt5_support():
    """Treat DXT1-only extension support as insufficient for DXT5 uploads."""
    context = Mock()
    context.info.have_extension.side_effect = lambda name: name == "GL_EXT_texture_compression_dxt1"
    assert GLCompressedTexture.supports_format(FORMAT, context)
    assert not GLCompressedTexture.supports_format(CompressionFormat(b"DXT5", alpha=True), context)


@require_graphics_api(GraphicsAPIGroups.GL3)
def test_unmapped_format_direct_upload_raises_specific_exception():
    """Report unknown formats through the dedicated exception without allocating a handle."""
    context = Mock()
    fmt = CompressionFormat(b"APP!", alpha=True)
    assert not GLCompressedTexture.supports_format(fmt, context)
    with pytest.raises(UnsupportedCompressedTextureError, match="Unsupported compressed texture format"):
        GLCompressedTexture.create(4, 4, fmt, bytes(8), context=context)
    context.glGenTextures.assert_not_called()
