#!/usr/bin/env python
"""Demonstrates how to manage two independent windows.
"""

import pyglet


w1 = pyglet.window.Window(200, 200, caption='First window', resizable=True)
w1.switch_to()
s1 = pyglet.shapes.Rectangle(100, 100, 100, 100, color=(50, 50, 200))
s1.anchor_position = 50, 50


@w1.event
def on_draw():
    w1.clear()
    s1.rotation -= 0.5
    s1.draw()


w2 = pyglet.window.Window(300, 300, caption='Second window', resizable=True)
w2.switch_to()
s2 = pyglet.shapes.Rectangle(150, 150, 150, 150, color=(50, 200, 50))
s2.anchor_position = 75, 75


@w2.event
def on_draw():
    w2.clear()
    s2.rotation += 0.5
    s2.draw()


pyglet.app.run()
