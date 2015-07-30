import pytest
from tests.interactive.interactive_test_base import InteractiveTestCase

from pyglet import app
from pyglet import gl
from pyglet import graphics
from pyglet import text
from pyglet.text import caret
from pyglet.text import layout
from pyglet import window
from pyglet.window import key, mouse

doctext = """STYLE.py test document.

{font_size 24}This is 24pt text.{font_size 12}

This is 12pt text (as is everything that follows).

This text has some {bold True}bold character style{bold False}, some
{italic True}italic character style{italic False}, some {underline [0, 0, 0,
255]}underlined text{underline None}, {underline [255, 0, 0, 255]}underline
in red{underline None}, a {color [255, 0, 0, 255]}change {color [0, 255, 0,
255]}in {color [0, 0, 255, 255]}color{color None}, and in 
{background_color [255, 255, 0, 255]}background 
{background_color [0, 255, 255, 255]}color{background_color None}.  
{kerning '2pt'}This sentence has 2pt kerning.{kerning 0} 
{kerning '-1pt'}This sentence has negative 1pt kerning.{kerning 0}

Superscript is emulated by setting a positive baseline offset and reducing the
font size, as in 
a{font_size 9}{baseline '4pt'}2{font_size None}{baseline 0} +
b{font_size 9}{baseline '4pt'}2{font_size None}{baseline 0} =
c{font_size 9}{baseline '4pt'}2{font_size None}{baseline 0}.
Subscript is similarly emulated with a negative baseline offset, as in 
H{font_size 9}{baseline '-3pt'}2{font_size None}{baseline 0}O.

This paragraph uses {font_name 'Courier New'}Courier New{font_name None} and
{font_name 'Times New Roman'}Times New Roman{font_name None} fonts.

{.leading '5pt'}This paragraph has 5pts leading. Lorem ipsum dolor sit amet,
consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et
dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation
ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor
in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla
pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui
officia deserunt mollit anim id est laborum.

{.leading None}{.line_spacing '12pt'}This paragraph has constant line spacing of
12pt.  When an {font_size 18}18pt font is used{font_size None}, the text
overlaps and the baselines stay equally spaced. Lorem ipsum dolor sit amet,
consectetur adipisicing elit, {font_size 18}sed do eiusmod tempor incididunt
ut labore et dolore{font_size None} magna aliqua. 

{.line_spacing None}{.indent '20pt'}This paragraph has a 20pt indent. Lorem
ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore
eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt
in culpa qui officia deserunt mollit anim id est laborum.

{.indent None}{.tab_stops [300, 500]}Tablated data:{#x09}Player{#x09}Score{}
{#x09}Alice{#x09}30,000{}
{#x09}Bob{#x09}20,000{}
{#x09}Candice{#x09}10,000{}
{#x09}David{#x09}500

{.indent None}{.align 'right'}This paragraph is right aligned. Lorem ipsum
dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt
ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud
exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis
aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu
fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in
culpa qui officia deserunt mollit anim id est laborum.

{.align 'center'}This paragraph is centered. Lorem ipsum dolor sit amet,
consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et
dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation
ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor
in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla
pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui
officia deserunt mollit anim id est laborum.

{.align 'left'}{.margin_left 50}This paragraph has a 50 pixel left margin.
Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod
tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam,
quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo
consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse
cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non
proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

{.margin_left 0}{.margin_right '50px'}This paragraph has a 50 pixel right
margin.  Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do
eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim
veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea
commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit
esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat
non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

{.margin_left 200}{.margin_right 200}This paragraph has 200 pixel left and
right margins. Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed
do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad
minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex
ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate
velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat
cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id
est laborum.

{.align 'right'}{.margin_left 100}{.margin_right 100}This paragraph is
right-aligned, and has 100 pixel left and right margins. Lorem ipsum dolor sit
amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore
et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation
ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor
in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla
pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui
officia deserunt mollit anim id est laborum.

{.align 'center'}{.margin_left 100}{.margin_right 100}This paragraph is
centered, and has 100 pixel left and right margins. Lorem ipsum dolor sit
amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore
et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation
ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor
in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla
pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui
officia deserunt mollit anim id est laborum.

{.align 'left'}{.margin_left 0}{.margin_right 0}{.wrap False}This paragraph
does not word-wrap. Lorem ipsum dolor sit amet, consectetur adipisicing elit,
sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad
minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea
commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit
esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat
non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

{.align 'left'}{.margin_left 0}{.margin_right 0}{.wrap 'char'}This paragraph
has character-level wrapping. Lorem ipsum dolor sit amet, consectetur
adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna
aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris
nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in
reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia
deserunt mollit anim id est laborum.

{.wrap True}{.margin_bottom 15}This and the following two paragraphs have a 15
pixel vertical margin separating them. Lorem ipsum dolor sit amet, consectetur
adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna
aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris
nisi ut aliquip ex ea commodo consequat.{}
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore
eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt
in culpa qui officia deserunt mollit anim id est laborum.{}
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore
eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt
in culpa qui officia deserunt mollit anim id est laborum.{}
{.margin_bottom 0}{.margin_top 30}This and the following two paragraphs have
a 30 pixel vertical margin (this time, the top margin is used instead of the
bottom margin).  There is a 45 pixel margin between this paragraph and the
previous one.{}
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore
eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt
in culpa qui officia deserunt mollit anim id est laborum.{}
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore
eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt
in culpa qui officia deserunt mollit anim id est laborum.{}
"""


class TestWindow(window.Window):
    def __init__(self, *args, **kwargs):
        super(TestWindow, self).__init__(*args, **kwargs)

        self.batch = graphics.Batch()
        self.document = text.decode_attributed(doctext)
        self.margin = 2
        self.layout = layout.IncrementalTextLayout(self.document,
            self.width - self.margin * 2, self.height - self.margin * 2,
            multiline=True,
            batch=self.batch)
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
class TextStyleTestCase(InteractiveTestCase):
    """Test that character and paragraph-level style is adhered to correctly in
    incremental layout.

    Examine and type over the text in the window that appears.  The window
    contents can be scrolled with the mouse wheel.  There are no formatting
    commands, however formatting should be preserved as expected when entering or
    replacing text and resizing the window.

    Press ESC to exit the test.
    """
    def test(self):
        self.window = TestWindow(resizable=True, visible=False)
        self.window.set_visible()
        app.run()
        self.user_verify('Pass test?', take_screenshot=False)

