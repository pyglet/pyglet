import pytest

from tests.base.interactive import InteractiveTestCase

from pyglet import app
from pyglet import gl
from pyglet import graphics
from pyglet import text
from pyglet.text import caret
from pyglet.text import layout
from pyglet import window
from pyglet.window import key, mouse

doctext = """test_content_valign.py test document.

Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Maecenas aliquet quam sit amet enim. Donec iaculis, magna vitae imperdiet convallis, lectus sem ultricies nulla, non fringilla quam felis tempus velit. Etiam et velit. Integer euismod. Aliquam a diam. Donec sed ante. Mauris enim pede, dapibus sed, dapibus vitae, consectetuer in, est. Donec aliquam risus eu ipsum. Integer et tortor. Ut accumsan risus sed ante.

Aliquam dignissim, massa a imperdiet fermentum, orci dolor facilisis ante, ut vulputate nisi nunc sed massa. Morbi sodales hendrerit tortor. Nunc id tortor ut lacus mollis malesuada. Sed nibh tellus, rhoncus et, egestas eu, laoreet eu, urna. Vestibulum massa leo, convallis et, pharetra vitae, iaculis at, ante. Pellentesque volutpat porta enim. Morbi ac nunc eget mi pretium viverra. Pellentesque felis risus, lobortis vitae, malesuada vitae, bibendum eu, tortor. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae; Phasellus dapibus tortor ac neque. Curabitur pulvinar bibendum lectus. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Aliquam tellus. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Nulla turpis leo, rhoncus vel, euismod non, consequat sed, massa. Quisque ultricies. Aliquam fringilla faucibus est. Proin nec felis eget felis suscipit vehicula.

Etiam quam. Aliquam at ligula. Aenean quis dolor. Suspendisse potenti. Sed lacinia leo eu est. Nam pede ligula, molestie nec, tincidunt vel, posuere in, tellus. Donec fringilla dictum dolor. Aenean tellus orci, viverra id, vehicula eget, tempor a, dui. Morbi eu dolor nec lacus fringilla dapibus. Nulla facilisi. Nulla posuere. Nunc interdum. Donec convallis libero vitae odio.

Aenean metus lectus, faucibus in, malesuada at, fringilla nec, risus. Integer enim. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Proin bibendum felis vel neque. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Donec ipsum dui, euismod at, dictum eu, congue tincidunt, urna. Sed quis odio. Integer aliquam pretium augue. Vivamus nonummy, dolor vel viverra rutrum, lacus dui congue pede, vel sodales dui diam nec libero. Morbi et leo sit amet quam sollicitudin laoreet. Vivamus suscipit.

Duis arcu eros, iaculis ut, vehicula in, elementum a, sapien. Phasellus ut tellus. Integer feugiat nunc eget odio. Morbi accumsan nonummy ipsum. Donec condimentum, tortor non faucibus luctus, neque mi mollis magna, nec gravida risus elit nec ipsum. Donec nec sem. Maecenas varius libero quis diam. Curabitur pulvinar. Morbi at sem eget mauris tempor vulputate. Aenean eget turpis.
"""

class TestWindow(window.Window):
    def __init__(self, content_valign, *args, **kwargs):
        super(TestWindow, self).__init__(*args, **kwargs)

        self.batch = graphics.Batch()
        self.document = text.decode_text(doctext)
        self.margin = 2
        self.layout = layout.IncrementalTextLayout(self.document,
                                                   self.width - self.margin * 2, self.height - self.margin * 2,
                                                   multiline=True,
                                                   batch=self.batch)
        self.layout.content_valign = content_valign
        self.caret = caret.Caret(self.layout)
        self.push_handlers(self.caret)

        self.set_mouse_cursor(self.get_system_mouse_cursor('text'))

    def on_resize(self, width, height):
        super(TestWindow, self).on_resize(width, height)
        self.layout.begin_update()
        self.layout.x = self.margin
        self.layout.y = self.margin
        self.layout.width = width - self.margin * 2
        self.layout.height = height - self.margin * 2
        self.layout.end_update()

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.layout.view_x -= scroll_x
        self.layout.view_y += scroll_y * 16

    def on_draw(self):
        gl.glClearColor(1, 1, 1, 1)
        self.clear()
        self.batch.draw()

    def on_key_press(self, symbol, modifiers):
        super(TestWindow, self).on_key_press(symbol, modifiers)
        if symbol == key.TAB:
            self.caret.on_text('\t')

@pytest.mark.requires_user_action
class ContentValignTestCase(InteractiveTestCase):
    def test_content_valign_bottom(self):
        """Test content_valign = 'bottom' property of IncrementalTextLayout.

        Examine and type over the text in the window that appears.  The window
        contents can be scrolled with the mouse wheel.  When the content height
        is less than the window height, the content should be aligned to the bottom
        of the window.

        Press ESC to exit the test.
        """
        self.window = TestWindow(resizable=True, visible=False, content_valign='bottom')
        self.window.set_visible()
        app.run()
        self.user_verify('Test passed?', take_screenshot=False)

    def test_content_valign_center(self):
        """Test content_valign = 'center' property of IncrementalTextLayout.

        Examine and type over the text in the window that appears.  The window
        contents can be scrolled with the mouse wheel.  When the content height
        is less than the window height, the content should be aligned to the center
        of the window.

        Press ESC to exit the test.
        """
        self.window = TestWindow(resizable=True, visible=False, content_valign='center')
        self.window.set_visible()
        app.run()
        self.user_verify('Test passed?', take_screenshot=False)

