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

"""
This example shows the KeyStateHandler polling approach when it comes to catching keyboard events.
"""

import pyglet

window = pyglet.window.Window()

key_handler = pyglet.window.key.KeyStateHandler()
window.push_handlers(key_handler)


def update(dt):

    if key_handler[pyglet.window.key.A]:
        print('The "A" key was pressed')
    elif key_handler[pyglet.window.key.LEFT]:
        print('The left arrow key was pressed.')
    elif key_handler[pyglet.window.key.ENTER]:
        print('The enter key was pressed.')


@window.event
def on_draw():
    window.clear()


pyglet.clock.schedule_interval(update, 1/60)


if __name__ == '__main__':
    pyglet.app.run()
