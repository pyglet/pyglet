#!/usr/bin/python
# $Id:$

'''OpenGL viewports and projections.

This is a simplified interface for setting up projections, and viewports
within projections.

A `Viewport` is a rectangular area in space that can be rendered into.  Most
viewports, with the exception of the top-level viewport, belong to an owning
projection. A `Projection` is a function for mapping 2D or 3D objects into an
owning viewport.

The top-level Viewport is an instance of `WindowViewport`, which fills
the entire window.  This viewport will automatically resize when the window
is resized.

The two possible projections are `OrthographicProjection` and
`PerspectiveProjection`.  OrthographicProjection maps to the same coordinate
space as the viewport it belongs to.  PerspectiveProjection uses an arbitrary
unit and a specified field-of-view, and is used to map 3D objects into the
2D viewport.

To use the projection module to render in 2D in a window:

    from pyglet.ext import projection

    w = window.Window()
    viewport = projection.WindowViewport(w)
    projection = projection.OrthographicProjection(viewport)

    @w.event
    def on_resize(width, height):
        projection.apply()

You can also embed additional viewports within a projection.  For example,
a 3D scene can be created within a 2D user interface::

    # x, y, width, height give dimensions of inner viewport within window
    inner_viewport = OrthographicViewport(projection, x, y, width, height)
    inner_projection = PerspectiveProjection(inner_viewport, fov=75)

    @w.event
    def on_resize(width, height):
        inner_projection.apply()

    while not w.has_exit:
        w.dispatch_events()

        w.projection.apply()
        # Draw 2D user interface...

        inner_projection.apply()
        # Draw 3D scene...

        w.flip()

'''

from pyglet.gl import *

class Projection(object):
    viewport = None

class OrthographicProjection(Projection):
    def __init__(self, viewport, near=-1, far=1):
        self.viewport = viewport
        self.near = near
        self.far = far

    def apply(self):
        self.viewport.apply()
        glMatrixMode(GL_PROJECTION)
        glOrtho(0, self.viewport.width, 
                0, self.viewport.height, 
                self.near, self.far)
        glMatrixMode(GL_MODELVIEW)

class PerspectiveProjection(Projection):
    def __init__(self, viewport, fov=60, near=0.1, far=1000):
        self.viewport = viewport
        self.fov = fov
        self.near = near
        self.far = far

    def apply(self):
        self.viewport.apply()
        glMatrixMode(GL_PROJECTION)
        gluPerspective(self.fov,
                      self.viewport.width/float(self.viewport.height),
                      self.near,
                      self.far)
        glMatrixMode(GL_MODELVIEW)

class Viewport(object):
    projection = None
    width = 0
    height = 0

class WindowViewport(Viewport):
    def __init__(self, window):
        self.window = window

    def apply(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glViewport(0, 0, self.window.width, self.window.height)

        glDisable(GL_CLIP_PLANE0)
        glDisable(GL_CLIP_PLANE1)
        glDisable(GL_CLIP_PLANE2)
        glDisable(GL_CLIP_PLANE3)

    width = property(lambda self: self.window.width)
    height = property(lambda self: self.window.height)

class OrthographicViewport(Viewport):
    def __init__(self, projection, x, y, width, height, near=-1, far=1):
        assert isinstance(projection, OrthographicProjection)
        self.projection = projection
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.near = near
        self.far = far

    def apply(self):
        l = self.x
        r = self.x + self.width
        b = self.y
        t = self.y + self.height
        n = self.near
        f = self.far

        self.projection.apply()
        glMatrixMode(GL_PROJECTION)
        glMultMatrixf((GLfloat * 16)(
            (r-l)/2, 0,       0,       0,
            0,       (t-b)/2, 0,       0,
            0,       0,       (f-n)/2, 0,
            (r+l)/2, (t+b)/2, (f+n)/2, 1))
        glMatrixMode(GL_MODELVIEW)

        glClipPlane(GL_CLIP_PLANE0, (GLdouble * 4)(1, 0, 0, 0))
        glClipPlane(GL_CLIP_PLANE1, (GLdouble * 4)(-1, 0, 0, self.width))
        glClipPlane(GL_CLIP_PLANE2, (GLdouble * 4)(0, 1, 0, 0))
        glClipPlane(GL_CLIP_PLANE3, (GLdouble * 4)(0, -1, 0, self.height))
      
        glEnable(GL_CLIP_PLANE0)
        glEnable(GL_CLIP_PLANE1)
        glEnable(GL_CLIP_PLANE2)
        glEnable(GL_CLIP_PLANE3)


