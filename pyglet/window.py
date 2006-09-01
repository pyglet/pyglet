#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

_frame_count = 0
_count_start_time = 0
_fps_atlas = None

from SDL import *
from OpenGL.GL import *

import pyglet.image

_width = 0
_height = 0

def set_window(width=640, height=480, 
             caption='pyglet', fullscreen=False, resizable=False):
    if not SDL_WasInit(SDL_INIT_VIDEO):
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

    global _width, _height
    _width = width
    _height = height

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, width, height, 0, -1, 1)
    glMatrixMode(GL_MODELVIEW)

    glClearColor(1, 1, 1, 1)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

def get_size():
    return _width, _height

def clear():
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()

def flip():
    SDL_GL_SwapBuffers()

    global _frame_count, _count_start_time
    now = SDL_GetTicks()
    if _frame_count == 0 or now - _count_start_time > 1000:
        _count_start_time += (now - _count_start_time) / 2
        _frame_count /= 2
    _frame_count += 1

def get_fps():
    return _frame_count * 1000 / (SDL_GetTicks() - _count_start_time)

def draw_fps():
    global _fps_atlas
    if not _fps_atlas:
        _fps_atlas = \
            pyglet.image.TextureAtlas(pyglet.image.load('pyglet/numbers.png'), 
                                      rows=1, cols=10)

    glPushMatrix()
    glTranslate(10, 10, 0)
    numbers = [int(c) for c in str(get_fps())]
    for digit in numbers:
        _fps_atlas.draw(0, digit)
        glTranslate(_fps_atlas.get_size(0, digit)[0], 0, 0)
    glPopMatrix()
