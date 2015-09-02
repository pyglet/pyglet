"""
Interactive tests for pyglet.font
"""
import pytest

from pyglet import gl
from pyglet import font

from tests.interactive.event_loop_test_base import TestWindow, EventLoopFixture


class FontTestWindow(TestWindow):
    def __init__(self,
                 *args,
                 **kwargs):
        super(FontTestWindow, self).__init__(*args, **kwargs)

        self.draw_baseline = False
        self.draw_metrics = False
        self.draw_custom_metrics = None

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
                     margin=5,
                     **options):

        assert self.label is None, 'Label already created'
        if self.font is None:
            self.load_font()

        if fill_width:
            options['width'] = self.width - 2*margin

        self.label = font.Text(self.font, text, margin, 200, color=color, **options)
        return self.label

    def on_draw(self):
        super(FontTestWindow, self).on_draw()
        self._draw_baseline()
        self.label.draw()
        self._draw_metrics()
        self._draw_custom_metrics()

    def _draw_baseline(self):
        if self.draw_baseline:
            gl.glColor3f(0, 0, 0)
            gl.glBegin(gl.GL_LINES)
            gl.glVertex2f(0, 200)
            gl.glVertex2f(self.width, 200)
            gl.glEnd()

    def _draw_metrics(self):
        if self.draw_metrics:
            self._draw_box(self.label.x,
                        self.label.y+self.font.descent,
                        self.label.width,
                        self.font.ascent-self.font.descent)

    def _draw_custom_metrics(self):
        if self.draw_custom_metrics is not None:
            assert len(self.draw_custom_metrics) == 2
            self._draw_box(self.label.x,
                        self.label.y+self.font.descent,
                        *self.draw_custom_metrics)

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

