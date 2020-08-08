
#!/usr/bin/env python
# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
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
'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import pyglet
from pyglet.gl import *

joysticks = pyglet.input.get_joysticks()
assert joysticks, 'No joystick device is connected'
joystick = joysticks[0]
joystick.open()

window = pyglet.window.Window()
main_batch = pyglet.graphics.Batch()

#Labels

pyglet.text.Label("Buttons:", x = 10, y = window.height - 25,
                  font_size = 14, batch = main_batch)
pyglet.text.Label("D Pad:", x = window.width - 125, y = window.height - 25,
                  font_size = 14, batch = main_batch)
y = window.height - 25
for i in range(len(joystick.buttons)):
    y-= 25
    pyglet.text.Label(f"{i}:", x = 10, y = y,font_size = 14, batch = main_batch)

@window.event
def on_draw():
    window.clear()
    main_batch.draw()
    x = round((.5*joystick.x + 1),2) * window.width / 2
    y = round((-.5*joystick.y + 1),2) * window.height / 2
    rx = (.5*joystick.rx + 1) * 20 
    ry = (-.5*joystick.ry + 1) * 20
    z = joystick.z *10 
    

    # Axes
    joystick_rect = pyglet.shapes.Rectangle(x, y, 10+rx+z, 10+ry+z)
    joystick_rect.anchor_x = joystick_rect.width//2
    joystick_rect.anchor_y = joystick_rect.height//2
    joystick_rect.draw()
    

    # Buttons
    
    x = 10
    y = window.height - 25
    for i in range(len(joystick.buttons)):
        y-= 25
        rect = pyglet.shapes.Rectangle(x + 20, y + 2, 10, 10, color = (255,0,0))
        if joystick.buttons[i]:
            rect.color = (0,255,0)
        rect.draw()

    # Hat

    x = window.width-75
    y = window.height- 100
    d_pad_rect = pyglet.shapes.Rectangle(x + joystick.hat_x * 50, y + joystick.hat_y * 50, 10, 10)
    d_pad_rect.color = (0,0,255)
    d_pad_rect.draw()

pyglet.clock.schedule(lambda dt: None)
pyglet.app.run()
