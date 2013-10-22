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

'''A simple tool that may be used to compare font faces.

Use the left/right cursor keys to change font faces.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'
import pyglet

FONTS = ['Andale Mono', 'Consolas', 'Inconsolata', 'Inconsolata-dz', 'Monaco',
    'Menlo']

SAMPLE = '''class Spam(object):
	def __init__(self):
		# The quick brown fox
		self.spam = {"jumped": 'over'}
    @the
	def lazy(self, *dog):
		self.dog = [lazy, lazy]'''

class Window(pyglet.window.Window):
    font_num = 0
    def on_text_motion(self, motion):
        if motion == pyglet.window.key.MOTION_RIGHT:
            self.font_num += 1
            if self.font_num == len(FONTS):
                self.font_num = 0
        elif motion == pyglet.window.key.MOTION_LEFT:
            self.font_num -= 1
            if self.font_num < 0:
                self.font_num = len(FONTS) - 1

        face = FONTS[self.font_num]
        self.head = pyglet.text.Label(face, font_size=24, y=0,
            anchor_y='bottom')
        self.text = pyglet.text.Label(SAMPLE, font_name=face, font_size=18,
            y=self.height, anchor_y='top', width=self.width, multiline=True)

    def on_draw(self):
        self.clear()
        self.head.draw()
        self.text.draw()

window = Window()
window.on_text_motion(None)
pyglet.app.run()
