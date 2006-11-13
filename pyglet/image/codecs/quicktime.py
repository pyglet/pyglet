#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: pil.py 163 2006-11-13 04:15:46Z Alex.Holkner $'

from ctypes import *

from pyglet.GL.VERSION_1_1 import *
from pyglet.image import *
from pyglet.image.codecs import *

from pyglet.window.carbon import carbon, quicktime
from pyglet.window.carbon.constants import _name
from pyglet.window.carbon.types import *

Handle = POINTER(POINTER(c_byte))
GWorldPtr = c_void_p
carbon.NewHandle.restype = Handle
HandleDataHandlerSubType = _name('hndl')
ComponentInstance = c_void_p

k1MonochromePixelFormat       = 0x00000001
k2IndexedPixelFormat          = 0x00000002
k4IndexedPixelFormat          = 0x00000004
k8IndexedPixelFormat          = 0x00000008
k16BE555PixelFormat           = 0x00000010
k24RGBPixelFormat             = 0x00000018
k32ARGBPixelFormat            = 0x00000020
k1IndexedGrayPixelFormat      = 0x00000021
k2IndexedGrayPixelFormat      = 0x00000022
k4IndexedGrayPixelFormat      = 0x00000024
k8IndexedGrayPixelFormat      = 0x00000028

class QuickTimeImageDecoder(ImageDecoder):
    def get_file_extensions(self):
        # Only most common ones shown here
        return ['.bmp', '.cur', '.gif', '.ico', '.jpg', '.jpeg', '.pcx', '.png',
                '.tga', '.tif', '.tiff', '.xbm', '.xpm']

    def decode(self, file, filename):
        data = file.read()
        handle = Handle()
        dataref = Handle()
        carbon.PtrToHand(data, byref(handle), len(data))
        carbon.PtrToHand(byref(handle), byref(dataref), sizeof(Handle))
        importer = ComponentInstance()
        quicktime.GetGraphicsImporterForDataRef(dataref, 
            HandleDataHandlerSubType, byref(importer))

        rect = Rect()
        quicktime.GraphicsImportGetNaturalBounds(importer, byref(rect))
        width = rect.right
        height = rect.bottom
        components = 4 # TODO

        buffer = (c_byte * width * height * components)()
        world = GWorldPtr()
        quicktime.QTNewGWorldFromPtr(byref(world), k32ARGBPixelFormat,
            byref(rect), c_void_p(), c_void_p(), 0, buffer,
            components * width)

        quicktime.GraphicsImportSetGWorld(importer, world, c_void_p())
        quicktime.GraphicsImportDraw(importer)
        quicktime.DisposeGWorld(world)

        # This is equivalent to ARGB with UNSIGNED_BYTE.  
        format = GL_BGRA
        type = GL_UNSIGNED_INT_8_8_8_8_REV

        return RawImage(buffer, width, height, format, type)

def get_decoders():
    return [QuickTimeImageDecoder()]

def get_encoders():
    return []
