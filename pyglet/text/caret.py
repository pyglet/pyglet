"""Provides keyboard and mouse editing procedures for text layout.

Example usage::

    from pyglet import window
    from pyglet.text import layout, caret

    my_window = window.Window(...)
    my_layout = layout.IncrementalTextLayout(...)
    my_caret = caret.Caret(my_layout)
    my_window.push_handlers(my_caret)
"""
from __future__ import annotations

import re
import time
from typing import TYPE_CHECKING, Any, Pattern

from pyglet import clock, event
from pyglet.window import key

if TYPE_CHECKING:
    from pyglet.graphics import Batch
    from pyglet.text.layout import IncrementalTextLayout


class Caret:
    """Visible text insertion marker for `pyglet.text.layout.IncrementalTextLayout`.

    The caret is drawn as a single vertical bar at the document `position` 
    on a text layout object.  If ``mark`` is not None, it gives the unmoving
    end of the current text selection.  The visible text selection on the
    layout is updated along with ``mark`` and ``position``.

    By default, the layout's graphics batch is used, so the caret does not need
    to be drawn explicitly.  Even if a different graphics batch is supplied,
    the caret will be correctly positioned and clipped within the layout.

    Updates to the document (and so the layout) are automatically propagated
    to the caret.

    The caret object can be pushed onto a window event handler stack with
    ``Window.push_handlers``.  The caret will respond correctly to keyboard,
    text, mouse and activation events, including double- and triple-clicks.
    If the text layout is being used alongside other graphical widgets, a
    GUI toolkit will be needed to delegate keyboard and mouse events to the
    appropriate widget.  Pyglet does not provide such a toolkit at this stage.
    """
    _next_word_re: Pattern[str] = re.compile(r"(?<=\W)\w")
    _previous_word_re: Pattern[str] = re.compile(r"(?<=\W)\w+\W*$")
    _next_para_re: Pattern[str] = re.compile(r"\n", flags=re.DOTALL)
    _previous_para_re: Pattern[str] = re.compile(r"\n", flags=re.DOTALL)

    _position: int = 0

    _active: bool = True
    _visible: bool = True
    _blink_visible: bool = True
    _click_count: int = 0
    _click_time: float = 0

    #: Blink period, in seconds.
    PERIOD: float = 0.5

    #: Pixels to scroll viewport per mouse scroll wheel movement.
    #: Defaults to 12pt at 96dpi.
    SCROLL_INCREMENT: int = 12 * 96 // 72

    _mark: int | None = None
    _next_attributes: dict[str, Any]

    def __init__(self, layout: IncrementalTextLayout, batch: Batch | None = None,
                 color: tuple[int, int, int, int] = (0, 0, 0, 255)) -> None:
        """Create a caret for a layout.

        By default the layout's batch is used, so the caret does not need to
        be drawn explicitly.

        :Parameters:
            `layout` : `~pyglet.text.layout.IncrementalTextLayout`
                Layout to control.
            `batch` : `~pyglet.graphics.Batch`
                Graphics batch to add vertices to.
            `color` : (int, int, int, int)
                An RGBA or RGB tuple with components in the range [0, 255].
                RGB colors will be treated as having an opacity of 255.

        """
        from pyglet import gl
        self._layout = layout

        self._custom_batch = batch is not None
        self._batch = batch or layout.batch
        self._group = layout.foreground_decoration_group

        # Handle both 3 and 4 byte colors
        r, g, b, *a = color

        # The alpha value when not in a hidden blink state
        self._visible_alpha = a[0] if a else 255

        colors = r, g, b, self._visible_alpha, r, g, b, self._visible_alpha

        self._list = self._group.program.vertex_list(2, gl.GL_LINES, self._batch, self._group,
                                                     colors=("Bn", colors),
                                                     visible=("f", (1, 1)))
        self._ideal_x = None
        self._ideal_line = None
        self._next_attributes = {}

        self.visible = True

        layout.push_handlers(self)

    @property
    def layout(self) -> IncrementalTextLayout:
        return self._layout

    @layout.setter
    def layout(self, layout: IncrementalTextLayout) -> None:
        if self._layout == layout and self._group == layout.group:
            return

        from pyglet.gl import GL_LINES
        self._layout = layout
        batch = self._batch if self._custom_batch else layout.batch
        self._group = layout.foreground_decoration_group
        self._batch.migrate(self._list, GL_LINES, self._group, batch)

    def delete(self) -> None:
        """Remove the caret from its batch.

        Also disconnects the caret from further layout events.
        """
        clock.unschedule(self._blink)
        self._list.delete()
        self._layout.remove_handlers(self)

    def _blink(self, dt: float) -> None:  # noqa: ARG002
        if self.PERIOD:
            self._blink_visible = not self._blink_visible

        if self._visible and self._active and self._blink_visible:
            alpha = self._visible_alpha
        else:
            alpha = 0

        # Only set the alpha rather than entire colors
        self._list.colors[3] = alpha
        self._list.colors[7] = alpha

    def _nudge(self) -> None:
        self.visible = True

    @property
    def visible(self) -> bool:
        """Caret visibility.

        The caret may be hidden despite this property due to the periodic blinking
        or by `on_deactivate` if the event handler is attached to a window.
        """
        return self._visible

    @visible.setter
    def visible(self, visible: bool) -> None:
        self._visible = visible
        clock.unschedule(self._blink)
        if visible and self._active and self.PERIOD:
            clock.schedule_interval(self._blink, self.PERIOD)
            self._blink_visible = False  # flipped immediately by next blink
        self._blink(0)

    @property
    def color(self) -> tuple[int, int, int, int]:
        """An RGBA tuple of the current caret color.

        When blinking off, the alpha channel will be set to ``0``.  The
        default caret color when visible is ``(0, 0, 0, 255)`` (opaque black).

        You may set the color to an RGBA or RGB color tuple.

        .. warning:: This setter can fail for a short time after layout / window init!

                     Use ``__init__``'s ``color`` keyword argument instead if you
                     run into this problem.

        Each color channel must be between 0 and 255, inclusive. If the color
        set to an RGB color, the previous alpha channel value will be used.
        """
        return self._list.colors[:4]

    @color.setter
    def color(self, color: tuple[int, int, int, int] | tuple[int, int, int]) -> None:
        r, g, b, *_a = color

        # Preserve alpha when setting an RGB color
        a = _a[0] if _a else self._list.colors[3]

        self._list.colors[:] = r, g, b, a, r, g, b, a

    @property
    def position(self) -> int:
        """Position of caret within document."""
        return self._position

    @position.setter
    def position(self, position: int) -> None:
        self._position = position
        self._next_attributes.clear()
        self._update()

    @property
    def mark(self) -> int:
        """Position of immovable end of text selection within document.

        An interactive text selection is determined by its immovable end (the
        caret's position when a mouse drag begins) and the caret's position, which
        moves interactively by mouse and keyboard input.

        This property is ``None`` when there is no selection.
        """
        return self._mark

    @mark.setter
    def mark(self, mark: int) -> None:
        self._mark = mark
        self._update(line=self._ideal_line)
        if mark is None:
            self._layout.set_selection(0, 0)

    @property
    def line(self) -> int:
        """Index of line containing the caret's position.

        When set, ``position`` is modified to place the caret on requested line
        while maintaining the closest possible X offset.
        """
        if self._ideal_line is not None:
            return self._ideal_line

        return self._layout.get_line_from_position(self._position)

    @line.setter
    def line(self, line: int) -> None:
        if self._ideal_x is None:
            self._ideal_x, _ = self._layout.get_point_from_position(self._position)
        self._position = self._layout.get_position_on_line(line, self._ideal_x)
        self._update(line=line, update_ideal_x=False)

    def get_style(self, attribute: str) -> Any:
        """Get the document's named style at the caret's current position.

        If there is a text selection and the style varies over the selection,
        `pyglet.text.document.STYLE_INDETERMINATE` is returned.

        Args:
            attribute:
                Name of style attribute to retrieve.  See
                :py:mod:`~pyglet.text.document` for a list of recognised attribute
                names.
        """
        if self._mark is None or self._mark == self._position:
            try:
                return self._next_attributes[attribute]
            except KeyError:
                return self._layout.document.get_style(attribute, self._position)

        start = min(self._position, self._mark)
        end = max(self._position, self._mark)
        return self._layout.document.get_style_range(attribute, start, end)

    def set_style(self, attributes: dict[str, Any]) -> None:
        """Set the document style at the caret's current position.

        If there is a text selection the style is modified immediately.
        Otherwise, the next text that is entered before the position is
        modified will take on the given style.

        Args:
            attributes:
                Dict mapping attribute names to style values.  See
                :py:mod:`~pyglet.text.document` for a list of recognised attribute
                names.

        """
        if self._mark is None or self._mark == self._position:
            self._next_attributes.update(attributes)
            return

        start = min(self._position, self._mark)
        end = max(self._position, self._mark)
        self._layout.document.set_style(start, end, attributes)

    def _delete_selection(self) -> None:
        start = min(self._mark, self._position)
        end = max(self._mark, self._position)
        self._position = start
        self._mark = None
        self._layout.document.delete_text(start, end)
        self._layout.set_selection(0, 0)

    def move_to_point(self, x: int, y: int) -> None:
        """Move the caret close to the given window coordinate.

        The `mark` will be reset to ``None``.
        """
        line = self._layout.get_line_from_point(x, y)
        self._mark = None
        self._layout.set_selection(0, 0)
        self._position = self._layout.get_position_on_line(line, x)
        self._update(line=line)
        self._next_attributes.clear()

    def select_to_point(self, x: int, y: int) -> None:
        """Move the caret close to the given window coordinate while maintaining the `mark`."""
        line = self._layout.get_line_from_point(x, y)
        self._position = self._layout.get_position_on_line(line, x)
        self._update(line=line)
        self._next_attributes.clear()

    def select_all(self) -> None:
        """Select all text in the document."""
        self._mark = 0
        self._position = len(self._layout.document.text)
        self._update()
        self._next_attributes.clear()

    def select_word(self, x: int, y: int) -> None:
        """Select the word at the given window coordinate."""
        line = self._layout.get_line_from_point(x, y)
        p = self._layout.get_position_on_line(line, x)
        match1 = self._previous_word_re.search(self._layout.document.text, 0, p + 1)
        if not match1:
            mark1 = 0
        else:
            mark1 = match1.start()
        self.mark = mark1

        match2 = self._next_word_re.search(self._layout.document.text, p)
        if not match2:
            mark2 = len(self._layout.document.text)
        else:
            mark2 = match2.start()

        self._position = mark2
        self._update(line=line)
        self._next_attributes.clear()

    def select_paragraph(self, x: int, y: int) -> None:
        """Select the paragraph at the given window coordinate."""
        line = self._layout.get_line_from_point(x, y)
        p = self._layout.get_position_on_line(line, x)
        self.mark = self._layout.document.get_paragraph_start(p)
        self._position = self._layout.document.get_paragraph_end(p)
        self._update(line=line)
        self._next_attributes.clear()

    def _update(self, line: int | None = None, update_ideal_x: bool = True) -> None:
        if line is None:
            line = self._layout.get_line_from_position(self._position)
            self._ideal_line = None
        else:
            self._ideal_line = line
        x, y = self._layout.get_point_from_position(self._position, line)
        z = self._layout.z
        if update_ideal_x:
            self._ideal_x = x

        x += self._layout.left
        y += self._layout.bottom + self._layout._get_content_height()  # noqa: SLF001

        if self._mark is not None:
            self._layout.set_selection(min(self._position, self._mark), max(self._position, self._mark))

        self._layout.ensure_line_visible(line)
        self._layout.ensure_x_visible(x)

        font = self._layout.document.get_font(max(0, self._position - 1))
        self._list.position[:] = [x, y + font.descent, z, x, y + font.ascent, z]

    def on_translation_update(self) -> None:
        self._list.translation[:] = (-self._layout.view_x, -self._layout.view_y, 0) * 2

    def on_layout_update(self) -> None:
        """Handler for the `IncrementalTextLayout.on_layout_update` event."""
        if self.position > len(self._layout.document.text):
            self.position = len(self._layout.document.text)
        self._update()

    def on_text(self, text: str) -> bool:
        """Handler for the `pyglet.window.Window.on_text` event.

        Caret keyboard handlers assume the layout always has keyboard focus.
        GUI toolkits should filter keyboard and text events by widget focus
        before invoking this handler.
        """
        if self._mark is not None:
            self._delete_selection()

        text = text.replace("\r", "\n")
        pos = self._position
        self._position += len(text)
        self._layout.document.insert_text(pos, text, self._next_attributes)
        self._nudge()
        return event.EVENT_HANDLED

    def on_text_motion(self, motion: int, select: bool = False) -> bool:
        """Handler for the `pyglet.window.Window.on_text_motion` event.

        Caret keyboard handlers assume the layout always has keyboard focus.
        GUI toolkits should filter keyboard and text events by widget focus
        before invoking this handler.
        """
        if motion == key.MOTION_BACKSPACE:
            if self.mark is not None:
                self._delete_selection()
            elif self._position > 0:
                self._position -= 1
                self._layout.document.delete_text(self._position, self._position + 1)
                self._update()
        elif motion == key.MOTION_DELETE:
            if self.mark is not None:
                self._delete_selection()
            elif self._position < len(self._layout.document.text):
                self._layout.document.delete_text(self._position, self._position + 1)

        if motion == key.MOTION_LEFT:
            if self.mark is not None and not select:
                self.position = self._layout._selection_start  # noqa: SLF001
            else:
                self.position = max(0, self.position - 1)
        elif motion == key.MOTION_RIGHT:
            if self.mark is not None and not select:
                self.position = self._layout._selection_end  # noqa: SLF001
            else:
                self.position = min(len(self._layout.document.text), self.position + 1)
        elif motion == key.MOTION_UP:
            self.line = max(0, self.line - 1)
        elif motion == key.MOTION_DOWN:
            line = self.line
            if line < self._layout.get_line_count() - 1:
                self.line = line + 1
        elif motion == key.MOTION_BEGINNING_OF_LINE:
            self.position = self._layout.get_position_from_line(self.line)
        elif motion == key.MOTION_END_OF_LINE:
            line = self.line
            if line < self._layout.get_line_count() - 1:
                self._position = self._layout.get_position_from_line(line + 1) - 1
                self._update(line)
            else:
                self.position = len(self._layout.document.text)
        elif motion == key.MOTION_BEGINNING_OF_FILE:
            self.position = 0
        elif motion == key.MOTION_END_OF_FILE:
            self.position = len(self._layout.document.text)
        elif motion == key.MOTION_NEXT_WORD:
            pos = self._position + 1
            m = self._next_word_re.search(self._layout.document.text, pos)
            if not m:
                self.position = len(self._layout.document.text)
            else:
                self.position = m.start()
        elif motion == key.MOTION_PREVIOUS_WORD:
            pos = self._position
            m = self._previous_word_re.search(self._layout.document.text, 0, pos)
            if not m:
                self.position = 0
            else:
                self.position = m.start()

        if self._mark is not None and not select:
            self._mark = None
            self._layout.set_selection(0, 0)

        self._next_attributes.clear()
        self._nudge()
        return event.EVENT_HANDLED

    def on_text_motion_select(self, motion: int) -> bool:
        """Handler for the `pyglet.window.Window.on_text_motion_select` event.

        Caret keyboard handlers assume the layout always has keyboard focus.
        GUI toolkits should filter keyboard and text events by widget focus
        before invoking this handler.
        """
        if self.mark is None:
            self.mark = self.position
        self.on_text_motion(motion, True)
        return event.EVENT_HANDLED

    def on_mouse_scroll(self, x: float, y: float, scroll_x: float, scroll_y: float) -> bool:  # noqa: ARG002
        """Handler for the `pyglet.window.Window.on_mouse_scroll` event.

        Mouse handlers do not check the bounds of the coordinates: GUI
        toolkits should filter events that do not intersect the layout
        before invoking this handler.

        The layout viewport is scrolled by `SCROLL_INCREMENT` pixels per
        "click".
        """
        self._layout.view_x -= scroll_x * self.SCROLL_INCREMENT
        self._layout.view_y += scroll_y * self.SCROLL_INCREMENT
        return event.EVENT_HANDLED

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> bool:  # noqa: ARG002
        """Handler for the `pyglet.window.Window.on_mouse_press` event.

        Mouse handlers do not check the bounds of the coordinates: GUI
        toolkits should filter events that do not intersect the layout
        before invoking this handler.

        This handler keeps track of the number of mouse presses within
        a short span of time and uses this to reconstruct double- and
        triple-click events for selecting words and paragraphs.  This
        technique is not suitable when a GUI toolkit is in use, as the active
        widget must also be tracked.  Do not use this mouse handler if
        a GUI toolkit is being used.
        """
        t = time.time()
        if t - self._click_time < 0.25:
            self._click_count += 1
        else:
            self._click_count = 1
        self._click_time = time.time()

        if self._click_count == 1:
            self.move_to_point(x, y)
        elif self._click_count == 2:
            self.select_word(x, y)
        elif self._click_count == 3:
            self.select_paragraph(x, y)
            self._click_count = 0

        self._nudge()
        return event.EVENT_HANDLED

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int) -> bool:  # noqa: ARG002
        """Handler for the `pyglet.window.Window.on_mouse_drag` event.

        Mouse handlers do not check the bounds of the coordinates: GUI
        toolkits should filter events that do not intersect the layout
        before invoking this handler.
        """
        if self.mark is None:
            self.mark = self.position
        self.select_to_point(x, y)
        self._nudge()
        return event.EVENT_HANDLED

    def on_activate(self) -> bool:
        """Handler for the `pyglet.window.Window.on_activate` event.

        The caret is hidden when the window is not active.
        """
        self._active = True
        self.visible = self._active
        return event.EVENT_HANDLED

    def on_deactivate(self) -> bool:
        """Handler for the `pyglet.window.Window.on_deactivate` event.

        The caret is hidden when the window is not active.
        """
        self._active = False
        self.visible = self._active
        return event.EVENT_HANDLED
