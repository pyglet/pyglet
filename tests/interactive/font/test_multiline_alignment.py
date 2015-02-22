from pyglet import font
from .font_test_base import FontTestBase

class MultilineAlignmentTestCase(FontTestBase):
    """Test that font.Text alignment works with multiple lines.

    Three labels will be rendered at the top-left, center and bottom-right of the
    window.  Resize the window to ensure the alignment is as specified.
    """
    font_name = ''
    window_size = 400, 500
    question = "The three labels should be aligned as they describe"

    def render(self):
        fnt = font.load(self.font_name, self.font_size)

        w = self.window.width
        h = self.window.height

        self.labels = [
            font.Text(fnt, 
                'This text is top-left aligned  with several lines.', 
                0, h, width=w, 
                halign='left', valign='top'),
            font.Text(fnt, 
                'This text is centered in the middle.',
                0, h//2, width=w, 
                halign='center', valign='center'),
            font.Text(fnt, 
                'This text is aligned to the bottom-right of the window.',
                0, 0, width=w, 
                halign='right', valign='bottom'),
        ]

    def on_resize(self, width, height):
        for label in self.labels:
            label.width = width
        self.labels[0].y = height
        self.labels[1].y = height // 2

    def draw(self):
        for label in self.labels:
            label.draw()

MultilineAlignmentTestCase.create_test_case(name='test_alignment')
