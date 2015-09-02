"""
Interactive tests for pyglet.font
"""
import pytest

from pyglet import gl
from pyglet import font

from tests.interactive.event_loop_test_base import TestWindow, EventLoopFixture
from tests.interactive.windowed_test_base import WindowedTestCase


class FontTestWindow(TestWindow):
    def __init__(self,
                 *args,
                 **kwargs):
        super(FontTestWindow, self).__init__(*args, **kwargs)

        self.draw_baseline = False
        self.draw_metrics = False

        self.font = None
        self.label = None

    def load_font(self,
                  name='',
                  size=24,
                  **options):
        self.font = font.load(name, size, **options)
        assert self.font is not None, 'Failed to load font'
        return self.font

    def create_label(self,
                     text='Quickly brown fox',
                     color=(0, 0, 0, 1),
                     fill_width=False,
                     **options):

        assert self.label is None, 'Label already created'
        if self.font is None:
            self.load_font()

        if fill_width:
            options['width'] = self.width - 10

        self.label = font.Text(self.font, text, 5, 200, color=color, **options)
        return self.label

    def on_draw(self):
        super(FontTestWindow, self).on_draw()
        if self.draw_baseline:
            self._draw_baseline()
        self.label.draw()
        if self.draw_metrics:
            self._draw_metrics()

    def _draw_baseline(self):
        gl.glColor3f(0, 0, 0)
        gl.glBegin(gl.GL_LINES)
        gl.glVertex2f(0, 200)
        gl.glVertex2f(self.width, 200)
        gl.glEnd()

    def _draw_metrics(self):
        self._draw_box(self.label.x,
                       self.label.y+self.font.descent,
                       self.label.width,
                       self.font.ascent-self.font.descent)

    def _draw_box(self, x, y, w, h):
        gl.glBegin(gl.GL_LINES)
        gl.glColor3f(0, 1, 0)
        gl.glVertex2f(x, y)
        gl.glVertex2f(x, y+h)
        gl.glColor3f(1, 0, 0)
        gl.glVertex2f(x, y+h)
        gl.glVertex2f(x+w, y+h)
        gl.glColor3f(0, 0, 1)
        gl.glVertex2f(x+w, y+h)
        gl.glVertex2f(x+w, y)
        gl.glColor3f(1, 0, 1)
        gl.glVertex2f(x+w, y)
        gl.glVertex2f(x, y)
        gl.glEnd()


class FontFixture(EventLoopFixture):
    window_class = FontTestWindow

    def test_font(self, question, **kwargs):
        self.create_window(**kwargs)
        self.ask_question(question)

    @property
    def label(self):
        assert self.window is not None
        return self.window.label


@pytest.fixture
def font_fixture(request):
    return FontFixture(request)


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

