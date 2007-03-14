#!/usr/bin/env python

'''Test that the clock effectively limits the FPS to 20 Hz when requested.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import time
import unittest

from pyglet import clock

__noninteractive = True

class FPS_LIMIT(unittest.TestCase):
    def test_fps_limit(self):
        clock.set_default(clock.Clock())
        clock.set_fps_limit(20)
        self.assertTrue(clock.get_fps() == 0)

        t1 = time.time()
        clock.tick() # One to get it going
        for i in range(20):
            clock.tick()
        t2 = time.time()
        self.assertTrue(abs((t2 - t1) - 1.) < 0.05)

if __name__ == '__main__':
    unittest.main()
