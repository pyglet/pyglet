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
from pyglet.gl import *

joysticks = pyglet.input.get_joysticks()
assert joysticks, 'No joystick device is connected'
joystick = joysticks[0]
joystick.open()

window = pyglet.window.Window(width=800, height=800)
batch = pyglet.graphics.Batch()

# Labels
pyglet.text.Label("Buttons:", x=15, y=window.height - 25, font_size=14, batch=batch)
pyglet.text.Label("D Pad:", x=window.width - 125, y=window.height - 25, font_size=14, batch=batch)


button_labels = []
button_shapes = []

for i in range(len(joystick.buttons)):
    rows = len(joystick.buttons) // 2
    y = window.height - 50 - 25 * (i % rows)
    x = 35 + 60 * (i // rows)
    label = pyglet.text.Label(f"{i}:", x=x, y=y, font_size=14, anchor_x='right', batch=batch)
    button_labels.append(label)
    shape = pyglet.shapes.Rectangle(x + 10, y + 1, 10, 10, color=(255, 0, 0), batch=batch)
    button_shapes.append(shape)


joystick_rect = pyglet.shapes.Rectangle(window.width // 2, window.height // 2, 10, 10, color=(255, 0, 255), batch=batch)
joystick_rect.anchor_position = joystick_rect.width // 2, joystick_rect.height // 2
d_pad_rect = pyglet.shapes.Rectangle(window.width - 75, window.height - 100, 10, 10, color=(0, 0, 255), batch=batch)


@window.event
def on_draw():
    window.clear()
    batch.draw()
    x = round((.5 * joystick.x + 1), 2) * window.width / 2
    y = round((-.5 * joystick.y + 1), 2) * window.height / 2
    rx = (.5 * joystick.rx + 1) * 60
    ry = (-.5 * joystick.ry + 1) * 60
    z = joystick.z * 50

    # Axes
    joystick_rect.position = x, y
    joystick_rect.anchor_position = joystick_rect.width // 2, joystick_rect.height // 2
    joystick_rect.width = 10 + rx + z
    joystick_rect.height = 10 + ry + z

    # Buttons
    for i in range(len(joystick.buttons)):
        rect = button_shapes[i]
        rect.color = (0, 255, 0) if joystick.buttons[i] else (255, 0, 0)

    # Hat
    d_pad_x = window.width - 100 + joystick.hat_x * 50
    d_pad_y = window.height - 100 + joystick.hat_y * 50
    d_pad_rect.position = d_pad_x, d_pad_y


pyglet.app.run()
