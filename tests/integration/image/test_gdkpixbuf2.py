from __future__ import absolute_import

import unittest

from ...base.data import PygletTestCase

try:
    from pyglet.image.codecs import gdkpixbuf2
except ImportError:
    gdkpixbuf2 = None


@unittest.skipIf(gdkpixbuf2 is None, 'GdkPixBuf not available')
class GdkPixBufTest(PygletTestCase):
    def test_load_image(self):
        filename = self.get_test_data_file('images', '8bpp.gif')
        with open(filename, 'rb') as f:
            loader = gdkpixbuf2.GdkPixBufLoader(f, filename)
            pixbuf = loader.get_pixbuf()
            assert pixbuf is not None
            assert pixbuf.height == 257
            assert pixbuf.width == 235
            assert pixbuf.channels == 4
            assert pixbuf.has_alpha
            image = pixbuf.to_image()
            assert image is not None
            assert image.height == 257
            assert image.width == 235

    def test_load_image_requires_loader_close(self):
        """Some image files require the loader to be closed to force it
        to read and parse all data."""
        filename = self.get_test_data_file('images', 'gdk_close.png')
        with open(filename, 'rb') as f:
            loader = gdkpixbuf2.GdkPixBufLoader(f, filename)
            pixbuf = loader.get_pixbuf()
            assert pixbuf is not None
            assert pixbuf.height == 200
            assert pixbuf.width == 200
            assert pixbuf.channels == 4
            assert pixbuf.has_alpha
            image = pixbuf.to_image()
            assert image is not None
            assert image.height == 200
            assert image.width == 200

    def test_load_animation(self):
        filename = self.get_test_data_file('images', 'dinosaur.gif')
        with open(filename, 'rb') as f:
            loader = gdkpixbuf2.GdkPixBufLoader(f, filename)
            gdk_anim = loader.get_animation()
            assert gdk_anim is not None
            anim = gdk_anim.to_animation()
            assert anim is not None
            assert len(anim.frames) == 12
            for frame in anim.frames:
                assert frame.image is not None
                assert frame.duration is not None
                assert frame.duration == 0.1
                assert frame.image.width == 129
                assert frame.image.height == 79

    def test_incomplete_load(self):
        """Start loading a file and stop. Should clean up correctly."""
        filename = self.get_test_data_file('images', 'gdk_close.png')
        with open(filename, 'rb') as f:
            loader = gdkpixbuf2.GdkPixBufLoader(f, filename)
            del loader
