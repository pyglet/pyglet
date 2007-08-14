#!/usr/bin/env python

'''Test that audio playback works.

You should hear white noise (static) for 0.25 seconds, then a 0.5 second pause
then another 0.25 seconds of noise.  The test will exit immediately after.  

You may want to turn down the volume of your speakers.
'''

import unittest

import time

from pyglet import media
from pyglet.media import procedural

class TEST_CASE(unittest.TestCase):
    def test_method(self):
        source = procedural.WhiteNoise(0.5)
        player = media.Player()
        player.queue(source)
        player.play()
        start_time = time.time()

        stage = 0
        while player.source:
            if stage == 0 and time.time() - start_time > 0.25:
                player.pause()
                stage = 1
            if stage == 1 and time.time() - start_time > 0.75:
                player.play()
                stage = 2
            player.dispatch_events()

if __name__ == '__main__':
    unittest.main()
