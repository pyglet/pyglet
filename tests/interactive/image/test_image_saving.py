from __future__ import division
from tests import mock

from pyglet.gl import *
from pyglet import image
from pyglet.image import codecs
from pyglet.window import *
from pyglet.window.event import *
from pyglet.compat import BytesIO

from tests.interactive.windowed_test_base import WindowedTestCase


class ImageSavingTestCase(WindowedTestCase):
    """Test saving of images using various encoders."""
    texture_file = None
    original_texture = None
    saved_texture = None
    show_checkerboard = True
    alpha = True
    has_exit = False
    encoder = None

    window_size = 800, 600

    def on_expose(self):
        self.draw()
        self.window.flip()

    def draw(self):
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

        self.draw_original()
        self.draw_saved()

    def draw_original(self):
        if self.original_texture:
            self.original_texture.blit(
                self.window.width // 4 - self.original_texture.width // 2,
                (self.window.height - self.original_texture.height) // 2, 
                0)

    def draw_saved(self):
        if self.saved_texture:
            self.saved_texture.blit(
                self.window.width * 3 // 4 - self.saved_texture.width // 2,
                (self.window.height - self.saved_texture.height) // 2, 
                0)

    def load_texture(self):
        if self.texture_file:
            self.texture_file = self.get_test_data_file('images', self.texture_file)
            self.original_texture = image.load(self.texture_file).texture

            file = BytesIO()
            self.original_texture.save(self.texture_file, file,
                                       encoder=self.encoder)
            file.seek(0)
            self.saved_texture = image.load(self.texture_file, file).texture

    def render(self):
        self.screen = image.get_buffer_manager().get_color_buffer()
        self.checkerboard = image.create(32, 32, image.CheckerImagePattern())

        self.load_texture()

        if self.alpha:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)


class TheImageSavingTestCase(ImageSavingTestCase):
    pass


def create_image_test_cases(name, description, encoder_class, image_files):
    for image_file in image_files:
        TheImageSavingTestCase.create_test_case(
                name='test_{}_{}'.format(name, image_file),
                description=description,
                question='Do you see the {} image twice on a checkerboard background?'.format(image_file),
                texture_file=image_file,
                encoder=encoder_class()
                )


# The test cases

# Saving using PIL
pil_description='Test saving using PIL. Reference image on the left and saved (and reloaded) image on the right.'
png_files = ['la.png', 'l.png', 'rgba.png', 'rgb.png']
from pyglet.image.codecs.pil import PILImageEncoder

create_image_test_cases(
        name='pil',
        description=pil_description,
        encoder_class=PILImageEncoder,
        image_files=png_files
        )

# Saving using PyPNG
pil_description='Test saving using PyPNG. Reference image on the left and saved (and reloaded) image on the right.'
png_files = ['la.png', 'l.png', 'rgba.png', 'rgb.png']
from pyglet.image.codecs.png import PNGImageEncoder

create_image_test_cases(
        name='pypng',
        description=pil_description,
        encoder_class=PNGImageEncoder,
        image_files=png_files
        )

# PIL not available, no encoder given
def _pil_raise_error(*args, **kwargs):
    raise codecs.ImageEncodeException()
TheImageSavingTestCase.create_test_case(
        name='test_no_pil_encoder',
        description='Test saving using PyPNG if no decoder is given, PIL is not available and PyPNG decoder is available.',
        question='Do you see the rgb.png image twice on a checkerboard background?',
        texture_file='rgb.png',
        decoder=None,
        decorators=[mock.patch('pyglet.image.codecs.pil.PILImageEncoder.encode', _pil_raise_error),
                    mock.patch('pyglet.image.codecs.get_encoders', lambda filename: [PILImageEncoder(), PNGImageEncoder()])]
        )

