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
        player = media.Player()
        player.pause()
        player.queue(source)

        while player.source:
            player.dispatch_events()
            player.play()

if __name__ == '__main__':
    unittest.main()
