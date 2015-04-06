import unittest
from tests import mock
import pyglet.clock


class ClockTestCase(unittest.TestCase):
    """Test clock using dummy time keeper

    not tested:
      positional and named arguments
    """

    def setUp(self):
        self.interval = .001
        self.time = 0
        self.callback_a = mock.Mock()
        self.callback_b = mock.Mock()
        self.callback_c = mock.Mock()
        self.callback_d = mock.Mock()
        self.clock = pyglet.clock.Clock(time_function=lambda: self.time)
        #import pyglet.clock_
        #self.clock = pyglet.clock_.Clock(time_function=lambda: self.time)

    def advance_clock(self, dt=1):
        """simulate the passage of time like a real clock would"""
        frames = 0
        end = self.time + dt
        while self.time < end:
            frames += 1
            self.time += self.interval
            self.clock.tick()
        self.time = round(self.time, 0)
        return frames

    def test_schedule(self):
        self.clock.schedule(self.callback_a)
        frames = self.advance_clock()
        self.assertEqual(self.callback_a.call_count, frames)

    def test_schedule_once(self):
        self.clock.schedule_once(self.callback_a, 1)
        self.advance_clock(2)
        self.assertEqual(self.callback_a.call_count, 1)

    def test_schedule_once_multiple(self):
        self.clock.schedule_once(self.callback_a, 1)
        self.clock.schedule_once(self.callback_b, 2)
        self.advance_clock(2)
        self.assertEqual(self.callback_a.call_count, 1)
        self.assertEqual(self.callback_b.call_count, 1)

    def test_schedule_interval(self):
        self.clock.schedule_interval(self.callback_a, 1)
        self.advance_clock(2)
        self.assertEqual(self.callback_a.call_count, 2)

    def test_schedule_interval_multiple(self):
        self.clock.schedule_interval(self.callback_a, 1)
        self.clock.schedule_interval(self.callback_b, 1)
        self.advance_clock(2)
        self.assertEqual(self.callback_a.call_count, 2)
        self.assertEqual(self.callback_b.call_count, 2)

    def test_schedule_interval_soft(self):
        self.clock.schedule_interval_soft(self.callback_a, 1)
        self.advance_clock(2)
        self.assertEqual(self.callback_a.call_count, 2)

    @unittest.skip('Requires changes to the clock')
    def test_schedule_interval_soft_multiple(self):
        self.clock.schedule_interval(self.callback_a, 1)
        self.clock.schedule_interval_soft(self.callback_b, 1)
        self.clock.schedule_interval_soft(self.callback_b, 1)
        next_ts = set(i.next_ts for i in self.clock._scheduled_items)
        self.assertEqual(len(next_ts), 3)
        self.advance_clock()
        self.assertEqual(self.callback_a.call_count, 1)
        self.assertEqual(self.callback_b.call_count, 2)

    def test_schedule_unschedule(self):
        self.clock.schedule(self.callback_a)
        self.clock.unschedule(self.callback_a)
        self.advance_clock()
        self.assertEqual(self.callback_a.call_count, 0)

    def test_schedule_once_unschedule(self):
        self.clock.schedule_once(self.callback_a, 1)
        self.clock.unschedule(self.callback_a)
        self.advance_clock()
        self.assertEqual(self.callback_a.call_count, 0)

    def test_schedule_interval_unschedule(self):
        self.clock.schedule_interval(self.callback_a, 1)
        self.clock.unschedule(self.callback_a)
        self.advance_clock()
        self.assertEqual(self.callback_a.call_count, 0)

    def test_schedule_interval_soft_unschedule(self):
        self.clock.schedule_interval_soft(self.callback_a, 1)
        self.clock.unschedule(self.callback_a)
        self.advance_clock()
        self.assertEqual(self.callback_a.call_count, 0)

    def test_unschedule_removes_all(self):
        self.clock.schedule(self.callback_a)
        self.clock.schedule_once(self.callback_a, 1)
        self.clock.schedule_interval(self.callback_a, 1)
        self.clock.schedule_interval_soft(self.callback_a, 1)
        self.clock.schedule(self.callback_a)
        self.clock.schedule(self.callback_b)
        self.clock.unschedule(self.callback_a)
        frames = self.advance_clock(10)
        self.assertEqual(self.callback_a.call_count, 0)
        self.assertEqual(self.callback_b.call_count, frames)

    def test_schedule_will_not_call_function(self):
        self.clock.schedule(self.callback_a)
        self.assertEqual(self.callback_a.call_count, 0)
        self.clock.schedule_once(self.callback_a, 0)
        self.assertEqual(self.callback_a.call_count, 0)
        self.clock.schedule_interval(self.callback_a, 1)
        self.assertEqual(self.callback_a.call_count, 0)
        self.clock.schedule_interval_soft(self.callback_a, 1)
        self.assertEqual(self.callback_a.call_count, 0)

    def test_unschedule_will_not_call_function(self):
        self.clock.schedule(self.callback_a)
        self.clock.unschedule(self.callback_a)
        self.assertEqual(self.callback_a.call_count, 0)
        self.clock.schedule_once(self.callback_a, 0)
        self.clock.unschedule(self.callback_a)
        self.assertEqual(self.callback_a.call_count, 0)
        self.clock.schedule_interval(self.callback_a, 1)
        self.clock.unschedule(self.callback_a)
        self.assertEqual(self.callback_a.call_count, 0)
        self.clock.schedule_interval_soft(self.callback_a, 1)
        self.clock.unschedule(self.callback_a)
        self.assertEqual(self.callback_a.call_count, 0)

    def test_unschedule_will_not_fail_if_already_unscheduled(self):
        self.clock.schedule(self.callback_a)
        self.clock.unschedule(self.callback_a)
        self.clock.unschedule(self.callback_a)
        self.clock.schedule_once(self.callback_a, 0)
        self.clock.unschedule(self.callback_a)
        self.clock.unschedule(self.callback_a)
        self.clock.schedule_interval(self.callback_a, 1)
        self.clock.unschedule(self.callback_a)
        self.clock.unschedule(self.callback_a)
        self.clock.schedule_interval_soft(self.callback_a, 1)
        self.clock.unschedule(self.callback_a)
        self.clock.unschedule(self.callback_a)

    def test_call_sched_return_True_if_called_functions(self):
        self.clock.schedule(self.callback_a)
        self.assertTrue(self.clock.call_scheduled_functions(0))

    @unittest.skip('Requires changes to the clock')
    def test_call_sched_return_True_if_called_functions_interval(self):
        self.clock.schedule_once(self.callback_a, 1)
        self.assertFalse(self.clock.call_scheduled_functions(0))
        self.clock.set_time(1)
        self.assertTrue(self.clock.call_scheduled_functions(0))

    def test_call_sched_return_False_if_no_called_functions(self):
        self.assertFalse(self.clock.call_scheduled_functions(0))

    def test_tick_return_last_delta(self):
        self.assertEqual(self.clock.tick(), 0)
        self.time = 1
        self.assertEqual(self.clock.tick(), 1)
        self.time = 3
        self.assertEqual(self.clock.tick(), 2)

    @unittest.skip('Requires changes to the clock')
    def test_get_sleep_time_None_if_no_items(self):
        self.assertIsNone(self.clock.get_sleep_time())

    @unittest.skip('Requires changes to the clock')
    def test_get_sleep_time_can_sleep(self):
        self.clock.schedule_once(self.callback_a, 3)
        self.clock.schedule_once(self.callback_b, 1)
        self.clock.schedule_once(self.callback_c, 6)
        self.clock.schedule_once(self.callback_d, 7)
        self.assertEqual(self.clock.get_sleep_time(), 1)
        self.advance_clock()
        self.assertEqual(self.clock.get_sleep_time(), 2)
        self.advance_clock(2)
        self.assertEqual(self.clock.get_sleep_time(), 3)
        self.advance_clock(3)
        self.assertEqual(self.clock.get_sleep_time(), 1)

    @unittest.skip('Requires changes to the clock')
    def test_get_sleep_time_cannot_sleep(self):
        self.clock.schedule(self.callback_a)
        self.clock.schedule_once(self.callback_b, 1)
        self.assertEqual(self.clock.get_sleep_time(), 0)

    def test_remove_item_during_processing_tasks(self):
        def suicidal_event(dt, sock):
            sock()
            self.clock.unschedule(suicidal_event)

        sock = mock.Mock()
        self.clock.schedule(suicidal_event, sock)
        self.advance_clock()
        self.assertEqual(sock.call_count, 1)

    def test_slow_clock(self):
        """pyglet's clock will not make up for lost time.  in this case, the
        interval scheduled for callback_[bcd] is 1, and 2 seconds have passed.
        since pyglet won't make up for lost time, they are only called once.
        """
        self.clock.schedule(self.callback_a)
        self.clock.schedule_once(self.callback_b, 1)
        self.clock.schedule_interval(self.callback_c, 1)
        self.clock.schedule_interval_soft(self.callback_d, 1)
        self.time = 2
        self.clock.tick()
        self.assertEqual(self.callback_a.call_count, 1)
        self.assertEqual(self.callback_b.call_count, 1)
        self.assertEqual(self.callback_c.call_count, 1)
        self.assertEqual(self.callback_d.call_count, 1)

    @unittest.skip('Requires changes to the clock')
    def test_get_interval(self):
        self.assertEqual(self.clock.get_interval(), 0)
        self.advance_clock(100)
        self.assertEqual(round(self.clock.get_interval(), 10), self.interval)
