#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from ctypes import *

from pyglet.GL.VERSION_1_1 import *
from pyglet.window import *
from pyglet.window.event import *
from pyglet.image import *
from pyglet.window.carbon import carbon 

CGGlyph = c_ushort

kCGImageAlphaNone = 0
kCGImageAlphaPremultipliedLast = 1
kCGTextFill = 0

carbon.CGColorSpaceCreateWithName.restype = c_void_p
carbon.CGBitmapContextCreate.restype = c_void_p

height = 256
width = 256

window = Window(width, height)

components = 4
pitch = width * components
data = (c_ubyte * (width * height * components))()
color_space = carbon.CGColorSpaceCreateDeviceRGB()
context = carbon.CGBitmapContextCreate(data, width, height, 8, pitch, 
    color_space, kCGImageAlphaPremultipliedLast)
carbon.CGColorSpaceRelease(color_space)

carbon.CGContextSelectFont( context, "Lucida Grande", c_float(16.0), 1);
#carbon.CGFontCreateWithPlatformFont(ats_font)
#carbon.CGContextSetFont(context, font)
#carbon.CGContextSetFontSize(context, c_float(66.))
#carbon.CGFontRelease(font)
carbon.CGContextSetRGBFillColor(context, c_float(1), c_float(1), c_float(1),
    c_float(1))
carbon.CGContextSetTextDrawingMode(context, kCGTextFill)

glyphs = (CGGlyph * 1)(61)
#carbon.CGContextShowGlyphsAtPoint(context, c_float(0.), c_float(0.), 
#    glyphs, len(glyphs))
carbon.CGContextShowTextAtPoint(context, c_float(40), c_float(40), "Hello", 5)


image = RawImage(data, width, height, 'RGBA', GL_UNSIGNED_BYTE)
carbon.CGContextRelease(context)

glClearColor(1, 1, 1, 1)
glClear(GL_COLOR_BUFFER_BIT)
glMatrixMode(GL_PROJECTION)
glOrtho(0, window.width, 0, window.height, -1, 1)
glMatrixMode(GL_MODELVIEW)
texture = image.texture()
texture.draw()

window.flip()

exit = ExitHandler()
window.push_handlers(exit)
while not exit.exit:
    window.dispatch_events()
