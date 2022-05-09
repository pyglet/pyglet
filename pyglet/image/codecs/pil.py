# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# Copyright (c) 2008-2022 pyglet contributors
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

import os.path

from pyglet.image import *
from pyglet.image.codecs import *

from PIL import Image


class PILImageDecoder(ImageDecoder):
    def get_file_extensions(self):
        # Only most common ones shown here
        return ['.bmp', '.cur', '.gif', '.ico', '.jpg', '.jpeg', '.pcx', '.png',
                '.tga', '.tif', '.tiff', '.xbm', '.xpm']

    # def get_animation_file_extensions(self):
    #     return ['.gif', '.ani']

    def decode(self, filename, file):
        if not file:
            file = open(filename, 'rb')

        try:
            image = Image.open(file)
        except Exception as e:
            raise ImageDecodeException('PIL cannot read %r: %s' % (filename or file, e))

        try:
            image = image.transpose(Image.FLIP_TOP_BOTTOM)
        except Exception as e:
            raise ImageDecodeException('PIL failed to transpose %r: %s' % (filename or file, e))

        # Convert bitmap and palette images to component
        if image.mode in ('1', 'P'):
            image = image.convert()

        if image.mode not in ('L', 'LA', 'RGB', 'RGBA'):
            raise ImageDecodeException('Unsupported mode "%s"' % image.mode)
        width, height = image.size

        return ImageData(width, height, image.mode, image.tobytes())


class PILImageEncoder(ImageEncoder):
    def get_file_extensions(self):
        # Most common only
        return ['.bmp', '.eps', '.gif', '.jpg', '.jpeg',
                '.pcx', '.png', '.ppm', '.tiff', '.xbm']

    def encode(self, image, filename, file):
        # File format is guessed from filename extension, otherwise defaults to PNG.
        pil_format = (filename and os.path.splitext(filename)[1][1:]) or 'png'

        if pil_format.lower() == 'jpg':
            pil_format = 'JPEG'

        image = image.get_image_data()
        fmt = image.format
        if fmt != 'RGB':
            # Only save in RGB or RGBA formats.
            fmt = 'RGBA'
        pitch = -(image.width * len(fmt))

        # fromstring is deprecated, replaced by frombytes in Pillow (PIL fork)
        # (1.1.7) PIL still uses it
        try:
            image_from_fn = getattr(Image, "frombytes")
        except AttributeError:
            image_from_fn = getattr(Image, "fromstring")
        pil_image = image_from_fn(fmt, (image.width, image.height), image.get_data(fmt, pitch))

        try:
            pil_image.save(file, pil_format)
        except Exception as e:
            raise ImageEncodeException(e)


def get_decoders():
    return [PILImageDecoder()]


def get_encoders():
    return [PILImageEncoder()]
