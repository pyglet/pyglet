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


class WidgetBase(pyglet.event.EventDispatcher):

    def __init__(self, x, y, width, height, parent=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self.parent = parent
    
    @property
    def position(self):
        return self.x, self.y

    @position.setter
    def position(self, position):
        self.x, self.y = position

    @property
    def aabb(self):
        return self.x, self.y, self.x + self.width, self.y + self.height
    
    @property
    def real_x(self):
        if self.parent is not None:
            return self.x + self.parent.x
        else:
            return self.x

    @property 
    def real_y(self):
        if self.parent is not None:
            return self.y + self.parent.y
        else:
            return self.y
    
    @property
    def real_position(self):
        return self.real_x, self.real_y

    def _check_hit(self, x, y):
        return self.real_x < x < self.real_x + self.width and self.real_y < y < self.real_y + self.height

    def on_mouse_press(self, x, y, buttons, modifiers):
        pass

    def on_mouse_release(self, x, y, buttons, modifiers):
        pass

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        pass

    def on_mouse_scroll(self, x, y, mouse, direction):
        pass


WidgetBase.register_event_type('on_mouse_press')
WidgetBase.register_event_type('on_mouse_release')
WidgetBase.register_event_type('on_mouse_motion')
WidgetBase.register_event_type('on_mouse_scroll')
WidgetBase.register_event_type('on_mouse_drag')


class PushButton(WidgetBase):

    def __init__(self, x, y, pressed, depressed, hover=None, batch=None, group=None, parent=None):
        super().__init__(x, y, depressed.width, depressed.height, parent)
        self._pressed_img = pressed
        self._depressed_img = depressed
        self._hover_img = hover
        self._sprite = pyglet.sprite.Sprite(
            self._depressed_img, 
            self.real_x, self.real_y, 
            batch=batch, group=group
        )
        self._pressed = False

    def on_mouse_press(self, x, y, buttons, modifiers):
        if not self._check_hit(x, y):
            return
        self._sprite.image = self._pressed_img
        self._pressed = True
        self.dispatch_event('on_press')

    def on_mouse_release(self, x, y, buttons, modifiers):
        if not self._pressed:
            return
        self._sprite.image = self._depressed_img
        self._pressed = False
        self.dispatch_event('on_release')

    def on_mouse_motion(self, x, y, dx, dy):
        if self._pressed:
            return
        if self._check_hit(x, y) and self._hover_img:
            self._sprite.image = self._hover_img
        else:
            self._sprite.image = self._depressed_img


PushButton.register_event_type('on_press')
PushButton.register_event_type('on_release')


class ToggleButton(PushButton):

    def on_mouse_press(self, x, y, buttons, modifiers):
        if not self._check_hit(x, y):
            return
        self._sprite.image = self._depressed_img if self._pressed else self._pressed_img
        self._pressed = not self._pressed
        self.dispatch_event('on_toggle', self._pressed)

    def on_mouse_release(self, x, y, buttons, modifiers):
        return


ToggleButton.register_event_type('on_toggle')


class Slider(WidgetBase):

    def __init__(self, x, y, base, knob, batch=None, group=None, parent=None):
        super().__init__(x, y, base.width, knob.height, parent)
        self._base_img = base
        self._knob_img = knob
        self._half_knob_width = knob.width / 2
        self._half_knob_height = knob.height / 2
        self._knob_img.anchor_y = knob.height / 2

        bg_group = pyglet.graphics.OrderedGroup(0, parent=group)
        fg_group = pyglet.graphics.OrderedGroup(1, parent=group)
        self._base_spr = pyglet.sprite.Sprite(
            self._base_img, 
            self.real_x, self.real_y, 
            batch=batch, group=bg_group
        )
        self._knob_spr = pyglet.sprite.Sprite(
            self._knob_img, 
            self.real_x, self.real_y + base.height / 2, 
            batch=batch, group=fg_group
        )

        self._value = 0
        self._in_update = False
    
    @property
    def _max_knob_x(self):
        return self.real_x + self.width - self._knob_img.width

    @property
    def _min_y(self):
        return self.real_y - self._half_knob_height

    @property
    def _max_y(self):
        return self.real_y + self._half_knob_height + self.height / 2

    def _check_hit(self, x, y):
        return self.real_x < x < self.real_x + self.width and self._min_y < y < self._max_y

    def _update_knob(self, x):
        self._knob_spr.x = max(self.real_x, min(x - self._half_knob_width, self._max_knob_x))
        self._value = abs(((self._knob_spr.x - self.real_x) * 100) / (self.real_x - self._max_knob_x))
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
