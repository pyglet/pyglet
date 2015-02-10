#!/usr/bin/python
# $Id:$

from pyglet.gl import *

def draw_client_border(window):
    glClearColor(0, 0, 0, 1)
    glClear(GL_COLOR_BUFFER_BIT)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, window.width, 0, window.height, -1, 1)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    def rect(x1, y1, x2, y2):
        glBegin(GL_LINE_LOOP)
        glVertex2f(x1, y1)
        glVertex2f(x2, y1)
        glVertex2f(x2, y2)
        glVertex2f(x1, y2)
        glEnd()
    
    glColor3f(1, 0, 0)
    rect(-2, -2, window.width + 2, window.height + 2)

    glColor3f(0, 1, 0)
    rect(1, 1, window.width - 2, window.height - 2)
