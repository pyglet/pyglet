from __future__ import annotations

from typing import TYPE_CHECKING

from pyglet.enums import Anchor, BlendFactor, GeometryMode
from pyglet.sprite import Sprite

if TYPE_CHECKING:
    from pyglet.image import Animation
    from pyglet.graphics import Batch, Group, Texture
    from pyglet.text.layout import TextLayout


class NinePatch(Sprite):
    """Pseudo Nine-patch object for variable sized dialog windows.

    This class takes in a single image, splits it into 9 equal parts,
    and allows creating variable sized dialog windows without distorting
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

    _left_edge: float
    _right_edge: float
    _bottom_edge: float
    _top_edge: float

    def __init__(self,
                 img: Texture | Animation,
                 x: float = 0, y: float = 0, z: float = 0,
                 anchor: Anchor | str | tuple[float, float] | None = None,
                 width: int | None = None, height: int | None = None,
                 blend_src: BlendFactor = BlendFactor.SRC_ALPHA,
                 blend_dest: BlendFactor = BlendFactor.ONE_MINUS_SRC_ALPHA,
                 batch: Batch | None = None,
                 group: Group | None = None,
                 edge_sizes: tuple[int, int, int, int] | None = None):
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
            anchor:
                Anchor offset relative to the NinePatch's lower-left corner.
                Pass a numeric ``(x, y)`` tuple for an explicit offset, or a
                named anchor such as ``"bottom_center"``. Named anchors are
                recalculated when the NinePatch dimensions change.
            width:
                The desired width of the NinePatch. This must be
                greater or equal to the provided image width.
            height:
                The desired height of the NinePatch. This must be
                greater or equal to the provided image height.
            blend_src:
                Blend source factor.
            blend_dest:
                Blend destination factor.
            batch:
                Optional batch to add the NinePatch to.
            group:
                Optional parent group of the NinePatch.
            edge_sizes:
                Optional ``(left, right, bottom, top)`` source-edge dimensions.
                When omitted, the source image is split into equal thirds.
        """
        self._width = max(width or img.width, img.width)
        self._height = max(height or img.height, img.height)
        self._set_edge_sizes(edge_sizes, img.width, img.height)
        self._rgba: tuple[int, int, int, int]
        super().__init__(img, x, y, z, anchor, blend_src, blend_dest, batch, group)

    @classmethod
    def create_around_layout(cls,
                             img: Texture | Animation,
                             layout: TextLayout,
                             border: int = 0,
                             blend_src: BlendFactor = BlendFactor.SRC_ALPHA,
                             blend_dest: BlendFactor = BlendFactor.ONE_MINUS_SRC_ALPHA,
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
                Blend source factor.
            blend_dest:
                Blend destination factor.
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
        return cls(img, x, y, z, width=width, height=height, blend_src=blend_src,
                   blend_dest=blend_dest, batch=batch, group=group)

    def _resolve_anchor(self) -> None:
        if self._anchor is not None:
            self._anchor_x, self._anchor_y = self._anchor.get_position(self._width, self._height)

    def _set_edge_sizes(
        self,
        edge_sizes: tuple[int, int, int, int] | None,
        width: int,
        height: int,
    ) -> None:
        if edge_sizes is None:
            self._left_edge = self._right_edge = width / 3
            self._bottom_edge = self._top_edge = height / 3
            return

        left, right, bottom, top = edge_sizes
        if min(left, right, bottom, top) < 0 or left + right >= width or bottom + top >= height:
            raise ValueError("NinePatch edge dimensions must leave a non-empty center region")
        self._left_edge = left
        self._right_edge = right
        self._bottom_edge = bottom
        self._top_edge = top

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

        self._vertex_list = self.program.vertex_list_indexed(
            16, GeometryMode.TRIANGLE_STRIP, indices, self._batch, self._group,
            position=self._get_vertices(),
            colors=self._rgba * 16,
            translate=(self._x, self._y, self._z) * 16,
            scale=(self._scale*self._scale_x, self._scale*self._scale_y) * 16,
            rotation=(self._rotation,) * 16,
            tex_coords=self._get_tex_coords())

    def _get_tex_coords(self) -> tuple[float, ...]:
        """Return texture coordinates split at this patch's source edges."""
        uv_x, uv_y, uv_w, uv_h = self._texture.uv
        u_scale = (uv_w - uv_x) / self._texture.width
        v_scale = (uv_h - uv_y) / self._texture.height
        u_values = uv_x, uv_x + self._left_edge * u_scale, uv_w - self._right_edge * u_scale, uv_w
        v_values = uv_y, uv_y + self._bottom_edge * v_scale, uv_h - self._top_edge * v_scale, uv_h
        return tuple(coordinate for v in v_values for u in u_values for coordinate in (u, v, 0))

    def _get_vertices(self) -> tuple:
        if not self._visible:
            return (0, 0, 0) * 16
        center_width = self._width - self._left_edge - self._right_edge
        center_height = self._height - self._bottom_edge - self._top_edge

        x0 = -self._anchor_x
        x1 = x0 + self._left_edge
        x2 = x1 + center_width
        x3 = x2 + self._right_edge
        y0 = -self._anchor_y
        y1 = y0 + self._bottom_edge
        y2 = y1 + center_height
        y3 = y2 + self._top_edge
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

        The NinePatch is rotated about its :attr:`anchor_position`.
        """
        return self._rotation

    @rotation.setter
    def rotation(self, rotation: float):
        self._rotation = rotation  # type: ignore[assignment]
        self._vertex_list.rotation[:] = (self._rotation,) * 16

    @property  # type: ignore[misc]
    def scale(self) -> float:
        raise NotImplementedError("Not supported. Use `width`/`height` instead.")

    @property  # type: ignore[misc]
    def scale_x(self) -> float:
        raise NotImplementedError("Not supported. Use `width` instead.")

    @property  # type: ignore[misc]
    def scale_y(self) -> float:
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
        self._resolve_anchor()
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
        self._resolve_anchor()
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
