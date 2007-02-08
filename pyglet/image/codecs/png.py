#!/usr/bin/env python

'''Encoder and decoder for PNG files, using PyPNG (pypng.py).
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import array

from pyglet.GL.future import *
from pyglet.image import *
from pyglet.image.codecs import *

import pyglet.image.codecs.pypng

class PNGImageDecoder(ImageDecoder):
    def get_file_extensions(self):
        return ['.png']

    def decode(self, file, filename):
        try:
            reader = pyglet.image.codecs.pypng.Reader(file=file)
            width, height, pixels, metadata = reader.read()
        except Exception, e:
            raise ImageDecodeException(
                'PyPNG cannot read %r: %s' % (filename or file, e))

        if metadata['greyscale']:
            if metadata['has_alpha']:
                format = 'LA'
            else:
                format = 'L'
        else:
            if metadata['has_alpha']:
                format = 'RGBA'
            else:
                format = 'RGB'
        type = GL_UNSIGNED_BYTE
        return RawImage(pixels.tostring(), width, height, format, type,
            top_to_bottom=True)

class PNGImageEncoder(ImageEncoder):
    def get_file_extensions(self):
        return ['.png']

    def encode(self, image, file, filename, options):
        image = image.get_raw_image()
        if image.type != GL_UNSIGNED_BYTE:
            raise ImageEncodeException('Unsupported sample type')

        has_alpha = 'A' in image.format
        greyscale = len(image.format) < 3
        if has_alpha:
            if greyscale:
                image.set_format('LA')
            else:
                image.set_format('RGBA')
        else:
            if greyscale:
                image.set_format('L')
            else:
                image.set_format('RGB')

        if not image.top_to_bottom:
            image.swap_rows()

        writer = pyglet.image.codecs.pypng.Writer(
            image.width, image.height,
            bytes_per_sample=1,
            greyscale=greyscale,
            has_alpha=has_alpha)

        data = array.array('B')
        data.fromstring(image.data)
        writer.write_array(file, data)

def get_decoders():
    return [PNGImageDecoder()]

def get_encoders():
    return [PNGImageEncoder()]
