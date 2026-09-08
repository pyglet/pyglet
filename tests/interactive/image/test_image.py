from io import BytesIO
import pytest

import pyglet
from pyglet import image, shapes
from pyglet.graphics.api.gl import texture
from pyglet.graphics.api import gl

from ...annotations import Platform, require_platform, require_gl_extension
from ...base.event_loop import EventLoopFixture


class ImageTestFixture(EventLoopFixture):
    COLOR_A = (128, 128, 128)   # light square
    COLOR_B = (60, 60, 60)      # dark square

    def __init__(self, request, test_data):
        super().__init__(request)
        self.test_data = test_data

        self.show_checkerboard = True
        self.show_text = True

        self.batch = None
        self.checkboard = None

        self.left_sprite = None
        self.right_sprite = None
        self.left_texture = None
        self.right_texture = None

        self.triangle = None

    def create_window(self, **kwargs):
        super().create_window(**kwargs)

        self.batch = pyglet.graphics.Batch()

        self.checkboard = self._create_checkerboard()

        self.triangle = self._create_triangle(200, 200)
        self.triangle.visible = False

    def _create_checkerboard(self, size=32):
        rects = []

        cell_size = min(self.window.width / size, self.window.height / size)

        for r in range(round(self.window.height / cell_size)):
            for c in range(round(self.window.width / cell_size)):
                x = c * cell_size
                y = r * cell_size
                is_dark = (r + c) % 2 == 1
                color = self.COLOR_B if is_dark else self.COLOR_A
                rects.append(shapes.Rectangle(x, y, cell_size, cell_size, color=color, batch=self.batch))

        return rects

    @property
    def show_triangle_left(self):
        if self.triangle:
            return False

        return self.triangle.visible

    @show_triangle_left.setter
    def show_triangle_left(self, value):
        if self.triangle:
            self.triangle.visible = value

    def _create_triangle(self, w, h):
        x = self.window.width // 4 - w // 2
        y = (self.window.height - h) // 2
        return shapes.Triangle(x, y, x+w, y, x, y + h, color=(255, 0, 0), batch=self.batch)

    def on_draw(self):
        self.clear()

        self.batch.draw()

        if self.show_text:
            self.draw_text()

    def load_left(self, image_file, decoder=None):
        self.left_texture = image.load(image_file, decoder=decoder).get_texture()
        self.left_sprite = pyglet.sprite.Sprite(self.left_texture,
                                                x=self.window.width // 4 - self.left_texture.width // 2,
                                                y=(self.window.height - self.left_texture.height) // 2,
                                                batch=self.batch)


    def copy_left_to_right(self, encoder=None):
        buf = BytesIO()
        self.left_texture.save("file.png",
                               buf,
                               encoder=encoder)
        buf.seek(0)
        self.right_texture = image.load("file.png", buf).get_texture()

    def enable_alpha(self):
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

    def load_right_arb(self, image_file, pixel_format):
        img = image.load(image_file)
        img.format = pixel_format
        img.get_bytes()  # forces conversion
        self.right_texture = img.get_texture()

    def copy_color_buffer(self):
        image = pyglet.graphics.api.gl.framebuffer.get_screenshot()
        self.right_texture = image.get_texture()
        self._set_right_sprite()

    def _set_right_sprite(self) -> None:
        x = self.window.width * 3 // 4 - self.right_texture.width // 2
        x = max((x, self.window.width // 2))
        y = (self.window.height - self.right_texture.height) // 2
        self.right_sprite = pyglet.sprite.Sprite(self.right_texture,
                                                x=x,
                                                y=y,
                                                batch=self.batch)
    def save_and_load_color_buffer(self):
        stream = BytesIO()
        img = pyglet.graphics.api.gl.framebuffer.get_screenshot()
        img.save('buffer.png', stream)
        stream.seek(0)
        self.right_texture = image.load('buffer.png', stream)
        self._set_right_sprite()

    def save_and_load_depth_buffer(self):
        stream = BytesIO()
        img = pyglet.graphics.api.gl.framebuffer.get_screenshot()
        img.save('buffer.png', stream)
        stream.seek(0)
        self.right_texture = image.load('buffer.png', stream)
        self._set_right_sprite()


    def test_image_loading(self, decoder, image_name):
        """Test loading images."""
        self.create_window(width=800, height=600)
        self.load_left(self.test_data.get_file("images", image_name), decoder)
        self.enable_alpha()
        self.ask_question(
                "Do you see the {} image on a checkerboard background?".format(image_name)
                )

    def test_image_saving(self, encoder, image_name):
        """Test saving images."""
        self.create_window(width=800, height=600)
        self.load_left(self.test_data.get_file("images", image_name))
        self.copy_left_to_right(encoder)
        self.enable_alpha()
        self.ask_question(
                "Do you see the {} image twice on a checkerboard background?".format(image_name)
                )

@pytest.fixture
def image_test(request, test_data):
    return ImageTestFixture(request, test_data)


bmp_images = ['rgb_16bpp.bmp', 'rgb_1bpp.bmp', 'rgb_24bpp.bmp', 'rgb_32bpp.bmp', 'rgb_4bpp.bmp',
              'rgb_8bpp.bmp', 'rgba_32bpp.bmp']
dds_images = ['rgba_bc7.dds', 'rgb_bc6s.dds', 'rgba_dxt1.dds', 'rgba_dxt3.dds', 'rgba_dxt5.dds', 'rgb_dxt1.dds']
png_images = ['la.png', 'l.png', 'rgba.png', 'rgb.png']
ktx2_images = ['rgba_bc7.ktx2']
pypng_images = png_images + ['rgb_8bpp.png', 'rgb_8bpp_trans.png']
gif_images = ['8bpp.gif']


@pytest.mark.parametrize('image_name', bmp_images)
def test_bmp_loading(image_test, image_name):
    """Test loading BMP images."""
    from pyglet.image.codecs.bmp import BMPImageDecoder
    image_test.test_image_loading(BMPImageDecoder(), image_name)


@pytest.mark.parametrize('image_name', dds_images)
def test_dds_loading(image_test, image_name):
    """Test loading DDS images."""
    from pyglet.image.codecs.dds import DDSImageDecoder
    image_test.test_image_loading(DDSImageDecoder(), image_name)

@pytest.mark.parametrize('image_name', ktx2_images)
def test_ktx2_loading(image_test, image_name):
    """Test loading KTX2 images."""
    from pyglet.image.codecs.ktx2 import KTX2ImageDecoder
    image_test.test_image_loading(KTX2ImageDecoder(), image_name)


@pytest.mark.parametrize('image_name', png_images)
def test_pil_loading(image_test, image_name):
    """Test loading PNG images using PIL"""
    try:
        from PIL import Image
    except ImportError:
        pytest.skip('PIL not available')
    from pyglet.image.codecs.pil import PILImageDecoder
    image_test.test_image_loading(PILImageDecoder(), image_name)


@pytest.mark.parametrize('image_name', png_images + gif_images)
@require_platform(Platform.LINUX)
def test_gdkpixbuf2_loading(image_test, image_name):
    """Test loading PNG images using Linux specific GdkPixbuf2."""
    from pyglet.image.codecs.gdkpixbuf2 import GdkPixbuf2ImageDecoder
    image_test.test_image_loading(GdkPixbuf2ImageDecoder(), image_name)


@pytest.mark.parametrize('image_name', png_images)
@require_platform(Platform.WINDOWS)
def test_gdiplus_loading(image_test, image_name):
    """Test loading PNG images using Windows specific GDI+."""
    from pyglet.image.codecs.gdiplus import GDIPlusDecoder
    image_test.test_image_loading(GDIPlusDecoder(), image_name)


@pytest.mark.parametrize('image_name', png_images + bmp_images)
@require_platform(Platform.WINDOWS)
def test_wic_loading(image_test, image_name):
    """Test loading PNG images using Windows specific GDI+."""
    from pyglet.image.codecs.wic import WICDecoder
    image_test.test_image_loading(WICDecoder(), image_name)


@pytest.mark.parametrize('image_name', png_images)
@require_platform(Platform.OSX)
def test_quartz_loading(image_test, image_name):
    """Test loading PNG images using OSX specific Quartz."""
    from pyglet.image.codecs.quartz import QuartzImageDecoder
    image_test.test_image_loading(QuartzImageDecoder(), image_name)


@pytest.mark.parametrize('image_name', pypng_images)
def test_pypng_loading(image_test, image_name):
    """Test loading PNG images using PyPNG."""
    from pyglet.image.codecs.png import PNGImageDecoder
    image_test.test_image_loading(PNGImageDecoder(), image_name)


@pytest.mark.parametrize('image_name', png_images)
def test_pil_saving(image_test, image_name):
    """Test saving images using PIL."""
    try:
        from PIL import Image
    except ImportError:
        pytest.skip('PIL not available')
    from pyglet.image.codecs.pil import PILImageEncoder
    image_test.test_image_saving(PILImageEncoder(), image_name)


@pytest.mark.parametrize('image_name', png_images)
def test_pypng_saving(image_test, image_name):
    """Test saving images using PyPNG."""
    from pyglet.image.codecs.png import PNGImageEncoder
    image_test.test_image_saving(PNGImageEncoder(), image_name)


@pytest.mark.parametrize('image_name', ['rgb.png', 'rgba.png'])
@require_gl_extension('GL_ARB_imaging')
def test_arb(image_test, image_name):
    """Test swapping color channels using the ARB imaging extension."""
    image_test.create_window()
    image_test.load_left(image_test.test_data.get_file('images', image_name))
    image_test.load_right_arb(image_test.test_data.get_file('images', image_name), 'GRB')
    image_test.ask_question(
            "In the right image red and green should be swapped."
            )


def test_buffer_copy(image_test):
    """Test colour buffer copy to texture.

    A scene consisting of a single coloured triangle will be rendered.  The
    colour buffer will then be saved to a stream and loaded as a texture.

    You might see the original scene first shortly before the
    buffer image appears (because retrieving and saving the image is a slow
    operation).
    """
    image_test.create_window(width=800, height=600)
    image_test.show_triangle_left = True
    image_test.show_text = False
    image_test.show_checkerboard = False

    def step(dt):
        image_test.copy_color_buffer()
        image_test.show_text = True
        return True
    image_test.schedule_once(step)

    image_test.ask_question(
            'You should see the same coloured triangle left and right.'
            )

def test_buffer_saving(image_test):
    """Test colour buffer save.

    A scene consisting of a single coloured triangle will be rendered.  The
    colour buffer will then be saved to a stream and loaded as a texture.

    You might see the original scene first shortly before the
    buffer image appears (because retrieving and saving the image is a slow
    operation).
    """
    image_test.create_window(width=800, height=600)
    image_test.show_triangle_left = True
    image_test.show_text = False
    image_test.show_checkerboard = False

    def step(dt):
        image_test.save_and_load_color_buffer()
        image_test.show_text = True
        return True
    image_test.schedule_once(step)

    image_test.ask_question(
            'You should see the same coloured triangle left and right.'
            )

def test_depth_buffer_saving(image_test):
    """Test depth buffer save.

    A scene consisting of a single coloured triangle will be rendered.  The
    depth buffer will then be saved to a stream and loaded as a texture.

    You might see the original scene first for up to several seconds before the
    depth buffer image appears (because retrieving and saving the image is
    a slow operation).
    """
    image_test.create_window(width=800, height=600)
    image_test.show_triangle_left = True
    image_test.show_text = False
    image_test.show_checkerboard = False

    def step(dt):
        image_test.save_and_load_depth_buffer()
        image_test.show_text = True
        return True
    image_test.schedule_once(step)

    image_test.ask_question(
            'You should see a coloured triangle left and its depth buffer right. '
            'The bottom-left corner is lightest, the bottom-right is darker and '
            'the top corner is darkest (corresponding the depth of the triangle.'
            )

