#!/usr/bin/env python

'''Encoder and decoder for PNG files, using PyPNG (pypng.py).
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from pyglet.GL.VERSION_1_1 import *
from pyglet.image import *
from pyglet.image.codecs import *

import pyglet.image.codecs.pypng

class PNGImageDecoder(ImageDecoder):
    def get_file_extensions(self):
        return ['png']

    def decode(self, file, filename):
        reader = pyglet.image.codecs.pypng.Reader(file=file)
        width, height, pixels, metadata = reader.read()
        if metadata['greyscale']:
            if metadata['has_alpha']:
                format = GL_LUMINANCE_ALPHA
            else:
                format = GL_LUMINANCE
        else:
            if metadata['has_alpha']:
                format = GL_RGBA
            else:
                format = GL_RGB
        type = GL_UNSIGNED_BYTE
        return pyglet.image.RawImage(pixels.tostring(), 
            width, height, format, type)

def get_decoders():
    return [PNGImageDecoder()]

def get_encoders():
    return []
