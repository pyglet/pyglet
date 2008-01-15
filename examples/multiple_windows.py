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

'''Demonstrates how to manage OpenGL calls between two independent windows.
'''

from pyglet.gl import *
from pyglet import window
from pyglet import clock

def on_resize(width, height):
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60., width / float(height), 1., 100.)
    glMatrixMode(GL_MODELVIEW)

def setup():
    glClearColor(1, 1, 1, 1)
    glColor3f(.5, .5, .5)

def draw():
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()
    glTranslatef(0, 0, -5)
    glRotatef(r, 0, 0, 1)
    glRectf(-1, -1, 1, 1)

w1 = window.Window(200, 200, caption='First window', resizable=True)
w1.on_resize = on_resize
w1.switch_to()
setup()

w2 = window.Window(300, 300, caption='Second window', resizable=True)
w2.on_resize = on_resize
w2.switch_to()
setup()

r = 0
clock.set_fps_limit(30)
while not (w1.has_exit or w2.has_exit):
    dt = clock.tick()
    r += 1
    if r > 360: r = 0

    w1.switch_to()
    w1.dispatch_events()
    draw()
    w1.flip()

    w2.switch_to()
    w2.dispatch_events()
    draw()
    w2.flip()
