#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from ctypes import *
from ctypes import util

from pyglet.GL.VERSION_1_1 import *
from pyglet.image import *
from pyglet.image.codecs import *

import pyglet.window

_path = util.find_library('gdk-x11-2.0')
if not _path:
    raise ImportError('Cannot locate libgdk-x11-2.0.so')
gdk = cdll.LoadLibrary(_path)

_path = util.find_library('gdk_pixbuf-2.0')
if not _path:
    raise ImportError('Cannot locate libgdk_pixbuf-2.0.so')
gdkpixbuf = cdll.LoadLibrary(_path)

GdkPixbufLoader = c_void_p
GdkPixbuf = c_void_p
gdkpixbuf.gdk_pixbuf_loader_new.restype = GdkPixbufLoader
gdkpixbuf.gdk_pixbuf_loader_get_pixbuf.restype = GdkPixbuf
gdkpixbuf.gdk_pixbuf_get_pixels.restype = c_void_p

class GdkPixbuf2ImageDecoder(ImageDecoder):
    def get_file_extensions(self):
        return ['.png', '.xpm', '.jpg', '.jpeg', '.tif', '.tiff', '.pnm',
                '.ras', '.bmp', '.gif']

    def decode(self, file, filename):
        data = file.read()

        # Load into pixbuf
        err = c_int()
        loader = gdkpixbuf.gdk_pixbuf_loader_new()
        gdkpixbuf.gdk_pixbuf_loader_write(loader, data, len(data))
        pixbuf = gdkpixbuf.gdk_pixbuf_loader_get_pixbuf(loader)
        if not gdkpixbuf.gdk_pixbuf_loader_close(loader, byref(err)):
            raise ImageDecodeException(filename)
        
        # Get format and dimensions
        width = gdkpixbuf.gdk_pixbuf_get_width(pixbuf)
        height = gdkpixbuf.gdk_pixbuf_get_height(pixbuf)
        channels = gdkpixbuf.gdk_pixbuf_get_n_channels(pixbuf)
        rowstride = gdkpixbuf.gdk_pixbuf_get_rowstride(pixbuf)
        has_alpha = gdkpixbuf.gdk_pixbuf_get_has_alpha(pixbuf)
        pixels = gdkpixbuf.gdk_pixbuf_get_pixels(pixbuf)
        print pixels

        # Copy pixel data.
        buffer = (c_ubyte * (rowstride * height))()
        memmove(buffer, pixels, rowstride * (height - 1) + width * channels)

        # Release pixbuf
        gdk.g_object_unref(pixbuf)

        # Determine appropriate GL type
        if channels == 3:
            format = 'RGB'
        else:
            format = 'RGBA'

        type = GL_UNSIGNED_BYTE

        return RawImage(buffer, width, height, format, type, 
            top_to_bottom=True)

def get_decoders():
    return [GdkPixbuf2ImageDecoder()]

def get_encoders():
    return []

def init():
    gdk.g_type_init()

init()

