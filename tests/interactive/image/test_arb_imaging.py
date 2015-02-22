import unittest

from pyglet.gl import gl_info

from .test_image_loading import ImageLoadingTestCase

class ARBImagingTestCase(ImageLoadingTestCase):
    """Test rearrangement of color components using the OpenGL color matrix.
    The test will be skipped if the GL_ARB_imaging extension is not present.
    """
    question = "You should see the RGB test image correctly rendered."

    def load_image(self):
        # Load image as usual then rearrange components
        super(ARBImagingTestCase, self).load_image()
        self.image.format = 'GRB'
        pixels = self.image.data # forces conversion


ARBImagingTestCase.create_test_case(
        name='test_arb_rgb',
        texture_file='rgb.png',
        decorators=[unittest.skipIf(not gl_info.have_extension('GL_ARB_imaging'),
                                    'GL_ARB_imaging extension not available')]
        )

ARBImagingTestCase.create_test_case(
        name='test_arb_rgba',
        texture_file='rgba.png',
        decorators=[unittest.skipIf(not gl_info.have_extension('GL_ARB_imaging'),
                                    'GL_ARB_imaging extension not available')]
        )

