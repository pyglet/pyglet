#!/usr/bin/python
'''Test that the event loop can do timing.

The test will display a series of intervals, iterations and sleep times.
It should then display an incrementing number up to 2x the number of
iterations, at a rate determined by the interval.
'''

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
        print 'Test interval=%s, iterations=%s, sleep=%s' % (interval,
            iterations, sleep_time)
        warmup_iterations = iterations

        self.last_t = 0.
        self.timer_count = 0
        def f(dt):
            sys.stdout.write('%s\r' % self.timer_count)
            sys.stdout.flush()
            t = time()
            self.timer_count += 1
            tc = self.timer_count
            if tc > warmup_iterations:
                self.assertAlmostEqual(dt, interval, places=2)
                self.assertAlmostEqual(t - self.last_t, interval, places=2)
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
        print

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
