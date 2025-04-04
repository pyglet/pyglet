from typing import Tuple

import pytest

import pyglet.text.layout
from tests.base.interactive import InteractiveTestCase

import pyglet
from pyglet.text import caret, document
from pyglet.text.layout import IncrementalTextLayout


doctext = """ELEMENT.py test document.

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

Nunc faucibus pretium ipsum. Sed ultricies ligula a arcu. Pellentesque vel
urna in augue euismod hendrerit. Donec consequat. Morbi convallis nulla at
ante bibendum auctor. In augue mi, tincidunt a, porta ac, tempor sit amet,
sapien. In sollicitudin risus. Vivamus leo turpis, elementum sed, accumsan eu,
scelerisque at, augue. Ut eu tortor non sem vulputate bibendum. Fusce
ultricies ultrices lorem. In hac habitasse platea dictumst. Morbi ac ipsum.
Nam tellus sem, congue in, fermentum a, ullamcorper vel, mauris. Etiam erat
tortor, facilisis ut, blandit id, placerat sed, orci. Donec quam eros,
bibendum eu, ultricies id, mattis eu, tellus. Ut hendrerit erat vel ligula.
Sed tellus. Quisque imperdiet ornare diam.

Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac
turpis egestas. Sed neque quam, pretium et, malesuada sed, porttitor eu, leo.
Sed varius ornare augue. Maecenas pede dui, nonummy eu, ullamcorper sed,
lobortis id, sem. In sed leo. Nulla ornare. Curabitur dui. Cras ipsum. Cras
massa augue, sodales nec, ultricies at, fermentum in, turpis. Aenean lorem
lectus, fermentum et, lacinia quis, ullamcorper ac, purus. Pellentesque
pharetra diam at elit. Donec dolor. Aenean turpis orci, aliquam vitae,
fermentum et, consectetuer sed, lacus. Maecenas pulvinar, nisi sit amet
lobortis rhoncus, est ipsum ullamcorper mauris, nec cursus felis neque et
dolor. Nulla venenatis sapien vitae lectus. Praesent in risus. In imperdiet
adipiscing nisi. Quisque volutpat, ante sed vehicula sodales, nisi quam
bibendum turpis, id bibendum pede enim porttitor tellus. Aliquam velit.
Pellentesque at mauris quis libero fermentum cursus.

Integer bibendum scelerisque elit. Curabitur justo tellus, vehicula luctus,
consequat vitae, convallis quis, nunc. Fusce libero nulla, convallis eu,
dignissim sit amet, sagittis ac, odio. Morbi dictum tincidunt nisi. Curabitur
hendrerit. Aliquam eleifend sodales leo. Donec interdum. Nam vulputate, purus
in euismod bibendum, pede mi pellentesque dolor, at viverra quam tellus eget
pede. Suspendisse varius mi id felis. Aenean in velit eu nisi suscipit mollis.
Suspendisse vitae augue et diam volutpat luctus.

Mauris et lorem. In mauris. Morbi commodo rutrum nibh. Pellentesque lobortis.
Sed eget urna ut massa venenatis luctus. Morbi egestas purus eget ante
pulvinar vulputate. Suspendisse sollicitudin. Cras tortor erat, semper
vehicula, suscipit non, facilisis ut, est. Aenean quis libero varius nisl
fringilla mollis. Donec viverra. Phasellus mi tortor, pulvinar id, pulvinar
in, lacinia nec, massa. Curabitur lectus erat, volutpat at, volutpat at,
pharetra nec, turpis. Donec ornare nonummy leo. Donec consectetuer posuere
metus. Quisque tincidunt risus facilisis dui. Ut suscipit turpis in massa.
Aliquam erat volutpat.
"""


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

    def update_view_translation(self, translate_x: float, translate_y: float):
        self.vertex_list.view_translation[:] = (-translate_x, -translate_y, 0) * self.vertex_list.count

    def update_rotation(self, rotation: float): ...
    def update_visibility(self, visible: bool): ...
    def update_anchor(self, anchor_x: float, anchor_y: float): ...
    def update_color(self, color: Tuple[int, int, int, int]): ...

    def remove(self, layout):
        self.vertex_list.delete()
        del self.vertex_list


class BaseTestWindow(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.batch = pyglet.graphics.Batch()
        self.document = pyglet.text.decode_attributed(doctext)
        for i in range(0, len(doctext), 300):
            self.document.insert_element(i, TestElement(60, -10, 70))
        self.margin = 2
        self.layout = IncrementalTextLayout(
            self.document,
            width=self.width - self.margin * 2,
            height=self.height - self.margin * 2,
            multiline=True,
            batch=self.batch)
        self.caret = caret.Caret(self.layout)
        self.push_handlers(self.caret)

        self.set_mouse_cursor(self.get_system_mouse_cursor('text'))

    def on_resize(self, width, height):
        super().on_resize(width, height)
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
        super().on_key_press(symbol, modifiers)
        if symbol == pyglet.window.key.TAB:
            self.caret.on_text('\t')


@pytest.mark.requires_user_action
class InlineElementTestCase(InteractiveTestCase):
    """Test that inline elements are positioned correctly and are repositioned
    within an incremental layout.

    Examine and type over the text in the window that appears.  There are several
    elements drawn with grey boxes.  These should maintain their sizes and
    relative document positions as the text is scrolled and edited.

    Press ESC to exit the test.
    """
    def test_inline_elements(self):
        self.window = None
        try:
            self.window = BaseTestWindow(resizable=True, visible=False)
            self.window.set_visible()
            pyglet.app.run()
            self.user_verify('Pass test?', take_screenshot=False)
        finally:
            if self.window:
                self.window.close()

