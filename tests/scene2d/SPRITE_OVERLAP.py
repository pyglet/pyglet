
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

from pyglet.GL.VERSION_1_1 import glClear
import pyglet.window
import pyglet.window.event
import pyglet.clock
from pyglet.scene2d import Sprite, Image2d, Scene, FlatView
from pyglet.scene2d.image import RectTintEffect
from pyglet.scene2d.camera import FlatCamera

ball_png = os.path.join(os.path.dirname(__file__), 'ball.png')

class BouncySprite(Sprite):
    def update(self):
        # move, check bounds
        p = self.properties
        self.x += p['dx']; self.y += p['dy']
        if self.left < 0: self.left = 0; p['dx'] = -p['dx']
        elif self.right > 320: self.right = 320; p['dx'] = -p['dx']
        if self.bottom < 0: self.bottom = 0; p['dy'] = -p['dy']
        elif self.top > 320: self.top = 320; p['dy'] = -p['dy']

class SpriteOverlapTest(unittest.TestCase):

    def test_sprite(self):
        w = pyglet.window.Window(width=320, height=320)

        image = Image2d.load(ball_png)
        ball1 = BouncySprite(0, 0, 64, 64, image, properties=dict(dx=10, dy=5))
        ball2 = BouncySprite(288, 0, 64, 64, image,
            properties=dict(dx=-10, dy=5))
        s = Scene(sprites=[ball1, ball2])
        view = FlatView(s, 0, 0, 320, 320)
        view.fx, view.fy = 160, 160

        clock = pyglet.clock.Clock(fps_limit=30)
        e = RectTintEffect((.5, 1, .5, 1))
        while not w.has_exit:
            clock.tick()
            w.dispatch_events()

            ball1.update()
            ball2.update()
            if ball1.overalps(ball2):
                if 'overlap' not in ball2.properties:
                    ball2.properties['overlap'] = e
                    ball2.add_effect(e)
            elif 'overlap' in ball2.properties:
                ball2.remove_effect(e)
                del ball2.properties['overlap']

            view.clear()
            view.draw()
            w.flip()

        w.close()

if __name__ == '__main__':
    unittest.main()
