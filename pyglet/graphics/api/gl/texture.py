from __future__ import annotations


from contextlib import contextmanager
from ctypes import byref, Array, sizeof
from typing import cast, Iterator, Sequence, TYPE_CHECKING

import pyglet
from pyglet.enums import TextureType, TextureFilter, ComponentFormat, AddressMode, GraphicsAPI
from pyglet.graphics import GraphicsAPIError, UnsupportedBackendError
from pyglet.graphics.api.gl import OpenGLSurfaceContext, GL_COMPRESSED_RGB8_ETC2
from pyglet.graphics.api.base import SurfaceContext
from pyglet.graphics.api.gl.gl import (
    GL_RED,
    GL_RG,
    GL_RGB,
    GL_BGR,
    GL_RGBA,
    GL_BGRA,
    GL_RED_INTEGER,
    GL_RG_INTEGER,
    GL_RGB_INTEGER,
    GL_BGR_INTEGER,
    GL_RGBA_INTEGER,
    GL_BGRA_INTEGER,
    GL_DEPTH_COMPONENT,
    GL_DEPTH_STENCIL,
    GL_UNSIGNED_BYTE,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MAX_LEVEL,
    GL_TEXTURE_2D,
    GLuint,
    GL_TEXTURE0,
    GL_READ_WRITE,
    GL_RGBA32F,
    GLubyte,
    GL_UNPACK_SKIP_PIXELS,
    GL_UNPACK_SKIP_ROWS,
    GL_UNPACK_ALIGNMENT,
    GL_UNPACK_ROW_LENGTH,
    GL_TEXTURE_2D_ARRAY,  # noqa: F401
    GL_TRIANGLES,  # noqa: F401
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
    GL_BYTE,  # noqa: F401
    GL_INT,  # noqa: F401
    GL_DEPTH_COMPONENT16,  # noqa: F401
    GL_DEPTH_COMPONENT24,  # noqa: F401
    GL_DEPTH_COMPONENT32,  # noqa: F401
    GL_DEPTH_COMPONENT32F,  # noqa: F401
    GL_FRAMEBUFFER,
    GL_COLOR_ATTACHMENT0,
    GL_COMPRESSED_RGBA_S3TC_DXT1_EXT,
    GL_COMPRESSED_RGBA_S3TC_DXT3_EXT,
    GL_COMPRESSED_RGBA_S3TC_DXT5_EXT,
    GL_COMPRESSED_RGB_S3TC_DXT1_EXT,
    GL_TEXTURE_SWIZZLE_R,
    GL_TEXTURE_SWIZZLE_G,
    GL_TEXTURE_SWIZZLE_B,
    GL_TEXTURE_SWIZZLE_A,
    GL_GREEN,
    GL_COMPRESSED_RED_RGTC1,
    GL_COMPRESSED_SIGNED_RED_RGTC1,
    GL_COMPRESSED_RG_RGTC2,
    GL_COMPRESSED_SIGNED_RG_RGTC2,
)

from pyglet.graphics.api.gl import gl
from pyglet.graphics.api.gl.enums import texture_map
from pyglet.image.base import ImageData, ImageDataRegion, CompressionFormat, \
    CompressedImageData
from pyglet.image.base import ImageException
from pyglet.graphics.texture import PixelData, PixelReadback, Texture, UniformTextureSequence, CompressedTexture, \
    _TextureRegionShared, _Texture3DShared, _TextureArrayShared, TextureGrid

if TYPE_CHECKING:
    from pyglet.customtypes import Buffer
    from pyglet.graphics.api.gl.framebuffer import GLFramebuffer
    from pyglet.graphics.resource import TextureKey


class GLPixelReadback(PixelReadback):
    """Context-owned resources and state handling for texture readback."""

    def __init__(self, context: OpenGLSurfaceContext) -> None:
        """Create a readback helper for an OpenGL surface context."""
        super().__init__(context)
        self._framebuffer: GLFramebuffer | None = None

    def get_framebuffer(self) -> GLFramebuffer:
        """Return the lazily created framebuffer used for texture readback."""
        if self._framebuffer is None:
            if self._context.core.gl_api in (GraphicsAPI.OPENGL_2, GraphicsAPI.OPENGL_ES_2):
                from pyglet.graphics.api.gl2.framebuffer import GL2Framebuffer  # noqa: PLC0415

                self._framebuffer = GL2Framebuffer(context=self._context)
            else:
                from pyglet.graphics.api.gl.framebuffer import GLFramebuffer  # noqa: PLC0415

                self._framebuffer = GLFramebuffer(context=self._context)
        return self._framebuffer

    @contextmanager
    def _pack_state(self) -> Iterator[None]:
        alignment = gl.GLint()
        self._context.glGetIntegerv(gl.GL_PACK_ALIGNMENT, alignment)
        self._context.glPixelStorei(gl.GL_PACK_ALIGNMENT, 1)
        try:
            yield
        finally:
            self._context.glPixelStorei(gl.GL_PACK_ALIGNMENT, alignment.value)

    def read_texture(self, texture: GLTexture, z: int, level: int,
                     gl_format: int, gl_type: int, component_type: type,
                     components: int) -> tuple[int, int, Buffer]:
        """Read one texture image or layer into tightly packed CPU memory."""
        width, height, depth = texture._get_mipmap_dimensions(level)
        if not 0 <= z < depth:
            msg = f"Texture layer {z} is outside the valid range 0..{depth - 1}."
            raise ValueError(msg)

        layer_elements = width * height * components
        direct_readback = self._context.info.pixel_transfer.direct_texture_readback

        with self._pack_state():
            if direct_readback:
                buffer = (component_type * (layer_elements * depth))()
                self._context.glBindTexture(texture.target, texture.handle)
                self._context.glGetTexImage(texture.target, level, gl_format, gl_type, buffer)

                if depth == 1:
                    data = buffer
                else:
                    start = z * layer_elements
                    data = (component_type * layer_elements).from_buffer(
                        buffer, start * sizeof(component_type),
                    )
            else:
                buffer = (component_type * layer_elements)()
                framebuffer = self.get_framebuffer()
                with framebuffer:
                    texture._set_readback_framebuffer_attachment(texture.handle, z, level)
                    try:
                        if not framebuffer.is_complete:
                            msg = f"Texture cannot be read through a framebuffer: {framebuffer.get_status()}"
                            raise GraphicsAPIError(msg)
                        self._context.glReadPixels(0, 0, width, height, gl_format, gl_type, buffer)
                    finally:
                        texture._set_readback_framebuffer_attachment(0, z, level)
                data = buffer

        return width, height, data

_api_base_internal_formats = {
    'R': 'GL_R',
    'RG': 'GL_RG',
    'RGB': 'GL_RGB',
    'RGBA': 'GL_RGBA',
    'BGR': 'GL_RGB',
    'BGRA': 'GL_RGBA',
    'D': 'GL_DEPTH_COMPONENT',
    'DS': 'GL_DEPTH_STENCIL',
    'L': 'GL_R',
    'LA': 'GL_RG',
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
    'L': 'GL_RED',
    'LA': 'GL_RG',
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
    if data_type == "I" and component_format != ComponentFormat.D:
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
    'L': GL_RED,
    'LA': GL_RG,
}


_data_types = {
    "b": gl.GL_BYTE,
    "B": gl.GL_UNSIGNED_BYTE,
    "h": gl.GL_SHORT,
    "H": gl.GL_UNSIGNED_SHORT,
    "i": gl.GL_INT,
    "I": gl.GL_UNSIGNED_INT,
    "f": gl.GL_FLOAT,
    "f.5": gl.GL_HALF_FLOAT,
    "d": gl.GL_DOUBLE,
}

_component_types = {
    "b": gl.GLbyte,
    "B": gl.GLubyte,
    "h": gl.GLshort,
    "H": gl.GLushort,
    "i": gl.GLint,
    "I": gl.GLuint,
    "f": gl.GLfloat,
    "d": gl.GLdouble,
}


def _get_gl_format_and_type(fmt: str, data_type: str) -> tuple[int | None, int | None]:
    fmt = _api_pixel_formats.get(fmt)
    if fmt:
        return fmt, _data_types.get(data_type)  # Eventually support others through ImageData.

    return None, None


def _normalize_upload_format(data_format: str) -> str:
    """Normalize an image format string into a supported upload format."""
    fmt = data_format
    if fmt not in _api_pixel_formats:
        fmt = {
            1: 'R',
            2: 'RG',
            3: 'RGB',
            4: 'RGBA',
        }.get(len(data_format))
    return fmt


def _get_upload_format(context: OpenGLSurfaceContext, data_format: str) -> str:
    """Return a component order that the active backend can upload directly."""
    if not context.info.pixel_transfer.bgra_upload:
        if data_format == "BGRA":
            return "RGBA"
        if data_format == "BGR":
            return "RGB"
    return _normalize_upload_format(data_format)


def _get_pixel_format(image_data: ImageData) -> tuple[int, int]:
    """Determine the pixel format from format string for the Graphics API."""
    data_format = _normalize_upload_format(image_data.format)
    fmt, gl_type = _get_gl_format_and_type(data_format, image_data.data_type)
    return fmt, gl_type


class GLTexture(Texture):
    """An image loaded into GPU memory.

    Typically, you will get an instance of Texture by accessing calling
    the ``get_texture()`` method of any AbstractImage class (such as ImageData).
    """

    region_class: type[GLTextureRegion]  # Set to GLTextureRegion after it's defined
    """The class to use when constructing regions of this texture.
     The class should be a subclass of TextureRegion.
    """

    def __init__(self, context: OpenGLSurfaceContext, width: int, height: int, handle: int,
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
        self.target = texture_map[self.tex_type]
        self._gl_min_filter = texture_map[self.min_filter]
        self._gl_mag_filter = texture_map[self.mag_filter]
        self._gl_internal_format = _get_internal_format(internal_format, internal_format_size, internal_format_type)
        if (
            internal_format == ComponentFormat.BGRA
            and context.info.get_opengl_api() in (GraphicsAPI.OPENGL_ES_2, GraphicsAPI.OPENGL_ES_3)
            and context.info.pixel_transfer.bgra_upload
        ):
            # GL_EXT_texture_format_BGRA8888 requires matching unsized BGRA
            # internal and external formats on OpenGL ES.
            self._gl_internal_format = GL_BGRA

    def delete(self) -> None:
        """Delete this texture and the memory it occupies.

        Textures are invalid after deletion, and may no longer be used.
        """
        self._context.glDeleteTextures(1, GLuint(self._handle))
        self._handle = None

    def bind(self, texture_unit: int = 0) -> None:
        """Bind to a specific Texture Unit by number."""
        self._context.glActiveTexture(GL_TEXTURE0 + texture_unit)
        self._context.glBindTexture(self.target, self._handle)

    def bind_image_texture(self, unit: int, level: int = 0, layered: bool = False,
                           layer: int = 0, access: int = GL_READ_WRITE, fmt: int = GL_RGBA32F):
        """Bind as an ImageTexture for use with a :py:class:`~pyglet.shader.ComputeShaderProgram`.

        OpenGL ES requires the texture to have immutable-format storage. Create
        it with ``immutable=True`` when it will be bound as an image texture.
        """
        self._context.glBindImageTexture(unit, self._handle, level, layered, layer, access, fmt)

    def _flush(self) -> None:
        self._context.glFlush()

    def _delete_resource(self) -> None:
        self._context.delete_texture(self._handle)
        self._handle = None

    def _begin_upload(self, image_data: ImageData | ImageDataRegion) -> None:
        align, row_length = self._get_image_alignment(image_data)

        self._context.glPixelStorei(GL_UNPACK_ALIGNMENT, align)
        if not self._context.info.pixel_transfer.unpack_row_length:
            return

        self._context.glPixelStorei(GL_UNPACK_ROW_LENGTH, row_length)

        if isinstance(image_data, ImageDataRegion):
            self._context.glPixelStorei(GL_UNPACK_SKIP_PIXELS, image_data.x)
            self._context.glPixelStorei(GL_UNPACK_SKIP_ROWS, image_data.y)

    def _end_upload(self, image_data: ImageData | ImageDataRegion) -> None:
        if not self._context.info.pixel_transfer.unpack_row_length:
            return

        self._context.glPixelStorei(GL_UNPACK_ROW_LENGTH, 0)

        if isinstance(image_data, ImageDataRegion):
            self._context.glPixelStorei(GL_UNPACK_SKIP_PIXELS, 0)
            self._context.glPixelStorei(GL_UNPACK_SKIP_ROWS, 0)

    def _apply_filters(self) -> None:
        self._gl_min_filter = texture_map[self.min_filter]
        self._gl_mag_filter = texture_map[self.mag_filter]

        self.bind()
        self._context.glTexParameteri(self.target, GL_TEXTURE_MIN_FILTER, self._gl_min_filter)
        self._context.glTexParameteri(self.target, GL_TEXTURE_MAG_FILTER, self._gl_mag_filter)

    def _allocate_mipmap_level(self, level: int, width: int, height: int, depth: int,
                               data_size: int | None) -> None:
        data = (GLubyte * data_size)() if data_size is not None else None
        if self.immutable:
            if data is not None:
                self._context.glTexSubImage2D(
                    self.target, level, 0, 0, width, height,
                    _get_base_format(self.internal_format), GL_UNSIGNED_BYTE, data,
                )
            return
        self._context.glTexImage2D(self.target, level,
                                   self._gl_internal_format,
                                   width, height,
                                   0,
                                   _get_base_format(self.internal_format),
                                   GL_UNSIGNED_BYTE,
                                   data)

    def _generate_mipmaps(self) -> None:
        self._context.glGenerateMipmap(self.target)
        self._context.glFlush()

    @classmethod
    def create_from_image(cls,
                          image_data: ImageData | ImageDataRegion,
                          tex_type: TextureType = TextureType.TYPE_2D,
                          internal_format_size: int = 8,
                          filters: TextureFilter | tuple[TextureFilter, TextureFilter] | None = None,
                          address_mode: AddressMode = AddressMode.REPEAT,
                          anisotropic_level: int = 0,
                          context: OpenGLSurfaceContext | None = None,
                          ) -> GLTexture:
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

        tex_id = GLuint()
        ctx.glGenTextures(1, byref(tex_id))
        target = texture_map[tex_type]
        ctx.glBindTexture(target, tex_id.value)

        pixel_fmt = _get_upload_format(ctx, image_data.format)
        texture = cls(ctx, image_data.width, image_data.height, tex_id.value, tex_type,
                      ComponentFormat(pixel_fmt), internal_format_size, image_data.data_type, filters,
                      address_mode, anisotropic_level)

        ctx.glTexParameteri(target, GL_TEXTURE_MIN_FILTER, texture._gl_min_filter)
        ctx.glTexParameteri(target, GL_TEXTURE_MAG_FILTER, texture._gl_mag_filter)

        image_bytes = image_data.get_bytes(pixel_fmt, image_data.width * len(pixel_fmt))
        gl_pfmt, gl_type = _get_gl_format_and_type(pixel_fmt, image_data.data_type)

        # !!! Better place for this?
        if pixel_fmt in ("L", "LA"):
            texture._swizzle_legacy_fmts(pixel_fmt)

        align, _ = texture._get_image_alignment(image_data)

        ctx.glPixelStorei(GL_UNPACK_ALIGNMENT, align)
        if ctx.info.pixel_transfer.unpack_row_length:
            # get_bytes above always returns tightly packed rows.
            ctx.glPixelStorei(GL_UNPACK_ROW_LENGTH, 0)

        ctx.glTexImage2D(target, 0,
                         texture._gl_internal_format,
                         image_data.width, image_data.height,
                         0,
                         gl_pfmt,
                         gl_type,
                         image_bytes)
        ctx.glFlush()
        texture._mark_mipmap_valid(0)
        return texture

    def _swizzle_legacy_fmts(self, pixel_fmt: str) -> None:
        # LUMINANCE and LUMINANCE_ALPHA are legacy and removed in core GL. Use swizzle to emulate.
        if pixel_fmt.startswith("L"):
            self._context.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_SWIZZLE_R, GL_RED)
            self._context.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_SWIZZLE_G, GL_RED)
            self._context.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_SWIZZLE_B, GL_RED)
        if pixel_fmt == "LA":
            self._context.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_SWIZZLE_A, GL_GREEN)

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
               context: SurfaceContext | None = None) -> GLTexture:
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
                If True, allocate immutable-format storage with ``glTexStorage2D``.
            mipmap_levels:
                Number of mipmap levels to allocate. Immutable textures cannot add levels later.
            context:
                A specific OpenGL Surface context, otherwise the current active context.

        Returns:
            A currently bound texture.
        """
        ctx = cast(OpenGLSurfaceContext, context or pyglet.graphics.api.core.current_context)

        max_mipmap_levels = max(width, height).bit_length()
        if not 1 <= mipmap_levels <= max_mipmap_levels:
            msg = f"Mipmap levels must be between 1 and {max_mipmap_levels} for this texture size."
            raise ImageException(msg)
        if immutable and not ctx.info.features.texture_storage:
            raise ImageException("Immutable texture storage is not supported by the current context.")

        tex_id = GLuint()
        target = texture_map[tex_type]
        ctx.glGenTextures(1, byref(tex_id))

        texture = cls(
            ctx, width, height, tex_id.value, tex_type, internal_format,
            internal_format_size, internal_format_type, filters, address_mode,
            anisotropic_level,
        )
        texture.immutable = immutable
        if immutable:
            texture._mipmap_levels = mipmap_levels
        ctx.glBindTexture(target, tex_id.value)
        ctx.glTexParameteri(target, GL_TEXTURE_MIN_FILTER, texture._gl_min_filter)
        ctx.glTexParameteri(target, GL_TEXTURE_MAG_FILTER, texture._gl_mag_filter)
        if immutable or mipmap_levels > 1:
            ctx.glTexParameteri(target, GL_TEXTURE_MAX_LEVEL, mipmap_levels - 1)

        data = (GLubyte * (width * height * len(internal_format)))() if blank_data else None
        texture._allocate(data)
        if blank_data:
            texture._mark_mipmap_valid(0)
        if mipmap_levels > 1:
            if immutable:
                for level in range(1, mipmap_levels):
                    level_width = max(1, width >> level)
                    level_height = max(1, height >> level)
                    data_size = level_width * level_height * len(internal_format) if blank_data else None
                    texture._allocate_mipmap_level(level, level_width, level_height, 1, data_size)
                    if blank_data:
                        texture._mark_mipmap_valid(level)
            else:
                texture.init_mipmaps(mipmap_levels, blank_data)
        return texture

    def _allocate(self, data: None | Array) -> None:
        if self.immutable:
            self._context.glTexStorage2D(
                self.target, self._mipmap_levels, self._gl_internal_format, self.width, self.height,
            )
            if data is not None:
                self._context.glTexSubImage2D(
                    self.target, 0, 0, 0, self.width, self.height,
                    _get_base_format(self.internal_format), GL_UNSIGNED_BYTE, data,
                )
            self._context.glFlush()
            return

        self._context.glTexImage2D(self.target, 0,
                             self._gl_internal_format,
                             self.width, self.height,
                             0,
                             _get_base_format(self.internal_format),
                             GL_UNSIGNED_BYTE,
                             data)
        self._context.glFlush()

    def _set_readback_framebuffer_attachment(self, texture_id: int, _z: int = 0, level: int = 0) -> None:
        self._context.glFramebufferTexture2D(
            GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, texture_id, level,
        )

    def fetch(self, z: int = 0, level: int = 0) -> ImageData:
        """Fetch an unsigned-byte, image-oriented copy of this texture.

        Floating-point and integer textures cannot be fetched as
        :class:`~pyglet.image.ImageData` without conversion. Use
        :meth:`read_pixels` for those typed values.
        Reading data back from the GPU can be a costly operation.

        Modifying the returned ImageData object has no effect on the
        texture itself. Uploading ImageData back to the GPU/texture
        can be done with the :py:meth:`~Texture.upload` method.

        Args:
            z:
                For 3D textures, the image slice to retrieve.
            level:
                The mipmap level of the texture to retrieve.
        """
        pixel_format = self._context.info.pixel_format_preferences.readback_format
        fmt = pixel_format.component_format
        gl_format = _api_pixel_formats[fmt]

        if self.internal_format_type in ("f", "i", "I"):
            msg = (
                "Texture.fetch() only supports normalized byte image formats. "
                "Use Texture.read_pixels() for floating-point or integer textures."
            )
            raise NotImplementedError(msg)

        width, height, image_bytes = self._context.pixel_readback.read_texture(
            self, z, level, gl_format, GL_UNSIGNED_BYTE, GLubyte, len(fmt),
        )
        return ImageData(width, height, fmt, image_bytes)

    def read_pixels(self, z: int = 0, level: int = 0) -> PixelData:
        """Read typed, tightly packed RGBA pixel values from this texture."""
        if self.internal_format in (ComponentFormat.D, ComponentFormat.DS):
            raise NotImplementedError("Typed depth and depth-stencil texture readback is not yet supported.")

        if self.internal_format_type in ("i", "I"):
            gl_format = GL_RGBA_INTEGER
            data_type = self.internal_format_type
        elif self.internal_format_type == "f":
            gl_format = GL_RGBA
            data_type = "f"
        else:
            gl_format = GL_RGBA
            data_type = "B"

        gl_type = _data_types[data_type]
        component_type = _component_types[data_type]
        width, height, data = self._context.pixel_readback.read_texture(
            self, z, level, gl_format, gl_type, component_type, 4,
        )
        return PixelData(width, height, ComponentFormat.RGBA, data_type, data)

    def _update_subregion(self, image_data: ImageData | ImageDataRegion, x: int, y: int, z: int,
                          level: int = 0) -> None:
        data_pitch = abs(image_data._current_pitch)

        api = self._context.info.get_opengl_api()
        upload_fmt = _get_upload_format(self._context, image_data.format)
        upload_pitch = data_pitch

        # GLES drivers can be strict about sub-image upload format compatibility.
        # Match upload format to the texture's component format.
        if api in (GraphicsAPI.OPENGL_ES_2, GraphicsAPI.OPENGL_ES_3):
            desired_fmt = self.internal_format.value
            if desired_fmt != upload_fmt:
                upload_fmt = desired_fmt
                upload_pitch = image_data.width * len(upload_fmt)

        # Get data in required format (hopefully will be the same format it's already
        # in, unless that's an obscure format, upside-down or the driver is old).
        if self._context.info.pixel_transfer.unpack_row_length:
            data = image_data.convert(upload_fmt, upload_pitch)
        else:
            upload_pitch = image_data.width * len(upload_fmt)
            data = image_data.get_bytes(upload_fmt, upload_pitch)

        upload_fmt = _normalize_upload_format(upload_fmt)
        fmt, gl_type = _get_gl_format_and_type(upload_fmt, image_data.data_type)

        self._context.glTexSubImage2D(self.target, level,
                                      x, y,
                                      image_data.width, image_data.height,
                                      fmt, gl_type,
                                      data)

class GLTextureRegion(_TextureRegionShared, GLTexture):
    """A rectangular region of a texture, presented as if it were a separate texture."""

    def __init__(self, x: int, y: int, z: int, width: int, height: int, owner: Texture):
        super().__init__(owner._context, width, height, owner.handle, owner.tex_type, owner.internal_format,
                         owner.internal_format_size, owner.internal_format_type, owner.filters, owner.address_mode,
                         owner.anisotropic_level, key=owner.key)
        self._init_region(x, y, z, width, height, owner)


GLTexture.region_class = GLTextureRegion


class GLTexture3D(_Texture3DShared[GLTextureRegion], GLTexture, UniformTextureSequence[GLTextureRegion]):
    """A texture with more than one image slice.

    Use the :py:meth:`create_for_images` or :py:meth:`create_for_image_grid`
    classmethod to construct a Texture3D.
    """
    item_width: int = 0
    item_height: int = 0
    items: tuple

    def _allocate(self, data: None | Array):
        self._context.glTexImage3D(self.target, 0,
                             self._gl_internal_format,
                             self.width, self.height, self.images,
                             0,
                             _get_base_format(self.internal_format),
                             GL_UNSIGNED_BYTE,
                             data)
        self._context.glFlush()

    def upload(self, image: ImageData | ImageDataRegion, x: int, y: int, z: int, level: int = 0) -> None:
        GLTexture.upload(self, image, x, y, z, level=level)

    def _get_mipmap_depth(self, level: int) -> int:
        depth = max(1, int(self.images))
        return max(1, depth >> level)

    def _allocate_mipmap_level(self, level: int, width: int, height: int, depth: int,
                               data_size: int | None) -> None:
        data = (GLubyte * data_size)() if data_size is not None else None
        self._context.glTexImage3D(self.target, level,
                                   self._gl_internal_format,
                                   width, height, depth,
                                   0,
                                   _get_base_format(self.internal_format),
                                   GL_UNSIGNED_BYTE,
                                   data)

    def _generate_mipmaps(self) -> None:
        self._context.glGenerateMipmap(self.target)
        self._context.glFlush()

    @classmethod
    def create_for_images(cls, images,
                 internal_format_size: int = 8,
                 internal_format_type: str = "b",
                 filters: TextureFilter | tuple[TextureFilter, TextureFilter] | None = None,
                 address_mode: AddressMode = AddressMode.REPEAT,
                 anisotropic_level: int = 0,
                 context: OpenGLSurfaceContext | None = None) -> GLTexture3D:
        ctx = context or pyglet.graphics.api.core.current_context
        item_width = images[0].width
        item_height = images[0].height
        pixel_fmt = images[0].format
        internal_format = ComponentFormat(pixel_fmt)

        if not all(img.width == item_width and img.height == item_height for img in images):
            raise ImageException('Images do not have same dimensions.')

        tex_id = GLuint()
        target = texture_map[TextureType.TYPE_3D]
        ctx.glGenTextures(1, byref(tex_id))
        ctx.glBindTexture(target, tex_id.value)
        texture = cls(
            ctx,
            item_width,
            item_height,
            tex_id.value,
            TextureType.TYPE_3D,
            internal_format,
            internal_format_size,
            internal_format_type,
            filters,
            address_mode,
            anisotropic_level,
        )
        ctx.glTexParameteri(target, GL_TEXTURE_MIN_FILTER, texture._gl_min_filter)
        ctx.glTexParameteri(target, GL_TEXTURE_MAG_FILTER, texture._gl_mag_filter)

        texture.images = len(images)

        size = texture.width * texture.height * texture.images * len(internal_format)
        data = (GLubyte * size)()

        ctx.glPixelStorei(GL_UNPACK_ALIGNMENT, 1)

        texture._allocate(data)

        items = []
        for i, image in enumerate(images):
            item = cls.region_class(0, 0, i, item_width, item_height, texture)
            items.append(item)
            texture.upload(image, 0, 0, z=i)
        ctx.glFlush()

        texture.items = items
        texture.item_width = item_width
        texture.item_height = item_height
        return texture

    def _set_readback_framebuffer_attachment(self, texture_id: int, z: int = 0, level: int = 0) -> None:
        self._context.glFramebufferTextureLayer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, texture_id, level, z)

    def _update_subregion(self, image_data: ImageData, x: int, y: int, z: int,
                          level: int = 0):
        data_pitch = abs(image_data._current_pitch)

        data = image_data.convert(image_data.format, data_pitch)

        fmt, gl_type = _get_pixel_format(image_data)

        self._context.glTexSubImage3D(self.target, level,
                                      x, y, z,
                                      image_data.width, image_data.height, 1,
                                      fmt, gl_type,
                                      data)

    def _bind_sequence_texture(self) -> None:
        self._context.glBindTexture(self.target, self._handle)


class GLTextureArrayRegion(GLTextureRegion):
    """A region of a TextureArray, presented as if it were a separate texture."""

    def __repr__(self):
        return f"{self.__class__.__name__}(handle={self._handle}, size={self.width}x{self.height}, layer={self.z})"


class GLTextureArray(_TextureArrayShared[GLTextureArrayRegion], GLTexture, UniformTextureSequence[GLTextureArrayRegion]):
    items: list[GLTextureArrayRegion]

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
               context: OpenGLSurfaceContext | None = None) -> GLTextureArray:
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
            context:
                A specific OpenGL Surface context, otherwise the current active context.
        .. versionadded:: 2.0
        """
        ctx = context or pyglet.graphics.api.core.current_context

        max_depth_limit = ctx.info.MAX_ARRAY_TEXTURE_LAYERS
        assert max_depth <= max_depth_limit, f"TextureArray max_depth supported is {max_depth_limit}."

        tex_id = GLuint()
        ctx.glGenTextures(1, byref(tex_id))

        texture = cls(ctx, width, height, tex_id.value, max_depth, internal_format, internal_format_size,
                      internal_format_type, filters, address_mode, anisotropic_level)

        ctx.glBindTexture(texture.target, tex_id.value)
        ctx.glTexParameteri(texture.target, GL_TEXTURE_MIN_FILTER, texture._gl_min_filter)
        ctx.glTexParameteri(texture.target, GL_TEXTURE_MAG_FILTER, texture._gl_min_filter)

        texture._allocate(None)
        return texture

    def _set_readback_framebuffer_attachment(self, texture_id: int, z: int = 0, level: int = 0) -> None:
        self._context.glFramebufferTextureLayer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, texture_id, level, z)

    def _update_subregion(self, image_data: ImageData, x: int, y: int, z: int,
                          level: int = 0):
        data_pitch = abs(image_data._current_pitch)

        data = image_data.convert(image_data.format, data_pitch)

        fmt, gl_type = _get_pixel_format(image_data)

        self._context.glTexSubImage3D(self.target, level,
                                      x, y, z,
                                      image_data.width, image_data.height, 1,
                                      fmt, gl_type,
                                      data)

    def _allocate(self, data: None | Array) -> None:
        self._context.glTexImage3D(self.target, 0,
                         self._gl_internal_format,
                         self.width, self.height, self.max_depth,
                         0,
                         _get_base_format(self.internal_format),
                         GL_UNSIGNED_BYTE,
                         data)

    def upload(self, image: ImageData | ImageDataRegion, x: int, y: int, z: int, level: int = 0) -> None:
        GLTexture.upload(self, image, x, y, z, level=level)

    def _get_mipmap_depth(self, level: int) -> int:
        return max(1, int(self.max_depth))

    def _allocate_mipmap_level(self, level: int, width: int, height: int, depth: int,
                               data_size: int | None) -> None:
        data = (GLubyte * data_size)() if data_size is not None else None
        self._context.glTexImage3D(self.target, level,
                                   self._gl_internal_format,
                                   width, height, self.max_depth,
                                   0,
                                   _get_base_format(self.internal_format),
                                   GL_UNSIGNED_BYTE,
                                   data)

    def _generate_mipmaps(self) -> None:
        self._context.glGenerateMipmap(self.target)
        self._context.glFlush()

    def _bind_sequence_texture(self) -> None:
        self._context.glBindTexture(self.target, self._handle)

    def _allocate_image(self, image: ImageData, layer: int) -> None:
        self.upload(image, 0, 0, layer)

    @classmethod
    def create_for_images(cls, images: Sequence[ImageData],
                 max_depth: int | None = None,
                 internal_format_size: int = 8,
                 internal_format_type: str = "b",
                 filters: TextureFilter | tuple[TextureFilter, TextureFilter] | None = None,
                 address_mode: AddressMode = AddressMode.REPEAT,
                 anisotropic_level: int = 0,
                 context: OpenGLSurfaceContext | None = None) -> GLTextureArray:
        ctx = context or pyglet.graphics.api.core.current_context
        item_width = images[0].width
        item_height = images[0].height
        pixel_fmt = images[0].format
        internal_format = ComponentFormat(pixel_fmt)

        if not all(img.width == item_width and img.height == item_height for img in images):
            raise ImageException('Images do not have same dimensions.')

        if max_depth is None:
            max_depth = len(images)

        tex_id = GLuint()
        target = texture_map[TextureType.TYPE_2D_ARRAY]
        ctx.glGenTextures(1, byref(tex_id))
        ctx.glBindTexture(target, tex_id.value)
        texture = cls(ctx, item_width, item_height, tex_id.value, max_depth, internal_format,
                      internal_format_size, internal_format_type, filters, address_mode, anisotropic_level)
        ctx.glTexParameteri(target, GL_TEXTURE_MIN_FILTER, texture._gl_min_filter)
        ctx.glTexParameteri(target, GL_TEXTURE_MAG_FILTER, texture._gl_mag_filter)

        texture.images = len(images)

        size = (texture.width * texture.height * texture.images * len(internal_format))
        data = (GLubyte * size)()
        ctx.glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        texture._allocate(data)

        items = []
        for i, image in enumerate(images):
            item = cls.region_class(0, 0, i, item_width, item_height, texture)
            items.append(item)
            texture.upload(image, 0, 0, z=i)
        ctx.glFlush()

        texture.items = items
        texture.item_width = item_width
        texture.item_height = item_height
        return texture

GLTextureArray.region_class = GLTextureArrayRegion
GLTextureArrayRegion.region_class = GLTextureArrayRegion


class GLTextureGrid(TextureGrid):
    pass

# DDS compression formats based on DirectX.
_dxgi_to_gl_format: dict[int, int] = {
    # --- BC1 ---
    71: GL_COMPRESSED_RGB_S3TC_DXT1_EXT,          # DXGI_FORMAT_BC1_UNORM
    72: GL_COMPRESSED_RGBA_S3TC_DXT1_EXT,         # DXGI_FORMAT_BC1_UNORM_SRGB

    # --- BC2 ---
    74: GL_COMPRESSED_RGBA_S3TC_DXT3_EXT,         # DXGI_FORMAT_BC2_UNORM
    75: GL_COMPRESSED_RGBA_S3TC_DXT3_EXT,         # DXGI_FORMAT_BC2_UNORM_SRGB

    # --- BC3 ---
    77: GL_COMPRESSED_RGBA_S3TC_DXT5_EXT,         # DXGI_FORMAT_BC3_UNORM
    78: GL_COMPRESSED_RGBA_S3TC_DXT5_EXT,         # DXGI_FORMAT_BC3_UNORM_SRGB

    # --- BC4 ---
    80: GL_COMPRESSED_RED_RGTC1,                  # DXGI_FORMAT_BC4_UNORM
    81: GL_COMPRESSED_SIGNED_RED_RGTC1,           # DXGI_FORMAT_BC4_SNORM

    # --- BC5 ---
    83: GL_COMPRESSED_RG_RGTC2,                   # DXGI_FORMAT_BC5_UNORM
    84: GL_COMPRESSED_SIGNED_RG_RGTC2,            # DXGI_FORMAT_BC5_SNORM

    # --- BC6H ---
    95: gl.GL_COMPRESSED_RGB_BPTC_UNSIGNED_FLOAT_ARB, # DXGI_FORMAT_BC6H_UF16
    96: gl.GL_COMPRESSED_RGB_BPTC_SIGNED_FLOAT_ARB,   # DXGI_FORMAT_BC6H_SF16

    # --- BC7 ---
    98: gl.GL_COMPRESSED_RGBA_BPTC_UNORM_ARB,         # DXGI_FORMAT_BC7_UNORM
    99: gl.GL_COMPRESSED_SRGB_ALPHA_BPTC_UNORM_ARB,   # DXGI_FORMAT_BC7_UNORM_SRGB
}

# KTX2 compression formats based on Vulkan.
vk_to_gl_format: dict[int, int] = {
    # --- BC1 ---
    131: GL_COMPRESSED_RGBA_S3TC_DXT1_EXT,  # VK_FORMAT_BC1_RGBA_UNORM_BLOCK
    132: GL_COMPRESSED_RGBA_S3TC_DXT1_EXT,  # VK_FORMAT_BC1_RGBA_SRGB_BLOCK
    # --- BC2 ---
    133: GL_COMPRESSED_RGBA_S3TC_DXT3_EXT,  # VK_FORMAT_BC2_UNORM_BLOCK
    134: GL_COMPRESSED_RGBA_S3TC_DXT3_EXT,  # VK_FORMAT_BC2_SRGB_BLOCK
    # --- BC3 ---
    135: GL_COMPRESSED_RGBA_S3TC_DXT5_EXT,  # VK_FORMAT_BC3_UNORM_BLOCK
    136: GL_COMPRESSED_RGBA_S3TC_DXT5_EXT,  # VK_FORMAT_BC3_SRGB_BLOCK
    # --- BC4 ---
    137: GL_COMPRESSED_RED_RGTC1,  # VK_FORMAT_BC4_UNORM_BLOCK
    138: GL_COMPRESSED_SIGNED_RED_RGTC1,  # VK_FORMAT_BC4_SNORM_BLOCK
    # --- BC5 ---
    139: GL_COMPRESSED_RG_RGTC2,  # VK_FORMAT_BC5_UNORM_BLOCK
    140: GL_COMPRESSED_SIGNED_RG_RGTC2,  # VK_FORMAT_BC5_SNORM_BLOCK
    # --- BC6H ---
    141: gl.GL_COMPRESSED_RGB_BPTC_UNSIGNED_FLOAT_ARB,  # VK_FORMAT_BC6H_UFLOAT_BLOCK
    142: gl.GL_COMPRESSED_RGB_BPTC_SIGNED_FLOAT_ARB,  # VK_FORMAT_BC6H_SFLOAT_BLOCK
    # --- BC7 ---
    146: gl.GL_COMPRESSED_RGBA_BPTC_UNORM_ARB,  # VK_FORMAT_BC7_UNORM_BLOCK
    147: gl.GL_COMPRESSED_SRGB_ALPHA_BPTC_UNORM_ARB,  # VK_FORMAT_BC7_SRGB_BLOCK
    # --- ETC2 / EAC ---
    74: GL_COMPRESSED_RGB8_ETC2,  # VK_FORMAT_ETC2_R8G8B8_UNORM_BLOCK
    75: gl.GL_COMPRESSED_SRGB8_ETC2,  # VK_FORMAT_ETC2_R8G8B8_SRGB_BLOCK
    76: gl.GL_COMPRESSED_RGB8_PUNCHTHROUGH_ALPHA1_ETC2,  # VK_FORMAT_ETC2_R8G8B8A1_UNORM_BLOCK
    77: gl.GL_COMPRESSED_SRGB8_PUNCHTHROUGH_ALPHA1_ETC2,  # VK_FORMAT_ETC2_R8G8B8A1_SRGB_BLOCK
    78: gl.GL_COMPRESSED_RGBA8_ETC2_EAC,  # VK_FORMAT_ETC2_R8G8B8A8_UNORM_BLOCK
    79: gl.GL_COMPRESSED_SRGB8_ALPHA8_ETC2_EAC,  # VK_FORMAT_ETC2_R8G8B8A8_SRGB_BLOCK
    67: gl.GL_COMPRESSED_R11_EAC,  # VK_FORMAT_EAC_R11_UNORM_BLOCK
    68: gl.GL_COMPRESSED_SIGNED_R11_EAC,  # VK_FORMAT_EAC_R11_SNORM_BLOCK
    69: gl.GL_COMPRESSED_RG11_EAC,  # VK_FORMAT_EAC_R11G11_UNORM_BLOCK
    70: gl.GL_COMPRESSED_SIGNED_RG11_EAC,  # VK_FORMAT_EAC_R11G11_SNORM_BLOCK
    # --- ASTC (LDR) ---
    157: gl.GL_COMPRESSED_RGBA_ASTC_4x4_KHR,  # VK_FORMAT_ASTC_4x4_UNORM_BLOCK
    158: gl.GL_COMPRESSED_SRGB8_ALPHA8_ASTC_4x4_KHR,  # VK_FORMAT_ASTC_4x4_SRGB_BLOCK
    159: gl.GL_COMPRESSED_RGBA_ASTC_5x4_KHR,
    160: gl.GL_COMPRESSED_SRGB8_ALPHA8_ASTC_5x4_KHR,
    161: gl.GL_COMPRESSED_RGBA_ASTC_5x5_KHR,
    162: gl.GL_COMPRESSED_SRGB8_ALPHA8_ASTC_5x5_KHR,
    163: gl.GL_COMPRESSED_RGBA_ASTC_6x5_KHR,
    164: gl.GL_COMPRESSED_SRGB8_ALPHA8_ASTC_6x5_KHR,
    165: gl.GL_COMPRESSED_RGBA_ASTC_6x6_KHR,
    166: gl.GL_COMPRESSED_SRGB8_ALPHA8_ASTC_6x6_KHR,
    167: gl.GL_COMPRESSED_RGBA_ASTC_8x5_KHR,
    168: gl.GL_COMPRESSED_SRGB8_ALPHA8_ASTC_8x5_KHR,
    169: gl.GL_COMPRESSED_RGBA_ASTC_8x6_KHR,
    170: gl.GL_COMPRESSED_SRGB8_ALPHA8_ASTC_8x6_KHR,
    171: gl.GL_COMPRESSED_RGBA_ASTC_8x8_KHR,
    172: gl.GL_COMPRESSED_SRGB8_ALPHA8_ASTC_8x8_KHR,
    173: gl.GL_COMPRESSED_RGBA_ASTC_10x5_KHR,
    174: gl.GL_COMPRESSED_SRGB8_ALPHA8_ASTC_10x5_KHR,
    175: gl.GL_COMPRESSED_RGBA_ASTC_10x6_KHR,
    176: gl.GL_COMPRESSED_SRGB8_ALPHA8_ASTC_10x6_KHR,
    177: gl.GL_COMPRESSED_RGBA_ASTC_10x8_KHR,
    178: gl.GL_COMPRESSED_SRGB8_ALPHA8_ASTC_10x8_KHR,
    179: gl.GL_COMPRESSED_RGBA_ASTC_10x10_KHR,
    180: gl.GL_COMPRESSED_SRGB8_ALPHA8_ASTC_10x10_KHR,
    181: gl.GL_COMPRESSED_RGBA_ASTC_12x10_KHR,
    182: gl.GL_COMPRESSED_SRGB8_ALPHA8_ASTC_12x10_KHR,
    183: gl.GL_COMPRESSED_RGBA_ASTC_12x12_KHR,
    184: gl.GL_COMPRESSED_SRGB8_ALPHA8_ASTC_12x12_KHR,
}

_required_exts = {
    "S3TC": ["GL_EXT_texture_compression_s3tc", "GL_EXT_texture_compression_dxt1"],
    "RGTC": ["GL_EXT_texture_compression_rgtc"],
    "BPTC": ["GL_ARB_texture_compression_bptc"],
    "ETC2": ["GL_ARB_ES3_compatibility", "GL_OES_compressed_ETC2_RGB8_texture"],
    "ASTC": ["GL_KHR_texture_compression_astc_ldr"],
}

def _get_format_family(gl_internal_format: int) -> str | None:
    """Get the format family of the given format to check extension support.

    Args:
        gl_internal_format: The OpenGL enum format.
             EX: GL_COMPRESSED_RGBA_S3TC_DXT1_EXT
    """
    if 33776 <= gl_internal_format <= 33780:
        return "S3TC"
    if 36283 <= gl_internal_format <= 36290:
        return "RGTC"
    if 36492 <= gl_internal_format <= 36495:
        return "BPTC"
    if 37492 <= gl_internal_format <= 37499:
        return "ETC2"
    if 37808 <= gl_internal_format <= 37855:
        return "ASTC"
    return None

def _get_extension_from_compression(cf: CompressionFormat) -> int:
    if cf.fmt in (b'DXT1', b'BC1 '):
        return GL_COMPRESSED_RGBA_S3TC_DXT1_EXT if cf.alpha else GL_COMPRESSED_RGB_S3TC_DXT1_EXT
    if cf.fmt in (b'DXT3', b'BC2 '):
        return GL_COMPRESSED_RGBA_S3TC_DXT3_EXT
    if cf.fmt in (b'DXT5', b'BC3 '):
        return GL_COMPRESSED_RGBA_S3TC_DXT5_EXT

    # Newer DDS formats:
    if cf.fmt == b'DX10' and (fmt := _dxgi_to_gl_format.get(cf.dxgi_format)):
        return fmt

    # KTX2 formats:
    if cf.fmt == b'KTX2' and (fmt := vk_to_gl_format.get(cf.vk_format)):
        return fmt
    msg = f"Unknown format received: {cf}"
    raise NotImplementedError(msg)

def _get_gl_compression_format(cf: CompressionFormat) -> int:
    # Old formats:: dwFourCC
    if cf.fmt in (b'DXT1', b'BC1 '):
        return GL_COMPRESSED_RGBA_S3TC_DXT1_EXT if cf.alpha else GL_COMPRESSED_RGB_S3TC_DXT1_EXT
    if cf.fmt in (b'DXT3', b'BC2 '):
        return GL_COMPRESSED_RGBA_S3TC_DXT3_EXT
    if cf.fmt in (b'DXT5', b'BC3 '):
        return GL_COMPRESSED_RGBA_S3TC_DXT5_EXT

    # Newer DDS formats:
    if cf.fmt == b'DX10' and (fmt := _dxgi_to_gl_format.get(cf.dxgi_format)):
        return fmt

    # KTX2 formats:
    if cf.fmt == b'KTX2' and (fmt := vk_to_gl_format.get(cf.vk_format)):
        return fmt

    msg = f"Unsupported compression format: {cf!r}"
    raise ValueError(msg)

class GLCompressedTexture(CompressedTexture):
    """A compressed texture created from CompressedImageData."""

    def __init__(self, context: OpenGLSurfaceContext, width: int, height: int,
                 handle: int,
                 compression_fmt: CompressionFormat,
                 tex_type: TextureType = TextureType.TYPE_2D,
                 filters: TextureFilter | tuple[TextureFilter, TextureFilter] | None = None,
                 address_mode: AddressMode = AddressMode.REPEAT, anisotropic_level: int = 0) -> None:
        super().__init__(width, height, handle, compression_fmt, tex_type, filters, address_mode, anisotropic_level)
        self._context = context
        self.target = texture_map[self.tex_type]
        self._gl_min_filter = texture_map[self.min_filter]
        self._gl_mag_filter = texture_map[self.mag_filter]
        self._gl_internal_format = _get_gl_compression_format(compression_fmt)
        self._compression_fmt = compression_fmt
        self._can_gpu_decode = self._is_format_supported()
        self.mipmap_data: list[bytes | None] = []

    def _is_format_supported(self) -> bool:
        family = _get_format_family(self._gl_internal_format)
        if not family:
            msg = f"Unsupported compression format: {self._compression_fmt}"
            raise ValueError(msg)

        if family == "ETC2" and self._context.info.get_opengl_api() == GraphicsAPI.OPENGL_ES_3:
            return True

        required = _required_exts.get(family, [])
        return any(self._context.info.have_extension(ext) for ext in required)

    @classmethod
    def create(cls, width: int, height: int,
               fmt: CompressionFormat,
               data: bytes | Array,
               tex_type: TextureType = TextureType.TYPE_2D,
               filters: TextureFilter | tuple[TextureFilter, TextureFilter] | None = None,
               address_mode: AddressMode = AddressMode.REPEAT,
               anisotropic_level: int = 0,
               context: OpenGLSurfaceContext | None = None) -> GLCompressedTexture:
        """Create a compressed texture from a complete compressed base level."""
        ctx = context or pyglet.graphics.api.core.current_context

        tex_id = GLuint()
        target = texture_map[tex_type]
        ctx.glGenTextures(1, byref(tex_id))

        texture = cls(ctx, width, height, tex_id.value, fmt, tex_type, filters, address_mode, anisotropic_level)
        ctx.glBindTexture(target, tex_id.value)
        ctx.glTexParameteri(target, GL_TEXTURE_MIN_FILTER, texture._gl_min_filter)
        ctx.glTexParameteri(target, GL_TEXTURE_MAG_FILTER, texture._gl_mag_filter)

        texture._allocate(data)
        return texture


    @classmethod
    def create_from_image(cls,
                          image_data: CompressedImageData,
                          tex_type: TextureType = TextureType.TYPE_2D,
                          filters: TextureFilter | tuple[TextureFilter, TextureFilter] | None = None,
                          address_mode: AddressMode = AddressMode.REPEAT,
                          anisotropic_level: int = 0,
                          context: OpenGLSurfaceContext | None = None,
                          ) -> GLCompressedTexture:
        """Create a Texture from image data.

        Args:
            image_data:
                The image instance.
            tex_type:
                The texture enum type.
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

        tex_id = GLuint()
        ctx.glGenTextures(1, byref(tex_id))
        target = texture_map[tex_type]
        ctx.glBindTexture(target, tex_id.value)

        texture = cls(ctx, image_data.width, image_data.height, tex_id.value, image_data.fmt, tex_type,
                      filters, address_mode, anisotropic_level)

        ctx.glTexParameteri(target, GL_TEXTURE_MIN_FILTER, texture._gl_min_filter)
        ctx.glTexParameteri(target, GL_TEXTURE_MAG_FILTER, texture._gl_mag_filter)
        texture._allocate(image_data.data)
        texture.mipmap_data = image_data.mipmap_data.copy()
        texture._upload_mipmap_data()
        return texture

    def set_mipmap_data(self, level: int, data: bytes) -> None:
        """Set compressed image data for a mipmap level.

        Supplied data gives a compressed image for the given mipmap level.
        This image data must be in the same format as was used in the
        constructor. The image data must also be of the correct dimensions for
        the level (i.e., width >> level, height >> level); but this is not checked.
        Source mipmap levels are uploaded when the texture is created. If none
        are supplied, call :meth:`generate_mipmaps` to create them from level 0.
        """
        if level < 1:
            raise ImageException("Compressed texture mipmap levels must be greater than zero.")

        # Extend mipmap_data list to required level
        self.mipmap_data += [None] * (level - len(self.mipmap_data))
        self.mipmap_data[level - 1] = data

    def bind(self, texture_unit: int = 0) -> None:
        """Bind to a specific Texture Unit by number."""
        self._context.glActiveTexture(GL_TEXTURE0 + texture_unit)
        self._context.glBindTexture(self.target, self._handle)

    def delete(self) -> None:
        """Delete this texture and its OpenGL resource."""
        if self._handle is not None:
            self._context.glDeleteTextures(1, GLuint(self._handle))
            self._handle = None

    def _compute_mipmap_count(self) -> int:
        max_dimension = max(self.width, self.height)
        count = 1
        while max_dimension > 1:
            max_dimension //= 2
            count += 1
        return count

    @property
    def mipmap_count(self) -> int:
        """Return the number of mipmap levels initialized for this texture."""
        return self._mipmap_levels

    @property
    def valid_mipmaps(self) -> tuple[int, ...]:
        """Return a sorted tuple of mipmap levels that contain valid data."""
        return tuple(sorted(self._valid_mipmaps))

    def generate_mipmaps(self) -> None:
        """Generate a complete mipmap chain from the compressed base level."""
        self.bind()
        info = self._context.info
        if info.get_opengl_api() == GraphicsAPI.OPENGL_ES_2:
            raise UnsupportedBackendError("Compressed texture mipmap generation")

        if not info.have_version(3):
            if not info.have_extension("GL_EXT_framebuffer_object"):
                raise UnsupportedBackendError("Compressed texture mipmap generation")
            self._context.glGenerateMipmapEXT(self.target)
        else:
            self._context.glGenerateMipmap(self.target)
        self._context.glFlush()
        self._mipmap_levels = self._compute_mipmap_count()
        self._valid_mipmaps = set(range(self._mipmap_levels))

    def _upload_mipmap_data(self) -> None:
        """Upload the compressed mip chain collected from an image container."""
        if not self.mipmap_data:
            self._valid_mipmaps = {0}
            return

        self.bind()
        for level, data in enumerate(self.mipmap_data, start=1):
            if data is None:
                msg = f"Compressed texture mipmap level {level} has no data."
                raise ImageException(msg)

            width = max(1, self.width >> level)
            height = max(1, self.height >> level)
            self._context.glCompressedTexImage2D(
                self.target, level, self._gl_internal_format, width, height, 0, len(data), data,
            )

        self._context.glFlush()
        self._mipmap_levels = len(self.mipmap_data) + 1
        self._valid_mipmaps = set(range(self._mipmap_levels))

    def _allocate(self, data: None | Array) -> None:
        if self._can_gpu_decode:
            self._context.glCompressedTexImage2D(self.target, 0,
                                                 self._gl_internal_format,
                                                 self.width, self.height, 0,
                                                 len(data), data)
            self._valid_mipmaps = {0}
        elif self.decoder:
            image = self.decoder(data, self.width, self.height)
            texture = image.get_texture()
            assert texture.width == self.width
            assert texture.height == self.height
        else:
            msg = f"No extension or fallback decoder is available to decode {self}"
            raise ImageException(msg)

        self._context.glFlush()
