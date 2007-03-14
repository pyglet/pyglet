#!/usr/bin/env python

'''Test that the clock tick function returns the elaspsed time between
frames, in seconds.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import time
import unittest

from pyglet import clock

__noninteractive = True

class TICK(unittest.TestCase):
    def test_tick(self):
        clock.set_default(clock.Clock())
        result = clock.tick()
        self.assertTrue(result == 0)
        time.sleep(1)
        result_1 = clock.tick()
        time.sleep(1)
        result_2 = clock.tick()
        self.assertTrue(abs(result_1 - 1.0) < 0.05)
        self.assertTrue(abs(result_2 - 1.0) < 0.05)

if __name__ == '__main__':
    unittest.main()
