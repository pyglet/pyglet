#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import os.path

from pyglet.GL.VERSION_1_1 import *
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

        if image.mode not in ('L', 'RGB', 'RGBA'):
            raise ImageDecodeException('Unsupported mode "%s"' % image.mode)
        type = GL_UNSIGNED_BYTE
        width, height = image.size

        return RawImage(image.tostring(), width, height, image.mode, type)

class PILImageEncoder(ImageEncoder):
    def get_file_extensions(self):
        # Most common only
        return ['.bmp', '.eps', '.gif', '.jpg', '.jpeg',
                '.pcx', '.png', '.ppm', '.tiff', '.xbm']

    def encode(self, image, file, filename, options={}):
        # Format can be given in options dict, otherwise extracted
        # from filename extension.  Defaults to PNG if no filename or format
        # given.
        format = options.get('format', 
            filename and os.path.splitext(filename)[1][1:]) or 'png'

        if format.lower() == 'jpg':
            format = 'JPEG'

        image = image.get_raw_image()
        if image.type != GL_UNSIGNED_BYTE:
            raise ImageEncodeException('Unsupported sample type')

        if len(image.format) == 2:
            image.set_format('RGBA')
        elif len(image.format) == 3:
            image.set_format('RGB')
        elif len(image.format) == 4:
            image.set_format('RGBA')

        # Note: Don't try and use frombuffer(..); different versions of
        # PIL will orient the image differently.
        pil_image = Image.fromstring(
            image.format, (image.width, image.height), image.data)

        if not image.top_to_bottom:
            pil_image = pil_image.transpose(Image.FLIP_TOP_BOTTOM)

        try:
            pil_image.save(file, format, **options)
        except Exception, e:
            raise ImageEncodeException(e)

def get_decoders():
    return [PILImageDecoder()]

def get_encoders():
    return [PILImageEncoder()]
