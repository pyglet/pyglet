from pyglet.gl import *
from pyglet import image
from pyglet.window import *
from pyglet.window.event import *

from tests.interactive.windowed_test_base import WindowedTestCase


class CheckerboardTestCase(WindowedTestCase):
    '''Test that the checkerboard pattern looks correct.

    One window will open, it should show one instance of the checkerboard
    pattern in two levels of grey.
    '''

    def on_expose(self):
        glClearColor(1, 1, 1, 1)
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
        self.texture.blit(0, 0, 0)
        self.window.flip()

    def render(self):
        self.texture = image.create(32, 32, image.CheckerImagePattern()).texture


CheckerboardTestCase.create_test_case(
        name='test_checkerboard',
        question='Do you see one instance of the checkerboard pattern in two levels of grey?'
        )
