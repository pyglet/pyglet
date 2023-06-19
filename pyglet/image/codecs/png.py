"""Encoder and decoder for PNG files, using PyPNG (png.py).
"""

import array
import itertools

from pyglet.image import ImageData, ImageDecodeException
from pyglet.image.codecs import ImageDecoder, ImageEncoder

import pyglet.extlibs.png as pypng


class PNGImageDecoder(ImageDecoder):
    def get_file_extensions(self):
        return ['.png']

    def decode(self, filename, file):
        if not file:
            file = open(filename, 'rb')

        try:
            reader = pypng.Reader(file=file)
            width, height, pixels, metadata = reader.asDirect()
        except Exception as e:
            raise ImageDecodeException('PyPNG cannot read %r: %s' % (filename or file, e))

        if metadata['greyscale']:
            if metadata['alpha']:
                fmt = 'LA'
            else:
                fmt = 'L'
        else:
            if metadata['alpha']:
                fmt = 'RGBA'
            else:
                fmt = 'RGB'
        pitch = len(fmt) * width

        pixels = array.array('BH'[metadata['bitdepth'] > 8], itertools.chain(*pixels))
        return ImageData(width, height, fmt, pixels.tobytes(), -pitch)


class PNGImageEncoder(ImageEncoder):
    def get_file_extensions(self):
        return ['.png']

    def encode(self, image, filename, file):
        image = image.get_image_data()

        has_alpha = 'A' in image.format
        greyscale = len(image.format) < 3
        if has_alpha:
            if greyscale:
                image.format = 'LA'
            else:
                image.format = 'RGBA'
        else:
            if greyscale:
                image.format = 'L'
            else:
                image.format = 'RGB'

        image.pitch = -(image.width * len(image.format))

        writer = pypng.Writer(image.width, image.height, greyscale=greyscale, alpha=has_alpha)

        data = array.array('B')
        data.frombytes(image.get_data(image.format, image.pitch))

        writer.write_array(file, data)


def get_decoders():
    return [PNGImageDecoder()]


def get_encoders():
    return [PNGImageEncoder()]
