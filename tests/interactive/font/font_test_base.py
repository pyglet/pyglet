"""
Interactive tests for pyglet.font
"""

from pyglet import gl
from pyglet import font

from tests.interactive.windowed_test_base import WindowedTestCase

class FontTestBase(WindowedTestCase):
    """
    Default test implementation. Use by creating a subclass and then calling the
    `create_test_case` class method with the name of the test case and any class/instance
    variables to set. This should be called outside the class definition!
    """

    # Defaults
    font_name = ''
    font_size = 24
    text = 'Quickly brown fox'
    color = 1, 1, 1, 1

    def on_expose(self):
        gl.glClearColor(0.5, 0, 0, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glLoadIdentity()
        self.draw()
        self.window.flip()

    def render(self):
        fnt = font.load(self.font_name, self.font_size) 
        self.label = font.Text(fnt, self.text, 10, 10, color=self.color)

    def draw(self):
        self.label.draw()

