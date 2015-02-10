#!/usr/bin/env python

'''Test that HTML data is decoded into a formatted document.

Press ESC to exit the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: ELEMENT.py 1764 2008-02-16 05:24:46Z Alex.Holkner $'

import unittest
import pyglet
from pyglet.text import caret, document, layout

doctext = '''
<html>
  <head>
    (metadata including title is not displayed.)
    <title>Test document</title>
  </head>

  <body>
    <h1>HTML test document</h1>

    <p>Several paragraphs of HTML formatted text follow.  Ensure they are
    formatted as they are described.  Here is a copyright symbol: &#169; and
    again, using hexadecimal ref: &#xa9;.</p>

    <P>This paragraph has some <b>bold</b> and <i>italic</i> and <b><i>bold
    italic</b> text. <!-- i tag does not need to be closed -->

    <p>This paragraph has some <em>emphasis</em> and <strong>strong</strong>
    and <em><strong>emphatic strong</em> text.

    <p>This paragraph demonstrates superscript: a<sup>2</sup> + b<sup>2</sup>
    = c<sup>2</sup>; and subscript: H<sub>2</sub>O.

    <p>This paragraph uses the &lt;font&gt; element: 
    <font face="Courier New">Courier New</font>, <font size=1>size 1</font>,
    <font size=2>size 2</font>, <font size=3>size 3</font>, <font size=4>size
    4</font>, <font size=5>size 5</font>, <font size=6>size 6</font>, <font
    size=7>size 7</font>.

    <p>This paragraph uses relative sizes: <font size=5>size 5<font
    size=-2>size 3</font><!--<font size=+1>size 6</font>--></font>

    <p>Font color changes to <font color=red>red</font>, <font
    color=green>green</font> and <font color=#0f0fff>pastel blue using a
    hexidecimal number</font>.

    <p><u>This text is underlined</u>.  <font color=green><u>This text is
    underlined and green.</u></font>

    <h1>Heading 1
    <h2>Heading 2
    <h3>Heading 3
    <h4>Heading 4
    <h5>Heading 5
    <h6>Heading 6

    <p align=center>Centered paragraph.

    <p align=right>Right-aligned paragraph.

    <div>&lt;div&gt; element instead of paragraph.
        <div>This sentence should start a new paragraph, as the div is nested.
        </div>
        This sentence should start a new paragraph, as the nested div was
        closed.
    </div>

    <pre>This text is preformatted.
Hard line breaks
   Indentation.  <b>Inline formatting</b> is still ok.</pre>

    <p>This paragraph<br>
    has a<br>
    line break<br>
    after every<br>
    two words.</p>

    <blockquote>This paragraph is blockquote. Lorem ipsum dolor sit amet,
    consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore
    et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation
    ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure
    dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat
    nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in
    culpa qui officia deserunt mollit anim id est laborum.

    <blockquote>Nested blockquote. Lorem ipsum dolor sit amet,
    consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore
    et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation
    ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure
    dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat
    nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in
    culpa qui officia deserunt mollit anim id est laborum.</blockquote>
    
    </blockquote>

    Here is a quotation.  The previous paragraph mentioned, <q>Lorem ipsum
    dolor sit amet, ...</q>.

    <ul>
        <li>
            Unordered list, level 1. Lorem ipsum dolor sit amet, consectetur
            adipisicing elit, sed do eiusmod tempor incididunt ut labore et
            dolore magna aliqua. Ut enim ad minim veniam, quis nostrud
            exercitation ullamco laboris nisi ut aliquip ex ea commodo
            consequat.
        <li>
            Item 2. Lorem ipsum dolor sit amet, consectetur
            adipisicing elit, sed do eiusmod tempor incididunt ut labore et
            dolore magna aliqua. Ut enim ad minim veniam, quis nostrud
            exercitation ullamco laboris nisi ut aliquip ex ea commodo
            consequat.
        <li>
            Item 3. Lorem ipsum dolor sit amet, consectetur
            adipisicing elit, sed do eiusmod tempor incididunt ut labore et
            dolore magna aliqua. Ut enim ad minim veniam, quis nostrud
            exercitation ullamco laboris nisi ut aliquip ex ea commodo
            consequat.

            <ul>
                <li>
                    A nested list. Lorem ipsum dolor sit amet, consectetur
                    adipisicing elit, sed do eiusmod tempor incididunt ut
                    labore et dolore magna aliqua. Ut enim ad minim veniam,
                    quis nostrud exercitation ullamco laboris nisi ut aliquip
                    ex ea commodo consequat.
                <li>
                    Item 3.2.  Lorem ipsum dolor sit amet, consectetur
                    adipisicing elit, sed do eiusmod tempor incididunt ut
                    labore et dolore magna aliqua.
            </ul>

    </ul>

    <ul type="circle">
        <li>Unordered list with circle bullets.
        <li>Item 2.
    </ul>

    <ul type="square">
        <li>Unordered list with square bullets.
        <li>Item 2.
    </ul>

    <ol>
        <li>Numbered list.
        <li>Item 2.
        <li>Item 3.
        <li value=10>Item 10
        <li>Item 11
    </ol>

    <ol start=12>
        <li>Numbered list starting at 12.
        <li>Item 13.
    </ol>

    <ol type="a">
        <li>Numbered list with "a" type
        <li>Item 2
        <li>Item 3
    </ol>

    <ol type="A">
        <li>Numbered list with "A" type
        <li>Item 2
        <li>Item 3
    </ol>

    <ol type="i">
        <li>Numbered list with "i" type
        <li>Item 2
        <li>Item 3
    </ol>

    <ol type="I">
        <li>Numbered list with "I" type
        <li>Item 2
        <li>Item 3
    </ol>

    Here's a definition list:

    <dl>
        <dt>Term</dt>
            <dd>Definition.</dd>
        <dt>Term</dt>
            <dd>Definition.</dd>
        <dt>Term</dt>
            <dd>Definition.</dd>
    </dl>

  </body>
</html>
'''

class TestWindow(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        super(TestWindow, self).__init__(*args, **kwargs)

        self.batch = pyglet.graphics.Batch()
        self.document = pyglet.text.decode_html(doctext)
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
        pyglet.gl.glClearColor(1, 1, 1, 1)
        self.clear()
        self.batch.draw()

    def on_key_press(self, symbol, modifiers):
        super(TestWindow, self).on_key_press(symbol, modifiers)
        if symbol == pyglet.window.key.TAB:
            self.caret.on_text('\t')

class TestCase(unittest.TestCase):
    def test(self):
        self.window = TestWindow(resizable=True, visible=False)
        self.window.set_visible()
        pyglet.app.run()

if __name__ == '__main__':
    unittest.main()
