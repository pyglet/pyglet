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
        return ['.png']

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
        return RawImage(pixels.tostring(), width, height, format, type,
            swap_rows=True)

class PNGImageEncoder(ImageEncoder):
    def get_file_extensions(self):
        return ['.png']

    def encode(self, image, file, filename, options):
        format = image.format
        type = GL_UNSIGNED_BYTE

        image = image.read(format, type)
        components = image.get_format_components(image.format)
        bytes_per_sample = 1
        has_alpha = image.format in (GL_RGBA, GL_LUMINANCE_ALPHA)

        writer = pyglet.image.codecs.pypng.Writer(
            image.width, image.height,
            bytes_per_sample=bytes_per_sample,
            has_alpha=has_alpha)
        print image.data
        writer.write_array(file, list(image.data))

def get_decoders():
    return [PNGImageDecoder()]

def get_encoders():
    return [PNGImageEncoder()]
