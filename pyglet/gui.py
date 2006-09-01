#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import math
import warnings

from OpenGL.GL import *

class DrawingContext(object):
    __slots__ = ['transitions']

    def __init__(self):
        self.transitions = []

    def draw(self, widget):
        if widget.transition:
            self.transtions.append(widget.transition)

        x, y = widget._global_rect.topleft
        for transition in self.transitions:
            x, y = transition.apply(widget, x, y)
        glTranslate(x, y, 0)
        widget.draw()
        glTranslate(-x, -y, 0)
        widget.draw_children(self)

        if widget.transition:
            self.transitions.pop()

class Layout(object):
    __slots__ = ['widget', 'child_properties']
    properties = []

    def __init__(self, widget):
        self.widget = widget
        self.child_properties = {}

    def set_properties(self, child, properties):
        if child not in self.child_properties:
            self.child_properties[child] = {}

        for key in properties.keys():
            if key not in self.__class__.properties:
                warnings.warn('%s does not understand property "%s"' % \
                    (self.__class__, key))
            else:
                self.child_properties[child][key] = value

    def update(self):
        pass

class CenterLayout(Layout):
    def update(self):
        center = self.widget.rect.center
        for child in self.widget.children:
            child.rect.center = center

class VerticalStackLayout(Layout):
    properties = ['pad']

    def __init__(self, widget):
        super(VerticalStackLayout, self).__init__(widget)
        self.child_properties[None] = {}
        self.child_properties[None]['pad'] = 10

    def update(self):
        pad = self.child_properties[None]['pad']
        x = self.widget.rect.centerx
        y = 0
        for child in self.widget.children:
            child.rect.midtop = x, y
            y += child.size[1] + pad

class Interpolator(object):
    def __call__(self, t, t1, dt, v1, dv):
        return self._function((t - t1) / dt) * dv + v1
    
    def _function(self, f):
        raise NotImplementedError, 'Abstract'

class LinearInterpolator(Interpolator):
    def _function(self, f):
        return f

class LogarithmicInterpolator(Interpolator):
    def _function(self, f):
        return math.log(f * math.e - f + 1.0)

class ExponentialInterpolator(Interpolator):
    def _function(self, f):
        return (4 - 2 ** (2 - 2 * f)) / 3

class SquareRootInterpolator(Interpolator):
    def _function(self, f):
        return math.sqrt(f)

class QuadraticInterpolator(Interpolator):
    def _function(self, f):
        return f * (2 - f)

class CubicInterpolator(Interpolator):
    def _function(self, f):
        return f * f * (3 - f * 2)

class SineInterpolator(Interpolator):
    def _function(self, f):
        return math.sin(f * math.pi / 2)

class Transition(object):
    __slots__ = ['parent', 't1', 'dt', 'interpolator']
    def __init__(self, parent, t1, t2):
        self.interpolator = CubicInterpolator()
        self.parent = parent
        self.t1 = t1
        self.dt = t2 - float(t1)

class SlideHorizontalTransition(Transition):
    __slots__ = Transition.__slots__ + ['start_x']

    def __init__(self, parent, t1, t2, start_x=0):
        super(SlideHorizontalTransition, self).__init__(parent, t1, t2)
        self.start_x = 0

    def apply(self, widget, time):
        glLoadMatrixf(self.parent.matrix)
        pos = widget.global_pos
        v = self.interpolator(time, self.t1, self.dt, 
                    self.start_x, pos[0] - self.start_x)
        glTranslate(v, pos[1], 0)



class Widget(object):
    __slots__ = ['parent', 'rect', 'transition']

    def __init__(self):
        self.parent = None
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.transition = None

    def draw(self):
        pass

    def _draw_internal(self, transition, time):
        if self.transition:
            transition = self.transition
        glTranslate(self.rect.x, self.rect.y, 0)
        if transition:
            glPushMatrix()
            transition.apply(self, time)
            self.draw()
            glPopMatrix()
        else:
            self.draw()
        glTranslate(-self.rect.x, -self.rect.y, 0)
        return transition

    def get_size(self):
        return self.rect.size

    def set_size(self, size):
        self.rect.size = size
        if self.parent:
            self.parent.layout.update()
    
    size = property(get_size, set_size)

    def get_global_pos(self):
        return (self.parent.rect.x + self.rect.x, 
                self.parent.rect.y + self.rect.y)

    global_pos = property(get_global_pos)

class Container(Widget):
    __slots__ = Widget.__slots__ + ['children', 'layout', 'matrix']

    def __init__(self):
        super(Container, self).__init__()
        self.children = []
        self.layout = VerticalStackLayout(self)

    def add(self, child, **parameters):
        assert child.parent is None
        child.parent = self
        self.children.append(child)
        self.layout.set_properties(child, parameters)
        self.layout.update()

    def _draw_internal(self, transition, time):
        transition = super(Container, self)._draw_internal(transition, time)
        glTranslate(self.rect.x, self.rect.y, 0)
        self.matrix = glGetFloat(GL_MODELVIEW_MATRIX)
        for child in self.children:
            child._draw_internal(transition, time)
        glTranslate(-self.rect.x, -self.rect.y, 0)

    def get_size(self):
        return self.rect.size

    def set_size(self, size):
        super(Container, self).set_size(size)
        self.layout.update()

    size = property(get_size, set_size)

class ImageButton(Widget):
    __slots__ = ['texture']

    def __init__(self, texture):
        super(ImageButton, self).__init__()
        self.texture = texture
        self.size = texture.size

    def draw(self):
        self.texture.draw()

class Desktop(Container):
    def __init__(self, width, height):
        super(Desktop, self).__init__()
        self.rect = pygame.Rect(0, 0, width, height)

class GUI(object):
    def __init__(self):
        self.desktop = None
        self.transitions = []

    def transition(self, widgets, transition):
        if not hasattr(widgets, '__len__'):
            widgets = (widgets,)
        for widget in widgets:
            widget.transition = transition
            self.transitions.append(widget)

    def update(self):
        t = pygame.time.get_ticks()
        for widget in self.transitions[:]:
            if t > widget.transition.t1 + widget.transition.dt:
                widget.transition = None
                self.transitions.remove(widget)
        self.desktop._draw_internal(None, t)
