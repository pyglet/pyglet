
"""Tests clock timing between frames and estimations
of frames per second.
"""

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import time
import unittest

from pyglet import clock

__noninteractive = True


class ClockTimingTestCase(unittest.TestCase):

    def setUp(self):
        # since clock is global,
        # we initialize a new clock on every test
        clock.set_default(clock.Clock())

    def test_first_tick_is_delta_zero(self):
        """
        Tests that the first tick is dt = 0.
        """
        dt = clock.tick()
        self.assertTrue(dt == 0)

    def test_start_at_zero_fps(self):
        """
        Tests that the default clock starts
        with zero fps.
        """
        self.assertTrue(clock.get_fps() == 0)

    def test_elapsed_time_between_tick(self):
        """
        Test that the tick function returns the correct elapsed
        time between frames, in seconds.

        Because we are measuring time differences, we
        expect a small error (1%) from the expected value.
        """
        sleep_time = 0.2

        # initialize internal counter
        clock.tick()

        # test between initialization and first tick
        time.sleep(sleep_time)
        delta_time_1 = clock.tick()

        # test between non-initialization tick and next tick
        time.sleep(sleep_time)
        delta_time_2 = clock.tick()

        self.assertAlmostEqual(delta_time_1, sleep_time, delta=0.01*sleep_time)
        self.assertAlmostEqual(delta_time_2, sleep_time, delta=0.01*sleep_time)

    def test_compute_fps(self):
        """
        Test that the clock computes a reasonable value of
        frames per second when simulated for 10 ticks at 5 frames per second.

        Because sleep is not very precise and fps are unbounded, we
        expect a moderate error (10%) from the expected value.
        """
        ticks = 10  # for averaging
        expected_fps = 5
        seconds_per_tick = 1./expected_fps

        for i in range(ticks):
            time.sleep(seconds_per_tick)
            clock.tick()
        computed_fps = clock.get_fps()

        self.assertAlmostEqual(computed_fps, expected_fps, delta=0.1*expected_fps)

    def test_limit_fps(self):
        """
        Test that the clock effectively limits the
        frames per second to 60 Hz when set to.

        Because the fps are bounded, we expect a small error (1%)
        from the expected value.
        """
        ticks = 20
        fps_limit = 60
        expected_delta_time = ticks*1./fps_limit

        clock.set_fps_limit(fps_limit)

        t1 = time.time()
        # Initializes the timer state.
        clock.tick()
        for i in range(ticks):
            clock.tick()
        t2 = time.time()

        computed_time_delta = t2 - t1

        self.assertAlmostEqual(computed_time_delta,
                               expected_delta_time,
                               delta=0.01*expected_delta_time)


if __name__ == '__main__':
    unittest.main()
