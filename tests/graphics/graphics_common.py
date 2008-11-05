#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from operator import add
import random

from pyglet.gl import *

n_vertices = 42
v3f_data = [v/float(n_vertices*3 + 10) for v in range(n_vertices * 3)]
v2f_data = reduce(add, zip(v3f_data[::3], v3f_data[1::3]))
c4f_data = [v/float(n_vertices*4) for v in range(n_vertices * 4)]
c3f_data = reduce(add, zip(c4f_data[::4], c4f_data[1::4], c4f_data[2::4]))
t4f_data = [v/float(n_vertices*4 + 5) for v in range(n_vertices * 4)]
t3f_data = reduce(add, zip(t4f_data[::4], t4f_data[1::4], t4f_data[2::4]))
t2f_data = reduce(add, zip(t3f_data[::3], t3f_data[1::3]))

index_data = range(n_vertices)
random.seed(1)
random.shuffle(index_data)

def get_ordered_data(data, dimensions):
    ordered = []
    for i in index_data:
        ordered.extend(data[i * dimensions:(i+1)*dimensions])
    return ordered

feedback_buffer = (GLfloat * 8096)()

def get_feedback(func):
    # Project in clip coords
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, 1, 0, 1, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    glFeedbackBuffer(len(feedback_buffer), GL_4D_COLOR_TEXTURE, feedback_buffer)
    glRenderMode(GL_FEEDBACK)
    func()
    size = glRenderMode(GL_RENDER)
    buffer = feedback_buffer[:size]
    vertices = []
    colors = []
    tex_coords = []
    while buffer:
        token = int(buffer.pop(0))
        assert token == GL_POLYGON_TOKEN
        n = int(buffer.pop(0))
        for i in range(n):
            vertices.extend(buffer[:4])
            colors.extend(buffer[4:8])
            tex_coords.extend(buffer[8:12])
            del buffer[:12]
    return vertices, colors, tex_coords

import sys
print >> sys.stderr, 'Note: Graphics tests fail with recent nvidia drivers'
print >> sys.stderr, '      due to reordering and optimisation of vertices'
print >> sys.stderr, '      before they are placed in the feedback queue.'
