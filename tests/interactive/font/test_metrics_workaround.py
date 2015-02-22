from pyglet.gl import *
from pyglet import font

from .font_test_base import FontTestBase


class MetricsWorkaroundTestCase(FontTestBase):
    """
    Test workaround for font missing metrics.

    Font should fit between top and bottom lines.
    """

    window_size = 600, 100

    def render(self):
        font.add_file(self.get_test_data_file('fonts', 'courR12-ISO8859-1.pcf'))

        fnt = font.load('Courier', 16)

        h = fnt.ascent - fnt.descent + 10
        self.texts = [
            font.Text(fnt, 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz', 10, h * 1),
        ]

    def draw(self):
        glPushAttrib(GL_CURRENT_BIT)

        for text in self.texts:
            text.draw()

            glBegin(GL_LINES)
            glColor3f(0, 1, 0)
            glVertex2f(text.x, text.y + text.font.descent)
            glVertex2f(text.x + text.width, text.y + text.font.descent)
            glColor3f(0, 0, 1)
            glVertex2f(text.x, text.y + text.font.ascent)
            glVertex2f(text.x + text.width, text.y + text.font.ascent)
            glEnd()
        glPopAttrib()


MetricsWorkaroundTestCase.create_test_case(
        name='test_metrics_workaround',
        question='Does the font properly fit between the top and bottom horizontal lines?'
        )
