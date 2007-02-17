#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import os.path

from pyglet.gl import *
from pyglet.image import *
from pyglet.image.codecs import *

import Image

class PILImageDecoder(ImageDecoder):
    def get_file_extensions(self):
        # Only most common ones shown here
        return ['.bmp', '.cur', '.gif', '.ico', '.jpg', '.jpeg', '.pcx', '.png',
                '.tga', '.tif', '.tiff', '.xbm', '.xpm']

    def decode(self, file, filename):
        try:
            image = Image.open(file)
        except Exception, e:
            raise ImageDecodeException(
                'PIL cannot read %r: %s' % (filename or file, e))

        image = image.transpose(Image.FLIP_TOP_BOTTOM)

        # Convert bitmap and palette images to component
        if image.mode in ('1', 'P'):
            image = image.convert()

        if image.mode not in ('L', 'LA', 'RGB', 'RGBA'):
            raise ImageDecodeException('Unsupported mode "%s"' % image.mode)
        type = GL_UNSIGNED_BYTE
        width, height = image.size

        return ImageData(width, height, image.mode, image.tostring())

class PILImageEncoder(ImageEncoder):
    def get_file_extensions(self):
        # Most common only
        return ['.bmp', '.eps', '.gif', '.jpg', '.jpeg',
                '.pcx', '.png', '.ppm', '.tiff', '.xbm']

    def encode(self, image, file, filename):
        # File format is guessed from filename extension, otherwise defaults
        # to PNG.
        format = (filename and os.path.splitext(filename)[1][1:]) or 'png'

        if format.lower() == 'jpg':
            format = 'JPEG'

        image = image.image_data
        image.pitch = -(image.width * len(image.format))

        # Only save in RGB or RGBA formats.
        if image.format != 'RGB':
            image.format = 'RGBA'

        # Note: Don't try and use frombuffer(..); different versions of
        # PIL will orient the image differently.
        pil_image = Image.fromstring(
            image.format, (image.width, image.height), image.data)

        try:
            pil_image.save(file, format)
        except Exception, e:
            raise ImageEncodeException(e)

def get_decoders():
    return [PILImageDecoder()]

def get_encoders():
    return [PILImageEncoder()]
