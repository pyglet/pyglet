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
        warmup_iterations = iterations

        self.last_t = 0.
        self.timer_count = 0
        def f(dt):
            t = time()
            self.timer_count += 1
            tc = self.timer_count
            if tc > warmup_iterations:
                self.assertAlmostEqual(dt, interval, 2)
                self.assertAlmostEqual(t - self.last_t, interval, 2)
            self.last_t = t

            if self.timer_count > iterations + warmup_iterations:
                pyglet.app.exit()
            if sleep_time:
                sleep(sleep_time)

        pyglet.clock.schedule_interval(f, interval)
        try:
            pyglet.app.run()
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
    if pyglet.version != '1.2dev':
        print 'Wrong version of pyglet imported; please check your PYTHONPATH'
    else:
        unittest.main()
