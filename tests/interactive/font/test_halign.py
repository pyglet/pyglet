from pyglet import font

from .font_test_base import FontTestBase


class HAlignTestCase(FontTestBase):
    """Test that font.Text horizontal alignment works.

    Three labels will be rendered aligned left, center and right.
    """

    def render(self):
        fnt = font.load('', self.font_size)

        h = fnt.ascent - fnt.descent
        w = self.window.width

        self.labels = [
            font.Text(fnt, 'LEFT', 0, 10 + 3 * h, width=w, halign='left'),
            font.Text(fnt, 'CENTER', 0, 10 + 2 * h, width=w, halign='center'),
            font.Text(fnt, 'RIGHT', 0, 10 + h, width=w, halign='right'),
        ]

    def on_resize(self, width, height):
        for label in self.labels:
            label.width = width

    def draw(self):
        for label in self.labels:
            label.draw()

HAlignTestCase.create_test_case(
        name='test_halign',
        question='Are the labels aligned left, center and right as they say?'
        )
