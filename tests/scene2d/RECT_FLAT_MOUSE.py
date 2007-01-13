#!/usr/bin/env python

'''Testing mouse interaction

NOTE: one cell in this map is a 2x2 grey check grid.

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
from pyglet.scene2d import Tile, Sprite
from pyglet.event import event
from pyglet.scene2d.event import for_cells, for_sprites
from pyglet.scene2d.image import RectTintEffect
from pyglet.scene2d.debug import gen_rect_map, RectCheckImage

hover_img = RectCheckImage(32, 32, (1, 0, 0, 1))
hover = Tile('hover', {}, hover_img)
clicked_img = RectCheckImage(32, 32, (0, 1, 0, 1))
clicked = Tile('clicked', {}, clicked_img)

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
        @for_sprites()
        def on_mouse_press(objs, button, x, y, modifiers):
            for obj in objs:
                if 'clicked' in obj.properties:
                    obj.remove_effect(obj.properties['clicked'])
                    del obj.properties['clicked']
                else:
                    e = RectTintEffect((.8, 1, .8, 1))
                    obj.properties['clicked'] = e
                    obj.add_effect(e)
                return

        self.show_focus()
        self.run_test()

if __name__ == '__main__':
    unittest.main()

