# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# Copyright (c) 2008-2021 pyglet contributors
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

"""Display different types of interactive widgets.
"""

import pyglet

from pyglet.event import EventDispatcher
from pyglet.graphics import Group
from pyglet.text.caret import Caret
from pyglet.text.layout import IncrementalTextLayout
from pyglet.window import mouse


class WidgetBase(EventDispatcher):

    def __init__(self,
                 x: int,
                 y: int,
                 width: int,
                 height: int):
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self._bg_group = None
        self._fg_group = None
        self.enabled = True
        self.frame = None

    def update_groups(self, order):
        pass

    @property
    def x(self):
        """X coordinate of the widget.

        :type: int
        """
        return self._x

    @property
    def y(self):
        """Y coordinate of the widget.

        :type: int
        """
        return self._y

    @property
    def width(self):
        """Width of the widget.

        :type: int
        """
        return self._width

    @property
    def height(self):
        """Height of the widget.

        :type: int
        """
        return self._height

    @property
    def aabb(self):
        """Bounding box of the widget.

        Expresesed as (x, y, x + width, y + height)

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

    def _check_hit(self, x, y):
        return self._x < x < self._x + self._width and self._y < y < self._y + self._height

    def on_mouse_press(self, x, y, buttons, modifiers):
        pass

    def on_mouse_release(self, x, y, buttons, modifiers):
        pass

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        pass

    def on_mouse_motion(self, x, y, dx, dy):
        pass

    def on_mouse_scroll(self, x, y, mouse, direction):
        pass

    def on_text(self, text):
        pass

    def on_text_motion(self, motion):
        pass

    def on_text_motion_select(self, motion):
        pass

    def on_drag(self, x, y, dx, dy, buttons, modifiers):
        pass


class PushButton(WidgetBase):
    """Instance of a push button.

    Triggers the event 'on_press' when it is clicked by the mouse.
    Triggers the event 'on_release' when the mouse is released.
    """

    def __init__(self,
                 x: int,
                 y: int,
                 pressed: pyglet.image.AbstractImage,
                 depressed: pyglet.image.AbstractImage,
                 hover: pyglet.image.AbstractImage = None,
                 batch: pyglet.graphics.Batch = None,
                 group: pyglet.graphics.Group = None):
        """Create a push button.

        :Parameters:
            `x` : int
                X coordinate of the push button.
            `y` : int
                Y coordinate of the push button.
            `pressed` : `~pyglet.image.AbstractImage`
                Image to display when the button is pressed.
            `depresseed` : `~pyglet.image.AbstractImage`
                Image to display when the button isn't pressed.
            `hover` : `~pyglet.image.AbstractImage`
                Image to display when the button is being hovered over.
            `batch` : `~pyglet.graphics.Batch`
                Optional batch to add the push button to.
            `group` : `~pyglet.graphics.Group`
                Optional parent group of the push button.
        """
        super().__init__(x, y, depressed.width, depressed.height)
        self._pressed_img = pressed
        self._depressed_img = depressed
        self._hover_img = hover or depressed

        # TODO: add `draw` method or make Batch required.
        self._batch = batch or pyglet.graphics.Batch()
        self._user_group = group
        bg_group = Group(order=0, parent=group)
        self._sprite = pyglet.sprite.Sprite(self._depressed_img, x, y, batch=batch, group=bg_group)

        self._pressed = False

    @property
    def value(self):
        return self._pressed

    @value.setter
    def value(self, value):
        assert type(value) is bool, "This Widget's value must be True or False."
        self._pressed = value
        self._sprite.image = self._pressed_img if self._pressed else self._depressed_img

    def update_groups(self, order):
        self._sprite.group = Group(order=order + 1, parent=self._user_group)

    def on_mouse_press(self, x, y, buttons, modifiers):
        if not self.enabled or not self._check_hit(x, y):
            return
        self._sprite.image = self._pressed_img
        self._pressed = True
        self.dispatch_event('on_press')

    def on_mouse_release(self, x, y, buttons, modifiers):
        if not self.enabled or not self._pressed:
            return
        self._sprite.image = self._hover_img if self._check_hit(x, y) else self._depressed_img
        self._pressed = False
        self.dispatch_event('on_release')

    def on_mouse_motion(self, x, y, dx, dy):
        if not self.enabled or self._pressed:
            return
        self._sprite.image = self._hover_img if self._check_hit(x, y) else self._depressed_img

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if not self.enabled or self._pressed:
            return
        self._sprite.image = self._hover_img if self._check_hit(x, y) else self._depressed_img

    def draw(self):
        self._sprite.draw()
        # Maybe can solve the `draw` method?


PushButton.register_event_type('on_press')
PushButton.register_event_type('on_release')


class ToggleButton(PushButton):
    """Instance of a toggle button.

    Triggers the event 'on_toggle' when the mouse is pressed or released.
    """

    def _get_release_image(self, x, y):
        return self._hover_img if self._check_hit(x, y) else self._depressed_img

    def on_mouse_press(self, x, y, buttons, modifiers):
        if not self.enabled or not self._check_hit(x, y):
            return
        self._pressed = not self._pressed
        self._sprite.image = self._pressed_img if self._pressed else self._get_release_image(x, y)
        self.dispatch_event('on_toggle', self._pressed)

    def on_mouse_release(self, x, y, buttons, modifiers):
        if not self.enabled or self._pressed:
            return
        self._sprite.image = self._get_release_image(x, y)


ToggleButton.register_event_type('on_toggle')


class Slider(WidgetBase):
    """Instance of a slider made of a base and a knob image.

    Triggers the event 'on_change' when the knob position is changed.
    The knob position can be changed by dragging with the mouse, or
    scrolling the mouse wheel.
    """

    def __init__(self,
                 x: int,
                 y: int,
                 base: pyglet.image.AbstractImage,
                 knob: pyglet.image.AbstractImage,
                 edge: int = 0,
                 batch: pyglet.graphics.Batch = None,
                 group: pyglet.graphics.Group = None):
        """Create a slider.

        :Parameters:
            `x` : int
                X coordinate of the slider.
            `y` : int
                Y coordinate of the slider.
            `base` : `~pyglet.image.AbstractImage`
                Image to display as the background to the slider.
            `knob` : `~pyglet.image.AbstractImage`
                Knob that moves to show the position of the slider.
            `edge` : int
                Pixels from the maximum and minimum position of the slider,
                to the edge of the base image.
            `batch` : `~pyglet.graphics.Batch`
                Optional batch to add the slider to.
            `group` : `~pyglet.graphics.Group`
                Optional parent group of the slider.
        """
        super().__init__(x, y, base.width, knob.height)
        self._edge = edge
        self._base_img = base
        self._knob_img = knob
        self._half_knob_width = knob.width / 2
        self._half_knob_height = knob.height / 2
        self._knob_img.anchor_y = knob.height / 2

        self._min_knob_x = x + edge
        self._max_knob_x = x + base.width - knob.width - edge

        self._user_group = group
        bg_group = Group(order=0, parent=group)
        fg_group = Group(order=1, parent=group)
        self._base_spr = pyglet.sprite.Sprite(self._base_img, x, y, batch=batch, group=bg_group)
        self._knob_spr = pyglet.sprite.Sprite(self._knob_img, x + edge, y + base.height / 2, batch=batch, group=fg_group)

        self._value = 0
        self._in_update = False

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        assert type(value) in (int, float), "This Widget's value must be an int or float."
        self._value = value
        x = (self._max_knob_x - self._min_knob_x) * value / 100 + self._min_knob_x + self._half_knob_width
        self._knob_spr.x = max(self._min_knob_x, min(x - self._half_knob_width, self._max_knob_x))

    def update_groups(self, order):
        self._base_spr.group = Group(order=order + 1, parent=self._user_group)
        self._knob_spr.group = Group(order=order + 2, parent=self._user_group)

    @property
    def _min_x(self):
        return self._x + self._edge

    @property
    def _max_x(self):
        return self._x + self._width - self._edge

    @property
    def _min_y(self):
        return self._y - self._half_knob_height

    @property
    def _max_y(self):
        return self._y + self._half_knob_height + self._base_img.height / 2

    def _check_hit(self, x, y):
        return self._min_x < x < self._max_x and self._min_y < y < self._max_y

    def _update_knob(self, x):
        self._knob_spr.x = max(self._min_knob_x, min(x - self._half_knob_width, self._max_knob_x))
        self._value = abs(((self._knob_spr.x - self._min_knob_x) * 100) / (self._min_knob_x - self._max_knob_x))
        self.dispatch_event('on_change', self._value)

    def on_mouse_press(self, x, y, buttons, modifiers):
        if not self.enabled:
            return
        if self._check_hit(x, y):
            self._in_update = True
            self._update_knob(x)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if not self.enabled:
            return
        if self._in_update:
            self._update_knob(x)

    def on_mouse_scroll(self, x, y, mouse, direction):
        if not self.enabled:
            return
        if self._check_hit(x, y):
            self._update_knob(self._knob_spr.x + self._half_knob_width + direction)

    def on_mouse_release(self, x, y, buttons, modifiers):
        if not self.enabled:
            return
        self._in_update = False


Slider.register_event_type('on_change')


class TextEntry(WidgetBase):
    """Instance of a text entry widget.

    Allows the user to enter and submit text.
    """

    def __init__(self,
                 text: str,
                 x: int,
                 y: int,
                 width: int,
                 color=(255, 255, 255, 255),
                 text_color=(0, 0, 0, 255),
                 caret_color=(0, 0, 0),
                 batch: pyglet.graphics.Batch = None,
                 group: pyglet.graphics.Group = None):
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
            `text_color` : (int, int, int)
                The color of the caret in RGB format.
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
        p = 2
        self._outline = pyglet.shapes.Rectangle(x - p, y - p, width + p + p, height + p + p, color[:3], batch, bg_group)
        self._outline.opacity = color[3]

        # Text and Caret:
        self._layout = IncrementalTextLayout(self._doc, width, height, multiline=False, batch=batch, group=fg_group)
        self._layout.x = x
        self._layout.y = y
        self._caret = Caret(self._layout, color=caret_color)
        self._caret.visible = False

        self._focus = False

        super().__init__(x, y, width, height)

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

    def update_groups(self, order):
        self._outline.group = Group(order=order + 1, parent=self._user_group)
        self._layout.group = Group(order=order + 2, parent=self._user_group)

    def on_mouse_motion(self, x, y, dx, dy):
        if not self.enabled:
            return
        if not self._check_hit(x, y):
            self._set_focus(False)

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

    def on_text(self, text):
        if not self.enabled:
            return
        if self._focus:
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


TextEntry.register_event_type('on_commit')


class DragSprite(WidgetBase):
    """Instance of a drag button.

    Triggers the event 'on_press' when it is clicked by the mouse.
    Triggers the event 'on_release' when the mouse is released.
    Triggers the event 'on_drag' when it is drag by mouse.
    """
    # TODO make it More standardized
    # TODO add group thing again(i don't know how to)
    # by shenjack

    def __init__(self,
                 x: int,
                 y: int,
                 image: pyglet.image.AbstractImage,
                 drag_by_all: bool = False,
                 drag_out_window: bool = False,
                 batch: pyglet.graphics.Batch = None,
                 group: pyglet.graphics.Group = None):
        """Create a draggable sprite.

        :Parameters:
            `x` : int
                X coordinate of the push button.
            `y` : int
                Y coordinate of the push button.
            `image` : `~pyglet.image.AbstractImage`
                Image to display when the sprite is pressed.
            `drag_by_all` : bool
                If True then sprite will move whatever witch mouse button drag the sprite,
                or the sprite will only move when Left mouse button drag.
            `drag_out_window` : bool
                If True then sprite will move out of the window with the mouse dragging,
                or the sprite will only stop on the edge of the window.
            `batch` : `~pyglet.graphics.Batch`
                Optional batch to add the sprite to.
            `group` : `~pyglet.graphics.Group`
                Optional parent group of the sprite.
        """
        super().__init__(x, y, image.width, image.height)
        self._image = image
        self._batch = batch or pyglet.graphics.Batch()
        self._sprite = pyglet.sprite.Sprite(self._image, x, y, batch=batch, group=group)
        self.drag_by_all = drag_by_all
        self.drag_out_window = drag_out_window
        self.dragging = False

    def on_mouse_press(self, x, y, buttons, modifiers):
        if (buttons == mouse.LEFT) or self.drag_by_all:
            if self._check_hit(x, y):
                self.dragging = True
                self.dispatch_event('on_press', buttons, self.dragging)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.dragging:
            # TODO find a way to get window height and width
            if (self._x + dx) < 0 and not self.drag_out_window:
                self._sprite.x = 0
                self._x = 0
            else:
                self._sprite.x += dx
                self._x += dx
            if (self._y + dy) < 0 and not self.drag_out_window:
                self._sprite.y = 0
                self._y = 0
            else:
                self._sprite.y += dy
                self._y += dy
            self.dispatch_event('on_drag', x, y, dx, dy, buttons, modifiers)

    def draw(self):
        self._sprite.draw()
        # just use self.draw can draw

    def on_mouse_release(self, x, y, buttons, modifiers):
        if self.dragging:
            self.dragging = not self.dragging
            self.dispatch_event('on_release', x, y, buttons, modifiers)


DragSprite.register_event_type('on_drag')
DragSprite.register_event_type('on_press')
DragSprite.register_event_type('on_release')
