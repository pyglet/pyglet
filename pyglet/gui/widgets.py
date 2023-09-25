"""Display different types of interactive widgets.
"""

import pyglet

from pyglet.event import EventDispatcher
from pyglet.graphics import Group
from pyglet.text.caret import Caret
from pyglet.text.layout import IncrementalTextLayout


class WidgetBase(EventDispatcher):

    def __init__(self, x, y, width, height):
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self._bg_group = None
        self._fg_group = None
        self.enabled = True

    def update_groups(self, order):
        pass

    @property
    def x(self):
        """X coordinate of the widget.

        :type: int
        """
        return self._x

    @x.setter
    def x(self, value):
        self._x = value
        self._update_position()

    @property
    def y(self):
        """Y coordinate of the widget.

        :type: int
        """
        return self._y

    @y.setter
    def y(self, value):
        self._y = value
        self._update_position()

    @property
    def position(self):
        """The x, y coordinate of the widget as a tuple.

        :type: tuple(int, int)
        """
        return self._x, self._y

    @position.setter
    def position(self, values):
        self._x, self._y = values[0], values[1]
        self._update_position()

    @property
    def width(self):
        """Width of the widget.

        :type: int
        """
        return self._width
    
    @width.setter
    def width(self, value):
        self.on_resize(value, self._height)

    @property
    def height(self):
        """Height of the widget.

        :type: int
        """
        return self._height
    
    @height.setter
    def height(self, value):
        self.on_resize(self._width, value)

    @property
    def size(self):
        return (self.width, self.height)

    @size.setter
    def size(self, size_value):
        self.on_resize(size_value[0], size_value[1])

    @property
    def aabb(self):
        """Bounding box of the widget.

        Expressed as (x, y, x + width, y + height)

        :type: (int, int, int, int)
        """
        return self._x, self._y, self._x + self._width, self._y + self._height

    @property
    def value(self):
        """Query or set the Widget's value.
        
        This property allows you to set the value of a Widget directly, without any
        user input.  This could be used, for example, to restore Widgets to a
        previous state, or if some event in your program is meant to naturally
        change the same value that the Widget controls.  Note that events are not
        dispatched when changing this property.
        """
        raise NotImplementedError("Value depends on control type!")
    
    @value.setter
    def value(self, value):
        raise NotImplementedError("Value depends on control type!")
    
    def draw(self):
        """Draw widget manually in case batch is not provided"""
        pass
    
    def on_resize(self, width, height):
        self._width = width
        self._height = height

    def _check_hit(self, x, y):
        return self._x < x < self._x + self._width and self._y < y < self._y + self._height

    def _update_position(self):
        raise NotImplementedError("Unable to reposition this Widget")

    def on_mouse_press(self, x, y, buttons, modifiers):
        pass

    def on_mouse_release(self, x, y, buttons, modifiers):
        pass

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        pass

    def on_mouse_motion(self, x, y, dx, dy):
        pass

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        pass

    def on_text(self, text):
        pass

    def on_text_motion(self, motion):
        pass

    def on_text_motion_select(self, motion):
        pass

    def on_key_press(self, symbol, modifiers):
        pass
    
    def on_key_release(self, symbol, modifiers):
        pass


class PushButton(WidgetBase):
    """Instance of a push button.

    Triggers the event 'on_press' when it is clicked by the mouse.
    Triggers the event 'on_release' when the mouse is released.
    """

    def __init__(self, x, y, 
                 pressed=(150, 150, 150, 255), 
                 depressed=(230, 230, 230, 255),
                 hover=(255, 255, 255, 255),
                 width=None, height=None,
                 batch=None, group=None):
        """Create a push button.

        :Parameters:
            `x` : int
                X coordinate of the push button.
            `y` : int
                Y coordinate of the push button.
            `pressed` : `~pyglet.image.AbstractImage` or (int, int, int, int)
                Image or color to display when the button is pressed.
            `depresseed` : `~pyglet.image.AbstractImage` or (int, int, int, int)
                Image or color to display when the button isn't pressed.
            `hover` : `~pyglet.image.AbstractImage` or (int, int, int, int)
                Image or color to display when the button is being hovered over.
            `batch` : `~pyglet.graphics.Batch`
                Optional batch to add the push button to.
            `group` : `~pyglet.graphics.Group`
                Optional parent group of the push button.
        """
        if type(pressed) != type(depressed) or type(hover) != type(depressed):
            raise Exception("pressed, depressed and hover values must be of equal types")
        image_provided = isinstance(depressed, pyglet.image.AbstractImage)
        
        if width is None:
            width = depressed.width if image_provided else 50
        if height is None:
            height = depressed.height if image_provided else 50
        
        super().__init__(x, y, width, height)
        self._pressed_visual = pressed
        self._depressed_visual = depressed
        self._hover_visual = hover or depressed

        # TODO: add `draw` method or make Batch required.
        self._batch = batch or pyglet.graphics.Batch()
        self._user_group = group
        bg_group = Group(order=0, parent=group)
        if image_provided:
            self._sprite = pyglet.sprite.Sprite(self._depressed_visual, x, y, batch=batch, group=bg_group)
        else:
            self._sprite = pyglet.shapes.Rectangle(x, y, width, height, self._depressed_visual, self._batch, bg_group)

        self._pressed = False
        self._hovered = False

    def _update_position(self):
        self._sprite.position = self._x, self._y, 0

    @property
    def value(self):
        return self._pressed
    
    def _get_current_visual(self):
        if self._pressed:
            return self._pressed_visual
        elif self._hovered:
            return self._hover_visual
        else:
            return self._depressed_visual
    
    def _update_visual_state(self):
        if isinstance(self._sprite, pyglet.sprite.Sprite):
            self._sprite.image = self._get_current_visual()
        else:
            self._sprite.color = self._get_current_visual()
    
    @value.setter
    def value(self, value):
        assert type(value) is bool, "This Widget's value must be True or False."
        self._pressed = value
        self._update_visual_state()

    def update_groups(self, order):
        self._sprite.group = Group(order=order + 1, parent=self._user_group)

    def on_mouse_press(self, x, y, buttons, modifiers):
        if not self.enabled or not self._check_hit(x, y):
            return
        self._pressed = True
        self._update_visual_state()
        self.dispatch_event('on_press')

    def on_mouse_release(self, x, y, buttons, modifiers):
        if not self.enabled or not self._pressed:
            return
        self._hovered = self._check_hit(x, y)
        self._pressed = False
        self._update_visual_state()
        self.dispatch_event('on_release')

    def on_mouse_motion(self, x, y, dx, dy):
        if not self.enabled:
            return
        self._hovered = self._check_hit(x, y)
        self._update_visual_state()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if not self.enabled:
            return
        self._hovered = self._check_hit(x, y)
        self._update_visual_state()

    def on_resize(self, width, height):
        super(PushButton, self).on_resize(width, height)
        self._sprite.width = width
        self._sprite.height = height

    def draw(self):
        self._sprite.draw()

PushButton.register_event_type('on_press')
PushButton.register_event_type('on_release')

class TextPushButton(PushButton):
    """Instance of a button with a label inside."""

    def __init__(self, x, y, 
                 text,
                 pressed=(150, 150, 150, 255), 
                 depressed=(230, 230, 230, 255),
                 hover=(255, 255, 255, 255),
                 text_color=(0, 0, 0, 255),
                 width=None, height=None,
                 batch=None, group=None):
        
        super().__init__(x, y, pressed=pressed, depressed=depressed, hover=hover, width=width, height=height, batch=batch, group=group)
        self._label = pyglet.text.Label(text, 
                                        x=x, y=y, width=self.width, height=self.height,
                                        anchor_y='bottom',
                                        batch=self._batch, color=text_color)
        self._label.content_halign = 'center'
        self._label.content_valign = 'center'

    def _update_position(self):
        super()._update_position()
        self._label.position = (self.x, self.y, 0)

    def on_resize(self, width, height):
        super().on_resize(width, height)
        self._label.width = width
        self._label.height = height

    def draw(self):
        super().draw()
        self._label.draw()

    @property
    def text(self):
        return self._label.text
    
    @text.setter
    def text(self, value):
        self._label.text = value


class ToggleButton(PushButton):
    """Instance of a toggle button.

    Triggers the event 'on_toggle' when the mouse is pressed or released.
    """

    def on_mouse_press(self, x, y, buttons, modifiers):
        if not self.enabled or not self._check_hit(x, y):
            return
        self._pressed = not self._pressed
        self._update_visual_state()
        self.dispatch_event('on_toggle', self._pressed)

    def on_mouse_release(self, x, y, buttons, modifiers):
        if not self.enabled:
            return
        self._hovered = self._check_hit(x, y)
        self._update_visual_state()

    def _get_current_visual(self):
        if self._hovered:
            return self._hover_visual
        elif self._pressed:
            return self._pressed_visual
        else:
            return self._depressed_visual


ToggleButton.register_event_type('on_toggle')


class Slider(WidgetBase):
    """Instance of a slider made of a base and a knob image.

    Triggers the event 'on_change' when the knob position is changed.
    The knob position can be changed by dragging with the mouse, or
    scrolling the mouse wheel.
    """

    def __init__(self, 
                 x, y,
                 width, height,
                 base=(230, 230, 230, 255),
                 knob=(150, 150, 150, 255), 
                 edge=0,
                 value_range=(0, 1),
                 integer=False,
                 orientation='horizontal', 
                 batch=None, group=None):
        """Create a slider.

        :Parameters:
            `x` : int
                X coordinate of the slider.
            `y` : int
                Y coordinate of the slider.
            `base` : `~pyglet.image.AbstractImage` or (int, int, int, int)
                Image or color to display as the background to the slider.
            `knob` : `~pyglet.image.AbstractImage` or (int, int, int, int)
                Knob or color that moves to show the position of the slider.
            `edge` : int or (int, int)
                Pixels from the maximum and minimum position of the slider,
                to the edge of the base image.
            `value_range` : (float, float)
                Slider value range.
            `integer` : bool
                Is slider counts only in integer numbers.
            `orientation` : str
                Optional parent group of the slider.
            `batch` : `~pyglet.graphics.Batch`
                Optional batch to add the slider to.
            `group` : `~pyglet.graphics.Group`
                Optional parent group of the slider.

        """
        if type(base) != type(knob):
            raise Exception("base and knob values must be of equal types")
        assert orientation in ('horizontal', 'vertical'), "Unknown orientation type, must be 'horizontal' or 'vertical'"
        image_provided = isinstance(base, pyglet.image.AbstractImage)

        if width is None:
            width = max(base.width, knob.width) if image_provided else (100 if orientation == 'horizontal' else 20)
        if height is None:
            height = max(base.height, knob.height) if image_provided else (100 if orientation == 'vertical' else 20)
        super().__init__(x, y, width, height)

        self.value_range = value_range
        self._horizontal = orientation == 'horizontal'
        self._integer = integer
        if isinstance(edge, int):
            edge = (edge, edge)
        self._edge = edge
        self._base_img = base
        self._knob_img = knob

        self._user_group = group
        bg_group = Group(order=0, parent=group)
        fg_group = Group(order=1, parent=group)
        if image_provided:
            self._base_spr = pyglet.sprite.Sprite(self._base_img, batch=batch, group=bg_group)
            self._knob_spr = pyglet.sprite.Sprite(self._knob_img, batch=batch, group=fg_group)
        else:
            self._base_spr = pyglet.shapes.Rectangle(x, y, width, height, self._base_img, batch=batch, group=bg_group)
            self._knob_spr = pyglet.shapes.Rectangle(x, y, min(width, height), min(width, height), self._knob_img, batch=batch, group=fg_group)

        if self._horizontal:
            self._base_display_style = ('padding', ((self.height - self._base_spr.height) / 2,) * 2)
            self._knob_display_style = ('padding', ((self.height - self._knob_spr.height) / 2,) * 2)
            self._min_knob_size = self._knob_spr.width
        else:
            self._base_display_style = ('padding', ((self.width - self._base_spr.width) / 2,) * 2)
            self._knob_display_style = ('padding', ((self.width - self._knob_spr.width) / 2,) * 2)
            self._min_knob_size = self._knob_spr.height

        self._knob_size = 0

        self._value = 0
        self._in_update = False

        self.on_resize(self.width, self.height)

    
    def _update_position(self):
        if self._horizontal:
            self._base_spr.x = self._x
            self._base_spr.y = self._y + self._calculate_offset(self._base_display_style, self.height)
            self._knob_spr.y = self._y + self._calculate_offset(self._knob_display_style, self.height)
        else:
            self._base_spr.x = self._x + self._calculate_offset(self._base_display_style, self.width)
            self._base_spr.y = self._y
            self._knob_spr.x = self._x + self._calculate_offset(self._knob_display_style, self.width)
        self.value = self._value

    def on_resize(self, width, height):
        super(Slider, self).on_resize(width, height)
        if self._horizontal:
            self._base_spr.width = width
            self._base_spr.height = self._calculate_size(self._base_display_style, self.height)
            self._knob_spr.width = max(self.knob_size, self._min_knob_size)
            self._knob_spr.height = self._calculate_size(self._knob_display_style, self.height)
        else:
            self._base_spr.height = height
            self._base_spr.width = self._calculate_size(self._base_display_style, self.width)
            self._knob_spr.height = max(self.knob_size, self._min_knob_size)
            self._knob_spr.width = self._calculate_size(self._knob_display_style, self.width)
        self._update_position()

    def _calculate_offset(self, display_style, max_size):
        if display_style[0] == 'padding':
            return display_style[1][0]
        if display_style[0] == 'percent':
            return max_size * (1 - display_style[1] / 100) / 2
        if display_style[0] == 'pixels':
            return (max_size - display_style[1]) / 2
        
    def _calculate_size(self, display_style, max_size):
        if display_style[0] == 'padding':
            return max_size - display_style[1][0] - display_style[1][1]
        if display_style[0] == 'percent':
            return max_size * display_style[1] / 100
        if display_style[0] == 'pixels':
            return display_style[1]
        
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        assert type(value) in (int, float), "This Widget's value must be an int or float."
        if self._integer: value = round(value)
        value = min(max(value, self.value_range[0]), self.value_range[1])
        self._value = value

        if self._horizontal:
            min_x, max_x = self._min_x, self._max_x
            self._knob_spr.x = (
                (value - self._value_range[0]) / 
                (self._value_range[1] - self._value_range[0]) *
                (max_x - min_x) + min_x
            )
        else:
            min_y, max_y = self._min_y, self._max_y
            self._knob_spr.y = (
                (value - self._value_range[0]) / 
                (self._value_range[1] - self._value_range[0]) *
                (max_y - min_y) + min_y
            )

    def update_groups(self, order):
        self._base_spr.group = Group(order=order + 1, parent=self._user_group)
        self._knob_spr.group = Group(order=order + 2, parent=self._user_group)

    @property
    def _min_x(self):
        return self._x + self._edge[0] - max(self._min_knob_size - self.knob_size, 0) / 2

    @property
    def _max_x(self):
        return self._x + self._width - self._edge[1] - max(self._min_knob_size / 2, self.knob_size)

    @property
    def _min_y(self):
        return self._y + self._edge[0] - max(self._min_knob_size - self.knob_size, 0) / 2

    @property
    def _max_y(self):
        return self._y + self._height - self._edge[1] - max(self._min_knob_size / 2, self.knob_size)

    @property
    def value_range(self):
        return self._value_range
    
    @value_range.setter
    def value_range(self, value):
        assert value[0] < value[1], "Range Min must be < Range Max"
        self._value_range = value
    
    @property
    def knob_size(self):
        return self._knob_size
    
    @knob_size.setter
    def knob_size(self, value):
        self._knob_size = value
        self.on_resize(self.width, self.height)

    def _check_hit(self, x, y):
        return self.x < x < self.x + self.width and self.y < y < self.y + self.height

    def _update_knob(self, x, y):
        if self._horizontal:
            x -= self.knob_size / 2
            min_x, max_x = self._min_x, self._max_x
            if min_x < max_x:
                self.value = (
                    (x - min_x) / (max_x - min_x) *
                    (self.value_range[1] - self.value_range[0]) + self.value_range[0]
                )
            else:
                self.value = 0
        else:
            y -= self.knob_size / 2
            min_y, max_y = self._min_y, self._max_y
            if min_y < max_y:
                self.value = (
                    (y - min_y) / (max_y - min_y) *
                    (self.value_range[1] - self.value_range[0]) + self.value_range[0]
                )
            else:
                self.value = 0
        self.dispatch_event('on_change', self._value)

    def set_sprite_style(self, sprite_name, size_type, value):
        if sprite_name == 'base':
            self._base_display_style = (size_type, value)
            self.on_resize(self.width, self.height)
        elif sprite_name == 'knob':
            self._knob_display_style = (size_type, value)
            self.on_resize(self.width, self.height)
        else:
            raise Exception('Unknown sprite type:', sprite_name)

    def on_mouse_press(self, x, y, buttons, modifiers):
        if not self.enabled:
            return
        if self._check_hit(x, y):
            self._in_update = True
            self._update_knob(x, y)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if not self.enabled:
            return
        if self._in_update:
            self._update_knob(x, y)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if not self.enabled:
            return
        if self._check_hit(x, y):
            self.value += scroll_y

    def on_mouse_release(self, x, y, buttons, modifiers):
        if not self.enabled:
            return
        self._in_update = False

    def draw(self):
        self._base_spr.draw()
        self._knob_spr.draw()

Slider.register_event_type('on_change')


class TextEntry(WidgetBase):
    """Instance of a text entry widget.

    Allows the user to enter and submit text.
    """

    def __init__(self, text, x, y, width,
                 color=(255, 255, 255, 255), text_color=(0, 0, 0, 255), caret_color=(0, 0, 0, 255),
                 batch=None, group=None):
        """Create a text entry widget.

        :Parameters:
            `text` : str
                Initial text to display.
            `x` : int
                X coordinate of the text entry widget.
            `y` : int
                Y coordinate of the text entry widget.
            `width` : int
                The width of the text entry widget.
            `color` : (int, int, int, int)
                The color of the outline box in RGBA format.
            `text_color` : (int, int, int, int)
                The color of the text in RGBA format.
            `caret_color` : (int, int, int, int)
                The color of the caret when it is visible in RGBA or RGB
                format.
            `batch` : `~pyglet.graphics.Batch`
                Optional batch to add the text entry widget to.
            `group` : `~pyglet.graphics.Group`
                Optional parent group of text entry widget.
        """
        self._doc = pyglet.text.document.UnformattedDocument(text)
        self._doc.set_style(0, len(self._doc.text), dict(color=text_color))
        font = self._doc.get_font()
        height = font.ascent - font.descent

        self._user_group = group
        bg_group = Group(order=0, parent=group)
        fg_group = Group(order=1, parent=group)

        # Rectangular outline with 2-pixel pad:
        self._pad = p = 2
        self._outline = pyglet.shapes.Rectangle(x-p, y-p, width+p+p, height+p+p, color[:3], batch, bg_group)
        self._outline.opacity = color[3]

        # Text and Caret:
        self._layout = IncrementalTextLayout(self._doc, width, height, multiline=False, batch=batch, group=fg_group)
        self._layout.x = x
        self._layout.y = y
        self._caret = Caret(self._layout, color=caret_color)
        self._caret.visible = False

        self._focus = False

        super().__init__(x, y, width, height)

    def _update_position(self):
        self._layout.position = self._x, self._y, 0
        self._outline.position = self._x - self._pad, self._y - self._pad

    @property
    def value(self):
        return self._doc.text

    @value.setter
    def value(self, value):
        assert type(value) is str, "This Widget's value must be a string."
        self._doc.text = value

    def _check_hit(self, x, y):
        return self._x < x < self._x + self._width and self._y < y < self._y + self._height

    def _set_focus(self, value):
        self._focus = value
        self._caret.visible = value
        self._caret.layout = self._layout

    def update_groups(self, order):
        self._outline.group = Group(order=order + 1, parent=self._user_group)
        self._layout.group = Group(order=order + 2, parent=self._user_group)

    def on_mouse_motion(self, x, y, dx, dy):
        if not self.enabled:
            return

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if not self.enabled:
            return
        if self._focus:
            self._caret.on_mouse_drag(x, y, dx, dy, buttons, modifiers)

    def on_mouse_press(self, x, y, buttons, modifiers):
        if not self.enabled:
            return
        if self._check_hit(x, y):
            self._set_focus(True)
            self._caret.on_mouse_press(x, y, buttons, modifiers)
        else:
            self._set_focus(False)

    def on_resize(self, width, height):
        super(TextEntry, self).on_resize(width, height)
        self._layout.width, self._layout.height = width, height
        self._outline.width, self._outline.height = width + self._pad * 2, height + self._pad * 2

    def on_key_press(self, symbol, modifiers):
        if not self._focus:
            return
        if symbol == pyglet.window.key.A and modifiers & pyglet.window.key.MOD_CTRL:
            self._caret.select_all()

    def on_text(self, text):
        if not self.enabled:
            return
        if self._focus:
            # Commit on Enter/Return:
            if text in ('\r', '\n'):
                self.dispatch_event('on_commit', self._layout.document.text)
                self._set_focus(False)
                return
            self._caret.on_text(text)

    def on_text_motion(self, motion):
        if not self.enabled:
            return
        if self._focus:
            self._caret.on_text_motion(motion)

    def on_text_motion_select(self, motion):
        if not self.enabled:
            return
        if self._focus:
            self._caret.on_text_motion_select(motion)

    def on_commit(self, text):
        if not self.enabled:
            return
        """Text has been commited via Enter/Return key."""

    def draw(self):
        self._outline.draw()
        self._layout.draw()


TextEntry.register_event_type('on_commit')
