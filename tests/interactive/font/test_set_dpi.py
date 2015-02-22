from pyglet.gl import *
from pyglet import font

from .font_test_base import FontTestBase


class SetDPITestCase(FontTestBase):
    """Test that a specific DPI can be set to render the text with.

    Some text in Action Man font will be displayed.  A green box should exactly
    bound the top and bottom of the text.
    """

    font_name = 'Action Man'

    def render(self):
        font.add_file(self.get_test_data_file('fonts', 'action_man.ttf'))

        # Hard-code 16-pt at 100 DPI, and hard-code the pixel coordinates
        # we see that font at when DPI-specified rendering is correct.
        fnt = font.load('Action Man', 16, dpi=120)

        self.text = font.Text(fnt, 'The DPI is 120', 10, 10)

    def draw(self):
        self.text.draw()

        x1 = self.text.x
        x2 = self.text.x + self.text.width
        y1 = 9
        y2 = 27

        glPushAttrib(GL_CURRENT_BIT)
        glColor3f(0, 1, 0)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x1, y1)
        glVertex2f(x2, y1)
        glVertex2f(x2, y2)
        glVertex2f(x1, y2)
        glEnd()
        glPopAttrib()

SetDPITestCase.create_test_case(
        name='test_set_dpi',
        question='Does the green box exactly bound the top and bottom of the text?'
        )
