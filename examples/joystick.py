#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import pyglet
from pyglet.gl import *

window = pyglet.window.Window()

joystick = pyglet.input.get_joysticks()[0]
joystick.device.open()

@window.event
def on_draw():
    x = (joystick.x + 1) * window.width / 2
    y = (-joystick.y + 1) * window.height / 2
    z = joystick.z
    angle = joystick.rz * 180

    glClear(GL_COLOR_BUFFER_BIT)
    glColor3f(1, 0, 0)
    glLoadIdentity()
    glTranslatef(x, y, 0)
    glScalef(1 + z, 1 + z, 1 + z)
    glRotatef(-angle, 0, 0, 1)
    glBegin(GL_TRIANGLES)
    glVertex2f(-10, 0)
    glVertex2f(0, 13)
    glVertex2f(10, 0)
    glEnd()

    glLoadIdentity()
    x = 10
    y = 10
    glPointSize(5)
    glBegin(GL_POINTS)
    for button in joystick.buttons:
        if button:
            glVertex2f(x, y)
        x += 20
    glEnd()

pyglet.clock.schedule(lambda dt: None)

pyglet.app.run()
