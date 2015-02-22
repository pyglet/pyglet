from pyglet import font

from .font_test_base import FontTestBase


class WrapInvariantTestCase(FontTestBase):
    """Test that text will not wrap when its width is set to its calculated
    width.

    You should be able to clearly see "TEST TEST" on a single line (not two)
    and "SPAM SPAM SPAM" over two lines, not three.
    """

    text = 'TEST TEST'

    def render(self):
        fnt = font.load('', 24)
        self.label1 = font.Text(fnt, 'TEST TEST', 10, 150)
        self.label1.width = self.label1.width + 1
        self.label2 = font.Text(fnt, 'SPAM SPAM\nSPAM', 10, 50)
        self.label2.width = self.label2.width + 1

    def draw(self):
        self.label1.draw()
        self.label2.draw()

WrapInvariantTestCase.create_test_case(
        name='test_wrap_invariant',
        question="""TEST TEST shold be on a single line.
                    SPAM SPAM SPAM should be divided over two lines."""
        )
