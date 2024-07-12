from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from pyglet import graphics
from pyglet.gl import (
    GL_BLEND,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_SRC_ALPHA,
    GL_TEXTURE0,
    glActiveTexture,
    glBindTexture,
    glBlendFunc,
    glDisable,
    glEnable,
)
from pyglet.text.layout.base import TextLayout

if TYPE_CHECKING:
    from pyglet.customtypes import AnchorX, AnchorY
    from pyglet.graphics import Batch
    from pyglet.graphics.shader import ShaderProgram
    from pyglet.image import Texture
    from pyglet.text.document import AbstractDocument


class ScrollableTextLayoutGroup(graphics.Group):
    """Default rendering group for :py:class:`~pyglet.text.layout.ScrollableTextLayout`.

    The group maintains internal state for specifying the viewable
    area, and for scrolling. Because the group has internal state
    specific to the text layout, the group is never shared.
    """
    scissor_area: ClassVar[tuple[int, int, int, int]] = 0, 0, 0, 0

    def __init__(self, texture: Texture, program: ShaderProgram, order: int = 1,  # noqa: D107
                 parent: graphics.Group | None = None) -> None:

        super().__init__(order=order, parent=parent)
        self.texture = texture
        self.program = program

    def set_state(self) -> None:
        self.program.use()
        self.program["scissor"] = True
        self.program["scissor_area"] = self.scissor_area

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(self.texture.target, self.texture.id)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def unset_state(self) -> None:
        glDisable(GL_BLEND)
        self.program.stop()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.texture})"

    def __eq__(self, other: object) -> bool:
        return self is other

    def __hash__(self) -> int:
        return id(self)


class ScrollableTextDecorationGroup(graphics.Group):
    """Create a text decoration rendering group.

    The group is created internally when a :py:class:`~pyglet.text.Label`
    is created; applications usually do not need to explicitly create it.
    """

    scissor_area: ClassVar[tuple[int, int, int, int]] = 0, 0, 0, 0

    def __init__(self, program: ShaderProgram, order: int = 0, parent: graphics.Group | None = None) -> None:  # noqa: D107
        super().__init__(order=order, parent=parent)
        self.program = program

    def set_state(self) -> None:
        self.program.use()
        self.program["scissor"] = True
        self.program["scissor_area"] = self.scissor_area

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def unset_state(self) -> None:
        glDisable(GL_BLEND)
        self.program.stop()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(scissor={self.scissor_area})"

    def __eq__(self, other: object) -> bool:
        return self is other

    def __hash__(self) -> int:
        return id(self)


class ScrollableTextLayout(TextLayout):
    """Display text in a scrollable viewport.

    This class does not display a scrollbar or handle scroll events; it merely
    clips the text that would be drawn in :py:func:`~pyglet.text.layout.TextLayout`
    to the bounds of the layout given by ``x``, ``y``, ``width`` and ``height``;
    and offsets the text by a scroll offset.

    Use ``view_x`` and ``view_y`` to scroll the text within the viewport.

    Attributes:
        group_class:
            Default group used to set the state for all glyphs.
        decoration_class:
            Default group used to set the state for all decorations including background colors and underlines.
    """

    group_class: ClassVar[type[ScrollableTextLayoutGroup]] = ScrollableTextLayoutGroup
    decoration_class: ClassVar[type[ScrollableTextDecorationGroup]] = ScrollableTextDecorationGroup

    _translate_x: int = 0
    _translate_y: int = 0

    def __init__(self, document: AbstractDocument, width: int, height: int, x: float = 0, y: float = 0, z: float = 0,  # noqa: D107
                 anchor_x: AnchorX = "left", anchor_y: AnchorY = "bottom", rotation: float = 0, multiline: bool = False,
                 dpi: int | None = None, batch: Batch | None = None, group: graphics.Group | None = None,
                 program: ShaderProgram | None = None, wrap_lines: bool = True) -> None:

        if width is None or height is None:
            msg = "Invalid size. ScrollableTextLayout width or height cannot be None."
            raise Exception(msg)

        super().__init__(document, width, height, x, y, z, anchor_x, anchor_y, rotation, multiline, dpi, batch, group,
                         program, wrap_lines)

    def _update_scissor_area(self) -> None:
        if not self.document.text:
            return

        area = (self.left, self.bottom, self._width, self._height)

        for group in self.group_cache.values():
            group.scissor_area = area

        self.background_decoration_group.scissor_area = area
        self.foreground_decoration_group.scissor_area = area

    def _update(self) -> None:
        super()._update()
        self._update_scissor_area()

    # Properties

    @property
    def x(self) -> float:
        return self._x

    @x.setter
    def x(self, x: float) -> None:
        super()._set_x(x)
        self._update_scissor_area()

    @property
    def y(self) -> float:
        return self._y

    @y.setter
    def y(self, y: float) -> None:
        super()._set_y(y)
        self._update_scissor_area()

    @property
    def z(self) -> float:
        return self._z

    @z.setter
    def z(self, z: float) -> None:
        super()._set_z(z)
        self._update_scissor_area()

    @property
    def position(self) -> tuple[float, float, float]:
        return self._x, self._y, self._z

    @position.setter
    def position(self, position: tuple[float, float, float]) -> None:
        super()._set_position(position)
        self._update_scissor_area()

    @property
    def anchor_x(self) -> AnchorX:
        return self._anchor_x

    @anchor_x.setter
    def anchor_x(self, anchor_x: AnchorX) -> None:
        self._anchor_x = anchor_x
        self._update_anchor()
        self._update_scissor_area()
        self._update_view_translation()

    @property
    def anchor_y(self) -> AnchorY:
        return self._anchor_y

    @anchor_y.setter
    def anchor_y(self, anchor_y: AnchorY) -> None:
        self._anchor_y = anchor_y
        self._update_anchor()
        self._update_scissor_area()
        self._update_view_translation()

    def _get_bottom_anchor(self) -> float:
        """Returns the anchor for the Y axis from the bottom."""
        height = self._height
        if self._content_valign == "top":
            offset = min(0, self._height)
        elif self._content_valign == "bottom":
            offset = 0
        elif self._content_valign == "center":
            offset = min(0, self._height) // 2
        else:
            msg = '`content_valign` must be either "top", "bottom", or "center".'
            raise Exception(msg)

        if self._anchor_y == "top":
            return -height + offset
        if self._anchor_y == "baseline":
            return -height + self._ascent
        if self._anchor_y == "bottom":
            return 0
        if self._anchor_y == "center":
            if self._line_count == 1 and self._height is None:
                # This "looks" more centered than considering all of the descent.
                return (self._ascent // 2 - self._descent // 4) - height

            return offset - height // 2

        msg = '`anchor_y` must be either "top", "bottom", "center", or "baseline".'
        raise Exception(msg)

    def _update_view_translation(self) -> None:
        # Offset of content within viewport
        for _vertex_list in self._vertex_lists:
            _vertex_list.view_translation[:] = (-self._translate_x, -self._translate_y, 0) * _vertex_list.count

    @property
    def view_x(self) -> int:
        """Horizontal scroll offset.

        The initial value is 0, and the left edge of the text will touch the left
        side of the layout bounds.  A positive value causes the text to "scroll"
        to the right.  Values are automatically clipped into the range
        ``[0, content_width - width]``
        """
        return self._translate_x

    @view_x.setter
    def view_x(self, view_x: int) -> None:
        translation = max(0, min(self._content_width - self._width, view_x))
        if translation != self._translate_x:
            self._translate_x = translation
            self._update_view_translation()

    @property
    def view_y(self) -> int:
        """Vertical scroll offset.

        The initial value is 0, and the top of the text will touch the top of the
        layout bounds (unless the content height is less than the layout height,
        in which case `content_valign` is used).

        A negative value causes the text to "scroll" upwards.  Values outside of
        the range ``[height - content_height, 0]`` are automatically clipped in
        range.
        """
        return self._translate_y

    @view_y.setter
    def view_y(self, view_y: int) -> None:
        # view_y must be negative.
        translation = min(0, max(self.height - self._content_height, view_y))
        if translation != self._translate_y:
            self._translate_y = translation
            self._update_view_translation()
