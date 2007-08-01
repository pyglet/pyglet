#!/usr/bin/env python

'''Testing mouse interaction

The cell the mouse is hovering over should highlight in red.

Clicking in a cell should highliht that cell green. Clicking again will
clear the highlighting.

Clicking on the ball sprite should highlight it and not underlying cells.

You may press the arrow keys to scroll the focus around the map (this
will move the map eventually)

Press escape or close the window to finish the test.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import unittest
from render_base import RenderBase
from scene2d import Tile, Sprite
from pyglet.event import event
from scene2d.event import for_cells, for_sprites
from scene2d.drawable import TintEffect
from scene2d.debug import gen_rect_map

class RectFlatMouseTest(RenderBase):
    def test_main(self):
        self.init_window(256, 256)
        self.set_map(gen_rect_map([[{}]*10]*10, 32, 32))
        self.w.push_handlers(self.view)
        self.view.allow_oob = False

        @event(self.view)
        @for_cells()
        def on_mouse_enter(cells):
            for cell in cells:
                e = TintEffect((1, .5, .5, 1))
                cell.properties['hover'] = e
                cell.add_effect(e)

        @event(self.view)
        @for_cells()
        def on_mouse_leave(cells):
            for cell in cells:
                cell.remove_effect(cell.properties['hover'])

        @event(self.view)
        @for_cells()
        @for_sprites()
        def on_mouse_press(objs, x, y, button, modifiers):
            for obj in objs:
                if 'clicked' in obj.properties:
                    obj.remove_effect(obj.properties['clicked'])
                    del obj.properties['clicked']
                else:
                    e = TintEffect((.5, 1, .5, 1))
                    obj.properties['clicked'] = e
                    obj.add_effect(e)
                return

        self.show_focus()
        self.run_test()

if __name__ == '__main__':
    unittest.main()

