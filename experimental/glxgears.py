#!/usr/bin/python
# $Id:$

import ctypes

import pyglet
from pyglet.window.xlib import xlib
from pyglet.gl import *
from pyglet.gl.glx import *

def reshape(width, height):
   h = height / float(width)
   glViewport(0, 0, width, height)
   glMatrixMode(GL_PROJECTION)
   glLoadIdentity()
   glFrustum(-1.0, 1.0, -h, h, 5.0, 60.0)
   glMatrixMode(GL_MODELVIEW)
   glLoadIdentity()
   glTranslatef(0.0, 0.0, -40.0)

def draw():
    glClearColor(1, 1, 0, 1)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    # TODO

def init():
    # TODO
    pass

def make_window(dpy, name, x,y, width, height):
    attrib = (ctypes.c_int * 11)(
        GLX_RGBA,
        GLX_RED_SIZE, 1,
        GLX_GREEN_SIZE, 1,
        GLX_BLUE_SIZE, 1,
        GLX_DOUBLEBUFFER,
        GLX_DEPTH_SIZE, 1,
        0)

    scrnum = xlib.XDefaultScreen(dpy)
    root = xlib.XRootWindow(dpy, scrnum)

    visinfo = glXChooseVisual(dpy, scrnum, attrib)
    
    attr = xlib.XSetWindowAttributes()
    attr.background_pixel = 0
    attr.border_pixel = 0
    attr.colormap = xlib.XCreateColormap(dpy, root, visinfo.contents.visual,
        xlib.AllocNone)
    attr.event_mask = (xlib.StructureNotifyMask | 
                       xlib.ExposureMask |
                       xlib.KeyPressMask)
    mask = (xlib.CWBackPixel |
            xlib.CWBorderPixel | 
            xlib.CWColormap | 
            xlib.CWEventMask)

    win = xlib.XCreateWindow(dpy, root, 0, 0, width, height, 0, 
                             visinfo.contents.depth, xlib.InputOutput,
                             visinfo.contents.visual, mask, attr)

    sizehints = xlib.XSizeHints()
    sizehints.x = x
    sizehints.y = y
    sizehints.width = width
    sizehints.height = height
    sizehints.flags = xlib.USSize | xlib.USPosition
    xlib.XSetNormalHints(dpy, win, sizehints)
    xlib.XSetStandardProperties(dpy, win, name, name, 0, None, 0, sizehints)

    ctx = glXCreateContext(dpy, visinfo, None, True)
    xlib.XFree(visinfo)

    return win, ctx

def event_loop(dpy, win):
    while True:
        while xlib.XPending(dpy) > 0:
            event = xlib.XEvent()
            xlib.XNextEvent(dpy, event)
            if event.type == xlib.Expose:
                pass
            elif event.type == xlib.ConfigureNotify:
                reshape(event.xconfigure.width, event.xconfigure.height)
            elif event.type == xlib.KeyPress:
                pass # TODO

        #angle += 2.0
        draw()
        glXSwapBuffers(dpy, win)

def main():
    dpy = xlib.XOpenDisplay(None) 
    win, ctx = make_window(dpy, 'glxgears', 0, 0, 300, 300)
    xlib.XMapWindow(dpy, win)
    glXMakeCurrent(dpy, win, ctx)
    reshape(300, 300)
    init()
    event_loop(dpy, win)

    glXDestroyContext(dpy, ctx)
    xlib.XDestroyWindow(dpy, win)
    xlib.XCloseDisplay(dpy)

if __name__ == '__main__':
    main()
