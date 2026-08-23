from __future__ import annotations

import sys
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
)

import pyglet

from pyglet import graphics
from pyglet.enums import BlendFactor, CompareOp, GraphicsAPI
from pyglet.graphics import Group, ShaderProgram
from pyglet.text.effects import LinearGradient
from pyglet.text.layout.boxes import (
    _AbstractBox,
    _InlineElementBox,  # noqa: F401
    _InvalidRange,  # noqa: F401
    _LayoutContext,
    _LayoutVertexList,
    _Line,  # noqa: F401
    _StaticLayoutContext,
    _parse_distance,
)
from pyglet.text.layout.flow import _FlowLayoutBase

if TYPE_CHECKING:
    from pyglet.customtypes import AnchorX, AnchorY, ContentVAlign, RGBAColor
    from pyglet.graphics import Batch
    from pyglet.graphics.shader import ShaderProgram
    from pyglet.graphics import Texture, TextureRenderTarget
    from pyglet.text.document import AbstractDocument

_is_pyglet_doc_run = hasattr(sys, "is_pyglet_doc_run") and sys.is_pyglet_doc_run

if pyglet.options.backend in (GraphicsAPI.OPENGL, GraphicsAPI.OPENGL_ES_3):
    from pyglet.graphics.api.gl.text import (
        get_default_decoration_shader,
        get_default_image_layout_shader,
        get_default_layout_shader,
        get_default_scrollable_layout_shader,  # noqa: F401
    )
elif pyglet.options.backend in (GraphicsAPI.OPENGL_2, GraphicsAPI.OPENGL_ES_2):
    from pyglet.graphics.api.gl2.text import (
        get_default_decoration_shader,
        get_default_image_layout_shader,
        get_default_layout_shader,
        get_default_scrollable_layout_shader,  # noqa: F401
    )
elif pyglet.options.backend == GraphicsAPI.WEBGL:
    from pyglet.graphics.api.webgl.text import (
        get_default_decoration_shader,
        get_default_image_layout_shader,  # noqa: F401
        get_default_layout_shader,
        get_default_scrollable_layout_shader,  # noqa: F401
    )


class TextLayoutGroup(Group):
    """Create a text layout rendering group.

    The group is created internally when a :py:class:`~pyglet.text.Label`
    is created; applications usually do not need to explicitly create it.
    """

    def __init__(
        self,
        texture: Texture,
        program: ShaderProgram,
        order: int = 1,  # noqa: D107
        parent: Group | None = None,
    ) -> None:
        super().__init__(order=order, parent=parent)
        self.uniforms = {"scissor": False}
        self.texture = texture
        self.set_shader_program(program)
        self.set_blend(BlendFactor.SRC_ALPHA, BlendFactor.ONE_MINUS_SRC_ALPHA)
        self.set_texture(texture, 0)
        self.set_shader_uniforms(program, self.uniforms)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.texture})"


class TextDecorationGroup(Group):
    """Create a text decoration rendering group.

    The group is created internally when a :py:class:`~pyglet.text.Label`
    is created; applications usually do not need to explicitly create it.
    """

    def __init__(
        self,
        program: ShaderProgram,
        order: int = 0,  # noqa: D107
        parent: Group | None = None,
    ) -> None:
        super().__init__(order=order, parent=parent)
        self.uniforms = {"scissor": False}
        self.set_shader_program(program)
        self.set_blend(BlendFactor.SRC_ALPHA, BlendFactor.ONE_MINUS_SRC_ALPHA)
        self.set_shader_uniforms(program, self.uniforms)


class ScrollableTextLayoutGroup(Group):
    """Default rendering group for :py:class:`~pyglet.text.layout.ScrollableTextLayout`.

    The group maintains internal state for specifying the viewable
    area, and for scrolling. Because the group has internal state
    specific to the text layout, the group is never shared.
    """

    scissor_area: ClassVar[tuple[int, int, int, int]] = 0, 0, 0, 0

    def __init__(
        self,
        texture: Texture,
        program: ShaderProgram,
        order: int = 1,  # noqa: D107
        parent: Group | None = None,
    ) -> None:

        super().__init__(order=order, parent=parent)
        self.texture = texture
        self.uniforms = {
            "scissor": True,
            "scissor_area": self.scissor_area,
        }
        self.set_shader_program(program)
        self.set_blend(BlendFactor.SRC_ALPHA, BlendFactor.ONE_MINUS_SRC_ALPHA)
        self.set_texture(texture, 0)
        self.set_shader_uniforms(program, self.uniforms)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.texture})"

    def __eq__(self, other: object) -> bool:
        return self is other

    def __hash__(self) -> int:
        return id(self)


class ScrollableTextDecorationGroup(Group):
    """Create a text decoration rendering group.

    The group is created internally when a :py:class:`~pyglet.text.Label`
    is created; applications usually do not need to explicitly create it.
    """

    scissor_area: ClassVar[tuple[int, int, int, int]] = 0, 0, 0, 0

    def __init__(self, program: ShaderProgram, order: int = 0, parent: Group | None = None) -> None:  # noqa: D107
        super().__init__(order=order, parent=parent)
        self.program = program
        self.set_shader_program(program)
        self.set_blend(BlendFactor.SRC_ALPHA, BlendFactor.ONE_MINUS_SRC_ALPHA)
        self.uniforms = {
            "scissor": True,
            "scissor_area": self.scissor_area,
        }
        self.set_shader_uniforms(program, self.uniforms)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(scissor={self.scissor_area})"

    def __eq__(self, other: object) -> bool:
        return self is other

    def __hash__(self) -> int:
        return id(self)


class TextLayout(_FlowLayoutBase):
    """Lay out and display documents.

    This class is intended for displaying documents.

    :py:func:`~pyglet.text.Label` and :py:func:`~pyglet.text.HTMLLabel` provide a convenient interface to this class.

    Some properties may cause the document to be recreated rather than updated. Refer to property documentation for
    details.

    Attributes:
        group_class:
            Default group used to set the state for all glyphs.
        effect_group_class:
            Default group used to set the state for glyph-backed effects, such
            as shadows and strokes.
        decoration_class:
            Default group used to set the state for all decorations including background colors and underlines.
    """

    _vertex_lists: list[_LayoutVertexList]
    _boxes: list[_AbstractBox]
    group_cache: dict[Texture | tuple[Texture, int], graphics.Group]

    _document: AbstractDocument | None = None

    _update_enabled: bool = True
    _own_batch: bool = False

    group_class: ClassVar[type[TextLayoutGroup]] = TextLayoutGroup
    effect_group_class: ClassVar[type[TextLayoutGroup]] = TextLayoutGroup
    decoration_class: ClassVar[type[TextDecorationGroup]] = TextDecorationGroup

    _ascent: float = 0
    _descent: float = 0
    _line_count: int = 0
    _anchor_left: float = 0
    _anchor_bottom: float = 0
    _x: float
    _y: float
    _z: float
    _rotation: float = 0

    _width: int | None = None
    _height: int | None = None

    _anchor_x: AnchorX = "left"
    _anchor_y: AnchorY = "bottom"
    _content_valign: ContentVAlign = "top"
    _multiline: bool = False
    _visible: bool = True

    #: Clip-space depth distance between text layers when ``depth_sorting`` is enabled.
    _depth_layer_offset: ClassVar[float] = 1e-5

    #: Depth comparison used when ``depth_sorting`` is enabled.
    depth_test_compare_op: ClassVar[CompareOp] = CompareOp.LESS

    def __init__(
        self,
        document: AbstractDocument,
        x: float = 0,
        y: float = 0,
        z: float = 0,
        width: int | None = None,
        height: int | None = None,
        anchor_x: AnchorX = 'left',
        anchor_y: AnchorY = 'bottom',
        rotation: float = 0,
        multiline: bool = False,
        dpi: float | None = None,
        batch: Batch | None = None,
        group: graphics.Group | None = None,
        program: ShaderProgram | None = None,
        decoration_shader: ShaderProgram | None = None,
        effect_shader: ShaderProgram | None = None,
        wrap_lines: bool = True,
        shaping: bool = True,
        init_document: bool = True,
        depth_sorting: bool = False,
    ) -> None:
        """Create a text layout.

        Args:
            document:
                Document to display.
            x:
                X coordinate of the label.
            y:
                Y coordinate of the label.
            z:
                Z coordinate of the label.
            width:
                Width of the layout in pixels, or None
            height:
                Height of the layout in pixels, or None
            anchor_x:
                Anchor point of the X coordinate.
            anchor_y:
                Anchor point of the Y coordinate.
            rotation:
                The amount to rotate the label in degrees. A positive amount
                will be a clockwise rotation, negative values will result in
                counter-clockwise rotation.
            multiline:
                If False, newline and paragraph characters are ignored, and
                text is not word-wrapped.
                If True, text is wrapped only if the `wrap_lines` is True.
            dpi:
                Font resolution; defaults to 96.
            batch:
                Optional graphics batch to add this layout to.
            group:
                Optional Group to parent all internal Groups that this text
                layout uses.  Note that layouts with the same Groups will
                be rendered simultaneously in a Batch.
            program:
                Optional graphics shader to use. Will affect all glyphs in the layout.
            decoration_shader:
                Optional graphics shader to use for all decorations in the
                layout, including backgrounds and underlines. It cannot vary
                between text runs.
            effect_shader:
                Optional graphics shader to use for all glyph-backed effects
                in the layout, including shadows and strokes. It cannot vary
                between text runs.
            wrap_lines:
                If True and `multiline` is True, the text is word-wrapped using the specified width.
            shaping:
                Whether this layout should use text shaping. The shaping backend is selected globally with
                ``pyglet.options.text_shaping``. If ``False``, glyph positions are based on their unshaped metrics.
            init_document:
                If True the document will be initialized. If subclassing then
                you may want to avoid duplicate initializations by changing to False.
            depth_sorting:
                If True, enable depth testing and preserve the text layer order
                using small clip-space depth offsets. This keeps backgrounds,
                shadows, strokes, glyphs, and decorations reliably ordered when
                multiple labels overlap.

        .. versionchanged:: 3.0
            Added the *shaping* parameter.
            Added the *depth_sorting* parameter.
        """
        self._x = x
        self._y = y
        self._z = z
        self._width = width
        self._height = height
        self._anchor_x = anchor_x
        self._anchor_y = anchor_y
        self._rotation = rotation
        self._multiline = multiline
        self._dpi = dpi or 96
        self._shaping = shaping
        self._depth_sorting = depth_sorting

        self._content_width = 0
        self._content_height = 0

        self._user_group = group

        # Accumulation of all child vertex lists, this is ONLY used for the draw function.
        self._vertex_lists = []

        # Boxes are all existing _AbstractBoxes, these are used to gather line information.
        # Note that this is only relevant to layouts that do not store directly on lines.
        self._boxes = []
        self._lines = []

        #: :meta private:
        self.group_cache = {}

        self._initialize_groups()

        if batch is None:
            batch = pyglet.graphics.Batch()
            # Create a batch as some text elements may require being drawn together.
            self._own_batch = True
        self._batch = batch

        self._program = program or get_default_layout_shader()
        self._decoration_shader = decoration_shader
        self._effect_shader = effect_shader

        self._wrap_lines_flag = wrap_lines
        self._wrap_lines_invariant()

        self._set_document(document)
        if init_document:
            self._init_document()

    def _initialize_groups(self) -> None:
        # Most labels do not contain effects, backgrounds, underlines, or carets.
        # Avoid constructing groups until one is used.
        self._background_decoration_group = None
        self._foreground_decoration_group = None
        self.effect_group_cache = {}

    def get_effect_group(self, texture: Texture, order: int = 0) -> TextLayoutGroup:
        cache_key = texture, order
        try:
            return self.effect_group_cache[cache_key]
        except KeyError:
            group = self.effect_group_class(texture, self.effect_shader, order=order, parent=self._user_group)
            self._set_depth_test(group)
            self.effect_group_cache[cache_key] = group
            return group

    def _set_depth_test(self, group: Group) -> None:
        if self._depth_sorting:
            group.set_depth_test(self.depth_test_compare_op)

    def get_depth_offset(self, layer: int) -> float:
        """Return the clip-space depth offset for a text rendering layer."""
        return layer * self._depth_layer_offset if self._depth_sorting else 0.0

    @property
    def background_decoration_group(self) -> TextDecorationGroup:
        if self._background_decoration_group is None:
            self._background_decoration_group = self.decoration_class(
                self.decoration_shader,
                order=0,
                parent=self._user_group,
            )
            self._set_depth_test(self._background_decoration_group)
        return self._background_decoration_group

    @background_decoration_group.setter
    def background_decoration_group(self, group: TextDecorationGroup | None) -> None:
        self._background_decoration_group = group

    @property
    def foreground_decoration_group(self) -> TextDecorationGroup:
        if self._foreground_decoration_group is None:
            self._foreground_decoration_group = self.decoration_class(
                self.decoration_shader,
                order=4 if self._depth_sorting else 2,
                parent=self._user_group,
            )
            self._set_depth_test(self._foreground_decoration_group)
        return self._foreground_decoration_group

    @foreground_decoration_group.setter
    def foreground_decoration_group(self, group: TextDecorationGroup | None) -> None:
        self._foreground_decoration_group = group

    @property
    def group(self) -> Group | None:
        """Get the Group specified by the user.

        Changing a group will cause the layout to be recreated.
        """
        return self._user_group

    @group.setter
    def group(self, group: Group) -> None:
        self._user_group = group
        self._initialize_groups()
        self.group_cache.clear()
        self._update()

    @property
    def decoration_shader(self) -> ShaderProgram:
        """Shader applied to every decoration in this layout.

        Assigning a shader recreates the layout's decoration vertex lists.
        A decoration shader applies to all text runs in the layout.
        """
        return self._decoration_shader or get_default_decoration_shader()

    @decoration_shader.setter
    def decoration_shader(self, shader: ShaderProgram | None) -> None:
        if self._decoration_shader is shader:
            return
        self._decoration_shader = shader
        self._background_decoration_group = None
        self._foreground_decoration_group = None
        self._update()

    @property
    def effect_shader(self) -> ShaderProgram:
        """Shader applied to every glyph-backed effect in this layout.

        Assigning a shader recreates the layout's effect vertex lists. An
        effect shader applies to all text runs in the layout.
        """
        return self._effect_shader or self._program

    @effect_shader.setter
    def effect_shader(self, shader: ShaderProgram | None) -> None:
        if self._effect_shader == shader:
            return
        self._effect_shader = shader
        self.effect_group_cache.clear()
        self._update()

    @property
    def depth_sorting(self) -> bool:
        """Whether this layout uses depth testing and depth-safe text layers."""
        return self._depth_sorting

    @depth_sorting.setter
    def depth_sorting(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if self._depth_sorting == enabled:
            return
        self._depth_sorting = enabled
        self._initialize_groups()
        self.group_cache.clear()
        self._update()

    @property
    def document(self) -> AbstractDocument:
        """Document to display.

        For :py:class:`~pyglet.text.layout.IncrementalTextLayout` it is
        far more efficient to modify a document in-place than to replace
        the document instance on the layout.
        """
        return self._document

    @document.setter
    def document(self, document: AbstractDocument) -> None:
        self._set_document(document)
        self._init_document()

    def _set_document(self, document: AbstractDocument) -> None:
        if self._document:
            self._document.remove_handlers(self)
            self._uninit_document()
        document.push_handlers(self)
        self._document = document

    @property
    def batch(self) -> Batch:
        """The Batch that this Layout is assigned to.

        If no Batch is assigned, an internal Batch is created and used.
        """
        return self._batch

    @batch.setter
    def batch(self, batch: Batch | None) -> None:
        if self._batch == batch:
            return

        if batch is None:
            self._batch = pyglet.graphics.Batch()
            self._own_batch = True
            self._update()
        elif batch is not None:
            self._batch = batch
            self._own_batch = False
            self._update()

    @property
    def program(self) -> ShaderProgram:
        """The ShaderProgram that is assigned to this Layout.

        If set, the shader will impact all Glyphs. InlineElements will not be affected.
        """
        return self._program

    @program.setter
    def program(self, shader_program: ShaderProgram) -> None:
        if self._program == shader_program:
            return

        self._program = shader_program
        self.group_cache.clear()
        if self._effect_shader is None:
            self.effect_group_cache.clear()
        self._update()

    @property
    def x(self) -> float:
        """X coordinate of the layout.

        See also :py:attr:`~pyglet.text.layout.TextLayout.anchor_x`.
        """
        return self._x

    @x.setter
    def x(self, x: float) -> None:
        self._set_x(x)

    def _set_x(self, x: float) -> None:
        self._x = x
        self._update_translation()

    @property
    def y(self) -> float:
        """Y coordinate of the layout.

        See also :py:attr:`~pyglet.text.layout.TextLayout.anchor_y`.
        """
        return self._y

    @y.setter
    def y(self, y: float) -> None:
        self._set_y(y)

    def _set_y(self, y: float) -> None:
        self._y = y
        self._update_translation()

    @property
    def z(self) -> float:
        """Z coordinate of the layout."""
        return self._z

    @z.setter
    def z(self, z: float) -> None:
        self._set_z(z)

    def _set_z(self, z: float) -> None:
        self._z = z
        self._update_translation()

    @property
    def rotation(self) -> float:
        """Rotation of the layout in degrees. Rotated based on the anchor of the layout.

        Negative values will rotate in reverse.

        See :py:attr:`~pyglet.text.layout.TextLayout.anchor_x`, and :py:attr:`~pyglet.text.layout.TextLayout.anchor_y`.
        """
        return self._rotation

    @rotation.setter
    def rotation(self, rotation: float) -> None:
        self._set_rotation(rotation)

    def _set_rotation(self, rotation: float) -> None:
        self._rotation = rotation
        self._update_rotation()

    def _update_rotation(self) -> None:
        for box in self._boxes:
            box.update_rotation(self._rotation)

    @property
    def position(self) -> tuple[float, float, float]:
        """The (X, Y, Z) coordinates of the layout, as a tuple.

        See also :py:attr:`~pyglet.text.layout.TextLayout.anchor_x`,
        and :py:attr:`~pyglet.text.layout.TextLayout.anchor_y`.
        """
        return self._x, self._y, self._z

    @position.setter
    def position(self, position: tuple[float, float, float]) -> None:
        self._set_position(position)

    def _set_position(self, position: tuple[float, float, float]) -> None:
        self._x, self._y, self._z = position
        self._update_translation()

    def _update_translation(self) -> None:
        for box in self._boxes:
            box.update_translation(self._x, self._y, self._z)

    def _update_anchor(self) -> None:
        self._anchor_left = self._get_left_anchor()
        self._anchor_bottom = self._get_bottom_anchor()

        anchor_y = self._get_top_anchor()

        for line in self._lines:
            acc_anchor_x = self._anchor_left
            for box in line.boxes:
                place_anchor_x = round(acc_anchor_x) if self._rotation == 0 else acc_anchor_x
                box.update_anchor(place_anchor_x, anchor_y)
                acc_anchor_x += box.advance

    @property
    def visible(self) -> bool:
        """True if the layout will be visible when drawn."""
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        if value != self._visible:
            self._visible = value

            for box in self._boxes:
                box.update_visibility(value)

    @property
    def content_width(self) -> int:
        """Calculated width of the text in the layout.

        This is the actual width of the text in pixels, not the
        user defined :py:attr:`~pyglet.text.layout.TextLayout.width`.
        The content width may overflow the layout width if word-wrapping
        is not possible.
        """
        return self._content_width

    @property
    def content_height(self) -> int:
        """The calculated height of the text in the layout.

        This is the actual height of the text in pixels, not the
        user defined :py:attr:`~pyglet.text.layout.TextLayout.height`.
        """
        return self._content_height

    @property
    def width(self) -> int | None:
        """The defined maximum width of the layout in pixels, or None.

        If `multiline` and `wrap_lines` is True, the `width` defines where the
        text will be wrapped. If `multiline` is False or `wrap_lines` is False,
        this property has no effect.
        """
        return self._width

    @width.setter
    def width(self, width: int | None) -> None:
        self._width = width
        self._wrap_lines_invariant()
        self._update()

    @property
    def height(self) -> int | None:
        """The defined maximum height of the layout in pixels, or None.

        When `height` is not None, it affects the positioning of the
        text when :py:attr:`~pyglet.text.layout.TextLayout.anchor_y` and
        :py:attr:`~pyglet.text.layout.TextLayout.content_valign` are
        used.
        """
        return self._height

    @height.setter
    def height(self, height: int | None) -> None:
        self._height = height
        self._update()

    @property
    def multiline(self) -> bool:
        """Set if multiline layout is enabled.

        If ``multiline`` is False, newline and paragraph characters are ignored and
        text is not word-wrapped.
        If True, the text is word-wrapped only if the ``wrap_lines`` is True.
        """
        return self._multiline

    @multiline.setter
    def multiline(self, multiline: bool) -> None:
        self._multiline = multiline
        self._wrap_lines_invariant()
        self._update()

    @property
    def anchor_x(self) -> AnchorX:
        """Horizontal anchor alignment.

        This property determines the meaning of the ``x`` coordinate.

        The following values are supported:

        ``"left"`` (default)
            The X coordinate gives the position of the left edge of the layout.
        ``"center"``
            The X coordinate gives the position of the center of the layout.
        ``"right"``
            The X coordinate gives the position of the right edge of the layout.

        For the purposes of calculating the position resulting from this
        alignment, the width of the layout is taken to be ``width`` if ``multiline``
        is True and ``wrap_lines`` is True, otherwise ``content_width``.
        """
        return self._anchor_x

    @anchor_x.setter
    def anchor_x(self, anchor_x: AnchorX) -> None:
        self._anchor_x = anchor_x
        self._update_anchor()

    @property
    def anchor_y(self) -> AnchorY:
        """Vertical anchor alignment.

        This property determines the meaning of the ``y`` coordinate.

        The following values are supported:

        ``"top"``
            The Y coordinate gives the position of the top edge of the layout.
        ``"center"``
            The Y coordinate gives the position of the center of the layout.
        ``"baseline"``
            The Y coordinate gives the position of the baseline of the first
            line of text in the layout.
        ``"bottom"`` (default)
            The Y coordinate gives the position of the bottom edge of the layout.

        For the purposes of calculating the position resulting from this
        alignment, the height of the layout is taken to be the smallest of
        ``height`` and ``content_height``.

        See also :py:attr:`~pyglet.text.layout.TextLayout.content_valign`.
        """
        return self._anchor_y

    @anchor_y.setter
    def anchor_y(self, anchor_y: AnchorY) -> None:
        self._anchor_y = anchor_y
        self._update_anchor()

    @property
    def content_valign(self) -> ContentVAlign:
        """Vertical alignment of content within larger layout box.

        This property determines how content is positioned within the layout
        box when ``content_height`` is less than ``height``.

        The following values are supported:

        ``top`` (default)
            Content is aligned to the top of the layout box.
        ``center``
            Content is centered vertically within the layout box.
        ``bottom``
            Content is aligned to the bottom of the layout box.

        This property has no effect when ``content_height`` is greater
        than ``height`` (in which case the content is aligned to the top) or when
        ``height`` is ``None`` (in which case there is no vertical layout box
        dimension).
        """
        return self._content_valign

    @content_valign.setter
    def content_valign(self, content_valign: ContentVAlign) -> None:
        self._content_valign = content_valign
        self._update()

    @property
    def left(self) -> float:
        """The x-coordinate of the left side of the layout."""
        return self._x + self._anchor_left

    @property
    def right(self) -> float:
        """The x-coordinate of the right side of the layout."""
        if self._width is None:
            width = self._content_width
        else:
            width = self._width

        return self.left + width

    @property
    def bottom(self) -> float:
        """The y-coordinate of the bottom side of the layout."""
        return self._y + self._anchor_bottom

    @property
    def top(self) -> float:
        """The y-coordinate of the top side of the layout."""
        if self._height is None:
            height = self._content_height
        else:
            height = self._height

        return self.bottom + height

    def _wrap_lines_invariant(self) -> None:
        self._wrap_lines = self._multiline and self._wrap_lines_flag
        assert not self._wrap_lines or self._width, (
            "When the parameters 'multiline' and 'wrap_lines' are True, the parameter 'width' must be a number."
        )

    def _parse_distance(self, distance: str | int | float | None) -> int | None:  # noqa: PYI041
        if distance is None:
            return None
        return _parse_distance(distance, self._dpi)

    def begin_update(self) -> None:
        """Indicate that a number of changes to the layout or document are about to occur.

        Changes to the layout or document between calls to `begin_update` and
        `end_update` do not trigger any costly relayout of text.  Relayout of
        all changes is performed when `end_update` is called.

        Note that between the `begin_update` and `end_update` calls, values
        such as `content_width` and `content_height` are undefined (i.e., they
        may or may not be updated to reflect the latest changes).
        """
        self._update_enabled = False

    def end_update(self) -> None:
        """Perform pending layout changes since `begin_update`.

        See `begin_update`.
        """
        self._update_enabled = True
        self._update()

    @property
    def dpi(self) -> float:
        """Get DPI used by this layout."""
        return self._dpi

    @dpi.setter
    def dpi(self, value: float) -> None:
        self._dpi = value
        self._update()

    def delete(self) -> None:
        """Deletes all vertices and boxes associated with the layout."""
        for box in self._boxes:
            box.delete(self)

        self._vertex_lists.clear()
        self._boxes.clear()

    def get_as_texture(self, render_target: TextureRenderTarget | None = None) -> Texture:
        """Draw the current layout into a new texture.

        When generating one texture, omit ``render_target`` and the temporary
        framebuffer and camera will be cleaned up automatically::

            texture = layout.get_as_texture()

        Reuse a :class:`~pyglet.graphics.framebuffer.TextureRenderTarget` when
        converting many layouts to avoid recreating that target state::

            target = pyglet.graphics.TextureRenderTarget()
            textures = [layout.get_as_texture(target) for layout in layouts]
            target.delete()

        Every returned texture is independent and owned by the caller. Delete
        each texture when it is no longer needed.

        .. warning::
            This allocates a GPU texture and renders the layout on the GPU.
            Generating many textures, especially every frame, can be slow.
            Reusing a render target reduces setup overhead but does not remove
            the texture allocation or rendering cost. The caller must delete
            returned textures to avoid GPU memory leaks.

        .. note:: Does not include InlineElements.

        Args:
            render_target:
                Optional reusable texture render target. When omitted, a temporary
                target is created and deleted for this operation.

        Returns:
            A new texture with the layout drawn into it.

        .. versionadded:: 2.0.11
        """
        width = round(self._content_width)
        height = round(self._content_height)
        owns_render_target = render_target is None
        render_target = render_target or pyglet.graphics.TextureRenderTarget()
        original_position = self.position

        try:
            self.position = -self._anchor_left, -self._anchor_bottom, 0
            with render_target.render_to_texture(width, height) as texture:
                self.draw()
            return texture
        finally:
            try:
                self.position = original_position
            finally:
                if owns_render_target:
                    render_target.delete()

    def draw(self) -> None:
        """Draw this text layout.

        .. note:: This method performs very badly if a batch was supplied to the constructor.
            If you add this layout to a batch, you should ideally use only the batch's draw method.

        .. note:: If this is not its own batch, InlineElements will not be drawn.

        """
        if self._own_batch:
            self._batch.draw()
        else:
            self._batch.draw_subset(self._vertex_lists)

    def _update(self) -> None:
        if not self._update_enabled:
            return

        for box in self._boxes:
            box.delete(self)

        self._vertex_lists.clear()
        self._boxes.clear()
        self._lines.clear()

        if not self._document or not self._document.text:
            self._ascent = 0
            self._descent = 0
            self._anchor_left = 0
            self._anchor_bottom = 0
            return

        self._lines = self._get_lines()
        self._ascent = self._lines[0].ascent
        self._descent = self._lines[0].descent

        colors_iter = self._document.get_style_runs("color")

        background_iter = self._document.get_style_runs("background_color")

        self._anchor_left = self._get_left_anchor()
        self._anchor_bottom = self._get_bottom_anchor()
        anchor_top = self._get_top_anchor()

        context = _StaticLayoutContext(self, self._document, colors_iter, background_iter)

        for line in self._lines:
            self._boxes.extend(line.boxes)
            self._create_vertex_lists(line.x, line.y, self._anchor_left, anchor_top, line.start, line.boxes, context)

    def _update_color(self, start: int, end: int, color: RGBAColor | LinearGradient) -> None:
        # This function usually is only called by Labels/HTML when updating just colors.
        if isinstance(color, LinearGradient):
            # Gradient colors depend on glyph positions, so rebuilding the
            # affected vertex data is required instead of the solid-color
            # in-place update below.
            self._init_document()
            return

        colors_iter = self._document.get_style_runs("color")
        colors = []
        for iter_start, iter_end, color in colors_iter.ranges(start, end):
            colors.extend(color * (iter_end - iter_start))

        char_index = 0

        # Search all boxes for the characters that are going to be updated.
        for box in self._boxes:
            box_length = box.length  # Number of glyphs in the box

            if char_index + box_length > start and char_index < end:
                box_start = max(0, start - char_index)
                box_end = min(box_length, end - char_index)
                box.update_colors(colors, box_start, box_end)

            char_index += box_length

    def _get_left_anchor(self) -> int:
        """Returns the anchor for the X axis from the left."""
        if self._multiline:
            width = self._width if self._wrap_lines else self._content_width
        else:
            width = self._content_width

        if self._anchor_x == "left":
            return 0
        if self._anchor_x == "center":
            return -(width // 2)
        if self._anchor_x == "right":
            return -width

        msg = '`anchor_x` must be either "left", "center", or "right".'
        raise Exception(msg)

    def _get_top_anchor(self) -> float:
        """Returns the anchor for the Y axis from the top."""
        if self._height is None:
            height = self._content_height
            offset = 0
        else:
            height = self._height
            if self._content_valign == "top":
                offset = 0
            elif self._content_valign == "bottom":
                offset = max(0, self._height - self._content_height)
            elif self._content_valign == "center":
                offset = max(0, self._height - self._content_height) // 2
            else:
                msg = '`content_valign` must be either "top", "bottom", or "center".'
                raise Exception(msg)

        if self._anchor_y == "top":
            return -offset
        if self._anchor_y == "baseline":
            return self._ascent - offset
        if self._anchor_y == "bottom":
            return height - offset
        if self._anchor_y == "center":
            if self._line_count == 1 and self._height is None:
                # This "looks" more centered than considering all of the descent.
                return self._ascent // 2 - self._descent // 4

            return height // 2 - offset

        msg = '`anchor_y` must be either "top", "bottom", "center", or "baseline".'
        raise Exception(msg)

    def _get_bottom_anchor(self) -> float:
        """Returns the anchor for the Y axis from the bottom."""
        if self._height is None:
            height = self._content_height
            offset = 0
        else:
            height = self._height
            if self._content_valign == "top":
                offset = min(0, self._height - self._content_height)
            elif self._content_valign == "bottom":
                offset = 0
            elif self._content_valign == "center":
                offset = min(0, self._height - self._content_height) // 2
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

    def _init_document(self) -> None:
        self._update()

    def _uninit_document(self) -> None:
        pass

    def on_insert_text(self, start: int, text: str) -> None:  # noqa: ARG002
        """Event handler for `AbstractDocument.on_insert_text`.

        The event handler is bound by the text layout; there is no need for
        applications to interact with this method.
        """
        self._init_document()

    def on_delete_text(self, start: int, end: int) -> None:  # noqa: ARG002
        """Event handler for `AbstractDocument.on_delete_text`.

        The event handler is bound by the text layout; there is no need for
        applications to interact with this method.
        """
        self._init_document()

    def on_style_text(self, start: int, end: int, attributes: dict[str, Any]) -> None:
        """Event handler for `AbstractDocument.on_style_text`.

        The event handler is bound by the text layout; there is no need for
        applications to interact with this method.
        """
        # To save performance when lerping colors, only update color values instead of recreating layout.
        if len(attributes) == 1 and "color" in attributes:
            self._update_color(start, end, attributes["color"])
        else:
            self._init_document()

    def _create_vertex_lists(
        self,
        line_x: float,
        line_y: float,
        anchor_x: float,
        anchor_y: float,
        i: int,
        boxes: list[_AbstractBox],
        context: _LayoutContext,
    ) -> None:
        acc_anchor_x = anchor_x
        # GlyphBoxes (boxes) are collection of Glyphs/Inline Elements. A line can have multiple GlyphBoxes.
        for box in boxes:
            place_anchor_x = round(acc_anchor_x) if self._rotation == 0 else acc_anchor_x
            box.place(
                self,
                i,
                self._x,
                self._y,
                self._z,
                line_x,
                line_y,
                self._rotation,
                self._visible,
                place_anchor_x,
                anchor_y,
                context,
            )
            i += box.length
            acc_anchor_x += box.advance

    def get_line_count(self) -> int:
        """Get the number of lines in the text layout."""
        return self._line_count
