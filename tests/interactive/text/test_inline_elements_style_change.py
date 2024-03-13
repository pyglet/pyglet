from typing import List

import pytest

import pyglet.text.layout
from tests.base.interactive import InteractiveTestCase

import pyglet
from pyglet.text import caret, document
from pyglet.text.layout import IncrementalTextLayout


doctext = """ELEMENT.py test document.

PLACE CURSOR AT THE END OF THE ABOVE LINE, AND DELETE ALL ITS TEXT,
BY PRESSING THE DELETE KEY REPEATEDLY.

IF THIS WORKS OK, AND THE ELEMENT (GRAY RECTANGLE) WITHIN THIS LINE
[element here]
REMAINS VISIBLE BETWEEN THE SAME CHARACTERS, WITH NO ASSERTIONS PRINTED TO
THE CONSOLE, THE TEST PASSES.

(In code with bug 538, the element sometimes moves within the text, and
eventually there is an assertion failure. Note that there is another bug,
unrelated to this one, which sometimes causes the first press of the delete
key to be ignored.)

Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Fusce venenatis
pharetra libero. Phasellus lacinia nisi feugiat felis. Sed id magna in nisl
cursus consectetuer. Aliquam aliquam lectus eu magna. Praesent sit amet ipsum
vitae nisl mattis commodo. Aenean pulvinar facilisis lectus. Phasellus sodales
risus sit amet lectus. Suspendisse in turpis. Vestibulum ac mi accumsan eros
commodo tincidunt. Nullam velit. In pulvinar, dui sit amet ullamcorper dictum,
dui risus ultricies nisl, a dignissim sapien enim sit amet tortor.
Pellentesque fringilla, massa sit amet bibendum blandit, pede leo commodo mi,
eleifend feugiat neque tortor dapibus mauris. Morbi nunc arcu, tincidunt vel,
blandit non, iaculis vel, libero. Vestibulum sed metus vel velit scelerisque
varius. Vivamus a tellus. Proin nec orci vel elit molestie venenatis. Aenean
fringilla, lorem vel fringilla bibendum, nibh mi varius mi, eget semper ipsum
ligula ut urna. Nullam tempor convallis augue. Sed at dui.
"""

element_index = doctext.index('[element here]')
doctext = doctext.replace('[element here]', '')

class TestElement(document.InlineElement):

    def __init__(self, ascent, descent, advance):
        self.vertex_list = None
        super().__init__(ascent, descent, advance)

    def place(self, layout, x, y, z, line_x, line_y, rotation, visible, anchor_x, anchor_y):
        group = layout.foreground_decoration_group
        program = pyglet.text.layout.get_default_decoration_shader()

        x1 = line_x
        y1 = line_y + self.descent
        x2 = line_x + self.advance
        y2 = line_y + self.ascent - self.descent

        self.vertex_list = program.vertex_list_indexed(4, pyglet.gl.GL_TRIANGLES, [0, 1, 2, 0, 2, 3],
                                                  layout.batch, group,
                                                  position=('f', (x1, y1, z, x2, y1, z, x2, y2, z, x1, y2, z)),
                                                  colors=('Bn', (200, 200, 200, 255) * 4),
                                                  translation=('f', (x, y, z) * 4),
                                                  visible=('f', (visible,) * 4),
                                                  rotation=('f', (rotation,) * 4),
                                                  anchor=('f', (anchor_x, anchor_y) * 4)
                                                  )
    def update_translation(self, x: float, y: float, z: float):
        self.vertex_list.translation[:] = (x, y, z) * self.vertex_list.count

    def update_color(self, color: List[int]):
        pass

    def update_view_translation(self, translate_x: float, translate_y: float):
        self.vertex_list.view_translation[:] = (-translate_x, -translate_y, 0) * self.vertex_list.count

    def update_rotation(self, rotation: float):
        pass

    def update_visibility(self, visible: bool):
        pass

    def update_anchor(self, anchor_x: float, anchor_y: float):
        pass

    def remove(self, layout):
        self.vertex_list.delete()
        del self.vertex_list

class TestWindow(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        super(TestWindow, self).__init__(*args, **kwargs)

        self.batch = pyglet.graphics.Batch()
        self.document = pyglet.text.decode_attributed(doctext)
        for i in [element_index]:
            self.document.insert_element(i, TestElement(60, -10, 70))
        self.margin = 2
        self.layout = IncrementalTextLayout(
            self.document, self.width - self.margin * 2, self.height - self.margin * 2,
            multiline=True,
            batch=self.batch)
        self.caret = caret.Caret(self.layout)
        self.push_handlers(self.caret)

        self.set_mouse_cursor(self.get_system_mouse_cursor('text'))

    def on_draw(self):
        pyglet.gl.glClearColor(1, 1, 1, 1)
        self.clear()
        self.batch.draw()

    def on_key_press(self, symbol, modifiers):
        super(TestWindow, self).on_key_press(symbol, modifiers)
        if symbol == pyglet.window.key.TAB:
            self.caret.on_text('\t')

        self.document.set_style(0, len(self.document.text), dict(bold = None)) ### trigger bug 538


@pytest.mark.requires_user_action
class InlineElementStyleChangeTestCase(InteractiveTestCase):
    """Test that inline elements can have their style changed, even after text
    has been deleted before them. [This triggers bug 538 if it has not yet been fixed.]

    To run the test, delete the first line, one character at a time,
    verifying that the element remains visible and no tracebacks are
    printed to the console.

    Press ESC to end the test.
    """

    def test_inline_elements_style_change(self):
        self.window = TestWindow(visible=False)
        self.window.set_visible()
        pyglet.app.run()
        self.user_verify('Pass test?', take_screenshot=False)
