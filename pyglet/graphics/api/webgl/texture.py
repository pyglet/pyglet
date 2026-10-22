from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, cast, Sequence

import js  # noqa: F821

import pyglet
from pyglet.libs.emscripten import zero_copy
from pyglet.enums import TextureFilter, TextureType, ComponentFormat, \
    AddressMode
from pyglet.graphics.api.webgl.enums import texture_map
from pyglet.graphics.api.webgl.gl import (
    GL_COLOR_ATTACHMENT0,
    GL_DEPTH_COMPONENT,
    GL_DEPTH_STENCIL,
    GL_FRAMEBUFFER,
    GL_FRAMEBUFFER_COMPLETE,
    GL_READ_FRAMEBUFFER,
    GL_READ_FRAMEBUFFER_BINDING,
    GL_DRAW_FRAMEBUFFER,
    GL_DRAW_FRAMEBUFFER_BINDING,
    GL_LINEAR_MIPMAP_LINEAR,
    GL_PACK_ALIGNMENT,
    GL_PACK_ROW_LENGTH,
    GL_PACK_SKIP_PIXELS,
    GL_PACK_SKIP_ROWS,
    GL_PIXEL_PACK_BUFFER,
    GL_PIXEL_UNPACK_BUFFER,
    GL_READ_WRITE,
    GL_RED,
    GL_RED_INTEGER,
    GL_RG,
    GL_RG_INTEGER,
    GL_RGB,
    GL_RGB_INTEGER,
    GL_RGBA,
    GL_RGBA32F,
    GL_RGBA_INTEGER,
    # Sized internal formats resolved dynamically by _get_internal_format:
    GL_R8,  # noqa: F401
    GL_R16,  # noqa: F401
    GL_RG8,  # noqa: F401
    GL_RG16,  # noqa: F401
    GL_RGB8,  # noqa: F401
    GL_RGB16,  # noqa: F401
    GL_RGBA8,  # noqa: F401
    GL_RGBA16,  # noqa: F401
    GL_R16F,  # noqa: F401
    GL_R32F,  # noqa: F401
    GL_RG16F,  # noqa: F401
    GL_RG32F,  # noqa: F401
    GL_RGB16F,  # noqa: F401
    GL_RGB32F,  # noqa: F401
    GL_RGBA16F,  # noqa: F401
    GL_R8I,  # noqa: F401
    GL_R8UI,  # noqa: F401
    GL_R16I,  # noqa: F401
    GL_R16UI,  # noqa: F401
    GL_R32I,  # noqa: F401
    GL_R32UI,  # noqa: F401
    GL_RG8I,  # noqa: F401
    GL_RG8UI,  # noqa: F401
    GL_RG16I,  # noqa: F401
    GL_RG16UI,  # noqa: F401
    GL_RG32I,  # noqa: F401
    GL_RG32UI,  # noqa: F401
    GL_RGB8I,  # noqa: F401
    GL_RGB8UI,  # noqa: F401
    GL_RGB16I,  # noqa: F401
    GL_RGB16UI,  # noqa: F401
    GL_RGB32I,  # noqa: F401
    GL_RGB32UI,  # noqa: F401
    GL_RGBA8I,  # noqa: F401
    GL_RGBA8UI,  # noqa: F401
    GL_RGBA16I,  # noqa: F401
    GL_RGBA16UI,  # noqa: F401
    GL_RGBA32I,  # noqa: F401
    GL_RGBA32UI,  # noqa: F401
    GL_TEXTURE0,
    GL_TEXTURE_2D,
    GL_TEXTURE_2D_ARRAY,
    GL_TEXTURE_3D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_UNPACK_ALIGNMENT,
    GL_UNPACK_IMAGE_HEIGHT,
    GL_UNPACK_ROW_LENGTH,
    GL_UNPACK_SKIP_PIXELS,
    GL_UNPACK_SKIP_ROWS,
    GL_UNPACK_SKIP_IMAGES,
    GL_UNSIGNED_BYTE,
)
from pyglet.graphics import UnsupportedBackendError
from pyglet.graphics.api.webgl.buffer import WebGLPixelPackBufferObject, WebGLPixelUnpackBufferObject
from pyglet.graphics.texture import TextureArrayDepthExceeded
from pyglet.graphics.texture import CompressedTexture, Texture, TextureStreamer, UniformTextureSequence, _TextureRegionShared, _Texture3DShared, \
    _TextureArrayShared, TextureGrid
from pyglet.image.base import (
    CompressedImageData,
    CompressionFormat,
    ImageData,
    ImageDataRegion,
    ImageException,
    _AbstractImage,
)

if TYPE_CHECKING:
    from pyglet.graphics.api.base import SurfaceContext
    from typing import Callable

    from pyglet.graphics.api.webgl import WebGL2SurfaceContext
    from pyglet.graphics.api.webgl.webgl_js import WebGL2RenderingContext
    from pyglet.graphics.resource import TextureKey

_api_base_internal_formats = {
    'R': 'GL_R',
    'RG': 'GL_RG',
    'RGB': 'GL_RGB',
    'RGBA': 'GL_RGBA',
    'BGR': 'GL_RGB',
    'BGRA': 'GL_RGBA',
    'D': 'GL_DEPTH_COMPONENT',
    'DS': 'GL_DEPTH_STENCIL',
}

_api_base_pixel_formats = {
    'R': 'GL_RED',
    'RG': 'GL_RG',
    'RGB': 'GL_RGB',
    'BGR': 'GL_RGB',
    'RGBA': 'GL_RGBA',
    'BGRA': 'GL_RGBA',
    'D': 'GL_DEPTH_COMPONENT',
    'DS': 'GL_DEPTH_STENCIL',
}


def _get_base_format(component_format: ComponentFormat) -> int:
    return globals()[_api_base_pixel_formats[component_format]]


def _get_internal_format(component_format: ComponentFormat, bit_size: int = 8, data_type: str = "B") -> int:
    """Convert our internal format class to the GL equivalent with size and type."""
    # Base format based on components
    base_format = _api_base_internal_formats.get(component_format.upper())

    if base_format is None:
        raise ValueError(f"Unknown format: {component_format}")

    # Type suffix based on data type (integer, float, or default)
    if data_type == "I":
        type_suffix = "UI"
    elif data_type == "i":
        type_suffix = 'I'
    elif data_type == "f":
        type_suffix = 'F'
    else:
        type_suffix = ''  # No suffix for unsigned normalized formats

    # Construct the final GL format string.
    # For example. Base_format: GL_RGBA, size: 32, "type": float -> GL_RGBA32F
    gl_format = f"{base_format}{bit_size}{type_suffix}"

    # Get the integer value of the GL constant using globals()
    if gl_format in globals():
        return globals()[gl_format]
    raise ValueError(f"GL constant '{gl_format}' not defined.")


_api_pixel_formats = {
    'R': GL_RED,
    'RG': GL_RG,
    'RGB': GL_RGB,
    'RGBA': GL_RGBA,
    'RI': GL_RED_INTEGER,
    'RGI': GL_RG_INTEGER,
    'RGBI': GL_RGB_INTEGER,
    'RGBAI': GL_RGBA_INTEGER,
    'D': GL_DEPTH_COMPONENT,
    'DS': GL_DEPTH_STENCIL,
}

def _get_gl_format_and_type(fmt: str):
    fmt = _api_pixel_formats.get(fmt)
    if fmt:
        return fmt, GL_UNSIGNED_BYTE  # Eventually support others through ImageData.

    return None, None


def _normalize_upload_format(data_format: str) -> str:
    """Normalize an image format string into a WebGL-supported upload format."""
    if data_format not in _api_pixel_formats:
        return {
            1: 'R',
            2: 'RG',
            3: 'RGB',
            4: 'RGBA',
        }.get(len(data_format))
    return data_format


_webgl_compression_formats = {
    b"DXT1": (0x83F1, "WEBGL_compressed_texture_s3tc"),
    b"BC1 ": (0x83F1, "WEBGL_compressed_texture_s3tc"),
    b"DXT3": (0x83F2, "WEBGL_compressed_texture_s3tc"),
    b"BC2 ": (0x83F2, "WEBGL_compressed_texture_s3tc"),
    b"DXT5": (0x83F3, "WEBGL_compressed_texture_s3tc"),
    b"BC3 ": (0x83F3, "WEBGL_compressed_texture_s3tc"),
}

_dxgi_to_webgl_format = {
    71: (0x83F0, "WEBGL_compressed_texture_s3tc"), 72: (0x83F1, "WEBGL_compressed_texture_s3tc"),
    74: (0x83F2, "WEBGL_compressed_texture_s3tc"), 75: (0x83F2, "WEBGL_compressed_texture_s3tc"),
    77: (0x83F3, "WEBGL_compressed_texture_s3tc"), 78: (0x83F3, "WEBGL_compressed_texture_s3tc"),
    80: (0x8DBB, "EXT_texture_compression_rgtc"), 81: (0x8DBC, "EXT_texture_compression_rgtc"),
    83: (0x8DBD, "EXT_texture_compression_rgtc"), 84: (0x8DBE, "EXT_texture_compression_rgtc"),
    95: (0x8E8C, "EXT_texture_compression_bptc"), 96: (0x8E8D, "EXT_texture_compression_bptc"),
    98: (0x8E8E, "EXT_texture_compression_bptc"), 99: (0x8E8F, "EXT_texture_compression_bptc"),
}

_vk_to_webgl_format = {
    131: (0x83F1, "WEBGL_compressed_texture_s3tc"), 132: (0x83F1, "WEBGL_compressed_texture_s3tc"),
    133: (0x83F2, "WEBGL_compressed_texture_s3tc"), 134: (0x83F2, "WEBGL_compressed_texture_s3tc"),
    135: (0x83F3, "WEBGL_compressed_texture_s3tc"), 136: (0x83F3, "WEBGL_compressed_texture_s3tc"),
    137: (0x8DBB, "EXT_texture_compression_rgtc"), 138: (0x8DBC, "EXT_texture_compression_rgtc"),
    139: (0x8DBD, "EXT_texture_compression_rgtc"), 140: (0x8DBE, "EXT_texture_compression_rgtc"),
    141: (0x8E8C, "EXT_texture_compression_bptc"), 142: (0x8E8D, "EXT_texture_compression_bptc"),
    146: (0x8E8E, "EXT_texture_compression_bptc"), 147: (0x8E8F, "EXT_texture_compression_bptc"),
    67: (0x9270, "WEBGL_compressed_texture_etc"), 68: (0x9271, "WEBGL_compressed_texture_etc"),
    69: (0x9272, "WEBGL_compressed_texture_etc"), 70: (0x9273, "WEBGL_compressed_texture_etc"),
    74: (0x9274, "WEBGL_compressed_texture_etc"), 75: (0x9275, "WEBGL_compressed_texture_etc"),
    76: (0x9276, "WEBGL_compressed_texture_etc"), 77: (0x9277, "WEBGL_compressed_texture_etc"),
    78: (0x9278, "WEBGL_compressed_texture_etc"), 79: (0x9279, "WEBGL_compressed_texture_etc"),
}


def _get_webgl_compression_format(fmt: CompressionFormat) -> tuple[int, str]:
    if fmt.fmt in (b"DXT1", b"BC1 "):
        return (0x83F1 if fmt.alpha else 0x83F0), "WEBGL_compressed_texture_s3tc"
    if result := _webgl_compression_formats.get(fmt.fmt):
        return result
    if fmt.fmt == b"DX10" and (result := _dxgi_to_webgl_format.get(fmt.dxgi_format)):
        return result
    if fmt.fmt == b"KTX2" and (result := _vk_to_webgl_format.get(fmt.vk_format)):
        return result
    msg = f"Compressed texture format is not supported by WebGL: {fmt!r}"
    raise UnsupportedBackendError(msg)


class WebGLCompressedTexture(CompressedTexture):
    """A WebGL texture created from GPU-ready compressed image data."""

    def __init__(self, context: WebGL2SurfaceContext, width: int, height: int, handle: Any,
                 compression_fmt: CompressionFormat,
                 tex_type: TextureType = TextureType.TYPE_2D,
                 filters: TextureFilter | tuple[TextureFilter, TextureFilter] | None = None,
                 address_mode: AddressMode = AddressMode.REPEAT,
                 anisotropic_level: int = 0) -> None:
        super().__init__(width, height, handle, compression_fmt, tex_type, filters, address_mode, anisotropic_level)
        self._context = context
        self._gl = context.gl
        self.target = texture_map[tex_type]
        self._gl_min_filter = texture_map[self.min_filter]
        self._gl_mag_filter = texture_map[self.mag_filter]
        self._gl_format, self._extension_name = _get_webgl_compression_format(compression_fmt)
        if not context.info.have_extension(self._extension_name):
            raise UnsupportedBackendError(f"Compressed texture format '{compression_fmt.fmt.decode()}'")
        self._extension = self._gl.getExtension(self._extension_name)
        if self._extension is None:
            raise UnsupportedBackendError(f"Compressed texture format '{compression_fmt.fmt.decode()}'")
        self.mipmap_data: list[bytes | None] = []
        self._mipmap_levels = 1
        self._valid_mipmaps: set[int] = set()

    @classmethod
    def create_from_image(cls, image_data: CompressedImageData,
                          tex_type: TextureType = TextureType.TYPE_2D,
                          filters: TextureFilter | tuple[TextureFilter, TextureFilter] | None = None,
                          address_mode: AddressMode = AddressMode.REPEAT,
                          anisotropic_level: int = 0,
                          context: WebGL2SurfaceContext | None = None) -> WebGLCompressedTexture:
        ctx = context or pyglet.graphics.api.core.current_context
        tex_id = ctx.gl.createTexture()
        texture = cls(ctx, image_data.width, image_data.height, tex_id, image_data.fmt, tex_type,
                      filters, address_mode, anisotropic_level)
        texture.bind()
        ctx.gl.texParameteri(texture.target, GL_TEXTURE_MIN_FILTER, texture._gl_min_filter)
        ctx.gl.texParameteri(texture.target, GL_TEXTURE_MAG_FILTER, texture._gl_mag_filter)
        texture._upload_level(0, image_data.width, image_data.height, image_data.data)
        texture.mipmap_data = image_data.mipmap_data.copy()
        texture._upload_mipmap_data()
        return texture

    def bind(self, texture_unit: int = 0) -> None:
        self._gl.activeTexture(GL_TEXTURE0 + texture_unit)
        self._gl.bindTexture(self.target, self._handle)

    def delete(self) -> None:
        """Delete this texture and its WebGL resource."""
        if self._handle is not None:
            self._gl.deleteTexture(self._handle)
            self._handle = None

    def _upload_level(self, level: int, width: int, height: int, data: bytes) -> None:
        with zero_copy(data) as js_array:
            self._gl.compressedTexImage2D(self.target, level, self._gl_format, width, height, 0, js_array)

    def _upload_mipmap_data(self) -> None:
        if not self.mipmap_data:
            self._valid_mipmaps = {0}
            return
        for level, data in enumerate(self.mipmap_data, start=1):
            if data is None:
                raise ImageException(f"Compressed texture mipmap level {level} has no data.")
            self._upload_level(level, max(1, self.width >> level), max(1, self.height >> level), data)
        self._mipmap_levels = len(self.mipmap_data) + 1
        self._valid_mipmaps = set(range(self._mipmap_levels))

def _get_pixel_format(image_data: ImageData) -> tuple[int, int]:
    """Determine the pixel format from format string for the Graphics API."""
    data_format = image_data.format
    fmt, gl_type = _get_gl_format_and_type(data_format)

    if fmt is None:
        # Need to convert data to a standard form
        data_format = {
            1: 'R',
            2: 'RG',
            3: 'RGB',
            4: 'RGBA',
        }.get(len(data_format))
        fmt, gl_type = _get_gl_format_and_type(data_format)

    return fmt, gl_type


class WebGLTexture(Texture):
    """An image loaded into GPU memory.

    Typically, you will get an instance of Texture by accessing calling
    the ``get_texture()`` method of any AbstractImage class (such as ImageData).
    """

    region_class: WebGLTextureRegion  # Set to WebGLTextureRegion after it's defined
    """The class to use when constructing regions of this texture.
     The class should be a subclass of TextureRegion.
    """

    _ctx: WebGL2SurfaceContext
    _gl: WebGL2RenderingContext

    def __init__(self, context: WebGL2SurfaceContext, width: int, height: int, handle: Any,
                 tex_type: TextureType = TextureType.TYPE_2D,
                 internal_format: ComponentFormat = ComponentFormat.RGBA,
                 internal_format_size: int = 8,
                 internal_format_type: str = "B",
                 filters: TextureFilter | tuple[TextureFilter, TextureFilter] | None = None,
                 address_mode: AddressMode = AddressMode.REPEAT,
                 anisotropic_level: int = 0,
                 *,
                 key: TextureKey | None = None):
        super().__init__(width, height, handle, tex_type, internal_format, internal_format_size, internal_format_type,
                         filters, address_mode, anisotropic_level, key=key)
        self._context = context
        self._gl = self._context.gl
        self.target = texture_map[self.tex_type]
        self._gl_min_filter = texture_map[self.min_filter]
        self._gl_mag_filter = texture_map[self.mag_filter]
        self._gl_internal_format = _get_internal_format(internal_format, internal_format_size, internal_format_type)

    def delete(self) -> None:
        """Delete this texture and the memory it occupies.

        Textures are invalid after deletion, and may no longer be used.
        """
        self._gl.deleteTexture(self._handle)
        self._handle = None

    def bind(self, texture_unit: int = 0) -> None:
        """Bind to a specific Texture Unit by number."""
        self._gl.activeTexture(GL_TEXTURE0 + texture_unit)
        self._gl.bindTexture(self.target, self._handle)

    def bind_image_texture(
        self,
        unit: int,
        level: int = 0,
        layered: bool = False,
        layer: int = 0,
        access: int = GL_READ_WRITE,
        fmt: int = GL_RGBA32F,
    ):
        """Bind as an ImageTexture for use with a :py:class:`~pyglet.shader.ComputeShaderProgram`.

        .. note:: OpenGL 4.3, or 4.2 with the GL_ARB_compute_shader extention is required.
        """
        raise NotImplementedError("Not supported.")

    def _flush(self) -> None:
        self._gl.flush()

    def _delete_resource(self) -> None:
        self._context.delete_texture(self._handle)
        self._handle = None

    def _begin_upload(self, image_data: ImageData | ImageDataRegion) -> None:
        align, row_length = self._get_image_alignment(image_data)

        self._gl.pixelStorei(GL_UNPACK_ALIGNMENT, align)
        if not self._context.info.pixel_transfer.unpack_row_length:
            return

        self._gl.pixelStorei(GL_UNPACK_ROW_LENGTH, row_length)

        if isinstance(image_data, ImageDataRegion):
            self._gl.pixelStorei(GL_UNPACK_SKIP_PIXELS, image_data.x)
            self._gl.pixelStorei(GL_UNPACK_SKIP_ROWS, image_data.y)
            if self.target in (GL_TEXTURE_3D, GL_TEXTURE_2D_ARRAY):
                self._gl.pixelStorei(GL_UNPACK_IMAGE_HEIGHT, image_data.y + image_data.height)

    def _end_upload(self, image_data: ImageData | ImageDataRegion) -> None:
        if not self._context.info.pixel_transfer.unpack_row_length:
            return

        self._gl.pixelStorei(GL_UNPACK_ROW_LENGTH, 0)

        if isinstance(image_data, ImageDataRegion):
            self._gl.pixelStorei(GL_UNPACK_SKIP_PIXELS, 0)
            self._gl.pixelStorei(GL_UNPACK_SKIP_ROWS, 0)
            if self.target in (GL_TEXTURE_3D, GL_TEXTURE_2D_ARRAY):
                self._gl.pixelStorei(GL_UNPACK_IMAGE_HEIGHT, 0)

    def _apply_filters(self) -> None:
        self._gl_min_filter = texture_map[self.min_filter]
        self._gl_mag_filter = texture_map[self.mag_filter]

        self.bind()
        self._gl.texParameteri(self.target, GL_TEXTURE_MIN_FILTER, self._gl_min_filter)
        self._gl.texParameteri(self.target, GL_TEXTURE_MAG_FILTER, self._gl_mag_filter)

    def _allocate_mipmap_level(self, level: int, width: int, height: int, depth: int,
                               data_size: int | None) -> None:
        data = js.Uint8Array.new(data_size) if data_size is not None else None
        self._gl.texImage2D(
            self.target,
            level,
            self._gl_internal_format,
            width,
            height,
            0,
            _get_base_format(self.internal_format),
            GL_UNSIGNED_BYTE,
            data,
        )

    def _generate_mipmaps(self) -> None:
        self._gl.generateMipmap(self.target)
        self._gl.flush()

    def _update_subregion(self, image_data: ImageData | ImageDataRegion, x: int, y: int, z: int,
                          level: int = 0) -> None:
        data_pitch = abs(image_data._current_pitch)
        upload_fmt = image_data.format
        upload_pitch = data_pitch

        # WebGL is strict about sub-image format compatibility. Convert only
        # when the source format cannot be uploaded to this texture directly.
        desired_fmt = _normalize_upload_format(self.internal_format.value)
        if _normalize_upload_format(upload_fmt) != desired_fmt or upload_fmt not in _api_pixel_formats:
            upload_fmt = desired_fmt
            upload_pitch = image_data.width * len(upload_fmt)

        # Get data in required format (hopefully will be the same format it's already
        # in, unless that's an obscure format, upside-down or the driver is old).
        if self._context.info.pixel_transfer.unpack_row_length:
            data = image_data.convert(upload_fmt, upload_pitch)
        else:
            upload_pitch = image_data.width * len(upload_fmt)
            data = image_data.get_bytes(upload_fmt, upload_pitch)
        fmt, gl_type = _get_gl_format_and_type(upload_fmt)

        with zero_copy(data) as js_array:
            if self.target == GL_TEXTURE_3D or self.target == GL_TEXTURE_2D_ARRAY:
                self._gl.texSubImage3D(
                    self.target, level, x, y, z, image_data.width, image_data.height, 1, fmt, gl_type, js_array,
                )
            else:
                self._gl.texSubImage2D(
                    self.target, level, x, y, image_data.width, image_data.height, fmt, gl_type, js_array,
                )

    def get_pbo_upload_size(self, image: ImageData | ImageDataRegion) -> int:
        upload_fmt = _normalize_upload_format(self.internal_format.value)
        return image.width * image.height * len(upload_fmt)

    def upload_to_pbo(self, pbo: WebGLPixelUnpackBufferObject, image: ImageData | ImageDataRegion, x: int, y: int, z: int,
                      level: int = 0) -> None:
        self.upload_regions_to_pbo(pbo, [(image, x, y, z, level)])

    def upload_regions_to_pbo(
        self, pbo: WebGLPixelUnpackBufferObject,
        uploads: Sequence[tuple[ImageData | ImageDataRegion, int, int, int, int]],
    ) -> None:
        """Pack upload regions into one PBO and issue their texture transfers."""
        prepared: list[tuple[ImageData | ImageDataRegion, int, int, int, int, int, int, int, bytes]] = []
        end = 0
        for image, x, y, z, level in uploads:
            self._validate_pbo_region(x, y, image.width, image.height, z, level)
            data_format = _normalize_upload_format(self.internal_format.value)
            data = bytes(image.get_bytes(data_format, image.width * len(data_format)))
            offset = (end + 7) & ~7
            end = offset + len(data)
            fmt, gl_type = _get_gl_format_and_type(data_format)
            prepared.append((image, x, y, z, level, fmt, gl_type, offset, data))
        assert pbo.size >= end, "Pixel unpack buffer is too small for grouped upload."
        try:
            if len(prepared) == 1 and pbo.size == end:
                pbo.set_bytes(prepared[0][-1])
            else:
                pbo.invalidate()
                for *_, offset, data in prepared:
                    with zero_copy(data) as js_array:
                        self._gl.bufferSubData(pbo.target, offset, js_array)
                pbo._set_data_uploaded()

            self.bind()
            pbo.bind()
            self._gl.pixelStorei(GL_UNPACK_ALIGNMENT, 1)
            self._gl.pixelStorei(GL_UNPACK_ROW_LENGTH, 0)
            self._gl.pixelStorei(GL_UNPACK_SKIP_PIXELS, 0)
            self._gl.pixelStorei(GL_UNPACK_SKIP_ROWS, 0)
            layered = self.target in (GL_TEXTURE_3D, GL_TEXTURE_2D_ARRAY)
            if layered:
                self._gl.pixelStorei(GL_UNPACK_IMAGE_HEIGHT, 0)
                self._gl.pixelStorei(GL_UNPACK_SKIP_IMAGES, 0)
            for image, x, y, z, level, fmt, gl_type, offset, _ in prepared:
                if layered:
                    self._gl.texSubImage3D(
                        self.target, level, x, y, z,
                        image.width, image.height, 1, fmt, gl_type, offset,
                    )
                else:
                    self._gl.texSubImage2D(
                        self.target, level, x, y,
                        image.width, image.height, fmt, gl_type, offset,
                    )
                self._mark_mipmap_valid(level)
        finally:
            pbo.unbind()

    def fetch_to_pbo(self, pbo, z: int = 0, level: int = 0) -> None:
        width, height, _ = self._get_mipmap_dimensions(level)
        self.fetch_region_to_pbo(pbo, 0, 0, width, height, z, level)

    def fetch_region_to_pbo(self, pbo, x: int, y: int, width: int, height: int,
                            z: int = 0, level: int = 0) -> None:
        self._validate_pbo_region(x, y, width, height, z, level)
        size = width * height * 4
        assert pbo.size >= size, f"Pixel pack buffer is too small for fetch ({pbo.size} < {size})."
        read_framebuffer = self._gl.getParameter(GL_READ_FRAMEBUFFER_BINDING)
        draw_framebuffer = self._gl.getParameter(GL_DRAW_FRAMEBUFFER_BINDING)
        pack_fields = ((GL_PACK_ALIGNMENT, 1), (GL_PACK_ROW_LENGTH, 0),
                       (GL_PACK_SKIP_PIXELS, 0), (GL_PACK_SKIP_ROWS, 0))
        pack_state = [(field, self._gl.getParameter(field)) for field, _ in pack_fields]
        fbo = self._gl.createFramebuffer()
        try:
            pbo.invalidate()
            for field, value in pack_fields:
                self._gl.pixelStorei(field, value)
            self._gl.bindFramebuffer(GL_FRAMEBUFFER, fbo)
            self._attach_texture_to_fbo(z, level)
            if self._gl.checkFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
                raise ImageException("Texture readback framebuffer is incomplete.")
            self._gl.readPixels(x, y, width, height, GL_RGBA, GL_UNSIGNED_BYTE, 0)
        finally:
            self._gl.bindFramebuffer(GL_READ_FRAMEBUFFER, read_framebuffer)
            self._gl.bindFramebuffer(GL_DRAW_FRAMEBUFFER, draw_framebuffer)
            for field, value in pack_state:
                self._gl.pixelStorei(field, value)
            self._gl.deleteFramebuffer(fbo)
            pbo.unbind()

    @classmethod
    def create_from_image(cls,
                          image_data: ImageData | ImageDataRegion,
                          tex_type: TextureType = TextureType.TYPE_2D,
                          internal_format_size: int = 8,
                          filters: TextureFilter | tuple[TextureFilter, TextureFilter] | None = None,
                          address_mode: AddressMode = AddressMode.REPEAT,
                          anisotropic_level: int = 0,
                          context: SurfaceContext | None = None,
                          ) -> WebGLTexture:
        """Create a Texture from image data.

        Args:
             image_data:
                 The image instance.
             tex_type:
                 The texture enum type.
             internal_format_size:
                 Byte size of the internal format.
             filters:
                 Texture format filter, passed as a list of min/mag filters, or a single filter to apply both.
             address_mode:
                 Texture address mode.
             anisotropic_level:
                 The maximum anisotropic level.
             context:
                 A specific OpenGL Surface context, otherwise the current active context.

        Returns:
             A currently bound texture.
        """
        ctx = cast("WebGL2SurfaceContext", context or pyglet.graphics.api.core.current_context)
        gl = ctx.gl

        tex_id = gl.createTexture()
        target = texture_map[tex_type]
        gl.bindTexture(target, tex_id)

        texture = cls(ctx, image_data.width, image_data.height, tex_id, tex_type,
                      ComponentFormat(image_data.format), internal_format_size, image_data.data_type, filters,
                      address_mode, anisotropic_level)

        gl.texParameteri(target, GL_TEXTURE_MIN_FILTER, texture._gl_min_filter)
        gl.texParameteri(target, GL_TEXTURE_MAG_FILTER, texture._gl_mag_filter)

        pixel_fmt = _normalize_upload_format(image_data.format)
        image_bytes = image_data.get_bytes(pixel_fmt, image_data.width * len(pixel_fmt))
        gl_pfmt, gl_type = _get_gl_format_and_type(pixel_fmt)

        align, _ = texture._get_image_alignment(image_data)

        gl.pixelStorei(GL_UNPACK_ALIGNMENT, align)
        if ctx.info.pixel_transfer.unpack_row_length:
            # get_bytes above always returns tightly packed rows.
            gl.pixelStorei(GL_UNPACK_ROW_LENGTH, 0)

        with zero_copy(image_bytes) as js_array:
            gl.texImage2D(
                target,
                0,
                texture._gl_internal_format,
                image_data.width,
                image_data.height,
                0,
                gl_pfmt,
                gl_type,
                js_array,
            )
        gl.flush()
        texture._mark_mipmap_valid(0)
        return texture

    @classmethod
    def create(cls, width: int, height: int,
               tex_type: TextureType = TextureType.TYPE_2D,
               internal_format: ComponentFormat = ComponentFormat.RGBA,
               internal_format_size: int = 8,
               internal_format_type: str = "B",
               filters: TextureFilter | tuple[TextureFilter, TextureFilter] | None = None,
               address_mode: AddressMode = AddressMode.REPEAT,
               anisotropic_level: int = 0,
               blank_data: bool = True,
               immutable: bool = False,
               mipmap_levels: int = 1,
               context: SurfaceContext | None = None) -> WebGLTexture:
        """Create a Texture.

        Create a Texture with the specified dimensions, and attributes.

        Args:
            width:
                Width of texture in pixels.
            height:
                Height of texture in pixels.
            tex_type:
                The texture enum type.
            internal_format:
                Component format of the image data.
            internal_format_size:
                Byte size of the internal format.
            internal_format_type:
                Internal format type in struct format.
            filters:
                Texture format filter, passed as a list of min/mag filter or a single filter to apply both.
            address_mode:
                Texture address mode.
            anisotropic_level:
                The maximum anisotropic level.
            blank_data:
                If True, initialize the texture data with all zeros. If False, do not pass initial data.
            immutable:
                If True, allocate immutable-format texture storage.
            mipmap_levels:
                Number of mipmap levels to allocate.
            context:
                A specific OpenGL Surface context, otherwise the current active context.

        Returns:
            A currently bound texture.
        """
        if immutable:
            raise NotImplementedError("Immutable texture creation is not implemented by the WebGL backend.")
        if mipmap_levels != 1:
            raise NotImplementedError("Explicit mipmap allocation is not implemented by the WebGL backend.")

        ctx = cast("WebGL2SurfaceContext", context or pyglet.graphics.api.core.current_context)
        gl = ctx.gl

        tex_id = gl.createTexture()
        target = texture_map[tex_type]

        texture = cls(ctx, width, height, tex_id, tex_type, internal_format, internal_format_size, internal_format_type, filters, address_mode, anisotropic_level)
        gl.bindTexture(target, tex_id)

        gl.texParameteri(target, GL_TEXTURE_MIN_FILTER, texture._gl_min_filter)
        gl.texParameteri(target, GL_TEXTURE_MAG_FILTER, texture._gl_mag_filter)

        data = js.Uint8Array.new(width * height * len(internal_format)) if blank_data else None
        texture._allocate(data)
        if blank_data:
            texture._mark_mipmap_valid(0)
        return texture

    def _allocate(self, data: None | js.Uint8Array) -> None:
        self._gl.texImage2D(self.target, 0,
                             self._gl_internal_format,
                             self.width, self.height,
                             0,
                             _get_base_format(self.internal_format),
                             GL_UNSIGNED_BYTE,
                             data)
        self._gl.flush()

    def _attach_texture_to_fbo(self, z: int = 0, level: int = 0) -> None:
        self._gl.framebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self._handle, level)

    def fetch(self, z: int = 0, level: int = 0) -> ImageData:
        """Fetch the image data of this texture from the GPU.

        Bind the texture, and read the pixel data back from the GPU.
        This can be a somewhat costly operation.
        Modifying the returned ImageData object has no effect on the
        texture itself. Uploading ImageData back to the GPU/texture
        can be done with the :py:meth:`~Texture.upload` method.

        Args:
            z:
                For 3D textures, the image slice to retrieve.
            level:
                The mipmap level of the texture to retrieve.
        """
        self._gl.bindTexture(self.target, self._handle)

        # Always extract complete RGBA data.  Could check internalformat
        # to only extract used channels. XXX
        fmt = 'RGBA'
        gl_format = GL_RGBA

        buffer_size = self.width * self.height * len(fmt)

        self._gl.pixelStorei(GL_PACK_ALIGNMENT, 1)
        fbo = self._gl.createFramebuffer()
        self._gl.bindFramebuffer(GL_FRAMEBUFFER, fbo)
        self._attach_texture_to_fbo(z, level)

        if self._gl.checkFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            raise Exception("Framebuffer is incomplete.")

        pixel_buf = js.Uint8Array.new(buffer_size)
        self._gl.readPixels(0, 0, self.width, self.height, gl_format, GL_UNSIGNED_BYTE, pixel_buf)
        self._gl.bindFramebuffer(GL_FRAMEBUFFER, None)
        self._gl.deleteFramebuffer(fbo)

        data = ImageData(self.width, self.height, fmt, pixel_buf)
        return data

class WebGLTextureRegion(_TextureRegionShared, WebGLTexture):
    """A rectangular region of a texture, presented as if it were a separate texture."""

    def __init__(self, x: int, y: int, z: int, width: int, height: int, owner: Texture):
        super().__init__(owner._context, width, height, owner.handle, owner.tex_type, owner.internal_format,
                         owner.internal_format_size, owner.internal_format_type, owner.filters, owner.address_mode,
                         owner.anisotropic_level, key=owner.key)
        self._init_region(x, y, z, width, height, owner)


WebGLTexture.region_class = WebGLTextureRegion


class WebGLTextureStreamer(TextureStreamer):
    """WebGL texture streamer with reusable pixel transfer buffers."""

    def get_backend_pixel_unpack_buffer(self, size: int) -> WebGLPixelUnpackBufferObject:
        return WebGLPixelUnpackBufferObject(self.context, size)

    def get_backend_pixel_pack_buffer(self, size: int) -> WebGLPixelPackBufferObject:
        return WebGLPixelPackBufferObject(self.context, size)


class WebGLTexture3D(_Texture3DShared[WebGLTextureRegion], WebGLTexture, UniformTextureSequence[WebGLTextureRegion]):
    """A texture with more than one image slice.

    Use the :py:meth:`create_for_images` or :py:meth:`create_for_image_grid`
    classmethod to construct a Texture3D.
    """

    item_width: int = 0
    item_height: int = 0
    items: tuple

    @classmethod
    def create_for_images(cls, images: Sequence[ImageData],
                          internal_format_size: int = 8,
                          internal_format_type: str = "b",
                          filters: TextureFilter | tuple[TextureFilter, TextureFilter] | None = None,
                          address_mode: AddressMode = AddressMode.REPEAT,
                          anisotropic_level: int = 0,
                          context: SurfaceContext | None = None) -> WebGLTexture3D:
        if not images:
            raise ImageException("At least one image is required.")
        ctx = cast("WebGL2SurfaceContext", context or pyglet.graphics.api.core.current_context)
        gl = ctx.gl
        item_width = images[0].width
        item_height = images[0].height
        pixel_fmt = images[0].format
        internal_format = ComponentFormat(pixel_fmt)

        if not all(img.width == item_width and img.height == item_height for img in images):
            raise ImageException('Images do not have same dimensions.')

        tex_id = gl.createTexture()
        target = texture_map[TextureType.TYPE_3D]
        gl.bindTexture(target, tex_id)
        texture = cls(ctx, item_width, item_height, tex_id, TextureType.TYPE_3D, internal_format, internal_format_size,
                             internal_format_type, filters, address_mode, anisotropic_level)
        gl.texParameteri(target, GL_TEXTURE_MIN_FILTER, texture._gl_min_filter)
        gl.texParameteri(target, GL_TEXTURE_MAG_FILTER, texture._gl_mag_filter)

        texture.images = len(images)

        size = (texture.width * texture.height * texture.images * len(internal_format))
        data = js.Uint8Array.new(size)
        gl.pixelStorei(GL_UNPACK_ALIGNMENT, 1)
        texture._allocate(data)

        items = []
        for i, image in enumerate(images):
            item = cls.region_class(0, 0, i, item_width, item_height, texture)
            items.append(item)
            texture.upload(image, 0, 0, z=i)
        gl.flush()

        texture.items = items
        texture.item_width = item_width
        texture.item_height = item_height
        return texture

    def _allocate(self, data: None | js.Uint8Array) -> None:
        self._gl.texImage3D(
            self.target,
            0,
            self._gl_internal_format,
            self.width,
            self.height,
            self.images,
            0,
            _get_base_format(self.internal_format),
            GL_UNSIGNED_BYTE,
            data,
        )

    def upload(self, image: ImageData | ImageDataRegion, x: int, y: int, z: int, level: int = 0) -> None:
        WebGLTexture.upload(self, image, x, y, z, level=level)

    def _get_mipmap_depth(self, level: int) -> int:
        depth = max(1, int(self.images))
        return max(1, depth >> level)

    def _allocate_mipmap_level(self, level: int, width: int, height: int, depth: int,
                               data_size: int | None) -> None:
        data = js.Uint8Array.new(data_size) if data_size is not None else None
        self._gl.texImage3D(
            self.target,
            level,
            self._gl_internal_format,
            width,
            height,
            depth,
            0,
            _get_base_format(self.internal_format),
            GL_UNSIGNED_BYTE,
            data,
        )

    def _attach_texture_to_fbo(self, z: int = 0, level: int = 0) -> None:
        self._gl.framebufferTextureLayer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, self._handle, level, z)

    def _bind_sequence_texture(self) -> None:
        self._gl.bindTexture(self.target, self._handle)

    @classmethod
    def create_from_image(cls, image_data: ImageData | ImageDataRegion,
                          tex_type: TextureType = TextureType.TYPE_3D,
                          internal_format_size: int = 8,
                          filters: TextureFilter | tuple[TextureFilter, TextureFilter] | None = None,
                          address_mode: AddressMode = AddressMode.REPEAT,
                          anisotropic_level: int = 0,
                          context: SurfaceContext | None = None) -> WebGLTexture3D:
        """Create a one image layer texture from an image."""
        if tex_type != TextureType.TYPE_3D:
            raise ImageException("Texture3D requires tex_type=TextureType.TYPE_3D.")
        return cls.create_for_images(
            [image_data], internal_format_size=internal_format_size, internal_format_type=image_data.data_type,
            filters=filters, address_mode=address_mode, anisotropic_level=anisotropic_level, context=context,
        )


class WebGLTextureArrayRegion(WebGLTextureRegion):
    """A region of a TextureArray, presented as if it were a separate texture."""

    def __repr__(self):
        return f"{self.__class__.__name__}(handle={self._handle}, size={self.width}x{self.height}, layer={self.z})"


class WebGLTextureArray(_TextureArrayShared[WebGLTextureArrayRegion], WebGLTexture, UniformTextureSequence[WebGLTextureArrayRegion]):
    items: list[WebGLTextureArrayRegion]

    def __init__(self, context: WebGL2SurfaceContext, width, height, tex_id, max_depth,
                 internal_format: ComponentFormat = ComponentFormat.RGBA,
                 internal_format_size: int = 8,
                 internal_format_type: str = "b",
                 filters: TextureFilter | tuple[TextureFilter, TextureFilter] | None = None,
                 address_mode: AddressMode = AddressMode.REPEAT,
                 anisotropic_level: int = 0):
        super().__init__(context, width, height, tex_id, TextureType.TYPE_2D_ARRAY, internal_format, internal_format_size,
                  internal_format_type, filters, address_mode, anisotropic_level)
        self.max_depth = max_depth
        self.items = []

    @classmethod
    def create(cls, width: int, height: int,
               tex_type: TextureType = TextureType.TYPE_2D_ARRAY,
               internal_format: ComponentFormat = ComponentFormat.RGBA,
               internal_format_size: int = 8,
               internal_format_type: str = "B",
               filters: TextureFilter | tuple[TextureFilter, TextureFilter] | None = None,
               address_mode: AddressMode = AddressMode.REPEAT,
               anisotropic_level: int = 0,
               blank_data: bool = False,
               immutable: bool = False,
               mipmap_levels: int = 1,
               context: SurfaceContext | None = None,
               *, max_depth: int = 256) -> WebGLTextureArray:
        """Create an empty texture array with capacity for ``max_depth`` layers."""
        if tex_type != TextureType.TYPE_2D_ARRAY:
            raise ImageException("TextureArray requires tex_type=TextureType.TYPE_2D_ARRAY.")
        ctx = cast("WebGL2SurfaceContext", context or pyglet.graphics.api.core.current_context)
        if not 1 <= max_depth <= ctx.info.MAX_ARRAY_TEXTURE_LAYERS:
            raise ImageException(f"Array depth must be between 1 and {ctx.info.MAX_ARRAY_TEXTURE_LAYERS}.")
        if immutable:
            raise NotImplementedError("Immutable texture array creation is not implemented.")
        if width <= 0 or height <= 0:
            raise ImageException("Texture dimensions must be positive.")
        if mipmap_levels != 1:
            raise NotImplementedError("Explicit mipmap allocation is not implemented by the WebGL backend.")
        texture = cls(
            context=ctx, width=width, height=height, tex_id=ctx.gl.createTexture(), max_depth=max_depth,
            internal_format=internal_format, internal_format_size=internal_format_size,
            internal_format_type=internal_format_type, filters=filters, address_mode=address_mode,
            anisotropic_level=anisotropic_level,
        )
        texture.bind()
        ctx.gl.texParameteri(texture.target, GL_TEXTURE_MIN_FILTER, texture._gl_min_filter)
        ctx.gl.texParameteri(texture.target, GL_TEXTURE_MAG_FILTER, texture._gl_mag_filter)
        data = js.Uint8Array.new(width * height * max_depth * len(internal_format)) if blank_data else None
        ctx.gl.pixelStorei(GL_UNPACK_ALIGNMENT, 1)
        texture._allocate(data)
        if blank_data:
            texture._mark_mipmap_valid(0)
        return texture

    @classmethod
    def create_for_images(cls, images: Sequence[ImageData],
                          internal_format_size: int = 8,
                          internal_format_type: str = "b",
                          filters: TextureFilter | tuple[TextureFilter, TextureFilter] | None = None,
                          address_mode: AddressMode = AddressMode.REPEAT,
                          anisotropic_level: int = 0,
                          context: SurfaceContext | None = None,
                          *, max_depth: int | None = None) -> WebGLTextureArray:
        """Create an array from equally sized images, with optional layer capacity."""
        if not images:
            raise ImageException("At least one image is required.")
        item_width, item_height = images[0].width, images[0].height
        if not all(image.width == item_width and image.height == item_height for image in images):
            raise ImageException("Images do not have same dimensions.")
        if max_depth is not None and max_depth < len(images):
            raise TextureArrayDepthExceeded("The images exceed the requested array capacity.")
        texture = cls.create(
            width=item_width, height=item_height,
            internal_format=ComponentFormat(images[0].format), internal_format_size=internal_format_size,
            internal_format_type=internal_format_type, filters=filters, address_mode=address_mode,
            anisotropic_level=anisotropic_level, context=context,
            max_depth=max_depth if max_depth is not None else len(images),
        )
        texture.images = len(images)
        texture.allocate(*images)
        texture.item_width, texture.item_height = item_width, item_height
        return texture

    def upload(self, image: ImageData | ImageDataRegion, x: int, y: int, z: int, level: int = 0) -> None:
        WebGLTexture.upload(self, image, x, y, z, level=level)

    def _attach_texture_to_fbo(self, z: int = 0, level: int = 0) -> None:
        self._gl.framebufferTextureLayer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, self._handle, level, z)

    def _allocate(self, data: None | js.Uint8Array) -> None:
        self._gl.texImage3D(
            self.target,
            0,
            self._gl_internal_format,
            self.width,
            self.height,
            self.max_depth,
            0,
            _get_base_format(self.internal_format),
            GL_UNSIGNED_BYTE,
            data,
        )

    def _get_mipmap_depth(self, level: int) -> int:
        return max(1, int(self.max_depth))

    def _allocate_mipmap_level(self, level: int, width: int, height: int, depth: int,
                               data_size: int | None) -> None:
        data = js.Uint8Array.new(data_size) if data_size is not None else None
        self._gl.texImage3D(
            self.target,
            level,
            self._gl_internal_format,
            width,
            height,
            self.max_depth,
            0,
            _get_base_format(self.internal_format),
            GL_UNSIGNED_BYTE,
            data,
        )

    def _generate_mipmaps(self) -> None:
        self._gl.generateMipmap(self.target)
        self._gl.flush()

    def _bind_sequence_texture(self) -> None:
        self._gl.bindTexture(self.target, self._handle)

    def _allocate_image(self, image: ImageData, layer: int) -> None:
        self.upload(image, 0, 0, layer)

    @classmethod
    def create_from_image(cls, image_data: ImageData | ImageDataRegion,
                          tex_type: TextureType = TextureType.TYPE_2D_ARRAY,
                          internal_format_size: int = 8,
                          filters: TextureFilter | tuple[TextureFilter, TextureFilter] | None = None,
                          address_mode: AddressMode = AddressMode.REPEAT,
                          anisotropic_level: int = 0,
                          context: SurfaceContext | None = None) -> WebGLTextureArray:
        """Create a one-layer texture from an image."""
        if tex_type != TextureType.TYPE_2D_ARRAY:
            raise ImageException("TextureArray requires tex_type=TextureType.TYPE_2D_ARRAY.")
        return cls.create_for_images(
            [image_data], internal_format_size=internal_format_size, internal_format_type=image_data.data_type,
            filters=filters, address_mode=address_mode, anisotropic_level=anisotropic_level, context=context,
        )

WebGLTextureArray.region_class = WebGLTextureArrayRegion
WebGLTextureArrayRegion.region_class = WebGLTextureArrayRegion


class WebGLTextureGrid(TextureGrid):
    pass
