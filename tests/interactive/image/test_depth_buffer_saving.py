from test_image_saving import ImageSavingTestCase

from pyglet.gl import *
from pyglet import image
from pyglet.compat import BytesIO


class DepthBufferSavingTestCase(ImageSavingTestCase):
    """Test depth buffer save.

    A scene consisting of a single coloured triangle will be rendered.  The
    depth buffer will then be saved to a stream and loaded as a texture.

    You will see the original scene first for up to several seconds before the
    depth buffer image appears (because retrieving and saving the image is
    a slow operation).  Messages will be printed to stdout indicating
    what stage is occuring.
    """

    alpha = False
    show_checkerboard = False

    def draw_original(self):
        print('Drawing scene...')
        glClear(GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)

        glBegin(GL_TRIANGLES)
        glColor4f(1, 0, 0, 1)
        glVertex3f(0, 0, -1)
        glColor4f(0, 1, 0, 1)
        glVertex3f(200, 0, 0)
        glColor4f(0, 0, 1, 1)
        glVertex3f(0, 200, 1)
        glEnd()

        glDisable(GL_DEPTH_TEST)
        glColor4f(1, 1, 1, 1)

        if not self.saved_texture:
            print('Saving depth image...')
            img = image.get_buffer_manager().get_depth_buffer()
            file = BytesIO()
            img.save('buffer.png', file)

            print('Loading depth image as texture...')
            file.seek(0)
            self.saved_texture = image.load('buffer.png', file)

        print('Done.')

DepthBufferSavingTestCase.create_test_case(
        name='test_save_depth_buffer',
        question='Do you see a coloured triangle and the copy of its depth buffer?'
        )

