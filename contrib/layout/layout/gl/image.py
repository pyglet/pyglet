#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import warnings

from pyglet.gl import *
from pyglet import image
from layout.frame import *

class ImageReplacedElementFactory(ReplacedElementFactory):
    accept_names = ['img']

    def __init__(self, locator):
        self.locator = locator
        self.cache = {}

    def create_drawable(self, element):
        file = None
        if 'src' not in element.attributes:
            warnings.warn('Image does not have src attribute')
            return None

        src = element.attributes['src']
        # TODO move cache onto context.
        if src in self.cache:
            return ImageReplacedElementDrawable(self.cache[src])

        file = self.locator.get_stream(src)
        if not file:
            # TODO broken image if not file
            warnings.warn('Image not loaded: "%s"' % attrs['src'])
            return None

        img = image.load('', file=file)
        self.cache[src] = img
        return ImageReplacedElementDrawable(img)

class ImageReplacedElementDrawable(ReplacedElementDrawable):
    def __init__(self, image):
        self.texture = image.texture

        self.intrinsic_width = image.width
        self.intrinsic_height = image.height
        self.intrinsic_ratio = image.width / float(image.height)

    def draw(self, frame, render_device, left, top, right, bottom):
        glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_COLOR_BUFFER_BIT)
        glColor3f(1, 1, 1)
        glEnable(GL_TEXTURE_2D)        
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glBindTexture(GL_TEXTURE_2D, self.texture.id)

        # Create interleaved array in T4F_V4F format
        t = self.texture.tex_coords
        array = (GLfloat * 32)(
             t[0],    t[1],    t[2],  1.,
             left,    bottom,  0,     1.,
             t[3],    t[4],    t[5],  1., 
             right,   bottom,  0,     1.,
             t[6],    t[7],    t[8],  1., 
             right,   top,     0,     1.,
             t[9],    t[10],   t[11], 1., 
             left,    top,     0,     1.)

        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        glInterleavedArrays(GL_T4F_V4F, 0, array)
        glDrawArrays(GL_QUADS, 0, 4)
        glPopClientAttrib()

        glPopAttrib()
