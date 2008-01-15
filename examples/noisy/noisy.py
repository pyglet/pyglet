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

'''Bounces balls around a window and plays noises.

This is a simple demonstration of how pyglet efficiently manages many sound
channels without intervention.
'''

import os
import random
import sys

from pyglet.gl import *
from pyglet.window import Window
from pyglet.window import key
from pyglet import image
from pyglet import clock
from pyglet import media
from pyglet import font

PKG = os.path.dirname(__file__)
BALL_IMAGE = os.path.join(PKG, 'ball.png')
BALL_SOUND = os.path.join(PKG, 'ball.wav')

if len(sys.argv) > 1:
    BALL_SOUND = sys.argv[1]

window = Window(640, 480)
sound = media.load(BALL_SOUND, streaming=False)

class Ball(object):
    ball_image = image.load(BALL_IMAGE)
    width = ball_image.width
    height = ball_image.height
    def __init__(self):
        self.x = random.random() * (window.width - self.width)
        self.y = random.random() * (window.height - self.height)
        self.dx = (random.random() - 0.5) * 1000
        self.dy = (random.random() - 0.5) * 1000

    def update(self, dt):
        if self.x <= 0 or self.x + self.width >= window.width:
            self.dx *= -1
            sound.play()
        if self.y <= 0 or self.y + self.height >= window.height:
            self.dy *= -1
            sound.play()
        self.x += self.dx * dt
        self.y += self.dy * dt

        self.x = min(max(self.x, 0), window.width - self.width)
        self.y = min(max(self.y, 0), window.height - self.height)

    def draw(self):
        self.ball_image.blit(self.x, self.y, 0)

balls = []

@window.event
def on_key_press(symbol, modifiers):
    if symbol == key.SPACE:
        balls.append(Ball())
    elif symbol == key.BACKSPACE:
        if balls:
            del balls[-1]
    elif symbol == key.ESCAPE:
        window.has_exit = True

if __name__ == '__main__':
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    label = font.Text(font.load('Arial', 14), 
        'Press space to add a ball, backspace to remove.', 
        window.width / 2, 10, 
        halign=font.Text.CENTER)

    while not window.has_exit:
        window.dispatch_events()
        media.dispatch_events()
        dt = clock.tick()

        glClear(GL_COLOR_BUFFER_BIT)
        for ball in balls:
            ball.update(dt)
            ball.draw()
        label.draw()

        window.flip()
