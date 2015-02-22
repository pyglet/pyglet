import mock

import pyglet
from pyglet.gl import *
from pyglet import image
from pyglet.image import codecs

from tests.annotations import Platform, require_platform
from tests.interactive.windowed_test_base import WindowedTestCase

class ImageLoadingTestCase(WindowedTestCase):
    """Test loading of images using various decoders."""
    texture_file = None
    image = None
    texture = None
    show_checkerboard = True
    alpha = True
    decoder = None

    window_size = 800, 600

    def on_expose(self):
        glClearColor(1, 1, 1, 1)
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
        if self.show_checkerboard:
            glPushMatrix()
            glScalef(self.window.width/float(self.checkerboard.width),
                     self.window.height/float(self.checkerboard.height),
                     1.)
            glMatrixMode(GL_TEXTURE)
            glPushMatrix()
            glScalef(self.window.width/float(self.checkerboard.width),
                     self.window.height/float(self.checkerboard.height),
                     1.)
            glMatrixMode(GL_MODELVIEW)
            self.checkerboard.blit(0, 0, 0)
            glMatrixMode(GL_TEXTURE)
            glPopMatrix()
            glMatrixMode(GL_MODELVIEW)
            glPopMatrix()

        if self.texture:
            glPushMatrix()
            glTranslatef((self.window.width - self.texture.width) / 2,
                         (self.window.height - self.texture.height) / 2,
                         0)
            self.texture.blit(0, 0, 0)
            glPopMatrix()
        self.window.flip()

    def load_image(self):
        if self.texture_file:
            self.texture_file = self.get_test_data_file('images', self.texture_file)
            self.image = image.load(self.texture_file, decoder=self.decoder)

    def render(self):

        self.screen = image.get_buffer_manager().get_color_buffer()
        self.checkerboard = image.create(32, 32, image.CheckerImagePattern())

        self.load_image()
        if self.image:
            self.texture = self.image.texture

        if self.alpha:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)


class TheImageLoadingTestCase(ImageLoadingTestCase):
    pass

def create_image_test_cases(name, description, decoder_class, image_files):
    for image_file in image_files:
        TheImageLoadingTestCase.create_test_case(
                name='test_{}_{}'.format(name, image_file),
                description=description,
                question='Do you see the {} image on a checkerboard background?'.format(image_file),
                texture_file=image_file,
                decoder=decoder_class()
                )


# The test cases

# BMP loading
bmp_description = "Test load using the Python BMP loader."
from pyglet.image.codecs.bmp import BMPImageDecoder
bmp_images = ['rgb_16bpp.bmp', 'rgb_1bpp.bmp', 'rgb_24bpp.bmp', 'rgb_32bpp.bmp', 'rgb_4bpp.bmp',
              'rgb_8bpp.bmp', 'rgba_32bpp.bmp']

create_image_test_cases(
        name='bmp',
        description=bmp_description,
        decoder_class=BMPImageDecoder,
        image_files=bmp_images
        )


# DDS loading
dds_description = "Test loading from a DDS file."
from pyglet.image.codecs.dds import DDSImageDecoder
dds_images = ['rgba_dxt1.dds', 'rgba_dxt3.dds', 'rgba_dxt5.dds', 'rgb_dxt1.dds']

create_image_test_cases(
        name='dds',
        description=dds_description,
        decoder_class=DDSImageDecoder,
        image_files=dds_images
        )


# PIL
pil_description = 'Test loading using PIL.'
from pyglet.image.codecs.pil import PILImageDecoder
png_images = ['la.png', 'l.png', 'rgba.png', 'rgb.png']

create_image_test_cases(
        name='pil',
        description=pil_description,
        decoder_class=PILImageDecoder,
        image_files=png_images
        )


# Platform specific decoders
platform_description = 'Test loading using the platform decoder (QuickTime, Quartz, GDI+ or Gdk)'

if pyglet.compat_platform in Platform.LINUX:
    from pyglet.image.codecs.gdkpixbuf2 import GdkPixbuf2ImageDecoder as platform_decoder_class
elif pyglet.compat_platform in Platform.WINDOWS:
    from pyglet.image.codecs.gdiplus import GDIPlusDecoder as platform_decoder_class
elif pyglet.compat_platform in Platform.OSX:
    if pyglet.options['darwin_cocoa']:
        from pyglet.image.codecs.quartz import QuartzImageDecoder as platform_decoder_class
    else:
        from pyglet.image.codecs.quicktime import QuickTimeDecoder as platform_decoder_class
else:
    platform_decoder_class = None

if platform_decoder_class:
    create_image_test_cases(
            name='platform',
            description=platform_description,
            decoder_class=platform_decoder_class,
            image_files=png_images
            )


# PyPNG decoder
pypng_description = 'Test loading images using PyPNG'
from pyglet.image.codecs.png import PNGImageDecoder
pypng_images = png_images + ['rgb_8bpp.png', 'rgb_8bpp_trans.png']

create_image_test_cases(
        name='pypng',
        description=pypng_description,
        decoder_class=PNGImageDecoder,
        image_files=png_images
        )


# No decoder given
def _pil_raise_error(obj, param):
    raise Exception()
TheImageLoadingTestCase.create_test_case(
        name='test_no_decoder',
        description='Test loading using PIL if no decoder is given, PIL is not available and PyPNG decoder is available.',
        question='Do you see the rgb.png image on a checkerboard background?',
        texture_file='rgb.png',
        decoder=None,
        decorators=[mock.patch('pyglet.image.codecs.pil.Image.Image.transpose', _pil_raise_error),
                    mock.patch('pyglet.image.codecs.get_decoders', lambda filename: [PILImageDecoder(), PNGImageDecoder()])]
        )


# GIF, only available on Linux
TheImageLoadingTestCase.create_test_case(
        name='test_gif',
        description='Test loading using the Python gdkpixbuf2 GIF loader.',
        question='Do you see the 8bpp.gif image on a checkerboard background?',
        texture_file='8bpp.gif',
        decoder=None,
        decorators=[require_platform(Platform.LINUX)]
        )


