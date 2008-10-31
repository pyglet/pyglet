#!/usr/bin/python
# $Id:$

import sys
import unittest

import pyglet

__noninteractive = True

if sys.platform in ('win32', 'cygwin'):
    from time import clock as time
else:
    from time import time
from time import sleep

class EVENT_LOOP(unittest.TestCase):
    def t_scheduled(self, interval, iterations, sleep_time=0):
        self.last_t = 0.
        self.timer_count = 0
        def f(dt):
            t = time()
            self.assertAlmostEqual(dt, interval, 1)
            self.assertAlmostEqual(t - self.last_t, interval, 2)
            self.last_t = t
            self.timer_count += 1
            if sleep_time:
                sleep(sleep_time)

        event_loop = pyglet.app.event_loop
        platform_event_loop = pyglet.app.platform_event_loop
        platform_event_loop.start()

        # Reset last clock time; a bit of a hack, because pyglet isn't really
        # designed to be run twice from the same process.
        pyglet.clock.tick()
        self.last_t = time()
        pyglet.clock.schedule_interval(f, interval)

        # Run app.run() for a short time only.
        try:
            while self.timer_count < iterations:
                timeout = event_loop.idle()
                platform_event_loop.step(timeout)
            platform_event_loop.stop()
        finally:
            pyglet.clock.unschedule(f)

    def test_1_5(self):
        self.t_scheduled(1, 5, 0)

    def test_1_5_d5(self):
        self.t_scheduled(1, 5, 0.5)

    def test_d1_50(self):
        self.t_scheduled(.1, 50)

    def test_d1_50_d05(self):
        self.t_scheduled(.1, 50, 0.05)

    def test_d05_50(self):
        self.t_scheduled(.05, 50)

    def test_d05_50_d03(self):
        self.t_scheduled(.05, 50, 0.03)

    def test_d02_50(self):
        self.t_scheduled(.02, 50)

    def test_d01_50(self):
        self.t_scheduled(.01, 50)

if __name__ == '__main__':
    unittest.main()
