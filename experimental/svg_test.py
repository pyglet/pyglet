#!/usr/bin/env python
# -*- coding: latin-1 -*-

"""
"""

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import math
import random
import re
import os.path
import pyglet
from pyglet.gl import *
import xml.dom
import xml.dom.minidom


class SmoothLineGroup(pyglet.graphics.Group):
    @staticmethod
    def set_state():
        glPushAttrib(GL_ENABLE_BIT)
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glHint(GL_LINE_SMOOTH_HINT, GL_DONT_CARE)

    @staticmethod
    def unset_state():
        glPopAttrib()


class Curve(object):
    PATH_RE = re.compile(r'([MLHVCSQTAZ])([^MLHVCSQTAZ]+)', re.IGNORECASE)
    INT = r'([+-]?\d+)'
    FLOAT = r'(?:[\s,]*)([+-]?\d+(?:\.\d+)?)'

    HANDLERS = {}

    def handle(self, rx, types, HANDLERS=HANDLERS):
        def register(function):
            HANDLERS[self] = (rx and re.compile(rx), function, types)
            return function

        return register

    def __init__(self, spec, batch):
        self.batch = batch

        self.start = None
        self.current = None
        self.min_x = self.min_y = self.max_x = self.max_y = None

        for cmd, value in self.PATH_RE.findall(spec):
            # print (cmd, value)
            if not cmd:
                continue
            rx, handler, types = self.HANDLERS[cmd.upper()]
            if rx is None:
                handler(self, cmd)
            else:
                v = []
                for fields in rx.findall(value):
                    v.append([types[i](e) for i, e in enumerate(fields)])
                handler(self, cmd, v)

    def _determine_rect(self, x, y):
        y = -y
        if self.min_x is None:
            self.min_x = self.max_x = x
            self.min_y = self.max_y = y
        else:
            if self.min_x > x:
                self.min_x = x
            elif self.max_x < x:
                self.max_x = x
            if self.min_y > y:
                self.min_y = y
            elif self.max_y < y:
                self.max_y = y

    @handle('M', FLOAT * 2, (float, float))
    def moveto(self, cmd, points):
        """Start a new sub-path at the given (x,y) coordinate. M (uppercase)
        indicates that absolute coordinates will follow; m (lowercase)
        indicates that relative coordinates will follow. If a relative moveto
        (m) appears as the first element of the path, then it is treated as a
        pair of absolute coordinates. If a moveto is followed by multiple pairs
        of coordinates, the subsequent pairs are treated as implicit lineto
        commands.

        Parameters are (x y)+
        """
        points = [list(map(float, point)) for point in points]
        # XXX handle relative
        # XXX confirm that we always reset start here
        self.start = self.current = points[0]
        if len(points) > 2:
            self.lineto({'m': 'l', 'M': 'L'}[cmd], points[1:])

    @handle('L', FLOAT * 2, (float, float))
    def lineto(self, cmd, points):
        """Draw a line from the current point to the given (x,y) coordinate
        which becomes the new current point. L (uppercase) indicates that
        absolute coordinates will follow; l (lowercase) indicates that relative
        coordinates will follow. A number of coordinates pairs may be specified
        to draw a polyline. At the end of the command, the new current point is
        set to the final set of coordinates provided.

        Parameters are (x y)+
        """
        l = []
        self._determine_rect(*self.current)
        for point in points:
            cx, cy = self.current
            x, y = list(map(float, point))
            l.extend([cx, -cy])
            l.extend([x, -y])
            self.current = (x, y)
            self._determine_rect(x, y)
        self.batch.add(len(l) // 2, GL_LINES, SmoothLineGroup(), ('v2f', l))

    @handle('H', FLOAT, (float,))
    def horizontal_lineto(self, cmd, xvals):
        """Draws a horizontal line from the current point (cpx, cpy) to (x,
        cpy). H (uppercase) indicates that absolute coordinates will follow; h
        (lowercase) indicates that relative coordinates will follow. Multiple x
        values can be provided (although usually this doesn't make sense). At
        the end of the command, the new current point becomes (x, cpy) for the
        final value of x.

        Parameters are x+
        """
        cx, cy = self.current
        self._determine_rect(*self.current)
        x = float(xvals[-1])
        self.batch.add(2, GL_LINES, None, ('v2f', (cx, -cy, x, -cy)))
        self.current = (x, cy)
        self._determine_rect(x, cy)

    @handle('V', FLOAT, (float,))
    def vertical_lineto(self, cmd, yvals):
        """Draws a vertical line from the current point (cpx, cpy) to (cpx, y).
        V (uppercase) indicates that absolute coordinates will follow; v
        (lowercase) indicates that relative coordinates will follow. Multiple y
        values can be provided (although usually this doesn't make sense). At
        the end of the command, the new current point becomes (cpx, y) for the
        final value of y.

        Parameters are y+
        """
        cx, cy = self.current
        self._determine_rect(*self.current)
        y = float(yvals[-1])
        self.batch.add(2, GL_LINES, None, ('v2f', [cx, -cy, cx, -y]))
        self.current = (cx, y)
        self._determine_rect(cx, y)

    @handle('Z', None, None)
    def closepath(self, cmd):
        """Close the current subpath by drawing a straight line from the
        current point to current subpath's initial point.
        """
        self.batch.add(2, GL_LINES, SmoothLineGroup(), ('v2f', self.current + tuple(self.start)))

    @handle('C', FLOAT * 6, (float,) * 6)
    def curveto(self, cmd, control_points):
        """Draws a cubic Bézier curve from the current point to (x,y) using
        (x1,y1) as the control point at the beginning of the curve and (x2,y2)
        as the control point at the end of the curve. C (uppercase) indicates
        that absolute coordinates will follow; c (lowercase) indicates that
        relative coordinates will follow. Multiple sets of coordinates may be
        specified to draw a polybézier. At the end of the command, the new
        current point becomes the final (x,y) coordinate pair used in the
        polybézier.

        Control points are (x1 y1 x2 y2 x y)+
        """
        l = []
        last = None
        for entry in control_points:
            x1, y1, x2, y2, x, y = list(map(float, entry))
            t = 0
            cx, cy = self.current
            self.last_control = (x2, y2)
            self.current = (x, y)
            x1 *= 3
            x2 *= 3
            y1 *= 3
            y2 *= 3
            while t <= 1.01:
                a = t
                a2 = a ** 2
                a3 = a ** 3
                b = 1 - t
                b2 = b ** 2
                b3 = b ** 3
                px = cx * b3 + x1 * b2 * a + x2 * b * a2 + x * a3
                py = cy * b3 + y1 * b2 * a + y2 * b * a2 + y * a3
                if last is not None:
                    l.extend(last)
                    l.extend((px, -py))
                last = (px, -py)
                self._determine_rect(px, py)
                t += 0.01
        self.batch.add(len(l) // 2, GL_LINES, SmoothLineGroup(), ('v2f', l))

    @handle('S', FLOAT * 4, (float,) * 4)
    def smooth_curveto(self, cmd, control_points):
        """Draws a cubic Bézier curve from the current point to (x,y). The
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
        """
        assert self.last_control is not None, 'S must follow S or C'

        l = []
        last = None
        for entry in control_points:
            x2, y2, x, y = list(map(float, entry))

            # Reflect last control point
            cx, cy = self.current
            lcx, lcy = self.last_control
            dx, dy = cx - lcx, cy - lcy
            x1, y1 = cx + dx, cy + dy

            t = 0
            cx, cy = self.current
            self.last_control = (x2, y2)
            self.current = (x, y)

            x1 *= 3
            x2 *= 3
            y1 *= 3
            y2 *= 3
            while t <= 1.01:
                a = t
                a2 = a ** 2
                a3 = a ** 3
                b = 1 - t
                b2 = b ** 2
                b3 = b ** 3
                px = cx * b3 + x1 * b2 * a + x2 * b * a2 + x * a3
                py = cy * b3 + y1 * b2 * a + y2 * b * a2 + y * a3
                if last is not None:
                    l.extend(last)
                    l.extend((px, -py))
                last = (px, -py)
                self._determine_rect(px, py)
                t += 0.01
        # degenerate vertices
        self.batch.add(len(l) // 2, GL_LINES, SmoothLineGroup(), ('v2f', l))

    @handle('Q', FLOAT * 4, (float,) * 4)
    def quadratic_curveto(self, cmd, control_points):
        """Draws a quadratic Bézier curve from the current point to (x,y)
        using (x1,y1) as the control point. Q (uppercase) indicates that
        absolute coordinates will follow; q (lowercase) indicates that
        relative coordinates will follow. Multiple sets of coordinates may
        be specified to draw a polybézier. At the end of the command, the
        new current point becomes the final (x,y) coordinate pair used in
        the polybézier.

        Control points are (x1 y1 x y)+
        """
        raise NotImplementedError('not implemented')

    @handle('T', FLOAT * 2, (float,) * 2)
    def smooth_quadratic_curveto(self, cmd, control_points):
        """Draws a quadratic Bézier curve from the current point to (x,y).
        The control point is assumed to be the reflection of the control
        point on the previous command relative to the current point. (If
        there is no previous command or if the previous command was not a
        Q, q, T or t, assume the control point is coincident with the
        current point.) T (uppercase) indicates that absolute coordinates
        will follow; t (lowercase) indicates that relative coordinates will
        follow. At the end of the command, the new current point becomes
        the final (x,y) coordinate pair used in the polybézier.

        Control points are (x y)+
        """
        raise NotImplementedError('not implemented')

    @handle('A', FLOAT * 3 + INT * 2 + FLOAT * 2, (float,) * 3 + (int,) * 2 + (float,) * 2)
    def elliptical_arc(self, cmd, parameters):
        """Draws an elliptical arc from the current point to (x, y). The
        size and orientation of the ellipse are defined by two radii (rx,
        ry) and an x-axis-rotation, which indicates how the ellipse as a
        whole is rotated relative to the current coordinate system. The
        center (cx, cy) of the ellipse is calculated automatically to
        satisfy the constraints imposed by the other parameters.
        large-arc-flag and sweep-flag contribute to the automatic
        calculations and help determine how the arc is drawn.

        Parameters are (rx ry x-axis-rotation large-arc-flag sweep-flag x y)+
        """
        raise NotImplementedError('not implemented')


class SVG(object):
    def __init__(self, filename, rect=None):
        self._rect = rect
        self.scale_x = None
        self.scale_y = None
        self.translate_x = None
        self.translate_y = None
        dom = xml.dom.minidom.parse(filename)
        tag = dom.documentElement
        if tag.tagName != 'svg':
            raise ValueError('document is <%s> instead of <svg>' % tag.tagName)

        # generate all the drawing elements
        self.batch = pyglet.graphics.Batch()
        self.objects = []
        for tag in tag.getElementsByTagName('g'):
            for tag in tag.getElementsByTagName('path'):
                self.objects.append(Curve(tag.getAttribute('d'), self.batch))

        # determine drawing bounds
        self.min_x = min(o.min_x for o in self.objects)
        self.max_x = max(o.max_x for o in self.objects)
        self.min_y = min(o.min_y for o in self.objects)
        self.max_y = max(o.max_y for o in self.objects)

        # determine or apply drawing rect
        if rect is None:
            self._rect = (self.min_x, self.min_y,
                          self.max_x - self.min_x,
                          self.max_y - self.min_y)

    @property
    def rect(self):
        return self._rect

    @rect.setter
    def rect(self, new_rect):
        self._rect = new_rect
        # figure transform for display rect
        self.translate_x, self.translate_y, rw, rh = new_rect
        self.scale_x = abs(rw / float(self.max_x - self.min_x))
        self.scale_y = abs(rh / float(self.max_y - self.min_y))

    def draw(self):
        glPushMatrix()
        if self._rect is not None:
            glScalef(self.scale_x, self.scale_y, 1)
            glTranslatef(self.translate_x - self.min_x, self.translate_x - self.min_y, 0)
        self.batch.draw()
        glPopMatrix()


window = pyglet.window.Window(width=600, height=300, resizable=True)

dirname = os.path.dirname(__file__)
svg = SVG(os.path.join(dirname, 'hello_world.svg'), rect=(0, 0, 600, 300))


@window.event
def on_draw():
    window.clear()
    svg.draw()


@window.event
def on_resize(w, h):
    print("Resized")
    svg.rect = svg.rect[:2] + (w, h)


pyglet.app.run()
