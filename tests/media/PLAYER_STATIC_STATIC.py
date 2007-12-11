#!/usr/bin/env python

'''Test that audio playback works.

You should hear white noise (static) for 0.5 seconds.  The test will exit
immediately after.  

You may want to turn down the volume of your speakers.
'''

import unittest

from pyglet import media
from pyglet.media import procedural

class TEST_CASE(unittest.TestCase):
    def test_method(self):
        source = procedural.WhiteNoise(0.5)
        source = media.StaticSource(source)
        source = media.StaticSource(source)
        player = media.Player()
        player.queue(source)
        player.play()

        while player.source:
            player.dispatch_events()

if __name__ == '__main__':
    unittest.main()
