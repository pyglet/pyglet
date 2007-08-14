#!/usr/bin/env python

'''Test that audio playback works.

You should hear a tone at 440Hz (A above middle C) for 1.0 seconds.  The test
will exit immediately after.  

You may want to turn down the volume of your speakers.
'''

import unittest

from pyglet import media
from pyglet.media import procedural

class TEST_CASE(unittest.TestCase):
    def test_method(self):
        source1 = procedural.Sine(0.5)
        source2 = procedural.Sine(0.5)
        player = media.Player()
        player.queue(source1)
        player.queue(source2)
        player.play()

        while player.source:
            player.dispatch_events()

if __name__ == '__main__':
    unittest.main()
