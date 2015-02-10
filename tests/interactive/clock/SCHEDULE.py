#!/usr/bin/env python

'''Test that a scheduled function gets called every tick with the correct
time delta.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: TICK.py 310 2006-12-23 15:56:35Z Alex.Holkner $'

import time
import unittest

from pyglet import clock

__noninteractive = True

class SCHEDULE(unittest.TestCase):
    callback_dt = None
    callback_count = 0
    def callback(self, dt):
        self.callback_dt = dt
        self.callback_count += 1

    def test_schedule(self):
        clock.set_default(clock.Clock())
        clock.schedule(self.callback)

        result = clock.tick()
        self.assertTrue(result == self.callback_dt)
        self.callback_dt = None
        time.sleep(1)

        result = clock.tick()
        self.assertTrue(result == self.callback_dt)
        self.callback_dt = None
        time.sleep(1)

        result = clock.tick()
        self.assertTrue(result == self.callback_dt)

    def test_unschedule(self):
        clock.set_default(clock.Clock())
        clock.schedule(self.callback)

        result = clock.tick()
        self.assertTrue(result == self.callback_dt)
        self.callback_dt = None
        time.sleep(1)
        clock.unschedule(self.callback)

        result = clock.tick()
        self.assertTrue(self.callback_dt == None)

    def test_schedule_multiple(self):
        clock.set_default(clock.Clock())
        clock.schedule(self.callback)
        clock.schedule(self.callback)
        self.callback_count = 0

        clock.tick()
        self.assertTrue(self.callback_count == 2)

        clock.tick()
        self.assertTrue(self.callback_count == 4)

    def test_schedule_multiple(self):
        clock.set_default(clock.Clock())
        clock.schedule(self.callback)
        clock.schedule(self.callback)
        self.callback_count = 0

        clock.tick()
        self.assertTrue(self.callback_count == 2)
        clock.unschedule(self.callback)

        clock.tick()
        self.assertTrue(self.callback_count == 2)

if __name__ == '__main__':
    unittest.main()
