#!/usr/bin/env python

'''Test that the clock returns a reasonable average FPS calculation when
stimulated at 5 Hz.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import time
import unittest

from pyglet import clock

__noninteractive = True

class FPS(unittest.TestCase):
    def test_fps(self):
        clock.set_default(clock.Clock())
        self.assertTrue(clock.get_fps() == 0)
        for i in range(10):
            time.sleep(0.2)
            clock.tick()
        result = clock.get_fps()
        self.assertTrue(abs(result - 5.0) < 0.05)

if __name__ == '__main__':
    unittest.main()
