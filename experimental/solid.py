#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from math import *
from ctypes import *

from pyglet.gl import *
from euclid import *

def FloatArray(*args):
    t = (c_float * len(args))
    return t(*args)

def IndexArray(*args):
    t = (c_uint * len(args))
    return t(*args)

class Polyhedron(object):
    vertices = None
    indices = None
    mode = GL_TRIANGLES

    def draw(self):
        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, self.vertices)
        glNormalPointer(GL_FLOAT, 0, self.vertices)
        glDrawElements(self.mode, len(self.indices), GL_UNSIGNED_INT,
            self.indices)
        glPopClientAttrib()

class Tetrahedron(Polyhedron):
    a = .5 * sqrt(.5)
    vertices = FloatArray(
                -a, a, a,
                a, -a, a,
                a, a, -a,
                -a, -a, -a)
    indices = IndexArray(
                0, 1, 2,
                0, 2, 3,
                0, 3, 1,
                3, 2, 1)

class Cube(Polyhedron):
    a = .5
    mode = GL_QUADS
    vertices = FloatArray(
                -a, -a, -a,
                -a, -a,  a,
                -a,  a, -a,
                -a,  a,  a,
                 a, -a, -a,
                 a, -a,  a,
                 a,  a, -a,
                 a,  a,  a)
    indices = IndexArray(
                0, 1, 3, 2,
                4, 5, 1, 0, #ok
                0, 2, 6, 4,
                6, 7, 5, 4,
                2, 3, 7, 6, #ok
                5, 7, 3, 1)

if __name__ == '__main__':

    def rand(min, max):
        return (random() * (max - min) + min)

    from random import *
    from pyglet import clock
    from pyglet.window import *
    from pyglet.window.event import *

    w = Window()
    @w.event
    def on_resize(width, height):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(65, width/float(height), 1, 100)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    glEnable(GL_NORMALIZE)
    glEnable(GL_COLOR_MATERIAL)
    glEnable(GL_CULL_FACE)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_LIGHT1)
    glLightfv(GL_LIGHT0, GL_POSITION, FloatArray(0, 1, 2, 0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, FloatArray(1, 1, .5, 1))
    glLightfv(GL_LIGHT1, GL_POSITION, FloatArray(1, -2, 0, 0))
    glLightfv(GL_LIGHT1, GL_DIFFUSE, FloatArray(.5, 1, 1, 1))

    shapes = []

    while not w.has_exit:
        dt = clock.tick()
        if len(shapes) < 100:
            shape = choice([Cube, Tetrahedron])()
            shape.y = -8 
            shape.dy = rand(1,10)
            shape.x = rand(-2, 2)
            shape.z = rand(0, -5)
            shape.yrot = 0
            shape.dyrot = rand(0, 100) 
            shape.xrot = 0
            shape.dxrot = rand(0, 100) 
            shape.scale = rand(.5, 1) 
            shape.color = (rand(.5, 1), rand(.5, 1), rand(.5, 1))
            shapes.append(shape)

        w.dispatch_events()
        glClearColor(.8, .8, 1 ,1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        #glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glLoadIdentity()
        glTranslatef(0, 0, -5)

        for shape in shapes:
            shape.yrot += shape.dyrot * dt 
            shape.xrot += shape.dxrot * dt 
            shape.y += shape.dy * dt

            glPushMatrix()
            glColor3f(*shape.color)
            glTranslatef(shape.x, shape.y, shape.z)
            glRotatef(shape.yrot, 0, 1, 0)
            glRotatef(shape.xrot, 1, 0, 0)
            glScalef(shape.scale, shape.scale, shape.scale)
            shape.draw()
            glPopMatrix()
        shapes = [s for s in shapes if s.y < 8]
        w.flip()

