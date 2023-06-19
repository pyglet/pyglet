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
