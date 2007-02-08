#!/usr/bin/env python

'''Simple viewer for DDS texture files.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from ctypes import *
import getopt
import sys
import textwrap

from SDL import *

from pyglet.gl.VERSION_1_1 import *
import pyglet.dds
import pyglet.event
import pyglet.image
import pyglet.sprite
import pyglet.window

from OpenGL.GLU import *

def usage():
    print textwrap.dedent('''
        Usage: ddsview.py [--header] texture1.dds texture2.dds ...

            --header    Dump the header of each file instead of displaying.

        Within the program, press:

            left/right keys     Flip between loaded textures
            up/down keys        Increase/decrease mipmap level for a texture
            space               Toggle flat or sphere view

        Click and drag with mouse to reposition texture with wrapping.
        ''')

texture_index = 0
textures = []
mipmap_level = 0
last_pos = None
texture_offset = [0, 0]
view = 'flat'
sphere_angle = 0

def keydown(character, symbol, modifiers):
    global mipmap_level, texture_index
    if symbol == SDLK_DOWN:
        mipmap_level = max(0, mipmap_level - 1)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_BASE_LEVEL, mipmap_level)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAX_LEVEL, mipmap_level)
    elif symbol == SDLK_UP:
        mipmap_level = mipmap_level + 1
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_BASE_LEVEL, mipmap_level)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAX_LEVEL, mipmap_level)
    elif symbol == SDLK_LEFT:
        texture_index = max(0, texture_index - 1)
    elif symbol == SDLK_RIGHT:
        texture_index = min(len(textures) - 1, texture_index + 1)
    elif symbol == SDLK_SPACE:
        toggle_view() 
    return True

def mousemotion(x, y):
    global last_pos
    state, x, y = SDL_GetMouseState()
    if state & SDL_BUTTON(1):
        texture_offset[0] += x - last_pos[0]
        texture_offset[1] += y - last_pos[1]
        update_texture_matrix()
    last_pos = x, y

def update_texture_matrix():
    glMatrixMode(GL_TEXTURE)
    glLoadIdentity()
    glTranslatef(-texture_offset[0] / float(textures[texture_index].size[0]),
                 -texture_offset[1] / float(textures[texture_index].size[1]),
                 0)
    glMatrixMode(GL_MODELVIEW)

def toggle_view():
    global view
    if view != 'flat':
        pyglet.event.pop()
        pyglet.window.set_2d()
        view = 'flat'
    else:
        pyglet.event.push()
        pyglet.event.on_mousemotion(sphere_mousemotion)
        pyglet.window.set_3d()
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, (c_float * 4)(0.5, 0.5, 1, 0))
        view = 'sphere'

def sphere_mousemotion(x, y):
    # TODO: virtual trackball
    return True

def draw_sphere():
    global sphere_angle

    glPushMatrix()
    glTranslatef(0., 0., -4)
    glRotatef(sphere_angle, 0, 1, 0)
    glRotatef(90, 1, 0, 0)
    sphere_angle += 0.01

    glPushAttrib(GL_ENABLE_BIT)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, textures[texture_index].id)
    glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
    sphere = gluNewQuadric()
    gluQuadricTexture(sphere, True)
    gluSphere(sphere, 1.0, 100, 100)    
    gluDeleteQuadric(sphere)
    glPopAttrib()

    glPopMatrix()

def main(args):
    header = False

    options, args = getopt.getopt(args[1:], 'h', ['help', 'header'])
    for option, value in options:
        if option in ('-h', '--help'):
            usage()
            sys.exit()
        elif option == '--header':
            header = True
    if len(args) < 1:
        usage()
        sys.exit()

    if header:
        for arg in args:
            print pyglet.dds.DDSURFACEDESC2(open(arg,
            'r').read(pyglet.dds.DDSURFACEDESC2.get_size()))
    else:
        pyglet.window.set_window(resizable=True)
        global textures, texture_index
        textures = [pyglet.dds.load_dds(arg) for arg in args]
        texture_index = 0
        pyglet.window.resize(*textures[0].size)
        pyglet.event.push()
        pyglet.event.on_keydown(keydown)
        pyglet.event.on_mousemotion(mousemotion)

        global last_pos
        state, x, y = SDL_GetMouseState()
        last_pos = x, y

        glClearColor(0, 0, 0, 0)

        while not pyglet.event.is_quit():
            pyglet.event.pump()
            pyglet.window.clear()
            if view == 'flat':
                textures[texture_index].draw()
            elif view == 'sphere':
                draw_sphere()
            pyglet.window.flip()


if __name__ == '__main__':
    main(sys.argv)
