#!/usr/bin/env python
# -*- coding: latin-1 -*-

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import math
import random
import re
import os.path
from pyglet.window import Window
from pyglet import clock
from pyglet.window.event import *
from pyglet.gl import *
import xml.dom
import xml.dom.minidom

# sample from http://www.w3.org/TR/SVG/paths.html#PathDataCubicBezierCommands
sample = 'M100,200 C100,100 250,100 250,200 S400,300 400,200'

class Curve:
    PATH_RE = re.compile(r'([MLHVCSQTAZ])([^MLHVCSQTAZ]+)', re.IGNORECASE)
    INT = r'([+-]?\d+)'
    FLOAT = r'(?:[\s,]*)([+-]?\d+(?:\.\d+)?)'

    HANDLERS = {}
    def handle(char, rx, types, HANDLERS=HANDLERS):
        def register(function):
            HANDLERS[char] = (rx and re.compile(rx), function, types)
            return function
        return register

    def __init__(self, spec):
        self.start = None
        self.current = None

        self.gl_list = glGenLists(1)
        glNewList(self.gl_list, GL_COMPILE)

        for cmd, value in self.PATH_RE.findall(spec):
#            print (cmd, value)
            if not cmd: continue
            rx, handler, types = self.HANDLERS[cmd.upper()]
            if rx is None:
                handler(self, cmd)
            else:
                v = []
                for fields in rx.findall(value):
                    v.append([types[i](e) for i, e in enumerate(fields)])
                handler(self, cmd, v)
        glEndList()

    def draw(self):
        glCallList(self.gl_list)

    @handle('M', FLOAT*2, (float, float))
    def moveto(self, cmd, points):
        '''Start a new sub-path at the given (x,y) coordinate. M (uppercase)
        indicates that absolute coordinates will follow; m (lowercase)
        indicates that relative coordinates will follow. If a relative moveto
        (m) appears as the first element of the path, then it is treated as a
        pair of absolute coordinates. If a moveto is followed by multiple pairs
        of coordinates, the subsequent pairs are treated as implicit lineto
        commands.

        Parameters are (x y)+
        '''
        points = [map(float, point) for point in points]
        # XXX handle relative
        # XXX confirm that we always reset start here
        self.start = self.current = points[0]
        if len(points) > 2:
            self.lineto({'m': 'l', 'M': 'L'}[cmd], points[1:])


    @handle('L', FLOAT*2, (float, float))
    def lineto(self, cmd, points):
        '''Draw a line from the current point to the given (x,y) coordinate
        which becomes the new current point. L (uppercase) indicates that
        absolute coordinates will follow; l (lowercase) indicates that relative
        coordinates will follow. A number of coordinates pairs may be specified
        to draw a polyline. At the end of the command, the new current point is
        set to the final set of coordinates provided.

        Parameters are (x y)+
        '''
        glBegin(GL_LINE_STRIP)
        for point in points:
            cx, cy = self.current
            x, y = map(float, point)
            glVertex2f(cx, cy)
            glVertex2f(x, y)
            self.current = (x, y)
        glEnd()


    @handle('H', FLOAT, (float,))
    def horizontal_lineto(self, cmd, xvals):
        '''Draws a horizontal line from the current point (cpx, cpy) to (x,
        cpy). H (uppercase) indicates that absolute coordinates will follow; h
        (lowercase) indicates that relative coordinates will follow. Multiple x
        values can be provided (although usually this doesn't make sense). At
        the end of the command, the new current point becomes (x, cpy) for the
        final value of x.

        Parameters are x+
        '''
        glBegin(GL_LINE_STRIP)
        cx, cy = self.current
        x = float(xvals[-1])
        glVertex2f(cx, cy)
        glVertex2f(x, cy)
        self.current = (x, cy)
        glEnd()


    @handle('V', FLOAT, (float,))
    def vertical_lineto(self, cmd, yvals):
        '''Draws a vertical line from the current point (cpx, cpy) to (cpx, y).
        V (uppercase) indicates that absolute coordinates will follow; v
        (lowercase) indicates that relative coordinates will follow. Multiple y
        values can be provided (although usually this doesn't make sense). At
        the end of the command, the new current point becomes (cpx, y) for the
        final value of y.

        Parameters are y+
        '''
        glBegin(GL_LINE_STRIP)
        cx, cy = self.current
        y = float(yvals[-1])
        glVertex2f(cx, cy)
        glVertex2f(cx, y)
        self.current = (cx, y)
        glEnd()


    @handle('Z', None, None)
    def closepath(self, cmd):
        '''Close the current subpath by drawing a straight line from the
        current point to current subpath's initial point.
        '''
        glBegin(GL_LINE_STRIP)
        glVertex2f(*self.current)
        glVertex2f(*self.start)
        glEnd()


    @handle('C', FLOAT*6, (float, )*6)
    def curveto(self, cmd, control_points):
        '''Draws a cubic Bézier curve from the current point to (x,y) using
        (x1,y1) as the control point at the beginning of the curve and (x2,y2)
        as the control point at the end of the curve. C (uppercase) indicates
        that absolute coordinates will follow; c (lowercase) indicates that
        relative coordinates will follow. Multiple sets of coordinates may be
        specified to draw a polybézier. At the end of the command, the new
        current point becomes the final (x,y) coordinate pair used in the
        polybézier.

        Control points are (x1 y1 x2 y2 x y)+
        '''
        glBegin(GL_LINE_STRIP)
        for entry in control_points:
            x1, y1, x2, y2, x, y = map(float, entry)
            t = 0
            cx, cy = self.current
            self.last_control = (x2, y2)
            self.current = (x, y)
            x1 *= 3; x2 *= 3
            y1 *= 3; y2 *= 3
            while t <= 1.01:
                a = t; a2 = a**2; a3 = a**3
                b = 1 - t; b2 = b**2; b3 = b**3
                px = cx*b3 + x1*b2*a + x2*b*a2 + x*a3
                py = cy*b3 + y1*b2*a + y2*b*a2 + y*a3
                glVertex2f(px, py)
                t += 0.01
        glEnd()


    @handle('S', FLOAT*4, (float, )*4)
    def smooth_curveto(self, cmd, control_points):
        '''Draws a cubic Bézier curve from the current point to (x,y). The
        first control point is assumed to be the reflection of the second
        control point on the previous command relative to the current point.
        (If there is no previous command or if the previous command was not an
        C, c, S or s, assume the first control point is coincident with the
        current point.) (x2,y2) is the second control point (i.e., the control
        point at the end of the curve). S (uppercase) indicates that absolute
        coordinates will follow; s (lowercase) indicates that relative
        coordinates will follow. Multiple sets of coordinates may be specified
        to draw a polybézier. At the end of the command, the new current point
        becomes the final (x,y) coordinate pair used in the polybézier.

        Control points are (x2 y2 x y)+
        '''
        assert self.last_control is not None, 'S must follow S or C'

        glBegin(GL_LINE_STRIP)
        for entry in control_points:
            x2, y2, x, y = map(float, entry)

            # Reflect last control point
            cx, cy = self.current; lcx, lcy = self.last_control
            dx, dy = cx - lcx, cy - lcy
            x1, y1 = cx + dx, cy + dy

            t = 0
            cx, cy = self.current
            self.last_control = (x2, y2)
            self.current = (x, y)

            x1 *= 3; x2 *= 3
            y1 *= 3; y2 *= 3
            while t <= 1.01:
                a = t; a2 = a**2; a3 = a**3
                b = 1 - t; b2 = b**2; b3 = b**3
                px = cx*b3 + x1*b2*a + x2*b*a2 + x*a3
                py = cy*b3 + y1*b2*a + y2*b*a2 + y*a3
                glVertex2f(px, py)
                t += 0.01
        glEnd()


    @handle('Q', FLOAT*4, (float, )*4)
    def quadratic_curveto(self, cmd, control_points):
        '''Draws a quadratic Bézier curve from the current point to (x,y)
        using (x1,y1) as the control point. Q (uppercase) indicates that
        absolute coordinates will follow; q (lowercase) indicates that
        relative coordinates will follow. Multiple sets of coordinates may
        be specified to draw a polybézier. At the end of the command, the
        new current point becomes the final (x,y) coordinate pair used in
        the polybézier.

        Control points are (x1 y1 x y)+
        '''
        raise NotImplementedError('not implemented')


    @handle('T', FLOAT*2, (float, )*2)
    def smooth_quadratic_curveto(self, cmd, control_points):
        '''Draws a quadratic Bézier curve from the current point to (x,y).
        The control point is assumed to be the reflection of the control
        point on the previous command relative to the current point. (If
        there is no previous command or if the previous command was not a
        Q, q, T or t, assume the control point is coincident with the
        current point.) T (uppercase) indicates that absolute coordinates
        will follow; t (lowercase) indicates that relative coordinates will
        follow. At the end of the command, the new current point becomes
        the final (x,y) coordinate pair used in the polybézier.

        Control points are (x y)+
        '''
        raise NotImplementedError('not implemented')


    @handle('A', FLOAT*3 + INT*2 + FLOAT*2, (float,)*3 + (int,)*2 + (float,)*2)
    def elliptical_arc(self, cmd, parameters):
        '''Draws an elliptical arc from the current point to (x, y). The
        size and orientation of the ellipse are defined by two radii (rx,
        ry) and an x-axis-rotation, which indicates how the ellipse as a
        whole is rotated relative to the current coordinate system. The
        center (cx, cy) of the ellipse is calculated automatically to
        satisfy the constraints imposed by the other parameters.
        large-arc-flag and sweep-flag contribute to the automatic
        calculations and help determine how the arc is drawn.

        Parameters are (rx ry x-axis-rotation large-arc-flag sweep-flag x y)+
        '''
        raise NotImplementedError('not implemented')


class SVG:
    def __init__(self, filename):
        dom = xml.dom.minidom.parse(filename)
        tag = dom.documentElement
        if tag.tagName != 'svg':
            raise ValueError('document is <%s> instead of <svg>'%tag.tagName)

        self.objects = []
        for tag in tag.getElementsByTagName('g'):
            for tag in tag.getElementsByTagName('path'):
                self.objects.append(Curve(tag.getAttribute('d')))

    def draw(self):
        glPushMatrix()
        glTranslatef(0, 1024, 0)
        glScalef(1, -1, 1)
        for object in self.objects:
            object.draw()
        glPopMatrix()

w = Window(width=1024, height=768)

# XXX move this into display list
glEnable(GL_LINE_SMOOTH)
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
glHint(GL_LINE_SMOOTH_HINT, GL_DONT_CARE)

dirname = os.path.dirname(__file__)
svg = SVG(os.path.join(dirname, 'hello_world.svg'))

clock.set_fps_limit(10)
while not w.has_exit:
    clock.tick()
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    w.dispatch_events()
    svg.draw()
    w.flip()

