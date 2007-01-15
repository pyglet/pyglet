#!/usr/bin/env python

'''Test that a scheduled function gets called every interval with the correct
time delta.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: TICK.py 310 2006-12-23 15:56:35Z Alex.Holkner $'

import time
import unittest

from pyglet.clock import *

__noninteractive = True

class SCHEDULE_INTERVAL(unittest.TestCase):
    callback_1_count = 0
    callback_2_count = 0
    callback_3_count = 0

    def callback_1(self, dt):
        self.assertTrue(abs(dt - 0.1) < 0.01)
        self.callback_1_count += 1

    def callback_2(self, dt):
        self.assertTrue(abs(dt - 0.35) < 0.01)
        self.callback_2_count += 1

    def callback_3(self, dt):
        self.assertTrue(abs(dt - 0.07) < 0.01)
        self.callback_3_count += 1

    def clear(self):
        self.callback_1_count = 0
        self.callback_2_count = 0
        self.callback_3_count = 0

    def test_schedule_interval(self):
        self.clear()
        clock = Clock()
        clock.schedule_interval(self.callback_1, 0.1) 
        clock.schedule_interval(self.callback_2, 0.35)
        clock.schedule_interval(self.callback_3, 0.07)

        t = 0
        while t < 2.04:   # number chosen to avoid +/- 1 errors in div
            t += clock.tick()
        self.assertTrue(self.callback_1_count == int(t / 0.1))
        self.assertTrue(self.callback_2_count == int(t / 0.35))
        self.assertTrue(self.callback_3_count == int(t / 0.07))

    def test_default_schedule_interval(self):
        self.clear()
        # simulate startup
        Clock.set_default(None)
        Clock.schedule_interval(self.callback_1, 0.1) 
        Clock.schedule_interval(self.callback_2, 0.35)
        Clock.schedule_interval(self.callback_3, 0.07)
        clock = Clock()

        t = 0
        while t < 2.04:   # number chosen to avoid +/- 1 errors in div
            t += clock.tick()
        self.assertTrue(self.callback_1_count == int(t / 0.1))
        self.assertTrue(self.callback_2_count == int(t / 0.35))
        self.assertTrue(self.callback_3_count == int(t / 0.07))

    def test_default_unschedule_interval(self):
        self.clear()
        # simulate startup
        Clock.set_default(None)
        Clock.schedule_interval(self.callback_1, 0.1) 
        Clock.schedule_interval(self.callback_2, 0.35)
        Clock.schedule_interval(self.callback_3, 0.07)
        Clock.unschedule(self.callback_2)
        clock = Clock()

        t = 0
        while t < 2.04:   # number chosen to avoid +/- 1 errors in div
            t += clock.tick()
        self.assertTrue(self.callback_1_count == int(t / 0.1))
        self.assertTrue(self.callback_2_count == 0)
        self.assertTrue(self.callback_3_count == int(t / 0.07))



if __name__ == '__main__':
    unittest.main()
