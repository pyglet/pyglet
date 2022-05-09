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

"""Encoder and decoder for the QOI image format.
"""

from ctypes import Structure, BigEndianStructure
from ctypes import c_uint8, c_uint32, c_char

from pyglet.image import ImageData, ImageDecodeException
from pyglet.image.codecs import ImageDecoder, ImageEncoder


class Header(BigEndianStructure):
    _pack_ = 1
    _fields_ = (
        ('magic', c_char * 4),      # char magic[4];       // magic bytes "qoif"
        ('width', c_uint32),        # uint32_t width;      // image width in pixels (BE)
        ('height', c_uint32),       # uint32_t height;     // image height in pixels (BE)
        ('channels', c_uint8),      # uint8_t channels;    // 3 = RGB, 4 = RGBA
        ('colorspace', c_uint8)     # uint8_t colorspace;  // 0 = sRGB with linear alpha, 1 = all channels linear
    )


class QOImageDecoder(ImageDecoder):
    def get_file_extensions(self):
        return ['.qoi']

    def decode(self, filename, file):
        if not file:
            file = open(filename, 'rb')

        header = Header()
        file.readinto(header)

        if header.magic != b'qoif':
            raise ImageDecodeException('Invalid QOI header.')

        # TODO: finish

        # pixels = array.array('BH'[metadata['bitdepth'] > 8], itertools.chain(*pixels))
        # return ImageData(width, height, fmt, pixels.tobytes(), -pitch)


class QOImageEncoder(ImageEncoder):
    def get_file_extensions(self):
        return ['.qoi']

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
        # TODO: finish


def get_decoders():
    return [QOImageDecoder()]


def get_encoders():
    return [QOImageEncoder()]
