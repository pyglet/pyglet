# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# Copyright (c) 2008-2020 pyglet contributors
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

import pyglet

from pyglet.event import EventDispatcher
from pyglet.graphics import OrderedGroup
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

    def update_groups(self, order):
        pass

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def aabb(self):
        return self._x, self._y, self._x + self._width, self._y + self._height

    def _check_hit(self, x, y):
        return self._x < x < self._x + self._width and self._y < y < self._y + self._height

    def on_mouse_press(self, x, y, buttons, modifiers):
        pass

    def on_mouse_release(self, x, y, buttons, modifiers):
        pass

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        pass

    def on_mouse_scroll(self, x, y, mouse, direction):
        pass

    def on_text(self, text):
        pass

    def on_text_motion(self, motion):
        pass

    def on_text_motion_select(self, motion):
        pass


WidgetBase.register_event_type('on_mouse_press')
WidgetBase.register_event_type('on_mouse_release')
WidgetBase.register_event_type('on_mouse_motion')
WidgetBase.register_event_type('on_mouse_scroll')
WidgetBase.register_event_type('on_mouse_drag')
WidgetBase.register_event_type('on_text')
WidgetBase.register_event_type('on_text_motion')
WidgetBase.register_event_type('on_text_motion_select')


class PushButton(WidgetBase):

    def __init__(self, x, y, pressed, depressed, hover=None, batch=None, group=None):
        super().__init__(x, y, depressed.width, depressed.height)
        self._pressed_img = pressed
        self._depressed_img = depressed
        self._hover_img = hover or depressed

        # TODO: add `draw` method or make Batch required.
        self._batch = batch or pyglet.graphics.Batch()
        self._user_group = group
        bg_group = OrderedGroup(0, parent=group)
        self._sprite = pyglet.sprite.Sprite(self._depressed_img, x, y, batch=batch, group=bg_group)

        self._pressed = False

    def update_groups(self, order):
        self._sprite.group = OrderedGroup(order + 1, self._user_group)

    def on_mouse_press(self, x, y, buttons, modifiers):
        if not self._check_hit(x, y):
            return
        self._sprite.image = self._pressed_img
        self._pressed = True
        self.dispatch_event('on_press')

    def on_mouse_release(self, x, y, buttons, modifiers):
        if not self._pressed:
            return
        self._sprite.image = self._hover_img if self._check_hit(x, y) else self._depressed_img
        self._pressed = False
        self.dispatch_event('on_release')

    def on_mouse_motion(self, x, y, dx, dy):
        if self._pressed:
            return
        self._sprite.image = self._hover_img if self._check_hit(x, y) else self._depressed_img

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self._pressed:
            return
        self._sprite.image = self._hover_img if self._check_hit(x, y) else self._depressed_img


PushButton.register_event_type('on_press')
PushButton.register_event_type('on_release')


class ToggleButton(PushButton):

    def _get_release_image(self, x, y):
        return self._hover_img if self._check_hit(x, y) else self._depressed_img

    def on_mouse_press(self, x, y, buttons, modifiers):
        if not self._check_hit(x, y):
            return
        self._pressed = not self._pressed
        self._sprite.image = self._pressed_img if self._pressed else self._get_release_image(x, y)
        self.dispatch_event('on_toggle', self._pressed)

    def on_mouse_release(self, x, y, buttons, modifiers):
        if self._pressed:
            return
        self._sprite.image = self._get_release_image(x, y)


ToggleButton.register_event_type('on_toggle')


class Slider(WidgetBase):

    def __init__(self, x, y, base, knob, edge=0, batch=None, group=None):
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
        bg_group = OrderedGroup(0, parent=group)
        fg_group = OrderedGroup(1, parent=group)
        self._base_spr = pyglet.sprite.Sprite(self._base_img, x, y, batch=batch, group=bg_group)
        self._knob_spr = pyglet.sprite.Sprite(self._knob_img, x+edge, y+base.height/2, batch=batch, group=fg_group)

        self._value = 0
        self._in_update = False

    def update_groups(self, order):
        self._base_spr.group = OrderedGroup(order + 1, self._user_group)
        self._knob_spr.group = OrderedGroup(order + 2, self._user_group)

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
        if self._check_hit(x, y):
            self._in_update = True
            self._update_knob(x)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self._in_update:
            self._update_knob(x)

    def on_mouse_scroll(self, x, y, mouse, direction):
        if self._check_hit(x, y):
            self._update_knob(self._knob_spr.x + self._half_knob_width + direction)

    def on_mouse_release(self, x, y, buttons, modifiers):
        self._in_update = False


Slider.register_event_type('on_change')


class TextEntry(WidgetBase):

    def __init__(self, text, x, y, width, color=(255, 255, 255, 255), batch=None, group=None):
        self._doc = pyglet.text.document.UnformattedDocument(text)
        self._doc.set_style(0, len(self._doc.text), dict(color=(0, 0, 0, 255)))
        font = self._doc.get_font()
        height = font.ascent - font.descent

        self._user_group = group
        bg_group = OrderedGroup(0, parent=group)
        fg_group = OrderedGroup(1, parent=group)

        # Rectangular outline with 2-pixel pad:
        p = 2
        self._outline = pyglet.shapes.Rectangle(x-p, y-p, width+p+p, height+p+p, color[:3], batch, bg_group)
        self._outline.opacity = color[3]

        # Text and Caret:
        self._layout = IncrementalTextLayout(self._doc, width, height, multiline=False, batch=batch, group=fg_group)
        self._layout.x = x
        self._layout.y = y
        self._caret = Caret(self._layout)
        self._caret.visible = False

        self._focus = False

        super().__init__(x, y, width, height)

    def _check_hit(self, x, y):
        return self._x < x < self._x + self._width and self._y < y < self._y + self._height

    def _set_focus(self, value):
        self._focus = value
        self._caret.visible = value

    def update_groups(self, order):
        self._outline.group = OrderedGroup(order + 1, self._user_group)
        self._layout.group = OrderedGroup(order + 2, self._user_group)

    def on_mouse_motion(self, x, y, dx, dy):
        if not self._check_hit(x, y):
            self._set_focus(False)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self._focus:
            self._caret.on_mouse_drag(x, y, dx, dy, buttons, modifiers)

    def on_mouse_press(self, x, y, buttons, modifiers):
        if self._check_hit(x, y):
            self._set_focus(True)
            self._caret.on_mouse_press(x, y, buttons, modifiers)

    def on_text(self, text):
        if self._focus:
            if text in ('\r', '\n'):
                self.dispatch_event('on_commit', self._layout.document.text)
                self._set_focus(False)
                return
            self._caret.on_text(text)

    def on_text_motion(self, motion):
        if self._focus:
            self._caret.on_text_motion(motion)

    def on_text_motion_select(self, motion):
        if self._focus:
            self._caret.on_text_motion_select(motion)

    def on_commit(self, text):
        """Text has been commited via Enter/Return key."""


TextEntry.register_event_type('on_commit')
