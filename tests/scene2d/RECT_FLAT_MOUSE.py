#!/usr/bin/env python

'''Testing mouse interaction

NOTE: one cell in this map is a 2x2 grey check grid.

The cell the mouse is hovering over should highlight in red.

Clicking in a cell should highliht that cell green. Clicking again will
clear the highlighting.

You may press the arrow keys to scroll the focus around the map (this
will move the map eventually)

Press escape or close the window to finish the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest
from render_base import RenderBase
from pyglet.scene2d import Tile
from pyglet.scene2d.event import event, for_cells
from pyglet.scene2d.image import RectTintEffect
from pyglet.scene2d.debug import gen_rect_map, RectCheckImage

hover_img = RectCheckImage(32, 32, (1, 0, 0, 1))
hover = Tile('hover', {}, hover_img)
clicked_img = RectCheckImage(32, 32, (0, 1, 0, 1))
clicked = Tile('clicked', {}, clicked_img)

class RectFlatDebugTest(RenderBase):
    def test_main(self):
        self.init_window(256, 256)
        m = gen_rect_map([[dict() for i in range(10)]]*20, 32, 32)
        self.set_map(m)
        self.w.push_handlers(self.view)
        self.view.allow_oob = False

        @event(self.view)
        @for_cells()
        def on_mouse_enter(cells):
            for cell in cells:
                e = RectTintEffect((1, .8, .8, 1))
                cell.properties['hover'] = e
                cell.add_effect(e)

        @event(self.view)
        @for_cells()
        def on_mouse_leave(cells):
            for cell in cells:
                cell.remove_effect(cell.properties['hover'])

        @event(self.view)
        @for_cells()
        def on_mouse_press(cells, button, x, y, modifiers):
            for cell in cells:
                if 'clicked' in cell.properties:
                    cell.remove_effect(cell.properties['clicked'])
                    del cell.properties['clicked']
                else:
                    e = RectTintEffect((.8, 1, .8, 1))
                    cell.properties['clicked'] = e
                    cell.add_effect(e)

        self.show_focus()
        self.run_test()

if __name__ == '__main__':
    unittest.main()

