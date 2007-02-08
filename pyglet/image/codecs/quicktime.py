#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: pil.py 163 2006-11-13 04:15:46Z Alex.Holkner $'

from ctypes import *

from pyglet.gl import *
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
kNativeEndianPixMap           = 1 << 8

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

        # TODO choose 24 bit where appropriate.
        format = 'ARGB'
        qtformat = k32ARGBPixelFormat

        buffer = (c_byte * (width * height * len(format)))()
        world = GWorldPtr()
        quicktime.QTNewGWorldFromPtr(byref(world), qtformat,
            byref(rect), c_void_p(), c_void_p(), kNativeEndianPixMap, buffer,
            len(format) * width)

        quicktime.GraphicsImportSetGWorld(importer, world, c_void_p())
        quicktime.GraphicsImportDraw(importer)
        quicktime.DisposeGWorld(world)

        type = GL_UNSIGNED_BYTE

        return RawImage(buffer, width, height, format, type, 
            top_to_bottom=True)

def get_decoders():
    return [QuickTimeImageDecoder()]

def get_encoders():
    return []
