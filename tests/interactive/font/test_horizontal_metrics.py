from pyglet.gl import *
from pyglet import font

from .font_test_base import FontTestBase


class HorizontalMetricsTestCase(FontTestBase):
    """Test that the horizontal font metrics are calculated correctly.

    Some text in various fonts will be displayed.  Green vertical lines mark
    the left edge of the text.  Blue vertical lines mark the right edge of the
    text.
    """

    window_size = 600, 300

    def render(self):
        font.add_file(self.get_test_data_file('fonts', 'action_man.ttf'))

        fnt1 = font.load('Action Man', 16)
        fnt2 = font.load('Arial', 16)
        fnt3 = font.load('Times New Roman', 16)

        h = fnt3.ascent - fnt3.descent + 10
        self.texts = [
            font.Text(fnt1, 'Action Man', 10, h * 1),
            font.Text(fnt1, 'Action Man longer test with more words', 10, h*2),
            font.Text(fnt2, 'Arial', 10, h * 3),
            font.Text(fnt2, 'Arial longer test with more words', 10, h*4),
            font.Text(fnt3, 'Times New Roman', 10, h * 5),
            font.Text(fnt3, 'Times New Roman longer test with more words', 
                      10, h*6),
        ]

    def draw(self):
        glPushAttrib(GL_CURRENT_BIT)

        for text in self.texts:
            text.draw()

            glBegin(GL_LINES)
            glColor3f(0, 1, 0)
            glVertex2f(text.x, text.y + text.font.descent)
            glVertex2f(text.x, text.y + text.font.ascent)
            glColor3f(0, 0, 1)
            glVertex2f(text.x + text.width, text.y + text.font.descent)
            glVertex2f(text.x + text.width, text.y + text.font.ascent)
            glEnd()
        glPopAttrib()

HorizontalMetricsTestCase.create_test_case(
        name='test_horizontal_metrics',
        question='A green line should mark the left edge of the text, a blue line the right edge.'
        )
