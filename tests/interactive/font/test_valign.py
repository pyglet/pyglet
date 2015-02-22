from pyglet import gl
from pyglet import font

from .font_test_base import FontTestBase


class VAlignTestCase(FontTestBase):
    """Test that font.Text vertical alignment works.

    Four labels will be aligned top, center, baseline and bottom.
    """

    window_size = 600, 200

    def render(self):
        fnt = font.load('', self.font_size)

        h = fnt.ascent - fnt.descent
        w = self.window.width

        self.labels = []
        x = 0
        for align in 'top center baseline bottom'.split():
            label = align.upper() + 'y'
            self.labels.append(font.Text(fnt, label, x, 50, valign=align))
            x += self.labels[-1].width

    def draw(self):
        gl.glColor3f(1, 1, 1)
        gl.glBegin(gl.GL_LINES)
        gl.glVertex2f(0, 50)
        gl.glVertex2f(self.window.width, 50)
        gl.glEnd()

        for label in self.labels:
            label.draw()

VAlignTestCase.create_test_case(
        name='test_valign',
        question='Are the four labels aligned top, center, baseline and bottom to the horizontal line?'
        )
