from __future__ import annotations

from abc import abstractmethod
from typing import Iterator, Literal, TYPE_CHECKING

import pyglet
from pyglet.enums import AddressMode, ComponentFormat, TextureFilter, TextureType
from pyglet.image.base import (
    _AbstractImage,
    _AbstractImageSequence,
    ImageData,
    ImageDataRegion,
    ImageException,
    ImageGrid,
    _AbstractGrid,
    CompressionFormat,
)

if TYPE_CHECKING:
    from pyglet.graphics.api.base import SurfaceContext


class TextureArraySizeExceeded(ImageException):
    """Exception occurs ImageData dimensions are larger than the array supports."""


class TextureArrayDepthExceeded(ImageException):
    """Exception occurs when depth has hit the maximum supported of the array."""


class TextureSequence(_AbstractImageSequence):
    """Interface for a sequence of textures.

    Typical implementations store multiple :py:class:`~pyglet.graphics.TextureRegion`s
    within one :py:class:`~pyglet.graphics.Texture` to minimise state changes.
    """

    def __getitem__(self, item) -> TextureBase:
        raise NotImplementedError

    def __setitem__(self, item, texture: type[TextureBase]) -> _AbstractImage:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    def __iter__(self) -> Iterator[TextureBase]:
        raise NotImplementedError

    def get_texture_sequence(self) -> TextureSequence:
        return self


class TextureBase(_AbstractImage):
    """An image loaded into GPU memory.

    Typically, you will get an instance of Texture by accessing calling
    the ``get_texture()`` method of any AbstractImage class (such as ImageData).
    """

    region_class: TextureRegionBase  # Set to TextureRegion after it's defined
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

    target: int
    """The GL texture target (e.g., ``GL_TEXTURE_2D``)."""

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

    def __init__(self, width: int, height: int, tex_id: int,
                 tex_type: TextureType = TextureType.TYPE_2D,
                 internal_format: ComponentFormat = ComponentFormat.RGBA,
                 internal_format_size: int = 8,
                 internal_format_type: str = "b",
                 filters: TextureFilter | tuple[TextureFilter, TextureFilter] | None = None,
                 address_mode: AddressMode = AddressMode.REPEAT,
                 anisotropic_level: int = 0,
                 ) -> None:
        super().__init__(width, height)
        self.id = tex_id
        self.tex_type = tex_type

        # Use class defaults if None:
        filters = filters or self.default_filters

        if isinstance(filters, TextureFilter):
            self.min_filter = filters
            self.mag_filter = filters
        else:
            self.min_filter, self.mag_filter = filters

        self.address_mode = address_mode
        self.internal_format = internal_format
        self.internal_format_size = internal_format_size
        self.internal_format_type = internal_format_type
        self.anisotropic_level = anisotropic_level

    def delete(self) -> None:
        """Delete this texture and the memory it occupies.

        Textures are invalid after deletion, and may no longer be used.
        """
        self.id = None

    #def __del__(self):
    #    raise NotImplementedError

    def bind(self, texture_unit: int = 0) -> None:
        """Bind to a specific Texture Unit by number."""
        raise NotImplementedError

    # def bind_image_texture(self, unit: int, level: int = 0, layered: bool = False,
    #                        layer: int = 0, access: int = GL_READ_WRITE, fmt: int = GL_RGBA32F):
    #     """Bind as an ImageTexture for use with a :py:class:`~pyglet.shader.ComputeShaderProgram`.
    #
    #     .. note:: OpenGL 4.3, or 4.2 with the GL_ARB_compute_shader extention is required.
    #     """
    #     raise NotImplementedError

    @classmethod
    def create(cls, width: int, height: int,
               tex_type: TextureType = TextureType.TYPE_2D,
               internal_format: ComponentFormat = ComponentFormat.RGBA,
               data_type: str = "b",
               filters: TextureFilter | tuple[TextureFilter, TextureFilter] | None = None,
               address_mode: AddressMode = AddressMode.REPEAT,
               anisotropic_level: int = 0,
               blank_data: bool = True,
               context: SurfaceContext | None = None) -> TextureBase:
        """Create a Texture.

        Create a Texture with the specified dimensions, target and format.
        On return, the texture will be bound.

        Args:
            width:
                Width of texture in pixels.
            height:
                Height of texture in pixels.
            tex_type:
                The type of texture.
            internal_format:
                The components of the internal format.
            data_type:
                The data type of the internal format, as a struct string value.
            filters:
                The texture filter for the min and mag filters. If a single value is passed, both values will
                be used as the filter.
            address_mode:
                The wrapping address mode of the texture.
            anisotropic_level:
                The anisotropic level of the texture.
            blank_data:
                If True, initialize the texture data with all zeros. If False, do not pass initial data.
            context:
                If multiple contexts are being used, a specified context the texture is tied to.
        """
        raise NotImplementedError

    @classmethod
    def create_from_image(cls, image_data: ImageData | ImageDataRegion,
                          tex_type: TextureType = TextureType.TYPE_2D,
                          internal_format_size: int = 8,
                          filters: TextureFilter | tuple[TextureFilter, TextureFilter] | None = None,
                          address_mode: AddressMode = AddressMode.REPEAT,
                          anisotropic_level: int = 0,
                          context: SurfaceContext | None = None,
                          ) -> TextureBase:
        """Create a Texture from image data.

        On return, the texture will be bound.

        Args:
            image_data:
                The image instance.
            tex_type:
                The type of texture.
            internal_format_size:
                The bit size of the internal format.
            filters:
                The texture filter for the min and mag filters. If a single value is passed, both values will
                be used as the filter.
            address_mode:
                The wrapping address mode of the texture.
            anisotropic_level:
                The anisotropic level of the texture.
            context:
                If multiple contexts are being used, a specified context the texture will be tied to.
        """

    def get_image_data(self, z: int = 0) -> ImageData:
        """To be removed and replaced with fetch."""
        raise NotImplementedError

    def get_texture(self) -> TextureBase:
        return self

    def blit(self, x: int, y: int, z: int = 0, width: int | None = None, height: int | None = None) -> None:
        """Blit the texture to the screen.

        Removed as of 3.0. Instead, consider creating a :py:class:`~pyglet.sprite.Sprite` with the Texture,
        and drawing it as part of a larger :py:class:`~pyglet.graphics.Batch`.
        """
        raise NotImplementedError("This method has been removed. See the 3.0 migration documentation.")

    def fetch(self, z: int = 0) -> ImageData:
        """Fetch the image data of this texture by reading pixel data back from the GPU.

        This can be a somewhat costly operation.

        Modifying the returned ImageData object has no effect on the
        texture itself. Uploading ImageData back to the GPU/texture
        can be done with the :py:meth:`~Texture.upload` method.

        Args:
            z:
                For 3D textures, the image slice to retrieve.
        """
        raise NotImplementedError

    def get_mipmapped_texture(self) -> TextureBase:
        raise NotImplementedError(f"Not implemented for {self}.")

    def upload(self, image: ImageData | ImageDataRegion, x: int, y: int, z: int) -> None:
        """Upload image data into the Texture at specific coordinates.

        You must have this texture bound before uploading data.

        The image's anchor point will be aligned to the given ``x`` and ``y``
        coordinates.  If this texture is a 3D texture, the ``z``
        parameter gives the image slice to blit into.
        """
        raise NotImplementedError(f"Not implemented for {self}")

    def get_region(self, x: int, y: int, width: int, height: int) -> TextureRegionBase:
        return self.region_class(x, y, 0, width, height, self)

    def get_transform(self, flip_x: bool = False, flip_y: bool = False,
                      rotate: Literal[0, 90, 180, 270, 360] = 0) -> TextureRegionBase:
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

    def _set_tex_coords_order(self, bl, br, tr, tl):
        tex_coords = (self.tex_coords[:3],
                      self.tex_coords[3:6],
                      self.tex_coords[6:9],
                      self.tex_coords[9:])
        self.tex_coords = tex_coords[bl] + tex_coords[br] + tex_coords[tr] + tex_coords[tl]

        order = self.tex_coords_order
        self.tex_coords_order = (order[bl], order[br], order[tr], order[tl])

    @property
    def uv(self) -> tuple[float, float, float, float]:
        """Tuple containing the left, bottom, right, top 2D texture coordinates."""
        tex_coords = self.tex_coords
        return tex_coords[0], tex_coords[1], tex_coords[3], tex_coords[7]

    @property
    def filters(self) -> tuple[TextureFilter, TextureFilter]:
        """The current Texture filters.

        Providing a single TextureFilter will adjust both minification and magnification filters. Otherwise, a tuple
        can be provided to adjust each individually.
        """
        return self.min_filter, self.mag_filter


    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, size={self.width}x{self.height})"


class TextureRegionBase(TextureBase):
    """A rectangular region of a texture, presented as if it were a separate texture."""

    def __init__(self, x: int, y: int, z: int, width: int, height: int, owner: TextureBase):
        super().__init__(width, height, owner.id, owner.tex_type, owner.internal_format,
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
        raise Exception

    def fetch(self, _z = 0) -> ImageDataRegion:
        image_data = self.owner.get_image_data(self.z)
        return image_data.get_region(self.x, self.y, self.width, self.height)

    def get_image_data(self) -> ImageDataRegion:
        return self.fetch()

    def get_region(self, x: int, y: int, width: int, height: int) -> TextureRegionBase:
        x += self.x
        y += self.y
        region = self.region_class(x, y, self.z, width, height, self.owner)
        region._set_tex_coords_order(*self.tex_coords_order)
        return region

    def upload(self, source: ImageData, x: int, y: int, z: int) -> None:
        assert source.width <= self._width and source.height <= self._height, f"{source} is larger than {self}"
        self.owner.upload(source, x + self.x, y + self.y, z + self.z)

    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}(id={self.id},"
                f" size={self.width}x{self.height}, owner={self.owner.width}x{self.owner.height})")

    def delete(self) -> None:
        """Deleting a TextureRegion has no effect. Operate on the owning texture instead."""

    def __del__(self):
        pass


class UniformTextureSequence(TextureSequence):
    """Interface for a sequence of textures, each with the same dimensions."""


class TextureArrayRegionBase(TextureRegionBase):
    """A region of a TextureArray, presented as if it were a separate texture."""

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, size={self.width}x{self.height}, layer={self.z})"


class TextureArrayBase(TextureBase, UniformTextureSequence):
    def __init__(self, width, height, tex_id, max_depth,
                 internal_format: ComponentFormat = ComponentFormat.RGBA,
                 internal_format_size: int = 8,
                 internal_format_type: str = "b",
                 filters: TextureFilter | tuple[TextureFilter, TextureFilter] | None = None,
                 address_mode: AddressMode = AddressMode.REPEAT,
                 anisotropic_level: int = 0,
                 ):
        super().__init__(width, height, tex_id, TextureType.TYPE_2D_ARRAY, internal_format, internal_format_size,
                  internal_format_type, filters, address_mode, anisotropic_level)
        self.max_depth = max_depth
        self.items = []

    @classmethod
    def create(cls, width: int, height: int,
               internal_format: ComponentFormat = ComponentFormat.RGBA,
               internal_format_size: int = 8,
               internal_format_type: str = "b",
               filters: TextureFilter | tuple[TextureFilter, TextureFilter] | None = None,
               address_mode: AddressMode = AddressMode.REPEAT,
               anisotropic_level: int = 0,
               max_depth: int = 256) -> TextureArray:
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
        raise NotImplementedError

    def _verify_size(self, image: _AbstractImage) -> None:
        if image.width > self.width or image.height > self.height:
            raise TextureArraySizeExceeded(
                f'Image ({image.width}x{image.height}) exceeds the size of the TextureArray ({self.width}x'
                f'{self.height})')

    def add(self, image: ImageData) -> TextureArrayRegion:
        if len(self.items) >= self.max_depth:
            raise TextureArrayDepthExceeded("TextureArray is full.")

        self._verify_size(image)
        start_length = len(self.items)
        item = self.region_class(0, 0, start_length, image.width, image.height, self)

        self.blit_into(image, image.anchor_x, image.anchor_y, start_length)
        self.items.append(item)
        return item

    def allocate(self, *images: _AbstractImage) -> list[TextureArrayRegion]:
        """Allocates multiple images at once."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def create_for_image_grid(cls, grid) -> TextureArray:
        ...

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index) -> TextureArrayRegion:
        return self.items[index]

    def __setitem__(self, index, value) -> None:
        raise NotImplementedError

    def __iter__(self) -> Iterator[TextureRegionBase]:
        return iter(self.items)


class Texture3D(TextureBase, UniformTextureSequence):
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
                 anisotropic_level: int = 0, blank_data=True):
        raise NotImplementedError

    @classmethod
    def create_for_image_grid(cls, grid,
                 internal_format: ComponentFormat = ComponentFormat.RGBA,
                 internal_format_size: int = 8,
                 internal_format_type: str = "b",
                 filters: TextureFilter | tuple[TextureFilter, TextureFilter] | None = None,
                 address_mode: AddressMode = AddressMode.REPEAT,
                 anisotropic_level: int = 0):
        return cls.create_for_images(grid[:], internal_format, internal_format_size, internal_format_type,
                 filters, address_mode, anisotropic_level)

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        return self.items[index]

    def __setitem__(self, index, value):
        raise NotImplementedError

    def __iter__(self) -> Iterator[TextureRegionBase]:
        return iter(self.items)



class TextureGridBase(_AbstractGrid):
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
    def __init__(self, texture: Texture | TextureRegion, rows: int, columns: int, item_width: int,
                 item_height: int, row_padding: int = 0, column_padding: int = 0) -> None:
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
    def from_image_grid(cls, image_grid: ImageGrid) -> TextureGridBase:
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


TextureBase.region_class = TextureRegionBase

TextureArrayBase.region_class = TextureArrayRegionBase
TextureArrayRegionBase.region_class = TextureArrayRegionBase

class CompressedTextureBase(_AbstractImage):
    tex_coords = (0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0)
    """12-tuple of float, named (u1, v1, r1, u2, v2, r2, ...).
    ``u, v, r`` give the 3D texture coordinates for vertices 1-4. The vertices
    are specified in the order bottom-left, bottom-right, top-right and top-left.
    """

    tex_coords_order: tuple[int, int, int, int] = (0, 1, 2, 3)
    """The default vertex winding order for a quad.
    This defaults to counter-clockwise, starting at the bottom-left.
    """

    target: int
    """The GL texture target (e.g., ``GL_TEXTURE_2D``)."""

    level: int = 0
    """The mipmap level of this texture."""

    images = 1

    x: int = 0
    y: int = 0
    z: int = 0

    def __init__(self, width: int, height: int, tex_id: int,
                 compression_format: CompressionFormat,
                 tex_type: TextureType = TextureType.TYPE_2D,
                 filters: TextureFilter | tuple[TextureFilter, TextureFilter] | None = None,
                 address_mode: AddressMode = AddressMode.REPEAT,
                 anisotropic_level: int = 0,
                 ) -> None:
        super().__init__(width, height)
        self.id = tex_id
        self.tex_type = tex_type

        if isinstance(filters, TextureFilter):
            self.min_filter = filters
            self.mag_filter = filters
        else:
            self.min_filter, self.mag_filter = filters

        self.address_mode = address_mode
        self.internal_format = compression_format
        self.anisotropic_level = anisotropic_level

    def get_texture(self) -> CompressedTextureBase:
        return self

if pyglet.options.backend in ("opengl", "gles3", "gl2", "gles2"):
    from pyglet.graphics.api.gl.framebuffer import (  # noqa: F401
        Framebuffer,
        Renderbuffer,
        get_max_color_attachments,
        get_screenshot,
    )
    from pyglet.graphics.api.gl.texture import (
        CompressedTexture,  # noqa: F401
        Texture,
        TextureRegion,
        Texture3D,
        TextureArray,
        TextureArrayRegion,
        TextureGrid,
        get_max_texture_size,
        get_max_array_texture_layers,
    )
elif pyglet.options.backend in ("webgl"):
    from pyglet.graphics.api.webgl.texture import (
        Texture,
        TextureRegion,
        Texture3D,  # noqa: F401
        TextureArray,
        TextureArrayRegion,
        TextureGrid,  # noqa: F401
        get_max_texture_size,  # noqa: F401
        get_max_array_texture_layers,  # noqa: F401
    )
elif pyglet.options.backend == "vulkan":
    pass
