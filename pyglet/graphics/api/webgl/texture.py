from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Iterator, Literal, Union

import js
import pyodide

import pyglet
from pyglet.enums import TextureFilter, TextureType, ComponentFormat, \
    AddressMode
from pyglet.graphics.api.webgl.enums import texture_map
from pyglet.graphics.api.webgl.gl import (
    GL_BGR,
    GL_BGR_INTEGER,
    GL_BGRA,
    GL_BGRA_INTEGER,
    GL_COLOR_ATTACHMENT0,
    GL_DEPTH_COMPONENT,
    GL_DEPTH_STENCIL,
    GL_FRAMEBUFFER,
    GL_FRAMEBUFFER_COMPLETE,
    GL_LINEAR_MIPMAP_LINEAR,
    GL_PACK_ALIGNMENT,
    GL_READ_WRITE,
    GL_RED,
    GL_RED_INTEGER,
    GL_RG,
    GL_RG_INTEGER,
    GL_RGB,
    GL_RGB_INTEGER,
    GL_RGBA,
    GL_RGBA8,  # noqa: F401
    GL_RGBA32F,
    GL_RGBA_INTEGER,
    GL_TEXTURE0,
    GL_TEXTURE_2D,
    GL_TEXTURE_2D_ARRAY,
    GL_TEXTURE_3D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_UNPACK_ALIGNMENT,
    GL_UNPACK_ROW_LENGTH,
    GL_UNPACK_SKIP_PIXELS,
    GL_UNPACK_SKIP_ROWS,
    GL_UNSIGNED_BYTE,
)
from pyglet.graphics.texture import TextureBase, TextureRegionBase, UniformTextureSequence, TextureArraySizeExceeded, \
    TextureArrayDepthExceeded
from pyglet.image.base import (
    CompressedImageData,
    ImageData,
    ImageDataRegion,
    ImageException,
    ImageGrid,
    T,
    _AbstractGrid,
    _AbstractImage,
)

# from pyglet.image.buffer import Framebuffer, Renderbuffer, get_max_color_attachments

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
    'RGBA': 'GL_RGBA',
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


if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Callable, Literal

    from pyglet.graphics.api.webgl import OpenGLSurfaceContext
    from pyglet.graphics.api.webgl.webgl_js import WebGL2RenderingContext

_api_pixel_formats = {
    'R': GL_RED,
    'RG': GL_RG,
    'RGB': GL_RGB,
    'BGR': GL_BGR,
    'RGBA': GL_RGBA,
    'BGRA': GL_BGRA,
    'RI': GL_RED_INTEGER,
    'RGI': GL_RG_INTEGER,
    'RGBI': GL_RGB_INTEGER,
    'BGRI': GL_BGR_INTEGER,
    'RGBAI': GL_RGBA_INTEGER,
    'BGRAI': GL_BGRA_INTEGER,
    'D': GL_DEPTH_COMPONENT,
    'DS': GL_DEPTH_STENCIL,
}


def get_max_texture_size() -> int:
    """Query the maximum texture size available"""
    return pyglet.graphics.api.core.current_context.get_info().MAX_ARRAY_TEXTURE_LAYERS


def get_max_array_texture_layers() -> int:
    return pyglet.graphics.api.core.current_context.get_info().MAX_ARRAY_TEXTURE_LAYERS


def _get_gl_format_and_type(fmt: str):
    fmt = _api_pixel_formats.get(fmt)
    if fmt:
        return fmt, GL_UNSIGNED_BYTE  # Eventually support others through ImageData.

    return None, None


class GLCompressedImageData(CompressedImageData):
    """Compressed image data suitable for direct uploading to GPU."""

    # TODO: Finish compressed.

    _current_texture = None
    _current_mipmap_texture = None

    def __init__(
        self,
        width: int,
        height: int,
        gl_format: int,
        data: bytes,
        extension: str | None = None,
        decoder: Callable[[bytes, int, int], _AbstractImage] | None = None,
    ) -> None:
        """Construct a CompressedImageData with the given compressed data.

        Args:
            width:
                The width of the image.
            height:
                The height of the image.
            gl_format:
                GL constant giving the format of the compressed data.
                For example: ``GL_COMPRESSED_RGBA_S3TC_DXT5_EXT``.
            data:
                An array of bytes containing the compressed image data.
            extension:
                If specified, gives the name of a GL extension to check for
                before creating a texture.
            decoder:
                An optional fallback function used to decode the compressed data.
                This function is called if the required extension is not present.
        """
        super().__init__(width, height)
        self.data = data
        self.gl_format = gl_format
        self.extension = extension
        self.decoder = decoder
        self.mipmap_data = []

    def set_mipmap_data(self, level: int, data: bytes) -> None:
        """Set compressed image data for a mipmap level.

        Supplied data gives a compressed image for the given mipmap level.
        This image data must be in the same format as was used in the
        constructor. The image data must also be of the correct dimensions for
        the level (i.e., width >> level, height >> level); but this is not checked.
        If *any* mipmap levels are specified, they are used; otherwise, mipmaps for
        ``mipmapped_texture`` are generated automatically.
        """
        # Extend mipmap_data list to required level
        self.mipmap_data += [None] * (level - len(self.mipmap_data))
        self.mipmap_data[level - 1] = data

    def _have_extension(self) -> bool:
        from pyglet.graphics.api import core

        return self.extension is None or core.have_extension(self.extension)

    def get_texture(self) -> TextureBase:
        if self._current_texture:
            return self._current_texture

        texture = TextureBase.create(self.width, self.height, blank_data=False)

        if self.anchor_x or self.anchor_y:
            texture.anchor_x = self.anchor_x
            texture.anchor_y = self.anchor_y

        gl = pyglet.graphics.api.core.current_context.gl
        gl.bindTexture(texture.target, texture.id)
        gl.texParameteri(texture.target, GL_TEXTURE_MIN_FILTER, texture.min_filter)
        gl.texParameteri(texture.target, GL_TEXTURE_MAG_FILTER, texture.mag_filter)

        if self._have_extension():
            gl.compressedTexImage2D(
                texture.target, texture.level, self.gl_format, self.width, self.height, 0, len(self.data), self.data,
            )
        elif self.decoder:
            image = self.decoder(self.data, self.width, self.height)
            texture = image.get_texture()
            assert texture.width == self.width
            assert texture.height == self.height
        else:
            msg = f"No extension or fallback decoder is available to decode {self}"
            raise ImageException(msg)

        gl.flush()
        self._current_texture = texture
        return texture

    def get_mipmapped_texture(self) -> TextureBase:
        if self._current_mipmap_texture:
            return self._current_mipmap_texture

        if not self._have_extension():
            # TODO: mip-mapped software decoded compressed textures.
            #       For now, just return a non-mipmapped texture.
            return self.get_texture()

        texture = TextureBase.create(self.width, self.height, GL_TEXTURE_2D, None)

        if self.anchor_x or self.anchor_y:
            texture.anchor_x = self.anchor_x
            texture.anchor_y = self.anchor_y

        gl = pyglet.graphics.api.core.current_context.gl
        gl.bindTexture(texture.target, texture.id)

        gl.texParameteri(texture.target, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)

        if not self.mipmap_data:
            gl.generateMipmap(texture.target)

        gl.compressedTexImage2D(
            texture.target, texture.level, self.gl_format, self.width, self.height, 0, len(self.data), self.data,
        )

        width, height = self.width, self.height
        level = 0
        for data in self.mipmap_data:
            width >>= 1
            height >>= 1
            level += 1
            gl.compressedTexImage2D(texture.target, level, self.gl_format, width, height, 0, len(data), data)

        gl.flush()

        self._current_mipmap_texture = texture
        return texture

    def blit_to_texture(self, target: int, level: int, x: int, y: int, z: int, internalformat: int = None):
        if not self._have_extension():
            raise ImageException(f"{self.extension} is required to decode {self}")

        # TODO: use glCompressedTexImage2D/3D if `internalformat` is specified.

        gl = pyglet.graphics.api.core.current_context.gl
        if target == GL_TEXTURE_3D:
            gl.compressedTexSubImage3D(
                target,
                level,
                x - self.anchor_x,
                y - self.anchor_y,
                z,
                self.width,
                self.height,
                1,
                self.gl_format,
                len(self.data),
                self.data,
            )
        else:
            gl.compressedTexSubImage2D(
                target,
                level,
                x - self.anchor_x,
                y - self.anchor_y,
                self.width,
                self.height,
                self.gl_format,
                len(self.data),
                self.data,
            )

    def get_image_data(self) -> CompressedImageData:
        return self

    def get_region(self, x: int, y: int, width: int, height: int) -> _AbstractImage:
        raise NotImplementedError(f"Not implemented for {self}")

    def blit(self, x: int, y: int, z: int = 0) -> None:
        self.get_texture().blit(x, y, z)

    def blit_into(self, source, x: int, y: int, z: int) -> None:
        raise NotImplementedError(f"Not implemented for {self}")


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


class Texture(TextureBase):
    """An image loaded into GPU memory.

    Typically, you will get an instance of Texture by accessing calling
    the ``get_texture()`` method of any AbstractImage class (such as ImageData).
    """

    region_class: TextureRegion  # Set to TextureRegion after it's defined
    """The class to use when constructing regions of this texture.
     The class should be a subclass of TextureRegion.
    """

    tex_coords = (0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0)
    """12-tuple of float, named (u1, v1, r1, u2, v2, r2, ...).
    ``u, v, r`` give the 3D texture coordinates for vertices 1-4. The vertices
    are specified in the order bottom-left, bottom-right, top-right and top-left.
    """

    tex_coords_order: tuple[int, int, int, int] = (0, 1, 2, 3)
    """The default vertex winding order for a quad.
    This defaults to counter-clockwise, starting at the bottom-left.
    """

    # If this backend supports pixel data conversion.
    # If False, will force data to be RGBA, even if CPU is used to order it.
    pixel_conversion = True

    level: int = 0
    """The mipmap level of this texture."""

    images = 1

    default_filters: TextureFilter | tuple[TextureFilter, TextureFilter] = TextureFilter.LINEAR, TextureFilter.LINEAR
    """The default minification and magnification filters, as a tuple.
    Both default to LINEAR. If a texture is created without specifying
    a filter, these defaults will be used. 
    """

    x: int = 0
    y: int = 0
    z: int = 0

    _ctx: OpenGLSurfaceContext
    _gl: WebGL2RenderingContext

    def __init__(self, context: OpenGLSurfaceContext, width: int, height: int, tex_id: int,
                 tex_type: TextureType = TextureType.TYPE_2D,
                 internal_format: ComponentFormat = ComponentFormat.RGBA,
                 internal_format_size: int = 8,
                 internal_format_type: str = "B",
                 filters: TextureFilter | tuple[TextureFilter, TextureFilter] | None = None,
                 address_mode: AddressMode = AddressMode.REPEAT,
                 anisotropic_level: int = 0):
        super().__init__(width, height, tex_id, tex_type, internal_format, internal_format_size, internal_format_type,
                         filters, address_mode, anisotropic_level)
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
        self._gl.deleteTexture(self.id)
        self.id = None

    def __del__(self):
        if self.id is not None:
            try:
                self._context.delete_texture(self.id)
                self.id = None
            except (AttributeError, ImportError):
                pass  # Interpreter is shutting down

    def bind(self, texture_unit: int = 0) -> None:
        """Bind to a specific Texture Unit by number."""
        self._gl.activeTexture(GL_TEXTURE0 + texture_unit)
        self._gl.bindTexture(self.target, self.id)

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

    @staticmethod
    def _get_image_alignment(image_data: ImageData) -> tuple[int, int]:
        """Image alignment and row length information on an Image to upload.

        Args:
            image_data: The image data to get the alignment from.

        Returns:
            (align, row_length)
                align: 1, 2, 4, or 8 \
                row_length: 0 if tightly packed.
        """
        components = len(image_data.format)
        width = image_data.width
        packed_row_bytes = width * components
        pitch = abs(image_data._current_pitch)
        if packed_row_bytes % 8 == 0:
            align = 8
        elif packed_row_bytes % 4 == 0:
            align = 4
        elif packed_row_bytes % 2 == 0:
            align = 2
        else:
            align = 1

        if pitch == packed_row_bytes:
            row_length = 0
        else:
            row_length = pitch // components

        return align, row_length
    @classmethod
    def create_from_image(cls,
                          image_data: ImageData | ImageDataRegion,
                          tex_type: TextureType = TextureType.TYPE_2D,
                          internal_format_size: int = 8,
                          filters: TextureFilter | tuple[TextureFilter, TextureFilter] | None = None,
                          address_mode: AddressMode = AddressMode.REPEAT,
                          anisotropic_level: int = 0,
                          context: OpenGLSurfaceContext | None = None,
                          ) -> Texture:
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
        ctx = context or pyglet.graphics.api.core.current_context
        gl = pyglet.graphics.api.core.current_context.gl

        tex_id = gl.createTexture()
        target = texture_map[tex_type]
        gl.bindTexture(target, tex_id)

        texture = cls(ctx, image_data.width, image_data.height, tex_id, tex_type,
                      ComponentFormat(image_data.format), internal_format_size, image_data.data_type, filters,
                      address_mode, anisotropic_level)

        gl.texParameteri(target, GL_TEXTURE_MIN_FILTER, texture._gl_min_filter)
        gl.texParameteri(target, GL_TEXTURE_MAG_FILTER, texture._gl_mag_filter)

        pixel_fmt = image_data.format
        image_bytes = image_data.get_bytes(pixel_fmt, image_data.width * len(pixel_fmt))
        buffer = pyodide.ffi.to_js(memoryview(image_bytes))
        js_array = js.Uint8Array.new(buffer)
        gl_pfmt, gl_type = _get_pixel_format(image_data)

        align, row_length = texture._get_image_alignment(image_data)

        gl.pixelStorei(GL_PACK_ALIGNMENT, align)
        gl.pixelStorei(GL_UNPACK_ROW_LENGTH, row_length)

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
               blank_data: bool = True, context: OpenGLSurfaceContext | None = None) -> TextureBase:
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
            context:
                A specific OpenGL Surface context, otherwise the current active context.

        Returns:
            A currently bound texture.
        """
        ctx = context or pyglet.graphics.api.core.current_context
        gl = ctx.gl

        tex_id = gl.createTexture()
        target = texture_map[tex_type]

        texture = cls(ctx, width, height, tex_id, tex_type, internal_format, internal_format_size, internal_format_type, filters, address_mode, anisotropic_level)
        gl.bindTexture(target, tex_id)

        gl.texParameteri(target, GL_TEXTURE_MIN_FILTER, texture._gl_min_filter)
        gl.texParameteri(target, GL_TEXTURE_MAG_FILTER, texture._gl_mag_filter)

        data = js.Uint8Array.new(width * height * len(internal_format)) if blank_data else None
        texture._allocate(data)
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

    def _attach_texture_to_fbo(self, z: int = 0) -> None:
        self._gl.framebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.id, self.level)

    def fetch(self, z: int = 0) -> ImageData:
        """Fetch the image data of this texture from the GPU.

        Bind the texture, and read the pixel data back from the GPU.
        This can be a somewhat costly operation.
        Modifying the returned ImageData object has no effect on the
        texture itself. Uploading ImageData back to the GPU/texture
        can be done with the :py:meth:`~Texture.upload` method.

        Args:
            z:
                For 3D textures, the image slice to retrieve.
        """
        self._gl.bindTexture(self.target, self.id)

        # Always extract complete RGBA data.  Could check internalformat
        # to only extract used channels. XXX
        fmt = 'RGBA'
        gl_format = GL_RGBA

        buffer_size = self.width * self.height * self.images * len(fmt)

        self._gl.pixelStorei(GL_PACK_ALIGNMENT, 1)
        fbo = self._gl.createFramebuffer()
        self._gl.bindFramebuffer(GL_FRAMEBUFFER, fbo)
        self._attach_texture_to_fbo(z)

        if self._gl.checkFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            raise Exception("Framebuffer is incomplete.")

        pixel_buf = js.Uint8Array(buffer_size)
        self._gl.readPixels(0, 0, self.width, self.height, gl_format, GL_UNSIGNED_BYTE, pixel_buf)
        self._gl.bindFramebuffer(GL_FRAMEBUFFER, None)
        self._gl.deleteFramebuffer(fbo)

        data = ImageData(self.width, self.height, fmt, pixel_buf)
        return data

    def get_image_data(self, z: int = 0) -> ImageData:
        """Get the image data of this texture.

        Bind the texture, and read the pixel data back from the GPU.
        This can be a somewhat costly operation.
        Modifying the returned ImageData object has no effect on the
        texture itself. Uploading ImageData back to the GPU/texture
        can be done with the :py:meth:`~Texture.upload` method.

        Args:
            z:
                For 3D textures, the image slice to retrieve.
        """
        return self.fetch(z)

    def _apply_region_unpack(self, image_data: ImageData | ImageDataRegion) -> None:
        if isinstance(image_data, ImageDataRegion):
            self._gl.pixelStorei(GL_UNPACK_SKIP_PIXELS, image_data.x)
            self._gl.pixelStorei(GL_UNPACK_SKIP_ROWS, image_data.y)

    def _default_region_unpack(self, image_data: ImageData | ImageDataRegion) -> None:
        if isinstance(image_data, ImageDataRegion):
            self._gl.pixelStorei(GL_UNPACK_SKIP_PIXELS, 0)
            self._gl.pixelStorei(GL_UNPACK_SKIP_ROWS, 0)

    def upload(self, image_data: ImageData | ImageDataRegion, x: int, y: int, z: int) -> None:
        """Upload image data into the Texture at specific coordinates.

        You must have this texture bound before uploading data.

        The image's anchor point will be aligned to the given ``x`` and ``y``
        coordinates.  If this texture is a 3D texture, the ``z``
        parameter gives the image slice to blit into.
        """
        x -= self.anchor_x
        y -= self.anchor_y

        data_format = image_data.format
        data_pitch = abs(image_data._current_pitch)

        fmt, gl_type = _get_pixel_format(image_data)

        # Get data in required format (hopefully will be the same format it's already
        # in, unless that's an obscure format, upside-down or the driver is old).
        data = image_data.convert(data_format, data_pitch)

        js_array = js.Uint8Array.new(data)

        if data_pitch & 0x1:
            align = 1
        elif data_pitch & 0x2:
            align = 2
        else:
            align = 4
        row_length = data_pitch // len(data_format)

        gl = self._gl
        gl.pixelStorei(GL_UNPACK_ALIGNMENT, align)
        gl.pixelStorei(GL_UNPACK_ROW_LENGTH, row_length)
        self._apply_region_unpack(image_data)

        if self.target == GL_TEXTURE_3D or self.target == GL_TEXTURE_2D_ARRAY:
            gl.texSubImage3D(
                self.target, self.level, x, y, z, image_data.width, image_data.height, 1, fmt, gl_type, js_array,
            )
        else:
            gl.texSubImage2D(self.target, self.level, x, y, image_data.width, image_data.height, fmt, gl_type, js_array)

        gl.pixelStorei(GL_UNPACK_ROW_LENGTH, 0)
        self._default_region_unpack(image_data)

        # Flush image upload before data gets GC'd:
        gl.flush()

    def get_texture(self) -> TextureBase:
        return self

    def get_mipmapped_texture(self) -> TextureBase:
        raise NotImplementedError(f"Not implemented for {self}.")

    def get_region(self, x: int, y: int, width: int, height: int) -> TextureRegionBase:
        return self.region_class(x, y, 0, width, height, self)

    def get_transform(
        self, flip_x: bool = False, flip_y: bool = False, rotate: Literal[0, 90, 180, 270, 360] = 0,
    ) -> TextureRegionBase:
        """Create a copy of this image applying a simple transformation.

        The transformation is applied to the texture coordinates only;
        :py:meth:`~pyglet.image.AbstractImage.get_image_data` will return the
        untransformed data. The transformation is applied around the anchor point.

        Args:
            flip_x:
                If True, the returned image will be flipped horizontally.
            flip_y:
                If True, the returned image will be flipped vertically.
            rotate:
                Degrees of clockwise rotation of the returned image.  Only
                90-degree increments are supported.
        """
        transform = self.get_region(0, 0, self.width, self.height)
        bl, br, tr, tl = 0, 1, 2, 3
        transform.anchor_x = self.anchor_x
        transform.anchor_y = self.anchor_y
        if flip_x:
            bl, br, tl, tr = br, bl, tr, tl
            transform.anchor_x = self.width - self.anchor_x
        if flip_y:
            bl, br, tl, tr = tl, tr, bl, br
            transform.anchor_y = self.height - self.anchor_y
        rotate %= 360
        if rotate < 0:
            rotate += 360
        if rotate == 0:
            pass
        elif rotate == 90:
            bl, br, tr, tl = br, tr, tl, bl
            transform.anchor_x, transform.anchor_y = transform.anchor_y, transform.width - transform.anchor_x
        elif rotate == 180:
            bl, br, tr, tl = tr, tl, bl, br
            transform.anchor_x = transform.width - transform.anchor_x
            transform.anchor_y = transform.height - transform.anchor_y
        elif rotate == 270:
            bl, br, tr, tl = tl, bl, br, tr
            transform.anchor_x, transform.anchor_y = transform.height - transform.anchor_y, transform.anchor_x
        else:
            raise ImageException("Only 90 degree rotations are supported.")
        if rotate in (90, 270):
            transform.width, transform.height = transform.height, transform.width
        transform._set_tex_coords_order(bl, br, tr, tl)
        return transform

    def _set_tex_coords_order(self, bl, br, tr, tl) -> None:
        tex_coords = (self.tex_coords[:3], self.tex_coords[3:6], self.tex_coords[6:9], self.tex_coords[9:])
        self.tex_coords = tex_coords[bl] + tex_coords[br] + tex_coords[tr] + tex_coords[tl]

        order = self.tex_coords_order
        self.tex_coords_order = (order[bl], order[br], order[tr], order[tl])

    @property
    def uv(self) -> tuple[float, float, float, float]:
        """Tuple containing the left, bottom, right, top 2D texture coordinates."""
        tex_coords = self.tex_coords
        return tex_coords[0], tex_coords[1], tex_coords[3], tex_coords[7]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, size={self.width}x{self.height})"


class TextureRegion(Texture):
    """A rectangular region of a texture, presented as if it were a separate texture."""

    def __init__(self, x: int, y: int, z: int, width: int, height: int, owner: TextureBase):
        super().__init__(owner._context, width, height, owner.id, owner.tex_type, owner.internal_format,
                         owner.internal_format_size, owner.internal_format_type, owner.filters, owner.address_mode,
                         owner.anisotropic_level)

        self.x = x
        self.y = y
        self.z = z
        self._width = width
        self._height = height
        self.owner = owner
        owner_u1 = owner.tex_coords[0]
        owner_v1 = owner.tex_coords[1]
        owner_u2 = owner.tex_coords[3]
        owner_v2 = owner.tex_coords[7]
        scale_u = owner_u2 - owner_u1
        scale_v = owner_v2 - owner_v1
        u1 = x / owner.width * scale_u + owner_u1
        v1 = y / owner.height * scale_v + owner_v1
        u2 = (x + width) / owner.width * scale_u + owner_u1
        v2 = (y + height) / owner.height * scale_v + owner_v1
        r = z / owner.images + owner.tex_coords[2]
        self.tex_coords = (u1, v1, r, u2, v1, r, u2, v2, r, u1, v2, r)

    def fetch(self, _z: int = 0) -> ImageDataRegion:
        image_data = self.owner.fetch(self.z)
        return image_data.get_region(self.x, self.y, self.width, self.height)

    def get_image_data(self):
        return self.fetch()

    def get_region(self, x: int, y: int, width: int, height: int) -> TextureRegionBase:
        x += self.x
        y += self.y
        region = self.region_class(x, y, self.z, width, height, self.owner)
        region._set_tex_coords_order(*self.tex_coords_order)
        return region

    def upload(self, source: _AbstractImage, x: int, y: int, z: int) -> None:
        assert source.width <= self._width and source.height <= self._height, f"{source} is larger than {self}"
        self.owner.blit_into(source, x + self.x, y + self.y, z + self.z)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.id},"
            f" size={self.width}x{self.height}, owner={self.owner.width}x{self.owner.height})"
        )

    def delete(self) -> None:
        """Deleting a TextureRegion has no effect. Operate on the owning texture instead."""

    def __del__(self):
        pass


Texture.region_class = TextureRegion


class Texture3D(Texture, UniformTextureSequence):
    """A texture with more than one image slice.

    Use the :py:meth:`create_for_images` or :py:meth:`create_for_image_grid`
    classmethod to construct a Texture3D.
    """

    item_width: int = 0
    item_height: int = 0
    items: tuple

    @classmethod
    def create_for_images(cls, images,
                 internal_format_size: int = 8,
                 internal_format_type: str = "b",
                 filters: TextureFilter | tuple[TextureFilter, TextureFilter] | None = None,
                 address_mode: AddressMode = AddressMode.REPEAT,
                 anisotropic_level: int = 0,
                 context: OpenGLSurfaceContext | None = None) -> Texture3D:
        ctx = context or pyglet.graphics.api.core.current_context
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

        base_image = images[0]
        if base_image.anchor_x or base_image.anchor_y:
            texture.anchor_x = base_image.anchor_x
            texture.anchor_y = base_image.anchor_y

        texture.images = len(images)

        size = (texture.width * texture.height * texture.images * len(internal_format))
        data = js.Uint8Array.new(size)
        texture._allocate(data)

        items = []
        for i, image in enumerate(images):
            item = cls.region_class(0, 0, i, item_width, item_height, texture)
            items.append(item)
            texture.upload(image, image.anchor_x, image.anchor_y, z=i)
        gl.flush()

        texture.items = items
        texture.item_width = item_width
        texture.item_height = item_height
        return texture

    def _allocate(self, data: None | js.Uint8Array) -> None:
        self._gl.texImage3D(self.target, 0,
                                   self._gl_internal_format,
                                   self.width, self.height, self.images,
                                   0,
                                   _get_base_format(self.internal_format),
                                   GL_UNSIGNED_BYTE,
                                   0)

    def _attach_texture_to_fbo(self, z: int = 0) -> None:
        self._gl.framebufferTextureLayer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, self.id, self.level, z)

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        return self.items[index]

    def __setitem__(self, index, value):
        if type(index) is slice:
            self._gl.bindTexture(self.target, self.id)

            for item, image in zip(self[index], value):
                self.upload(self, image, image.anchor_x, image.anchor_y, item.z)
        else:
            self.upload(value, value.anchor_x, value.anchor_y, self[index].z)

    def __iter__(self) -> Iterator[TextureRegionBase]:
        return iter(self.items)


class TextureArrayRegion(TextureRegion):
    """A region of a TextureArray, presented as if it were a separate texture."""

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, size={self.width}x{self.height}, layer={self.z})"


class TextureArray(Texture, UniformTextureSequence):
    items: list[TextureArrayRegion]

    def __init__(self, context: OpenGLSurfaceContext, width, height, tex_id, max_depth,
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
               max_depth: int = 256,
               internal_format: ComponentFormat = ComponentFormat.RGBA,
               internal_format_size: int = 8,
               internal_format_type: str = "b",
               filters: TextureFilter | tuple[TextureFilter, TextureFilter] | None = None,
               address_mode: AddressMode = AddressMode.REPEAT,
               anisotropic_level: int = 0,
               context: OpenGLSurfaceContext | None = None) -> TextureArray:
        """Create an empty TextureArray.

        You may specify the maximum depth, or layers, the Texture Array should have. This defaults
        to 256, but will be hardware and driver dependent.

        Args:
            width:
                Width of the texture.
            height:
                Height of the texture.
            descriptor:
                Texture description.
            max_depth:
                The number of layers in the texture array.

        .. versionadded:: 2.0
        """
        ctx = pyglet.graphics.api.core.current_context or context

        max_depth_limit = get_max_array_texture_layers()
        assert max_depth <= max_depth_limit, f"TextureArray max_depth supported is {max_depth_limit}."

        gl = ctx.gl

        tex_id = gl.createTexture()


        texture = cls(ctx, width, height, tex_id, max_depth, internal_format, internal_format_size,
                      internal_format_type, filters, address_mode, anisotropic_level)

        gl.bindTexture(texture.target, tex_id)
        gl.texParameteri(texture.target, GL_TEXTURE_MIN_FILTER, texture._gl_min_filter)
        gl.texParameteri(texture.target, GL_TEXTURE_MAG_FILTER, texture._gl_mag_filter)

        texture._allocate(None)
        return texture

    def _update_subregion(self, image_data: ImageData, x: int, y: int, z: int):
        data_pitch = abs(image_data._current_pitch)

        data = image_data.convert(image_data.format, data_pitch)

        fmt, gl_type = _get_pixel_format(image_data)

        self._gl.texSubImage3D(self.target, self.level,
                                      x, y, z,
                                      image_data.width, image_data.height, 1,
                                      fmt, gl_type,
                                      data)

    def _attach_texture_to_fbo(self, z: int = 0) -> None:
        self._gl.framebufferTextureLayer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, self.id, self.level, z)

    def _allocate(self, data: None | js.Uint8Array) -> None:
        self._gl.texImage3D(self.target, 0,
                                   self._gl_internal_format,
                                   self.width, self.height, self.max_depth,
                                   0,
                                   _get_base_format(self.internal_format),
                                   GL_UNSIGNED_BYTE,
                                   0)

    def _verify_size(self, image: _AbstractImage) -> None:
        if image.width > self.width or image.height > self.height:
            raise TextureArraySizeExceeded(
                f'Image ({image.width}x{image.height}) exceeds the size of the TextureArray ({self.width}x'
                f'{self.height})',
            )

    def add(self, image: pyglet.image.ImageData) -> TextureArrayRegion:
        if len(self.items) >= self.max_depth:
            raise TextureArrayDepthExceeded("TextureArray is full.")

        self._verify_size(image)
        start_length = len(self.items)
        item = self.region_class(0, 0, start_length, image.width, image.height, self)

        self.upload(image, image.anchor_x, image.anchor_y, start_length)
        self.items.append(item)
        return item

    def allocate(self, *images: _AbstractImage) -> list[TextureArrayRegion]:
        """Allocates multiple images at once."""
        if len(self.items) + len(images) > self.max_depth:
            raise TextureArrayDepthExceeded("The amount of images being added exceeds the depth of this TextureArray.")

        self._gl.bindTexture(self.target, self.id)

        start_length = len(self.items)
        for i, image in enumerate(images):
            self._verify_size(image)
            item = self.region_class(0, 0, start_length + i, image.width, image.height, self)
            self.items.append(item)
            image.blit_to_texture(self.target, self.level, image.anchor_x, image.anchor_y, start_length + i)

        return self.items[start_length:]

    @classmethod
    def create_for_image_grid(cls, grid) -> TextureArray:
        texture_array = cls.create(grid[0].width, grid[0].height,
                                   internal_format=ComponentFormat(grid[0].format),
                                   max_depth=len(grid))
        texture_array.allocate(*grid[:])
        return texture_array

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index) -> TextureArrayRegion:
        return self.items[index]

    def __setitem__(self, index, value) -> None:
        if type(index) is slice:
            self._gl.bindTexture(self.target, self.id)

            for old_item, image in zip(self[index], value):
                self._verify_size(image)
                item = self.region_class(0, 0, old_item.z, image.width, image.height, self)
                image.blit_to_texture(self.target, self.level, image.anchor_x, image.anchor_y, old_item.z)
                self.items[old_item.z] = item
        else:
            self._verify_size(value)
            item = self.region_class(0, 0, index, value.width, value.height, self)
            self.upload(value, value.anchor_x, value.anchor_y, index)
            self.items[index] = item

    def __iter__(self) -> Iterator[TextureRegionBase]:
        return iter(self.items)


TextureArray.region_class = TextureArrayRegion
TextureArrayRegion.region_class = TextureArrayRegion


class TextureGrid(_AbstractGrid[Union[Texture, TextureRegion]]):
    """A texture containing a regular grid of texture regions.

    To construct, create an :py:class:`~pyglet.image.ImageGrid` first::

        image_grid = ImageGrid(...)
        texture_grid = TextureGrid(image_grid)

    The texture grid can be accessed as a single texture, or as a sequence
    of :py:class:`~pyglet.graphics.TextureRegion`.  When accessing as a sequence, you can specify
    integer indexes, in which the images are arranged in rows from the
    bottom-left to the top-right::

        # assume the texture_grid is 3x3:
        current_texture = texture_grid[3] # get the middle-left image

    You can also specify tuples in the sequence methods, which are addressed
    as ``row, column``::

        # equivalent to the previous example:
        current_texture = texture_grid[1, 0]

    When using tuples in a slice, the returned sequence is over the
    rectangular region defined by the slice::

        # returns center, center-right, center-top, top-right images in that
        # order:
        images = texture_grid[(1,1):]
        # equivalent to
        images = texture_grid[(1,1):(3,3)]

    """

    def __init__(
        self,
        texture: Texture | TextureRegion,
        rows: int,
        columns: int,
        item_width: int,
        item_height: int,
        row_padding: int = 0,
        column_padding: int = 0,
    ) -> None:
        """Construct a grid for the given image.

        You can specify parameters for the grid, for example setting
        the padding between cells.  Grids are always aligned to the
        bottom-left corner of the image.

        Args:
            texture:
                A texture or region over which to construct the grid.
            rows:
                Number of rows in the grid.
            columns:
                Number of columns in the grid.
            item_width:
                Width of each column.  If unspecified, is calculated such
                that the entire texture width is used.
            item_height:
                Height of each row.  If unspecified, is calculated such that
                the entire texture height is used.
            row_padding:
                Pixels separating adjacent rows.  The padding is only
                inserted between rows, not at the edges of the grid.
            column_padding:
                Pixels separating adjacent columns.  The padding is only
                inserted between columns, not at the edges of the grid.
        """
        if isinstance(texture, TextureRegion):
            owner = texture.owner
        else:
            owner = texture

        item_width = item_width or (texture.width - column_padding * (columns - 1)) // columns
        item_height = item_height or (texture.height - row_padding * (rows - 1)) // rows
        self.texture = owner
        super().__init__(rows, columns, item_width, item_height, row_padding, column_padding)

    @classmethod
    def from_image_grid(cls, image_grid: ImageGrid) -> TextureGrid:
        texture = image_grid.image.get_texture()
        return cls(
            texture,
            image_grid.rows,
            image_grid.columns,
            image_grid.item_width,
            image_grid.item_height,
            image_grid.row_padding,
            image_grid.column_padding,
        )

    def _create_item(self, x: int, y: int, width: int, height: int) -> TextureRegion:
        return self.texture.get_region(x, y, width, height)

    def _update_item(self, existing_item: T, new_item: T) -> None:
        existing_item.upload(new_item, new_item.anchor_x, new_item.anchor_y, 0)
