import math

import pyglet
from pyglet.gl import *

class SmoothLineGroup(pyglet.graphics.Group):
    def set_state(self):
        glPushAttrib(GL_ENABLE_BIT)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LINE_SMOOTH)
        glLineWidth(2)

    def unset_state(self):
        glPopAttrib()

    def __hash__(self):
        return hash(self.__class__.__name__)

    def __eq__(self, other):
        return self.__class__ is other.__class__

def add_circle(batch, x, y, radius, color, num_points=20, antialised=True):
    l = []
    for n in range(num_points):
        angle = (math.pi * 2 * n) / num_points
        l.append(int(x + radius * math.cos(angle)))
        l.append(int(y + radius * math.sin(angle)))
    l.append(int(x + radius * 1))
    l.append(int(y))
    num_points += 3
    l[0:0] = l[0:2]
    l.extend(l[-2:])
    if antialised:
        group = SmoothLineGroup()
    else:
        group = None
    return batch.add(num_points, GL_LINE_STRIP, group, ('v2i', l),
        ('c4B', color*num_points))

