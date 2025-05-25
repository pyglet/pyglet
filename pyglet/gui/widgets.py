"""Display different types of interactive widgets."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pyglet
from pyglet.event import EventDispatcher
from pyglet.graphics import Group
from pyglet.text.caret import Caret
from pyglet.text.layout import IncrementalTextLayout

if TYPE_CHECKING:
    from pyglet.graphics import Batch
    from pyglet.image import AbstractImage


class WidgetBase(EventDispatcher):
    """The base of all widgets."""
    def __init__(self, x: int, y: int, width: int, height: int) -> None:  # noqa: D107
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self._parent = None
        self._bg_group = None
        self._fg_group = None
        self._enabled = True

    def _set_enabled(self, enabled: bool) -> None:
        """Internal hook for setting enabled.

        Override this in subclasses to perform effects when a widget is
        enabled or disabled.
        """

    @property
    def enabled(self) -> bool:
        """Get/set whether this widget is enabled.

        To react to changes in this value, override
        :py:meth:`._set_enabled` on widgets. For example, you may want
        to cue the user by:

        - Playing an animation and/or sound
        - Setting a highlight color
        - Displaying a toast or notification
        """
        return self._enabled

    @enabled.setter
    def enabled(self, new_enabled: bool) -> None:
        if self._enabled == new_enabled:
            return
        self._enabled = new_enabled
        self._set_enabled(new_enabled)

    def update_groups(self, order: int) -> None:
        pass

    @property
    def x(self) -> int:
        """X coordinate of the widget."""
        return self._x

    @x.setter
    def x(self, value: int) -> None:
        self._x = value
        self._update_position()
        self.dispatch_event("on_reposition", self)

    @property
    def y(self) -> int:
        """Y coordinate of the widget."""
        return self._y

    @y.setter
    def y(self, value: int) -> None:
        self._y = value
        self._update_position()
        self.dispatch_event("on_reposition", self)

    @property
    def parent(self):
        """The frame this widget belongs to.

        :type: `~pyglet.gui.frame.Frame`
        """
        return self._parent

    @parent.setter
    def parent(self, value):
        self._parent = value

    @property
    def position(self) -> tuple[int, int]:
        """The x, y coordinate of the widget as a tuple."""
        return self._x, self._y

    @position.setter
    def position(self, values: tuple[int, int]) -> None:
        self._x, self._y = values
        self._update_position()
        self.dispatch_event("on_reposition", self)

    @property
    def width(self) -> int:
        """Width of the widget."""
        return self._width

    @property
    def height(self) -> int:
        """Height of the widget."""
        return self._height

    @property
    def aabb(self) -> tuple[int, int, int, int]:
        """Bounding box of the widget.

        The "left", "bottom", "right", and "top" coordinates of the
        widget. This is expressed as (x, y, x + width, y + height).
        """
        return self._x, self._y, self._x + self._width, self._y + self._height

    @property
    def value(self) -> int | float | bool:
        """Query or set the Widget's value.

        This property allows you to set the value of a Widget directly, without any
        user input.  This could be used, for example, to restore Widgets to a
        previous state, or if some event in your program is meant to naturally
        change the same value that the Widget controls.  Note that events are not
        dispatched when changing this property directly.
        """
        raise NotImplementedError('Value depends on control type!')

    @value.setter
    def value(self, value: int | float | bool) -> None:
        raise NotImplementedError('Value depends on control type!')

    def _check_hit(self, x: int, y: int) -> bool:
        return self._x < x < self._x + self._width and self._y < y < self._y + self._height

    def _update_position(self) -> None:
        raise NotImplementedError('Unable to reposition this Widget')

    # Handlers

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        pass

    def on_key_release(self, symbol: int, modifiers: int) -> None:
        pass

    def on_mouse_press(self, x: int, y: int, buttons: int, modifiers: int) -> None:
        pass

    def on_mouse_release(self, x: int, y: int, buttons: int, modifiers: int) -> None:
        pass

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int) -> None:
        pass

    def on_mouse_scroll(self, x: int, y: int, scroll_x: float, scroll_y: float) -> None:
        pass

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        pass

    def on_mouse_enter(self, x: int, y: int) -> None:
        pass

    def on_mouse_leave(self, x: int, y: int) -> None:
        pass

    def on_text(self, text: str) -> None:
        pass

    def on_text_motion(self, motion: int) -> None:
        pass

    def on_text_motion_select(self, motion: int) -> None:
        pass


WidgetBase.register_event_type("on_reposition")


class PushButton(WidgetBase):
    """Instance of a push button.

    Triggers the event 'on_press' when it is clicked by the mouse.
    Triggers the event 'on_release' when the mouse is released.
    """

    def __init__(self, x: int, y: int,
                 pressed: AbstractImage,
                 unpressed: AbstractImage,
                 hover: AbstractImage | None = None,
                 batch: Batch | None = None,
                 group: Group | None = None) -> None:
        """Create a push button.

        Args:
            x:
                X coordinate of the push button.
            y:
                Y coordinate of the push button.
            pressed:
                Image to display when the button is pressed.
            unpressed:
                Image to display when the button isn't pressed.
            hover:
                Image to display when the button is being hovered over.
            batch:
                Optional batch to add the push button to.
            group:
                Optional parent group of the push button.
        """
        super().__init__(x, y, unpressed.width, unpressed.height)
        self._pressed_img = pressed
        self._unpressed_img = unpressed
        self._hover_img = hover or unpressed

        self._batch = batch or pyglet.graphics.Batch()
        self._user_group = group
        bg_group = Group(order=0, parent=group)
        self._sprite = pyglet.sprite.Sprite(self._unpressed_img, x=x, y=y, batch=batch, group=bg_group)

        self._pressed = False

    def _update_position(self) -> None:
        self._sprite.position = self._x, self._y, 0

    @property
    def value(self) -> bool:
        """Whether the button is pressed or not."""
        return self._pressed

    @value.setter
    def value(self, value: bool) -> None:
        assert type(value) is bool, "This Widget's value must be True or False."
        self._pressed = value
        self._sprite.image = self._pressed_img if self._pressed else self._unpressed_img

    def update_groups(self, order: int) -> None:
        self._sprite.group = Group(order=order + 1, parent=self._user_group)

    def on_mouse_press(self, x: int, y: int, buttons: int, modifiers: int) -> None:
        if not self.enabled or not self._check_hit(x, y):
            return
        self._sprite.image = self._pressed_img
        self._pressed = True
        self.dispatch_event('on_press', self)

    def on_mouse_release(self, x: int, y: int, buttons: int, modifiers: int) -> None:
        if not self.enabled or not self._pressed:
            return
        self._sprite.image = self._hover_img if self._check_hit(x, y) else self._unpressed_img
        self._pressed = False
        self.dispatch_event('on_release', self)

    def on_mouse_leave(self, x: int, y: int) -> None:
        if not self.enabled or not self._pressed:
            return
        self._sprite.image = self._unpressed_img
        self._pressed = False
        self.dispatch_event('on_release')

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        if not self.enabled or self._pressed:
            return
        self._sprite.image = self._hover_img if self._check_hit(x, y) else self._unpressed_img

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int) -> None:
        if not self.enabled or self._pressed:
            return
        self._sprite.image = self._hover_img if self._check_hit(x, y) else self._unpressed_img

    def on_press(self, widget: PushButton) -> None:
        """Event: Dispatched when the button is clicked."""

    def on_release(self, widget: PushButton) -> None:
        """Event: Dispatched when the button is released."""


PushButton.register_event_type('on_press')
PushButton.register_event_type('on_release')


class ToggleButton(PushButton):
    """Instance of a toggle button.

    Triggers the event 'on_toggle' when the mouse is pressed or released.
    """

    def _get_release_image(self, x: int, y: int) -> AbstractImage:
        return self._hover_img if self._check_hit(x, y) else self._unpressed_img

    def on_mouse_press(self, x: int, y: int, buttons: int, modifiers: int) -> None:
        if not self.enabled or not self._check_hit(x, y):
            return
        self._pressed = not self._pressed
        self._sprite.image = self._pressed_img if self._pressed else self._get_release_image(x, y)
        self.dispatch_event('on_toggle', self, self._pressed)

    def on_mouse_release(self, x: int, y: int, buttons: int, modifiers: int) -> None:
        if not self.enabled or self._pressed:
            return
        self._sprite.image = self._get_release_image(x, y)

    def on_toggle(self, widget: ToggleButton, value: bool) -> None:
        """Event: returns True or False to indicate the current state."""


ToggleButton.register_event_type('on_toggle')


class Slider(WidgetBase):
    """Instance of a slider made of a base and a knob image.

    Triggers the event 'on_change' when the knob position is changed.
    The knob position can be changed by dragging with the mouse, or
    scrolling the mouse wheel.
    """

    def __init__(self, x: int, y: int,
                 base: AbstractImage, knob: AbstractImage,
                 edge: int = 0,
                 batch: Batch | None = None,
                 group: Group | None = None) -> None:
        """Create a slider.

        Args:
            x:
                X coordinate of the slider.
            y:
                Y coordinate of the slider.
            base:
                Image to display as the background to the slider.
            knob:
                Knob that moves to show the position of the slider.
            edge:
                Pixels from the maximum and minimum position of the slider,
                to the edge of the base image.
            batch:
                Optional batch to add the slider to.
            group:
                Optional parent group of the slider.
        """
        super().__init__(x, y, base.width, knob.height)
        self._edge = edge
        self._base_img = base
        self._knob_img = knob
        self._half_knob_width = knob.width / 2
        self._half_knob_height = knob.height / 2
        self._knob_img.anchor_y = int(knob.height / 2)

        self._min_knob_x = x + edge
        self._max_knob_x = x + base.width - knob.width - edge

        self._user_group = group
        bg_group = Group(order=0, parent=group)
        fg_group = Group(order=1, parent=group)
        self._base_spr = pyglet.sprite.Sprite(self._base_img, x, y, batch=batch, group=bg_group)
        self._knob_spr = pyglet.sprite.Sprite(self._knob_img, x+edge, y+base.height/2, batch=batch, group=fg_group)

        self._value = 0
        self._in_update = False

    def _update_position(self) -> None:
        self._base_spr.position = self._x, self._y, 0
        self._min_knob_x = self._x + self._edge
        self._max_knob_x = self._x + self._base_img.width - self._knob_img.width - self._edge
        x = (self._max_knob_x - self._min_knob_x) * self._value / 100 + self._min_knob_x + self._half_knob_width
        x = max(self._min_knob_x, min(x - self._half_knob_width, self._max_knob_x))
        y = self._y + self._base_img.height / 2
        self._knob_spr.position = x, y, 0

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, value: float) -> None:
        assert type(value) in (int, float), "This Widget's value must be an int or float."
        self._value = value
        x = (self._max_knob_x - self._min_knob_x) * value / 100 + self._min_knob_x + self._half_knob_width
        self._knob_spr.x = max(self._min_knob_x, min(x - self._half_knob_width, self._max_knob_x))

    def update_groups(self, order: int) -> None:
        self._base_spr.group = Group(order=order + 1, parent=self._user_group)
        self._knob_spr.group = Group(order=order + 2, parent=self._user_group)

    @property
    def _min_x(self) -> int:
        return self._x + self._edge

    @property
    def _max_x(self) -> int:
        return self._x + self._width - self._edge

    @property
    def _min_y(self) -> int:
        return int(self._y - self._half_knob_height)

    @property
    def _max_y(self) -> int:
        return int(self._y + self._half_knob_height + self._base_img.height / 2)

    def _check_hit(self, x: int, y: int) -> bool:
        return self._min_x < x < self._max_x and self._min_y < y < self._max_y

    def _update_knob(self, x: int) -> None:
        self._knob_spr.x = max(self._min_knob_x, min(x - self._half_knob_width, self._max_knob_x))
        self._value = abs(((self._knob_spr.x - self._min_knob_x) * 100) / (self._min_knob_x - self._max_knob_x))
        self.dispatch_event('on_change', self, self._value)

    def on_mouse_press(self, x: int, y: int, buttons: int, modifiers: int) -> None:
        if not self.enabled:
            return
        if self._check_hit(x, y):
            self._in_update = True
            self._update_knob(x)

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int) -> None:
        if not self.enabled:
            return
        if self._in_update:
            self._update_knob(x)

    def on_mouse_scroll(self, x: int, y: int, scroll_x: float, scroll_y: float) -> None:
        if not self.enabled:
            return
        if self._check_hit(x, y):
            self._update_knob(self._knob_spr.x + self._half_knob_width + scroll_y)  # type: ignore reportArgumentType

    def on_mouse_release(self, x: int, y: int, buttons: int, modifiers: int) -> None:
        if not self.enabled:
            return
        self._in_update = False

    def on_change(self, widget: Slider, value: float) -> None:
        """Event: Returns the current value when the slider is changed."""


Slider.register_event_type('on_change')


class TextEntry(WidgetBase):
    """Instance of a text entry widget. Allows the user to enter and submit text.

    Triggers the event 'on_commit', when the user hits the Enter or Return key.
    The current text string is passed along with the event.
    """

    def __init__(self, text: str,
                 x: int, y: int, width: int,
                 color: tuple[int, int, int, int] = (255, 255, 255, 255),
                 text_color: tuple[int, int, int, int] = (0, 0, 0, 255),
                 caret_color: tuple[int, int, int, int] = (0, 0, 0, 255),
                 batch: Batch | None = None,
                 group: Group | None = None) -> None:
        """Create a text entry widget.

        Args:
            text:
                Initial text to display.
            x:
                X coordinate of the text entry widget.
            y:
                Y coordinate of the text entry widget.
            width:
                The width of the text entry widget.
            color:
                The color of the outline box in RGBA format.
            text_color:
                The color of the text in RGBA format.
            caret_color:
                The color of the caret (when it is visible) in RGBA or RGB format.
            batch:
                Optional batch to add the text entry widget to.
            group:
                Optional parent group of text entry widget.
        """
        self._doc = pyglet.text.document.UnformattedDocument(text)
        self._doc.set_style(0, len(self._doc.text), {'color': text_color})
        font = self._doc.get_font()
        height = font.ascent - font.descent

        self._user_group = group
        bg_group = Group(order=0, parent=group)
        fg_group = Group(order=1, parent=group)

        # Rectangular outline with 2-pixel pad:
        self._pad = p = 2
        self._outline = pyglet.shapes.Rectangle(x-p, y-p, width+p+p, height+p+p, color, batch=batch, group=bg_group)

        # Text and Caret:
        self._layout = IncrementalTextLayout(self._doc, x, y, 0, width, height, batch=batch, group=fg_group)
        self._caret = Caret(self._layout, color=caret_color)
        self._caret.visible = False

        self._focus = False

        super().__init__(x, y, width, height)

    def _update_position(self) -> None:
        self._layout.position = self._x, self._y, 0
        self._outline.position = self._x - self._pad, self._y - self._pad

    @property
    def value(self) -> str:
        return self._doc.text

    @value.setter
    def value(self, value: str) -> None:
        assert type(value) is str, "This Widget's value must be a string."
        self._doc.text = value

    @property
    def width(self) -> int:
        return self._width

    @width.setter
    def width(self, value: int) -> None:
        self._width = value
        self._layout.width = value
        self._outline.width = value

    @property
    def height(self) -> int:
        return self._height

    @height.setter
    def height(self, value: int) -> None:
        self._height = value
        self._layout.height = value
        self._outline.height = value

    @property
    def focus(self) -> bool:
        return self._focus

    @focus.setter
    def focus(self, value: bool) -> None:
        self._set_focus(value)

    def _check_hit(self, x: int, y: int) -> bool:
        return self._x < x < self._x + self._width and self._y < y < self._y + self._height

    def _set_focus(self, value: bool) -> None:
        self._focus = value
        self._caret.visible = value
        self._caret.layout = self._layout

    def update_groups(self, order: int) -> None:
        self._outline.group = Group(order=order + 1, parent=self._user_group)
        self._layout.group = Group(order=order + 2, parent=self._user_group)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        if not self.enabled:
            return

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int) -> None:
        if not self.enabled:
            return
        if self._focus:
            self._caret.on_mouse_drag(x, y, dx, dy, buttons, modifiers)

    def on_mouse_press(self, x: int, y: int, buttons: int, modifiers: int) -> None:
        if not self.enabled:
            return
        if self._check_hit(x, y):
            self._set_focus(True)
            self._caret.on_mouse_press(x, y, buttons, modifiers)
        else:
            self._set_focus(False)

    def on_text(self, text: str) -> None:
        if not self.enabled:
            return
        if self._focus:
            # Commit on Enter/Return:
            if text in ('\r', '\n'):
                self.dispatch_event('on_commit', self, self._layout.document.text)
                self._set_focus(False)
                return
            self._caret.on_text(text)

    def on_text_motion(self, motion: int) -> None:
        if not self.enabled:
            return
        if self._focus:
            self._caret.on_text_motion(motion)

    def on_text_motion_select(self, motion: int) -> None:
        if not self.enabled:
            return
        if self._focus:
            self._caret.on_text_motion_select(motion)

    def on_commit(self, widget: TextEntry, text: str) -> None:
        """Event: dispatches the current text when committed via Enter/Return key."""


TextEntry.register_event_type('on_commit')
