from dataclasses import FrozenInstanceError

import pytest

from pyglet import image
from pyglet.enums import PixelFormat
from pyglet.graphics.api.gl.gl_info import GLInfo
from tests.annotations import GraphicsAPIGroups, require_graphics_api


pytestmark = require_graphics_api(GraphicsAPIGroups.GL3)


class _TestSurfaceInfo(GLInfo):
    def __init__(self) -> None:
        super().__init__(platform_info=None)

    def query(self) -> None:
        pass


def test_surface_features_cover_gles3_versions_and_extensions() -> None:
    surface_info = _TestSurfaceInfo()
    surface_info.api = "gles3"
    surface_info.major_version, surface_info.minor_version = 3, 0
    surface_info.update_features()

    assert surface_info.features.uniform_buffers
    assert surface_info.features.sync_objects
    assert surface_info.features.texture_storage
    assert not surface_info.features.compute_shaders
    assert not surface_info.features.shader_storage_buffers

    surface_info.minor_version = 1
    surface_info.update_features()
    assert surface_info.features.compute_shaders
    assert surface_info.features.shader_storage_buffers
    assert surface_info.features.texture_storage
    assert not surface_info.features.tessellation_shaders
    assert surface_info.features.pixel_buffer_objects
    assert surface_info.pixel_transfer.unpack_row_length
    assert not surface_info.pixel_transfer.direct_texture_readback
    assert surface_info.pixel_format_preferences.preferred_decode_format == PixelFormat.RGBA8

    surface_info.api = "opengl"
    surface_info.major_version, surface_info.minor_version = 4, 2
    surface_info.extensions = {"GL_ARB_compute_shader", "GL_ARB_shader_storage_buffer_object"}
    surface_info.update_features()
    assert surface_info.features.compute_shaders
    assert surface_info.features.shader_storage_buffers


def test_surface_features_are_immutable() -> None:
    surface_info = _TestSurfaceInfo()

    with pytest.raises(FrozenInstanceError):
        surface_info.features.compute_shaders = True
    with pytest.raises(FrozenInstanceError):
        surface_info.pixel_transfer.bgra_upload = True
    with pytest.raises(FrozenInstanceError):
        surface_info.pixel_format_preferences.readback_format = PixelFormat.BGRA8


def test_surface_info_publishes_image_decode_policy() -> None:
    surface_info = _TestSurfaceInfo()
    surface_info.api = "gles3"
    surface_info.major_version, surface_info.minor_version = 3, 1
    surface_info.update_features()

    assert image.get_default_decode_policy() == image.ImageDecodePolicy(
        surface_info.pixel_format_preferences.preferred_decode_format,
    )


def test_gles2_pixel_transfer_features_use_extension_support() -> None:
    surface_info = _TestSurfaceInfo()
    surface_info.api = "gles2"
    surface_info.major_version, surface_info.minor_version = 2, 0
    surface_info.extensions = {"GL_EXT_unpack_subimage", "GL_EXT_texture_format_BGRA8888"}
    surface_info.update_features()

    assert surface_info.pixel_transfer.bgra_upload
    assert not surface_info.pixel_transfer.bgra_readback
    assert surface_info.pixel_transfer.unpack_row_length
    assert not surface_info.pixel_transfer.pack_row_length
    assert not surface_info.pixel_transfer.direct_texture_readback
    assert not surface_info.features.pixel_buffer_objects
