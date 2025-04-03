from __future__ import annotations

from typing import Iterator, Literal, NamedTuple, Sequence

import pyglet
from pyglet.enums import AddressMode, ComponentFormat, TextureFilter, TextureType
from pyglet.image.base import (
    AbstractImage,
    AbstractImageSequence,
    ImageData,
    ImageDataRegion,
    ImageException,
    ImageGrid,
)


class TextureArraySizeExceeded(ImageException):
    """Exception occurs ImageData dimensions are larger than the array supports."""


class TextureArrayDepthExceeded(ImageException):
    """Exception occurs when depth has hit the maximum supported of the array."""


class TextureSequence(AbstractImageSequence):
    """Interface for a sequence of textures.

    Typical implementations store multiple :py:class:`~pyglet.graphics.TextureRegion`s
    within one :py:class:`~pyglet.graphics.Texture` to minimise state changes.
    """

    def __getitem__(self, item) -> TextureBase:
        raise NotImplementedError

    def __setitem__(self, item, texture: type[TextureBase]) -> AbstractImage:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    def __iter__(self) -> Iterator[TextureBase]:
        raise NotImplementedError

    def get_texture_sequence(self) -> TextureSequence:
        return self


class TextureInternalFormat(NamedTuple):
    component: ComponentFormat | str
    depth: int | None = None
    data_type: type[float, int] | None = None


class TextureDescriptor:
    __slots__ = ("tex_type", "min_filter", "mag_filter", "address_mode", "internal_format", "pixel_format",
                 "anisotropic_level", "depth", "mipmap_levels")

    def __init__(self,
                 tex_type: TextureType = TextureType.TYPE_2D,
                 min_filter: TextureFilter = TextureFilter.LINEAR,
                 mag_filter: TextureFilter = TextureFilter.LINEAR,
                 address_mode: AddressMode = AddressMode.REPEAT,
                 internal_format: TextureInternalFormat | None = None,
                 pixel_format: ComponentFormat = ComponentFormat.RGBA,
                 anisotropic_level: int = 0,
                 depth: int = 1,
                 mipmap_levels: int = 1):
        """Create a description of the texture.

        Args:
            tex_type:
                The default texture type. Defaults to TYPE_2D.
            min_filter:
                The default minification filter. Defaults to LINEAR.
            mag_filter:
                The default magnification filter. Defaults to LINEAR.
            address_mode:
                The border repeat mode for textures once values fall outside 0-1.
            internal_format:
                The internal pixel format of the intended texture. Defaults to RGBA 8bits per channel.
            pixel_format:
                The pixel format order of the data that will be written. Defaults to RGBA.
            anisotropic_level:
                The anisotropic filtering level, 0 is disabled. Not always supported.
        """
        self.tex_type = tex_type
        self.min_filter = min_filter
        self.mag_filter = mag_filter
        self.address_mode = address_mode
        self.internal_format = internal_format or TextureInternalFormat(ComponentFormat.RGBA, 8)
        self.pixel_format = pixel_format
        self.anisotropic_level = anisotropic_level


class TextureBase(AbstractImage):
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

    colors = (0, 0, 0, 0) * 4

    level: int = 0
    """The mipmap level of this texture."""

    images = 1

    x: int = 0
    y: int = 0
    z: int = 0

    # Default image descriptor used. This is a backend agnostic implementation.
    default_descriptor = TextureDescriptor(
        tex_type=TextureType.TYPE_2D,
        min_filter=TextureFilter.LINEAR,
        mag_filter=TextureFilter.LINEAR,
        address_mode=AddressMode.REPEAT,
        internal_format=TextureInternalFormat(ComponentFormat.RGBA, 8),
        pixel_format=ComponentFormat.RGBA,
    )

    def __init__(self, width: int, height: int, tex_id: int, descriptor: TextureDescriptor | None) -> None:
        super().__init__(width, height)
        self.id = tex_id
        self.descriptor = descriptor or self.default_descriptor

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
    def create(cls, width: int, height: int, descriptor: TextureDescriptor | None = None,
               blank_data: bool = True) -> TextureBase:
        """Create a Texture.

        Create a Texture with the specified dimentions, target and format.
        On return, the texture will be bound.

        Args:
            width:
                Width of texture in pixels.
            height:
                Height of texture in pixels.
            descriptor:
                The descriptor information of the intended texture.
            blank_data:
                If True, initialize the texture data with all zeros. If False, do not pass initial data.
        """
        raise NotImplementedError

    @classmethod
    def create_from_image(cls, image_data: ImageData | ImageDataRegion, texture_descriptor: TextureDescriptor | None = None) -> TextureBase:
        """Create a Texture from image data.

        On return, the texture will be bound.

        Args:
            image_data:
                The image instance.
            texture_descriptor:
                Description of the Texture.
        """

    def get_image_data(self, z: int = 0) -> ImageData:
        """To be removed and replaced with fetch."""
        raise NotImplementedError

    def get_texture(self) -> TextureBase:
        return self

    def blit(self, x: int, y: int, z: int = 0, width: int | None = None, height: int | None = None) -> None:
        """Blit the texture to the screen.

        This is a costly operation, and should not be used for performance critical
        code. Blitting a texture requires binding it, setting up throwaway buffers,
        creating a VAO, uploading attribute data, and then making a single draw call.
        This is quite wasteful and slow, so blitting should not be used for more than
        a few images. This method is provided to assist with debugging, but not intended
        for drawing of multiple images.

        Instead, consider creating a :py:class:`~pyglet.sprite.Sprite` with the Texture,
        and drawing it as part of a larger :py:class:`~pyglet.graphics.Batch`.
        """
        raise NotImplementedError

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

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, size={self.width}x{self.height})"


class TextureRegionBase(TextureBase):
    """A rectangular region of a texture, presented as if it were a separate texture."""

    def __init__(self, x: int, y: int, z: int, width: int, height: int, owner: TextureBase):
        super().__init__(width, height, owner.id, owner.descriptor)

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
        import traceback
        traceback.print_stack()
        raise Exception

    def fetch(self, _z = 0) -> ImageDataRegion:
        image_data = self.owner.get_image_data(self.z)
        return image_data.get_region(self.x, self.y, self.width, self.height)

    def get_image_data(self):
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


class TextureArrayRegion(TextureRegionBase):
    """A region of a TextureArray, presented as if it were a separate texture."""

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, size={self.width}x{self.height}, layer={self.z})"


class TextureArray(TextureBase, UniformTextureSequence):
    default_descriptor = TextureDescriptor(
        tex_type=TextureType.TYPE_2D_ARRAY,
        min_filter=TextureFilter.LINEAR,
        mag_filter=TextureFilter.LINEAR,
    )
    def __init__(self, width, height, tex_id, max_depth, descriptor: TextureDescriptor | None = None):
        super().__init__(width, height, tex_id, descriptor or self.default_descriptor)
        self.max_depth = max_depth
        self.items = []

    @classmethod
    def create(cls, width: int, height: int, descriptor: TextureDescriptor | None = None, max_depth: int = 256) -> TextureArray:
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

    def _verify_size(self, image: AbstractImage) -> None:
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

    def allocate(self, *images: AbstractImage) -> list[TextureArrayRegion]:
        """Allocates multiple images at once."""
        raise NotImplementedError

    @classmethod
    def create_for_image_grid(cls, grid, descriptor: TextureDescriptor | None = None) -> TextureArray:
        texture_array = cls.create(grid[0].width, grid[0].height, descriptor, max_depth=len(grid))
        texture_array.allocate(*grid[:])
        return texture_array

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
    default_descriptor = TextureDescriptor(
        tex_type=TextureType.TYPE_3D,
        min_filter=TextureFilter.LINEAR,
        mag_filter=TextureFilter.LINEAR,
    )

    @classmethod
    def create_for_images(cls, images, descriptor: TextureDescriptor | None = None, blank_data=True):
        raise NotImplementedError

    @classmethod
    def create_for_image_grid(cls, grid, descriptor: TextureDescriptor | None = None):
        return cls.create_for_images(grid[:], descriptor)

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        return self.items[index]

    def __setitem__(self, index, value):
        raise NotImplementedError

    def __iter__(self) -> Iterator[TextureRegionBase]:
        return iter(self.items)


class TileableTexture(TextureBase):
    """A texture that can be tiled efficiently.

    Use :py:class:`~pyglet.image.create_for_image` classmethod to construct.
    """

    def get_region(self, x: int, y: int, width: int, height: int):
        raise ImageException(f"Cannot get region of {self}")

    def blit_tiled(self, x: int, y: int, z: int, width: int, height: int) -> None:
        """Blit this texture tiled over the given area.

        The image will be tiled with the bottom-left corner of the destination
        rectangle aligned with the anchor point of this texture.
        """
        raise NotImplementedError

    @classmethod
    def create_for_image(cls, image: AbstractImage) -> TextureBase:
        raise NotImplementedError


class TextureGridBase(TextureRegionBase, UniformTextureSequence):
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
    items: list
    rows: int
    columns: int
    item_width: int
    item_height: int

    def __init__(self, grid: ImageGrid) -> None:
        image = grid.get_texture()
        if isinstance(image, TextureRegionBase):
            owner = image.owner
        else:
            owner = image

        super().__init__(image.x, image.y, image.z, image.width, image.height, owner)

        items = []
        y = 0
        for row in range(grid.rows):
            x = 0
            for col in range(grid.columns):
                items.append(self.get_region(x, y, grid.item_width, grid.item_height))
                x += grid.item_width + grid.column_padding
            y += grid.item_height + grid.row_padding

        self.items = items
        self.rows = grid.rows
        self.columns = grid.columns
        self.item_width = grid.item_width
        self.item_height = grid.item_height

    def get(self, row: int, column: int):
        return self[(row, column)]

    def __getitem__(self, index: int | tuple[int, int] | slice) -> TextureRegionBase | list[TextureRegionBase]:
        if type(index) is slice:
            if type(index.start) is not tuple and type(index.stop) is not tuple:
                return self.items[index]
            else:
                row1 = 0
                col1 = 0
                row2 = self.rows
                col2 = self.columns
                if type(index.start) is tuple:
                    row1, col1 = index.start
                elif type(index.start) is int:
                    row1 = index.start // self.columns
                    col1 = index.start % self.columns
                assert 0 <= row1 < self.rows and 0 <= col1 < self.columns

                if type(index.stop) is tuple:
                    row2, col2 = index.stop
                elif type(index.stop) is int:
                    row2 = index.stop // self.columns
                    col2 = index.stop % self.columns
                assert 0 <= row2 <= self.rows and 0 <= col2 <= self.columns

                result = []
                i = row1 * self.columns
                for row in range(row1, row2):
                    result += self.items[i + col1:i + col2]
                    i += self.columns
                return result
        else:
            if type(index) is tuple:
                row, column = index
                assert 0 <= row < self.rows and 0 <= column < self.columns
                return self.items[row * self.columns + column]
            elif type(index) is int:
                return self.items[index]

    def __setitem__(self, index: int | slice, value: AbstractImage | Sequence[AbstractImage]):
        if type(index) is slice:
            for region, image in zip(self[index], value):
                if image.width != self.item_width or image.height != self.item_height:
                    raise ImageException('Image has incorrect dimensions')
                image.blit_into(region, image.anchor_x, image.anchor_y, 0)
        else:
            image = value
            if image.width != self.item_width or image.height != self.item_height:
                raise ImageException('Image has incorrect dimensions')
            image.blit_into(self[index], image.anchor_x, image.anchor_y, 0)

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self) -> Iterator[TextureRegionBase]:
        return iter(self.items)


class BufferImage(AbstractImage):
    """An abstract "default" framebuffer."""

    #: The OpenGL read and write target for this buffer.
    #gl_buffer = GL_BACK

    #: The OpenGL format constant for image data.
    #gl_format = 0

    #: The format string used for image data.
    format = ''

    owner = None

    def __init__(self, x, y, width, height):
        super().__init__(width, height)
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def get_image_data(self) -> ImageData:
        raise NotImplementedError

    def get_region(self, x, y, width, height):
        if self.owner:
            return self.owner.get_region(x + self.x, y + self.y, width, height)

        region = self.__class__(x + self.x, y + self.y, width, height)
        #region.gl_buffer = self.gl_buffer
        region.owner = self
        return region

    def get_texture(self ) -> TextureBase:
        raise NotImplementedError(f"Not implemented for {self}")

    def get_mipmapped_texture(self) -> TextureBase:
        raise NotImplementedError(f"Not implemented for {self}")

    def blit(self, x: int, y: int, z: int = 0) -> None:
        raise NotImplementedError(f"Not implemented for {self}")

    def blit_into(self, source, x: int, y: int, z: int) -> None:
        raise NotImplementedError(f"Not implemented for {self}")

    def blit_to_texture(self, target: int, level: int, x: int, y: int, z: int, internalformat: int = None):
        raise NotImplementedError(f"Not implemented for {self}")


class ColorBufferImage(BufferImage):
    """A color framebuffer.

    This class is used to wrap the primary color buffer (i.e., the back
    buffer)
    """
    #gl_format = GL_RGBA
    #format = 'RGBA'

    def get_texture(self):
        texture = TextureBase.create(self.width, self.height, TextureDescriptor(), blank_data=False)
        self.blit_to_texture(texture.target, texture.level, self.anchor_x, self.anchor_y, 0)
        return texture

    def blit_to_texture(self, target: int, level: int, x: int, y: int, z: int, internalformat: int = None):
        raise NotImplementedError


class DepthBufferImage(BufferImage):
    """The depth buffer.
    """
    #gl_format = GL_DEPTH_COMPONENT
    #format = 'R'

    def get_texture(self):
        image_data = self.get_image_data()
        return image_data.get_texture()

    def blit_to_texture(self, target: int, level: int, x: int, y: int, z: int, internalformat: int = None):
        raise NotImplementedError


class BufferImageMask(BufferImage):
    """A single bit of the stencil buffer."""
    #gl_format = GL_STENCIL_INDEX
    #format = 'R'

    # TODO mask methods

TextureBase.region_class = TextureRegionBase

TextureArray.region_class = TextureArrayRegion
TextureArrayRegion.region_class = TextureArrayRegion


if pyglet.options.backend in ("opengl", "gl2", "gles2"):
    from pyglet.graphics.api.gl.framebuffer import (  # noqa: F401
        BufferImage,
        BufferImageMask,
        BufferManager,
        DepthBufferImage,
        get_buffer_manager,
        Framebuffer,
        Renderbuffer,
        get_max_color_attachments,
    )
    from pyglet.graphics.api.gl.texture import (  # noqa: F401
        Texture,
        TextureRegion,
        Texture3D,
        TextureArray,
        TextureArrayRegion,
        TextureGrid,
        get_max_texture_size,
        get_max_array_texture_layers,
    )
elif pyglet.options.backend == "vulkan":
    pass
