#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import math
import warnings

from OpenGL.GL import *
from SDL import *

import pyglet
import pyglet.image

try:
    from pyglet.GL.VERSION_1_5 import *
except ImportError:
    warnings.warn('OpenGL 1.5 or later is required collision detection. '\
                  'Please update your video card driver.')

class Sprite(object):
    __slots__ = ['texture', 'anchor', 'position', 'rotation', 'scale', 'color']

    _collision_stencil = 1

    def __init__(self, image, anchor=None):
        if not isinstance(image, pyglet.image.Texture):
            if not isinstance(image, SDL_Surface):
                image = pyglet.image.load(image)
            image = pyglet.image.Texture.from_surface(image)
        self.texture = image

        self.position = (0,0)
        self.anchor = (self.texture.size[0] / 2,
                       self.texture.size[1] / 2)
        self.rotation = 0.0
        self.scale = 1.0
        self.color = (1, 1, 1, 1)

    def draw(self):
        glPushMatrix()
        glPushAttrib(GL_CURRENT_BIT)

        glColor4fv(self.color)
        glTranslate(self.position[0], self.position[1], 0)
        glRotate(self.rotation, 0, 0, -1)
        glScale(self.scale, self.scale, 1)
        glTranslate(-self.anchor[0], -self.anchor[1], 0)

        self.texture.draw()

        glPopAttrib()
        glPopMatrix()

    def translate(self, dx, dy):
        '''Move the sprite by the given units, transformed by its current
        rotation.  Useful for moving a sprite "forward" according to
        its current direction.'''
        r = math.pi * self.rotation / 180.0
        c = math.cos(r)
        s = math.sin(r)
        x = self.position[0]
        y = self.position[1]
        self.position = x + c * dx + s * dy,  y + s * dx + c * dy

    def collide(self, other):
        '''Get the number of pixels of overlap between self and other.
        other can be a Sprite or list of Sprites.'''
        glPushAttrib(GL_COLOR_BUFFER_BIT | \
                     GL_STENCIL_BUFFER_BIT | \
                     GL_ENABLE_BIT)
        glColorMask(0, 0, 0, 0)
        glEnable(GL_ALPHA_TEST)
        glAlphaFunc(GL_GEQUAL, 0.5)

        # Draw collider into stencil
        glClear(GL_STENCIL_BUFFER_BIT)
        glStencilFunc(GL_ALWAYS, 
                      self._collision_stencil, 
                      self._collision_stencil)
        glStencilOp(GL_KEEP, GL_REPLACE, GL_REPLACE)
        glEnable(GL_STENCIL_TEST)
        if hasattr(other, '__len__'):
            for o in other:
                other.draw()
        else:
            other.draw()

        # Occlusion query self
        glStencilFunc(GL_EQUAL, 
                      self._collision_stencil,
                      self._collision_stencil)

        query = c_uint()
        glGenQueries(1, byref(query))
        glBeginQuery(GL_SAMPLES_PASSED, query)
        self.draw()
        glEndQuery(GL_SAMPLES_PASSED)
        result = c_int()
        glGetQueryObjectiv(query, GL_QUERY_RESULT, byref(result))
        glDeleteQueries(1, byref(query))

        glPopAttrib()

        return result.value

    def collide_list(self, others):
        '''Get a list of Sprites in others that collide with self.'''
        glPushAttrib(GL_COLOR_BUFFER_BIT | \
                     GL_STENCIL_BUFFER_BIT | \
                     GL_ENABLE_BIT)
        glColorMask(0, 0, 0, 0)
        glEnable(GL_ALPHA_TEST)
        glAlphaFunc(GL_GEQUAL, 0.5)

        # Draw self into stencil
        glClear(GL_STENCIL_BUFFER_BIT)
        glStencilFunc(GL_ALWAYS, 
                      self._collision_stencil, 
                      self._collision_stencil)
        glStencilOp(GL_KEEP, GL_REPLACE, GL_REPLACE)
        glEnable(GL_STENCIL_TEST)
        self.draw()

        # Occlusion query each other
        glStencilFunc(GL_EQUAL, 
                      self._collision_stencil,
                      self._collision_stencil)

        # Using multiple queries is noticeably faster than reusing the
        # one query.
        n_query = len(others)
        query = (c_uint * n_query)()
        glGenQueries(n_query, query)
        collisions = []
        for i, other in enumerate(others):
            glBeginQuery(GL_SAMPLES_PASSED, query[i])
            other.draw()
            glEndQuery(GL_SAMPLES_PASSED)
        for i, other in enumerate(others):
            result = c_int()
            glGetQueryObjectiv(query[i], GL_QUERY_RESULT, byref(result))
            if result.value > 0:
                collisions.append(other)
        glDeleteQueries(n_query, query)

        glPopAttrib()

        return collisions

class Window(object):
    frame_count = 0
    count_start_time = 0

    def __init__(self, width=640, height=480, 
                 caption='pyglet', fullscreen=False, resizable=False):
        SDL_Init(SDL_INIT_VIDEO | SDL_INIT_TIMER)

        flags = SDL_OPENGL
        if fullscreen:
            flags |= SDL_FULLSCREEN
        if resizable:
            flags |= SDL_RESIZABLE

        SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1)
        SDL_GL_SetAttribute(SDL_GL_STENCIL_SIZE, 1)
        SDL_SetVideoMode(width, height, 32, flags)
        SDL_WM_SetCaption(caption, caption)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, height, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)

        glClearColor(1, 1, 1, 1)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    @staticmethod
    def clear():
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()

    @staticmethod
    def flip():
        SDL_GL_SwapBuffers()
        if Window.frame_count == 0:
            count_start_time = SDL_GetTicks()
        Window.frame_count += 1

    @staticmethod
    def get_fps():
        return Window.frame_count * 1000 / \
               (SDL_GetTicks() - Window.count_start_time)
