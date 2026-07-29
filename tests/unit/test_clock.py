from __future__ import annotations

import unittest

import pytest

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

    def test_schedule_interval_for_duration(self):
        self.clock.schedule_interval_for_duration(self.callback_a, 1, 5)
        self.advance_clock(10)
        self.assertEqual(self.callback_a.call_count, 4)

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
        # callback_b is used to verify that the entire event queue was not cleared
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

    @unittest.skip
    def test_schedule_item_during_tick(self):
        def replicating_event(dt):
            self.clock.schedule(replicating_event)
            counter()

        counter = mock.Mock()
        self.clock.schedule(replicating_event)

        # one tick for the original event
        self.clock.tick()
        self.assertEqual(counter.call_count, 1)

        # requires access to private member
        self.assertEqual(len(self.clock._schedule_items), 2)

        # one tick from original, then two for new
        # now event queue should have two items as well
        self.clock.tick()
        self.assertEqual(counter.call_count, 3)

        # requires access to private member
        self.assertEqual(len(self.clock._schedule_items), 4)

    def test_unschedule_interval_item_during_tick(self):
        def suicidal_event(dt):
            counter()
            self.clock.unschedule(suicidal_event)

        counter = mock.Mock()
        self.clock.schedule_interval(suicidal_event, 1)
        self.advance_clock()
        self.assertEqual(counter.call_count, 1)

    @unittest.skip
    def test_schedule_interval_item_during_tick(self):
        def replicating_event(dt):
            self.clock.schedule_interval(replicating_event, 1)
            counter()

        counter = mock.Mock()
        self.clock.schedule_interval(replicating_event, 1)

        # advance time for the original event
        self.advance_clock()
        self.assertEqual(counter.call_count, 1)

        # requires access to private member
        self.assertEqual(len(self.clock._schedule_interval_items), 2)

        # one tick from original, then two for new
        # now event queue should have two items as well
        self.advance_clock()
        self.assertEqual(counter.call_count, 3)

        # requires access to private member
        self.assertEqual(len(self.clock._schedule_interval_items), 4)

    def test_scheduler_integrity(self):
        """most tests in this suite do not care about which order
        scheduled items are executed.  this test will verify that
        the order things are executed is correct.
        """
        expected_order = [self.callback_a, self.callback_b,
                          self.callback_c, self.callback_d]

        # schedule backwards to verify that they are scheduled correctly,
        # even if scheduled out-of-order.
        for delay, func in reversed(list(enumerate(expected_order, start=1))):
            self.clock.schedule_once(func, delay)

        for index, func in enumerate(expected_order, start=1):
            self.advance_clock()
            self.assertTrue(func.called)
            self.assertFalse(any(i.called for i in expected_order[index:]))

    def test_slow_clock(self):
        """pyglet's clock will not make up for lost time.  in this case, the
        interval scheduled for callback_[bcd] is 1, and 2 seconds have passed.
        since pyglet won't make up for lost time, they are only called once.
        """
        self.clock.schedule(self.callback_a)
        self.clock.schedule_once(self.callback_b, 1)
        self.clock.schedule_interval(self.callback_c, 1)
        self.clock.schedule_interval_soft(self.callback_d, 1)

        # simulate a slow clock
        self.time = 2
        self.clock.tick()

        self.assertEqual(self.callback_a.call_count, 1)
        self.assertEqual(self.callback_b.call_count, 1)
        self.assertEqual(self.callback_c.call_count, 1)
        self.assertEqual(self.callback_d.call_count, 1)

    def test_slow_clock_reschedules(self):
        """pyglet's clock will not make up for lost time.  in this case, the
        interval scheduled for callback_[bcd] is 1, and 2 seconds have passed.
        since pyglet won't make up for lost time (call events that missed their
        execution time), they are only called once.  this test verifies that
        missed events are rescheduled and executed later
        """
        self.clock.schedule(self.callback_a)
        self.clock.schedule_once(self.callback_b, 1)
        self.clock.schedule_interval(self.callback_c, 1)
        self.clock.schedule_interval_soft(self.callback_d, 1)

        # simulate slow clock
        self.time = 2
        self.clock.tick()

        # simulate a proper clock (advance clock time by one)
        frames = self.advance_clock()

        # make sure our clock is at 3 seconds
        self.assertEqual(self.time, 3)

        # the +1 is the call during the slow clock period
        self.assertEqual(self.callback_a.call_count, frames + 1)

        # only scheduled to happen once
        self.assertEqual(self.callback_b.call_count, 1)

        # 2 because they 'missed' a call when the clock lagged
        # with a good clock, this would be 3
        self.assertEqual(self.callback_c.call_count, 2)
        self.assertEqual(self.callback_d.call_count, 2)

    @unittest.skip('Requires changes to the clock')
    def test_get_interval(self):
        self.assertEqual(self.clock.get_interval(), 0)
        self.advance_clock(100)
        self.assertEqual(round(self.clock.get_interval(), 10), self.interval)

    def test_soft_scheduling_stress_test(self):
        """test that the soft scheduler is able to correctly soft-schedule
        several overlapping events.
        this test delves into implementation of the clock, and may break
        """
        # this value represents evenly scheduled items between 0 & 1
        # and what is produced by the correct soft-scheduler
        expected = [0.0625, 0.125, 0.1875, 0.25, 0.3125, 0.375, 0.4375, 0.5,
                    0.5625, 0.625, 0.6875, 0.75, 0.8125, 0.875, 0.9375, 1]

        for i in range(16):
            self.clock.schedule_interval_soft(None, 1)

        # sort the clock items
        items = sorted(i.next_ts for i in self.clock._schedule_interval_items)

        self.assertEqual(items, expected)


@pytest.fixture
def tween_clock():
    now = [0.0]
    instance = pyglet.clock.Clock(lambda: now[0])
    instance.tick(poll=True)
    return instance, now


def test_easing_functions():
    assert pyglet.clock.linear(0.25) == pytest.approx(0.25)
    assert pyglet.clock.ease_in(0.5) == pytest.approx(0.25)
    assert pyglet.clock.ease_out(0.5) == pytest.approx(0.75)
    assert pyglet.clock.ease_in_out(0.25) == pytest.approx(0.125)
    assert pyglet.clock.ease_in_out(0.75) == pytest.approx(0.875)
    assert pyglet.clock.smoothstep(0.0) == pytest.approx(0.0)
    assert pyglet.clock.smoothstep(0.5) == pytest.approx(0.5)
    assert pyglet.clock.smoothstep(1.0) == pytest.approx(1.0)


@pytest.mark.parametrize(
    ('kwargs', 'exception'),
    [
        ({'duration': -1.0, 'update': lambda _progress: None}, ValueError),
        ({'duration': 1.0, 'update': None}, TypeError),
        ({'duration': 1.0, 'update': lambda _progress: None, 'easing': None}, TypeError),
    ],
)
def test_tween_validates_arguments(kwargs, exception):
    with pytest.raises(exception):
        pyglet.clock.tween(**kwargs)


def test_tween_updates_from_zero_to_one_and_completes(tween_clock):
    instance, now = tween_clock
    values = []
    completed = []

    tween = instance.tween(1.0, values.append)
    tween.add_callbacks(on_complete=completed.append, on_error=pytest.fail).start()

    assert values == [0.0]

    now[0] = 0.25
    instance.tick(poll=True)
    now[0] = 1.0
    instance.tick(poll=True)
    instance.tick(poll=True)

    assert values == [0.0, 0.25, 1.0]
    assert completed == [None]
    assert instance.get_sleep_time(True) is None


def test_zero_duration_tween_completes_immediately(tween_clock):
    instance, _now = tween_clock
    values = []
    completed = []

    tween = instance.tween(0.0, values.append)
    tween.add_callbacks(on_complete=completed.append, on_error=pytest.fail).start()

    assert values == [1.0]
    instance.tick(poll=True)
    assert completed == [None]
    assert instance.get_sleep_time(True) is None


def test_tween_pause_excludes_paused_time(tween_clock):
    instance, now = tween_clock
    values = []
    tween = instance.tween(1.0, values.append).start()

    now[0] = 0.25
    instance.tick(poll=True)
    tween.pause()

    now[0] = 10.0
    instance.tick(poll=True)
    assert values == [0.0, 0.25]

    tween.resume()
    now[0] = 10.25
    instance.tick(poll=True)
    assert values == [0.0, 0.25, 0.5]


def test_tween_failure_is_reported(tween_clock):
    instance, now = tween_clock
    error = RuntimeError('update failed')
    failures = []

    def update(progress):
        if progress:
            raise error

    tween = instance.tween(1.0, update)
    tween.add_callbacks(
        on_complete=lambda _result: pytest.fail('completed unexpectedly'),
        on_error=failures.append,
    ).start()

    now[0] = 0.5
    instance.tick(poll=True)
    instance.tick(poll=True)
    instance.tick(poll=True)

    assert failures == [error]
    assert instance.get_sleep_time(True) is None


def test_chain_can_yield_module_clock_tween(tween_clock):
    instance, now = tween_clock
    default = pyglet.clock.get_default()
    pyglet.clock.set_default(instance)

    class Sprite:
        opacity = 255.0
        deleted = False

        def delete(self):
            self.deleted = True

    class FadeOut:
        def __init__(self, target):
            self.target = target
            self.start_opacity = target.opacity

        def __call__(self, progress):
            self.target.opacity = self.start_opacity * (1.0 - progress)

    @pyglet.clock.chain
    def remove_sprite(sprite):
        yield pyglet.clock.tween(0.5, FadeOut(sprite))
        sprite.delete()

    try:
        sprite = Sprite()
        chain = remove_sprite(sprite).start()
        now[0] = 0.25
        instance.tick(poll=True)
        assert sprite.opacity == pytest.approx(127.5)
        assert not sprite.deleted

        now[0] = 0.5
        instance.tick(poll=True)
        instance.tick(poll=True)
        instance.tick(poll=True)
    finally:
        pyglet.clock.set_default(default)

    assert chain.done
    assert sprite.opacity == pytest.approx(0.0)
    assert sprite.deleted


def test_tweens_can_run_in_parallel(tween_clock):
    instance, now = tween_clock
    first_values = []
    second_values = []

    @instance.chain
    def sequence():
        return (
            yield instance.parallel(
                instance.tween(0.5, first_values.append),
                instance.tween(1.0, second_values.append),
            )
        )

    chain = sequence().start()
    now[0] = 0.5
    instance.tick(poll=True)
    instance.tick(poll=True)
    now[0] = 1.0
    instance.tick(poll=True)
    instance.tick(poll=True)
    instance.tick(poll=True)

    assert chain.done
    assert chain.result == (None, None)
    assert first_values[-1] == pytest.approx(1.0)
    assert second_values[-1] == pytest.approx(1.0)


def test_tweens_can_race(tween_clock):
    instance, now = tween_clock
    slow_values = []

    @instance.chain
    def sequence():
        return (
            yield instance.race(
                instance.tween(0.5, lambda _progress: None),
                instance.tween(1.0, slow_values.append),
            )
        )

    chain = sequence().start()
    now[0] = 0.5
    instance.tick(poll=True)
    instance.tick(poll=True)
    instance.tick(poll=True)

    assert chain.done
    assert chain.result == (0, None)
    assert slow_values[-1] == pytest.approx(0.5)
    assert instance.get_sleep_time(True) is None


def test_stopping_chain_cancels_its_tween(tween_clock):
    instance, now = tween_clock
    values = []

    @instance.chain
    def sequence():
        yield instance.tween(1.0, values.append)

    chain = sequence().start()
    now[0] = 0.25
    instance.tick(poll=True)
    chain.stop()

    now[0] = 1.0
    instance.tick(poll=True)
    assert values == [0.0, 0.25]
    assert instance.get_sleep_time(True) is None


def test_clock_uses_one_scheduled_callback_for_multiple_tweens(tween_clock):
    instance, _now = tween_clock

    first = instance.tween(1.0, lambda _progress: None).start()
    second = instance.tween(1.0, lambda _progress: None).start()

    assert len(instance._schedule_items) == 1  # noqa: SLF001

    first.stop()
    second.stop()
    assert instance.get_sleep_time(True) is None
