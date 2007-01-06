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

from pyglet.GL.VERSION_1_1 import *
import pyglet.window
import pyglet.window.event
import pyglet.clock
from pyglet.scene2d import Sprite, Image2d, Scene, FlatView
from pyglet.scene2d.camera import FlatCamera

ball_png = os.path.join(os.path.dirname(__file__), 'ball.png')

class SpriteModelTest(unittest.TestCase):

    def test_sprite(self):
        w = pyglet.window.Window(width=320, height=320)

        image = Image2d.load(ball_png)
        ball = Sprite(0, 0, 64, 64, image)
        s = Scene(sprites=[ball])
        r = FlatView(s, 0, 0, 320, 320)

        class running(pyglet.window.event.ExitHandler):
            def __init__(self, fps=30):
                self.clock = pyglet.clock.Clock(fps)
            def __nonzero__(self):
                if self.exit: return False
                self.clock.tick()
                return True
        running = running()
        w.push_handlers(running)
        w.push_handlers(r.camera)

        dx, dy = (10, 5)

        # XXX this belongs in sprite somewhere
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_BLEND)
        glEnable(GL_COLOR_MATERIAL)

        while running:
            w.dispatch_events()
            glClear(GL_COLOR_BUFFER_BIT)
            
            # move, check bounds
            ball.x += dx; ball.y += dy
            if ball.left < 0: ball.left = 0; dx = -dx
            elif ball.right > w.width: ball.right = w.width; dx = -dx
            if ball.bottom < 0: ball.bottom = 0; dy = -dy
            elif ball.top > w.height: ball.top = w.height; dy = -dy

            # XXX listen for events
            r.fx = w.width/2
            r.fy = w.height/2
            r.width = w.width
            r.height = w.height

            r.draw()
            w.flip()

        w.close()

if __name__ == '__main__':
    unittest.main()
