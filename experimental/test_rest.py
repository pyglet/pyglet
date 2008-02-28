#!/usr/bin/python
# $Id:$

text='''
A treatise on things
====================

This is some *emphasised* and **strong** text.  Here is a ``string literal``.

Another paragraph is here.

Here is a code block::
    
    def fib(n):
        if n == 0:
            return 0
        return n + fib(n - 1)

Section 2
=========

This para belongs to section 2.
'''

import pyglet
import rest

document = rest.DocutilsDecoder().decode(text)

window = pyglet.window.Window(resizable=True)
label = pyglet.text.DocumentLabel(document, 
                                  valign='top',
                                  multiline=True)

@window.event
def on_resize(width, height):
    label.y = height
    label.width = width

@window.event
def on_draw():
    window.clear()
    label.draw()

pyglet.gl.glClearColor(1, 1, 1, 1)
pyglet.app.run()
