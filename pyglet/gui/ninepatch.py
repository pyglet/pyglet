from __future__ import annotations

from typing import TYPE_CHECKING

from pyglet.gl import GL_TRIANGLE_STRIP, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA
from pyglet.sprite import Sprite

if TYPE_CHECKING:
    from pyglet.image import AbstractImage, Animation
    from pyglet.graphics import Batch, Group
    from pyglet.text.layout import TextLayout


class NinePatch(Sprite):
    """Pseudo Nine-patch object for variable sized dialog windows.

    This class takes in a single image, splits it into 9 equal parts,
    and allows creating variable sized dialog windows without distoring
    the aspect of the edges. This is not a "real" nine-patch, as it
    does not look for any embedded markers in the image data. Instead,
    it simply splits the source image into 9 equally sized segments,
    and stretches the center segments to allow dynamic sizing. Make
    sure your input images do not have any transparent borders, as
    this can affect the final size.

    NinePatch is a subclass of :py:class:`~pyglet.sprite.Sprite`,
    and shares most of the same API. The exception is that scaling
    properties cannot be used, and will raise an exception. Instead,
    use :py:meth:`NinePatch.width` and :py:meth:`NinePatch.height`
    properties if you want to change the size after creation.
    """

    def __init__(self,
                 img: AbstractImage | Animation,
                 x: float = 0, y: float = 0, z: float = 0,
                 width: int | None = None, height: int | None = None,
                 blend_src: int = GL_SRC_ALPHA,
                 blend_dest: int = GL_ONE_MINUS_SRC_ALPHA,
                 batch: Batch | None = None,
                 group: Group | None = None):
        """Create a NinePatch instance.

        Args:
            img:
                The Image to split into segments.
            x:
                The X coordinate of the NinePatch.
            y:
                The Y coordinate of the NinePatch.
            z:
                The Z coordinate of the NinePatch.
            width:
                The desired width of the NinePatch. This must be
                greater or equal to the provided image width.
            height:
                The desired height of the NinePatch. This must be
                greater or equal to the provided image height.
            blend_src:
                OpenGL blend source mode; for example, ``GL_SRC_ALPHA``.
            blend_dest:
                OpenGL blend destination mode; for example, ``GL_ONE_MINUS_SRC_ALPHA``.
            batch:
                Optional batch to add the NinePatch to.
            group:
                Optional parent group of the NinePatch.
        """

        self._width = max(width, img.width)
        self._height = max(height, img.height)
        super().__init__(img, x, y, z, blend_src, blend_dest, batch, group)

    @classmethod
    def create_around_layout(cls,
                             img: AbstractImage | Animation,
                             layout: TextLayout,
                             border: int = 0,
                             blend_src: int = GL_SRC_ALPHA,
                             blend_dest: int = GL_ONE_MINUS_SRC_ALPHA,
                             batch: Batch | None = None,
                             group: Group | None = None):
        """Given a Label, create a NinePatch instance sized to surround it.

        A NinePatch instance will be created that is sized to the Layout's left, bottom,
        right, and top attributes. This happens at the time of creation, and is not dynamic.

        The NinePatch's ``z`` position will be set to the Layout's ``z`` position - 1. This
        will help ensure the NinePatch renders below the label *if* OpenGL depth testing is
        enabled. If not, you should provide a Group with a proper ordering to ensure the
        correct rendering order.

        Args:
            img:
                The Image to split into segments.
            layout:
                A pyglet Label or Layout instance to query the size from.
            border:
                Additional padding, in pixels, to place around the label.
            blend_src:
                OpenGL blend source mode; for example, ``GL_SRC_ALPHA``.
            blend_dest:
                OpenGL blend destination mode; for example, ``GL_ONE_MINUS_SRC_ALPHA``.
            batch:
                Optional batch to add the NinePatch to.
            group:
                Optional parent group of the NinePatch.
        """

        x = layout.left - border
        y = layout.bottom - border
        z = layout.z - 1
        width = int(layout.right - x + border)
        height = int(layout.top - y + border)
        return cls(img, x, y, z, width, height, blend_src, blend_dest, batch, group)

    def _create_vertex_list(self) -> None:
        # Vertex layout for 9 quads:
        #
        #   12----13----14----15
        #   |  /  |  /  |  /  |
        #   8-----9-----10----11
        #   |  /  |  /  |  /  |
        #   4-----5-----6-----7
        #   |  /  |  /  |  /  |
        #   0-----1-----2-----3

        # Triangle strip indices, including degenerates (duplicates)
        indices = (0, 0, 4, 1, 5, 2, 6, 3, 7,       # bottom row -->
                   11, 6, 10, 5, 9, 4, 8,           # center row <--
                   12, 9, 13, 10, 14, 11, 15, 15)   # upper row  -->

        # Get the 1/3 size of texture width & height:
        uv_x, uv_y, uv_w, uv_h = self._texture.uv
        seg_w = (uv_w - uv_x) / 3
        seg_h = (uv_h - uv_y) / 3

        # Create new UV coordinates for each of the 9 quads:
        uvs = [i for v in range(4) for h in range(4) for i in (uv_x + seg_w * h, uv_y + seg_h * v, 0)]

        self._vertex_list = self.program.vertex_list_indexed(
            16, GL_TRIANGLE_STRIP, indices, self._batch, self._group,
            position=('f', self._get_vertices()),
            colors=('Bn', self._rgba * 16),
            translate=('f', (self._x, self._y, self._z) * 16),
            scale=('f', (self._scale*self._scale_x, self._scale*self._scale_y) * 16),
            rotation=('f', (self._rotation,) * 16),
            tex_coords=('f', uvs))

    def _get_vertices(self) -> tuple:
        if not self._visible:
            return (0, 0, 0) * 16
        else:
            img = self._texture
            edge_width = img.width / 3
            edge_height = img.height / 3
            center_width = self._width - edge_width - edge_width
            center_height = self._height - edge_height - edge_height

            x0 = -img.anchor_x
            x1 = x0 + edge_width
            x2 = x1 + center_width
            x3 = x2 + edge_width
            y0 = -img.anchor_y
            y1 = y0 + edge_height
            y2 = y1 + center_height
            y3 = y2 + edge_height
            z = 0   # handled by translate attribute

            return (x0, y0, z, x1, y0, z, x2, y0, z, x3, y0, z,
                    x0, y1, z, x1, y1, z, x2, y1, z, x3, y1, z,
                    x0, y2, z, x1, y2, z, x2, y2, z, x3, y2, z,
                    x0, y3, z, x1, y3, z, x2, y3, z, x3, y3, z)

    @property
    def position(self) -> tuple[float, float, float]:
        """The (x, y, z) coordinates of the NinePatch, as a tuple."""
        return self._x, self._y, self._z

    @position.setter
    def position(self, position: tuple[float, float, float]) -> None:
        self._x, self._y, self._z = position
        self._vertex_list.translate[:] = position * 16

    @property
    def x(self) -> float:
        """X coordinate of the NinePatch."""
        return self._x

    @x.setter
    def x(self, x):
        self._x = x
        self._vertex_list.translate[:] = (x, self._y, self._z) * 16

    @property
    def y(self) -> float:
        """Y coordinate of the NinePatch."""
        return self._y

    @y.setter
    def y(self, y):
        self._y = y
        self._vertex_list.translate[:] = (self._x, y, self._z) * 16

    @property
    def z(self) -> float:
        """Z coordinate of the NinePatch."""
        return self._z

    @z.setter
    def z(self, z):
        self._z = z
        self._vertex_list.translate[:] = (self._x, self._y, z) * 16

    @property
    def rotation(self) -> float:
        """Clockwise rotation of the NinePatch, in degrees.

        The NinePatch will be rotated about its image's (anchor_x, anchor_y)
        position.
        """
        return self._rotation

    @rotation.setter
    def rotation(self, rotation: float):
        self._rotation = rotation
        self._vertex_list.rotation[:] = (self._rotation,) * 16

    @property
    def scale(self) -> float:
        raise NotImplementedError("Not supported. Use `width`/`height` instead.")

    @property
    def scale_x(self) -> float:
        raise NotImplementedError("Not supported. Use `width` instead.")

    @property
    def scale_y(self):
        raise NotImplementedError("Not supported. Use `height` instead.")

    def update(self, *args, **kwargs):
        raise NotImplementedError("Not supported on NinePatch objects.")

    @property
    def width(self) -> float:
        """The width of the NinePatch.

        Invariant under rotation.
        """
        return self._width

    @width.setter
    def width(self, width: float):
        self._width = width
        self._update_position()

    @property
    def height(self) -> float:
        """The height of the NinePatch.

        Invariant under rotation.
        """
        return self._height

    @height.setter
    def height(self, height: float):
        self._height = height
        self._update_position()

    @property
    def opacity(self) -> int:
        """Blend opacity.

        This property sets the alpha component of the colour of the sprite's
        vertices.  With the default blend mode (see the constructor), this
        allows the sprite to be drawn with fractional opacity, blending with the
        background.

        An opacity of 255 (the default) has no effect.  An opacity of 128 will
        make the sprite appear translucent.
        """
        return self._rgba[3]

    @opacity.setter
    def opacity(self, opacity: int):
        r, g, b, _ = self._rgba
        self._rgba = r, g, b, opacity
        self._vertex_list.colors[:] = self._rgba * 16

    @property
    def color(self) -> tuple[int, int, int, int]:
        """Blend color.

        This property sets the color of the sprite's vertices. This allows the
        sprite to be drawn with a color tint.

        The color is specified as either an RGBA tuple of integers
        '(red, green, blue, opacity)' or an RGB tuple of integers
        `(red, blue, green)`.

        If there are fewer than three components, a :py:func`ValueError`
        will be raised. Each color component must be an int in the range
        0 (dark) to 255 (saturated). If any component is not an int, a
        :py:class:`TypeError` will be raised.
        """
        return self._rgba

    @color.setter
    def color(self, rgba: tuple[int, int, int, int] | tuple[int, int, int]):
        # ValueError raised by unpacking if len(rgba) < 3
        r, g, b, *a = rgba
        new_color = r, g, b, a[0] if a else 255

        # Only update if we actually have to
        if new_color != self._rgba:
            self._rgba = new_color
            self._vertex_list.colors[:] = new_color * 16
