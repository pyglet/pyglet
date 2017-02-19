#!/usr/bin/env python

'''Testing a sprite.

The ball should bounce off the sides of the window. You may resize the
window.

This test should just run without failing.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import os
import unittest

from pyglet.gl import glClear
import pyglet.window
import pyglet.window.event
from pyglet import clock
from scene2d import Sprite, Image2d, FlatView
from scene2d.camera import FlatCamera

ball_png = os.path.join(os.path.dirname(__file__), 'ball.png')

class FlatSpriteTest(unittest.TestCase):

    def test_sprite(self):
        w = pyglet.window.Window(width=320, height=320)

        image = Image2d.load(ball_png)
        ball = Sprite(0, 0, 64, 64, image)
        view = FlatView(0, 0, 320, 320, sprites=[ball])

        w.push_handlers(view.camera)

        dx, dy = (10, 5)

        clock.set_fps_limit(30)
        while not w.has_exit:
            clock.tick()
            w.dispatch_events()

            # move, check bounds
            ball.x += dx; ball.y += dy
            if ball.left < 0: ball.left = 0; dx = -dx
            elif ball.right > w.width: ball.right = w.width; dx = -dx
            if ball.bottom < 0: ball.bottom = 0; dy = -dy
            elif ball.top > w.height: ball.top = w.height; dy = -dy

            # keep our focus in the middle of the window
            view.fx = w.width/2
            view.fy = w.height/2

            view.clear()
            view.draw()
            w.flip()

        w.close()

if __name__ == '__main__':
    unittest.main()
