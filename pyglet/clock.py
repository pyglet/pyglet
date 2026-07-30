"""Precise framerate calculation function scheduling.

The :py:mod:`~pyglet.clock` module allows you to schedule functions
to run periodically, or for one-shot future execution. pyglet's default
event loop (:py:func:`~pyglet.app.run`) keeps an internal instance of
a :py:class:`~pyglet.clock.Clock`, which is ticked automatically.

.. note:: Some internal modules will schedule items on the clock. If you
          are using a custom event loop, always remember to `tick` the clock!

Scheduling
==========

You can schedule a function to be called every time the clock is ticked::

    def callback(dt):
        print(f"{dt} seconds since last callback")

    clock.schedule(callback)

The `schedule_interval` method causes a function to be called every "n"
seconds::

    clock.schedule_interval(callback, 0.5)   # called twice a second

The `schedule_once` method causes a function to be called once "n" seconds
in the future::

    clock.schedule_once(callback, 5)        # called in 5 seconds

All the `schedule` methods will pass on any additional args or keyword args
you specify to the callback function::

    def move(dt, velocity, sprite):
        sprite.position += dt * velocity

    clock.schedule(move, velocity=5.0, sprite=alien)

You can cancel a function scheduled with any of these methods using
`unschedule`::

    clock.unschedule(move)

Using multiple clocks
=====================

The clock functions are all relayed to an instance of
:py:class:`~pyglet.clock.Clock` which is initialised with the module.  You can
get this instance to use directly::

    clk = pyglet.clock.get_default()

You can also replace the default clock with your own:

    myclk = pyglet.clock.Clock()
    pyglet.clock.set_default(myclk)

Each clock maintains its own set of scheduled functions and frequency
measurement.  Each clock must be "ticked" separately.

Multiple and derived clocks potentially allow you to separate "game-time" and
"wall-time", or to synchronise your clock to an audio or video stream instead
of the system clock.
"""
from __future__ import annotations

import time as _time

from bisect import bisect_left as _bisect_left
from bisect import insort_right as _insort_right
from typing import Any, Callable

from heapq import heappop as _heappop
from heapq import heappush as _heappush
from heapq import heappushpop as _heappushpop
from collections import deque as _deque


class _ScheduledItem:
    __slots__ = ['func', 'args', 'kwargs']

    def __init__(self, func: Callable, args: Any, kwargs: Any) -> None:
        self.func = func
        self.args = args
        self.kwargs = kwargs


class _ScheduledIntervalItem:
    __slots__ = ['func', 'interval', 'last_ts', 'next_ts', 'args', 'kwargs']

    def __init__(self, func: Callable, interval: float, last_ts: float, next_ts: float, args: Any, kwargs: Any) -> None:
        self.func = func
        self.interval = interval
        self.last_ts = last_ts
        self.next_ts = next_ts
        self.args = args
        self.kwargs = kwargs

    def __lt__(self, other: _ScheduledIntervalItem) -> bool:
        return self.next_ts < other.next_ts


class _ScheduledFixedDelayItem(_ScheduledIntervalItem):
    """Marker type for intervals rescheduled from callback completion."""

    __slots__ = ()


class Clock:
    """Schedule callbacks against a single time source.

    Each clock maintains its own scheduled callbacks and frequency
    measurements. Custom clocks can be ticked independently to separate
    gameplay time, UI time, or other application timelines.
    """

    # List of functions to call every tick.
    _schedule_items: list

    # List of schedule interval items kept in sort order.
    _schedule_interval_items: list

    # Lazily-built sorted deadline cache used by the soft scheduler.
    # Creation of soft schedule and recovery of timers is faster.
    _schedule_interval_timestamps: list[float] | None

    # If True, a sleep(0) is inserted on every tick.
    _force_sleep: bool = False

    def __init__(self, time_function: Callable = _time.perf_counter) -> None:
        """Initialize a Clock, with optional custom time function.

        You can provide a custom time function to return the elapsed
        time of the application, in seconds. Defaults to ``time.perf_counter``,
        but can be replaced to allow for easy time dilation effects or game
        pausing.
        """
        self.time = time_function
        self.last_ts = None
        self.next_ts = self.time()

        # Used by self.get_frequency to show update frequency
        self.times: _deque = _deque()
        self.cumulative_time = 0.0
        self.window_size = 60

        self._schedule_items = []
        self._schedule_interval_items = []
        self._schedule_interval_timestamps = None
        self._current_interval_item = None

    @staticmethod
    def sleep(microseconds: float) -> None:
        _time.sleep(microseconds * 1e-6)

    def update_time(self) -> float:
        """Get the elapsed time since the last call to `update_time`.

        This updates the clock's internal measure of time and returns
        the difference (in seconds) since the last time it was called.
        The first call of this method always returns 0.
        """
        ts = self.time()
        if self.last_ts is None:
            delta_t = 0.0
        else:
            delta_t = ts - self.last_ts
            self.times.appendleft(delta_t)
            if len(self.times) > self.window_size:
                self.cumulative_time -= self.times.pop()
        self.cumulative_time += delta_t
        self.last_ts = ts

        return delta_t

    def call_scheduled_functions(self, dt: float) -> bool:
        """Call scheduled functions that elapsed on the last `update_time`.

        This method is called automatically when the clock is ticked
        (see :py:meth:`~pyglet.clock.tick`), so you need not call it
        yourself in most cases.

        Args:
            dt:
                The elapsed time since the last update to pass to each
                scheduled function. This is *not* used to calculate which
                functions have elapsed.

        Returns: ``True`` if any functions were called, else ``False``.
        """
        now = self.last_ts or self.time()
        result = False  # flag indicates if any function was called

        # handle items scheduled for every tick
        if self._schedule_items:
            result = True
            # duplicate list in case event unschedules itself
            for item in list(self._schedule_items):
                item.func(dt, *item.args, **item.kwargs)

        # check the next scheduled item that is not called each tick
        # if it is scheduled in the future, then exit
        interval_items = self._schedule_interval_items
        try:
            if interval_items[0].next_ts > now:
                return result
        except IndexError:
            # The interval_items list is empty
            return result

        # Ordinary heap dispatch does not need the soft scheduler's sorted
        # deadline view. Invalidate it up front; a recovery batch will rebuild
        # it once and keep it synchronized for the rest of that batch.
        self._schedule_interval_timestamps = None

        # NOTE: there is no special handling required to manage things
        #       that are scheduled during this loop, due to the heap
        self._current_interval_item = item = None
        get_soft_next_ts = self._get_soft_next_ts
        while interval_items:

            # the scheduler will hold onto a reference to an item in
            # case it needs to be rescheduled.  it is more efficient
            # to push and pop the heap at once rather than two operations
            if item is None:
                item = _heappop(interval_items)
                timestamps = self._schedule_interval_timestamps
                if timestamps is not None:
                    index = _bisect_left(timestamps, item.next_ts)
                    timestamps.pop(index)
            else:
                if self._schedule_interval_timestamps is None:
                    item = _heappushpop(interval_items, item)
                else:
                    item = self._pushpop_interval_item(item)

            # a scheduled function may try to unschedule itself,
            # so we need to keep a reference to the current
            # item no longer on heap to be able to check
            self._current_interval_item = item

            # if next item is scheduled in the future then break
            if item.next_ts > now:
                break

            scheduled_ts = item.next_ts
            if isinstance(item, _ScheduledFixedDelayItem):
                # Fixed-delay callbacks use their actual start and completion
                # timestamps. Eligibility remains bounded by ``now`` above, so
                # callback runtime cannot pull more timers into this dispatch.
                callback_ts = self.time()
                item.func(callback_ts - item.last_ts, *item.args, **item.kwargs)
                finished_ts = self.time()
                if item.interval:
                    item.last_ts = callback_ts
                    item.next_ts = finished_ts + item.interval
                else:
                    # The callback unscheduled itself while it was executing.
                    self._current_interval_item = item = None
            else:
                # Phase-based callbacks share the clock tick's timestamp.
                item.func(now - item.last_ts, *item.args, **item.kwargs)
                if item.interval:
                    item.last_ts = now
                    # Preserve the requested phase while the following period
                    # is still in the future. If at least one complete period
                    # was missed, coalesce it and spread recovery deadlines.
                    item.next_ts = scheduled_ts + item.interval
                    if item.next_ts <= now:
                        item.next_ts = get_soft_next_ts(now, item.interval)
                else:
                    # The callback unscheduled itself while it was executing.
                    self._current_interval_item = item = None

        if item is not None:
            if self._schedule_interval_timestamps is None:
                _heappush(interval_items, item)
            else:
                self._push_interval_item(item, preserve_timestamps=True)

        return True

    def tick(self, poll: bool = False) -> float:
        """Signify that one frame has passed.

        This will call any scheduled functions that have elapsed,
        and returns the number of seconds since the last time this
        method has been called. The first time this method is called,
        0 is returned.

        Args:
            poll:
                If True, the function will call any scheduled functions
                but will not sleep or busy-wait for any reason.  Recommended
                for advanced applications managing their own sleep timers
                only.
        """
        if not poll and self._force_sleep:
            self.sleep(0)

        delta_t = self.update_time()
        self.call_scheduled_functions(delta_t)
        return delta_t

    def get_sleep_time(self, sleep_idle: bool) -> float | None:
        """Get the time until the next item is scheduled, if any.

        Applications can choose to continue receiving updates at the
        maximum framerate during idle time (when no functions are scheduled),
        or they can sleep through their idle time and allow the CPU to
        switch to other processes or run in low-power mode.

        If ``sleep_idle`` is ``True`` the latter behaviour is selected, and
        ``None`` will be returned if there are no scheduled items.

        Otherwise, if ``sleep_idle`` is ``False``, or if any scheduled items
        exist, a value of 0 is returned.

        Args:
            sleep_idle:
                If True, the application intends to sleep through its idle
                time; otherwise it will continue ticking at the maximum
                frame rate allowed.
        """
        if self._schedule_items or not sleep_idle:
            return 0.0

        if self._schedule_interval_items:
            return max(self._schedule_interval_items[0].next_ts - self.time(), 0.0)

        return None

    def get_frequency(self) -> float:
        """Get the average clock update frequency of recent history.

        The result is the average of a sliding window of the last "n" updates,
        where "n" is some number designed to cover approximately 1 second.
        This is the clock frequency, **not** the Window redraw rate (fps).
        """
        if not self.cumulative_time:
            return 0
        return len(self.times) / self.cumulative_time

    def _get_nearest_ts(self) -> float:
        """Get the nearest timestamp.

        Schedule from now, unless now is sufficiently close to last_ts, in
        which case use last_ts.  This clusters together scheduled items that
        probably want to be scheduled together.
        """
        last_ts = self.last_ts or self.next_ts
        ts = self.time()
        if ts - last_ts > 0.2:
            return ts
        return last_ts

    def _push_interval_item(
        self,
        item: _ScheduledIntervalItem,
        *,
        preserve_timestamps: bool = False,
    ) -> None:
        """Push an interval item and update or invalidate the timestamp cache."""
        _heappush(self._schedule_interval_items, item)
        if preserve_timestamps and self._schedule_interval_timestamps is not None:
            _insort_right(self._schedule_interval_timestamps, item.next_ts)
        else:
            self._schedule_interval_timestamps = None

    def _pushpop_interval_item(self, item: _ScheduledIntervalItem) -> _ScheduledIntervalItem:
        """Push and pop an interval item while keeping a timestamp cache synchronized."""
        timestamps = self._schedule_interval_timestamps
        if timestamps is not None:
            _insort_right(timestamps, item.next_ts)
        popped_item = _heappushpop(self._schedule_interval_items, item)
        if timestamps is not None:
            index = _bisect_left(timestamps, popped_item.next_ts)
            timestamps.pop(index)
        return popped_item

    def _get_soft_next_ts(self, last_ts: float, interval: float) -> float:
        timestamps = self._schedule_interval_timestamps
        if timestamps is None:
            timestamps = sorted(item.next_ts for item in self._schedule_interval_items)
            self._schedule_interval_timestamps = timestamps

        def taken(ts: float, e: float) -> bool:
            """Check if `ts` has already got an item scheduled nearby."""
            # The first timestamp >= ts - e is in range when it is <= ts + e.
            index = _bisect_left(timestamps, ts - e)
            return index < len(timestamps) and timestamps[index] <= ts + e

        # Binary division over interval:
        #
        # 0                          interval
        # |--------------------------|
        #   5  3   6   2   7  4  8   1          Order of search
        #
        # i.e., first scheduled at interval,
        #       then at            interval/2
        #       then at            interval/4
        #       then at            interval*3/4
        #       then at            ...
        #
        # Schedule is hopefully then evenly distributed for any interval,
        # and any number of scheduled functions.

        next_ts = last_ts + interval
        if not taken(next_ts, interval / 4):
            return next_ts

        dt = interval
        divs = 1
        while True:
            next_ts = last_ts
            for _ in range(divs - 1):
                next_ts += dt
                if not taken(next_ts, dt / 4):
                    return next_ts
            dt /= 2
            divs *= 2

            # Avoid infinite loop in pathological case
            if divs > 16:
                return next_ts

    def schedule(self, func: Callable, *args: Any, **kwargs: Any) -> None:
        """Schedule a function to be called every tick.

        The scheduled function should have a prototype that includes ``dt``
        as the first argument, which gives the elapsed time in seconds since
        the last clock tick. Any additional args or kwargs given to this
        method are passed on to the callback::

            def callback(dt, *args, **kwargs):
                pass


        .. note:: Functions scheduled using this method will be called
                  every tick by the default pyglet event loop, which can
                  lead to high CPU usage. It is usually better to use
                  :py:meth:`~pyglet.clock.schedule_interval` unless
                  this is desired.
        """
        item = _ScheduledItem(func, args, kwargs)
        self._schedule_items.append(item)

    def schedule_once(self, func: Callable, delay: float, *args: Any, **kwargs: Any) -> None:
        """Schedule a function to be called once after ``delay`` seconds.

        The callback function prototype is the same as for
        :py:meth:`~pyglet.clock.Clock.schedule`.
        """
        last_ts = self._get_nearest_ts()
        next_ts = last_ts + delay
        item = _ScheduledIntervalItem(func, 0, last_ts, next_ts, args, kwargs)
        _heappush(self._schedule_interval_items, item)
        if self._schedule_interval_timestamps is not None:
            self._schedule_interval_timestamps = None

    def schedule_interval(self, func: Callable, interval: float, *args: Any, **kwargs: Any) -> None:
        """Schedule a function to be called every ``interval`` seconds.

        To schedule a function to be called at 60Hz (60fps), you would use ``1/60``
        for the interval, and so on. The schedule remains aligned with its original
        phase when a callback is called late. If pyglet misses one or more complete
        periods, those calls are skipped (not accumulated) and the schedule is
        moved out of phase with other overdue schedules during recovery. This can
        occur if the main thread is overloaded, or other hard blocking calls take
        place.

        The callback function prototype is the same as for
        :py:meth:`~pyglet.clock.Clock.schedule`.

        .. note:: Specifying an interval of ``0`` will prevent the function from
                  being called again. If you want to schedule a function to be called
                  as often as possible, see :py:meth:`~pyglet.clock.Clock.schedule`.
        """
        last_ts = self._get_nearest_ts()
        next_ts = last_ts + interval
        item = _ScheduledIntervalItem(func, interval, last_ts, next_ts, args, kwargs)
        _heappush(self._schedule_interval_items, item)
        if self._schedule_interval_timestamps is not None:
            self._schedule_interval_timestamps = None

    def schedule_interval_fixed_delay(
        self,
        func: Callable,
        interval: float,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Schedule a function with a fixed delay after each completed call.

        Unlike :py:meth:`~pyglet.clock.Clock.schedule_interval`, the next
        deadline is calculated from the time the callback finishes. This
        prevents a long-running callback from immediately becoming due again
        and naturally moves equal-deadline callbacks out of phase.

        The time from the start of one call to the next is approximately the
        callback's runtime plus ``interval``. Missed calls are never accumulated,
        and callback runtime does not expand the set of callbacks eligible in
        the current clock tick.

        This is useful for polling and maintenance work where the delay between
        completed operations matters more than alignment to an original phase.

        .. note:: Specifying an interval of ``0`` will prevent the function from
                  being called again.

        .. note:: This is not a fixed time step implementation.
        """
        last_ts = self._get_nearest_ts()
        next_ts = last_ts + interval
        item = _ScheduledFixedDelayItem(
            func,
            interval,
            last_ts,
            next_ts,
            args,
            kwargs,
        )
        _heappush(self._schedule_interval_items, item)
        if self._schedule_interval_timestamps is not None:
            self._schedule_interval_timestamps = None

    def schedule_interval_for_duration(self, func: Callable, interval: float,
                                       duration: float, *args: Any, **kwargs: Any) -> None:
        """Temporarily schedule a function to be called every ``interval`` seconds.

        This method will schedule a function to be called every ``interval``
        seconds (see  :py:meth:`~pyglet.clock.Clock.schedule_interval`), but
        will automatically unschedule it after ``duration`` seconds.

        The callback function prototype is the same as for
        :py:meth:`~pyglet.clock.Clock.schedule`.

        :Args:
            func:
                The function to call when the timer lapses.
            interval:
                The number of seconds to wait between each call.
            duration:
                The number of seconds for which the function is scheduled.
        """
        # NOTE: unschedule wrapper that takes `dt` argument
        def _unschedule(_dt: float, _func: Callable) -> None:
            self.unschedule(_func)

        self.schedule_interval(func, interval, *args, **kwargs)
        self.schedule_once(_unschedule, duration, func)

    def schedule_interval_soft(self, func: Callable, interval: float, *args: Any, **kwargs: Any) -> None:
        """Schedule a function to be called approximately every ``interval`` seconds.

        This method is similar to :py:meth:`~pyglet.clock.Clock.schedule_interval`,
        except that the clock will move the interval out of phase with other
        scheduled functions in order to distribute CPU load more evenly.

        This is useful for functions that need to be called regularly,
        but not relative to the initial start time.  :py:mod:`pyglet.media`
        does this for scheduling audio buffer updates, which need to occur
        regularly -- if all audio updates are scheduled at the same time
        (for example, mixing several tracks of a music score, or playing
        multiple videos back simultaneously), the resulting load on the
        CPU is excessive for those intervals but idle outside.  Using
        the soft interval scheduling, the load is more evenly distributed.

        Soft interval scheduling can also be used as an easy way to schedule
        graphics animations out of phase; for example, multiple flags
        waving in the wind.
        """
        next_ts = self._get_soft_next_ts(self._get_nearest_ts(), interval)
        last_ts = next_ts - interval
        item = _ScheduledIntervalItem(func, interval, last_ts, next_ts, args, kwargs)
        self._push_interval_item(item, preserve_timestamps=True)

    def unschedule(self, func: Callable) -> None:
        """Remove a function from the schedule.

        If the function appears in the schedule more than once, all occurrences
        are removed.  If the function was not scheduled, no error is raised.
        """
        # clever remove item without disturbing the heap:
        # 1. set function to an empty lambda -- original function is not called
        # 2. set interval to 0               -- item will be removed from heap eventually
        valid_items = {item for item in self._schedule_interval_items if item.func == func}

        if self._current_interval_item and self._current_interval_item.func == func:
            valid_items.add(self._current_interval_item)

        for item in valid_items:
            item.interval = 0
            item.func = lambda x, *args, **kwargs: x

        self._schedule_items = [i for i in self._schedule_items if i.func != func]


# Default clock.
_default = Clock()


def set_default(default: Clock) -> None:
    """Set the default clock to use for all module-level functions.

    By default, an instance of :py:class:`~pyglet.clock.Clock` is used.
    """
    global _default
    _default = default


def get_default() -> Clock:
    """Get the pyglet default Clock.

    Return the :py:class:`~pyglet.clock.Clock` instance that is used by all
    module-level clock functions.
    """
    return _default


def tick(poll: bool = False) -> float:
    """:see: :py:meth:`~pyglet.clock.Clock.tick`."""
    return _default.tick(poll)


def get_sleep_time(sleep_idle: bool) -> float | None:
    """:see: :py:meth:`~pyglet.clock.Clock.get_sleep_time`."""
    return _default.get_sleep_time(sleep_idle)


def get_frequency() -> float:
    """:see: :py:meth:`~pyglet.clock.Clock.get_frequency`."""
    return _default.get_frequency()


def schedule(func: Callable, *args: Any, **kwargs: Any) -> None:
    """:see: :py:meth:`~pyglet.clock.Clock.schedule`."""
    _default.schedule(func, *args, **kwargs)


def schedule_interval(func: Callable, interval: float, *args: Any, **kwargs: Any) -> None:
    """:see: :py:meth:`~pyglet.clock.Clock.schedule_interval`."""
    _default.schedule_interval(func, interval, *args, **kwargs)


def schedule_interval_fixed_delay(func: Callable, interval: float, *args: Any, **kwargs: Any) -> None:
    """:see: :py:meth:`~pyglet.clock.Clock.schedule_interval_fixed_delay`."""
    _default.schedule_interval_fixed_delay(func, interval, *args, **kwargs)


def schedule_interval_for_duration(func: Callable, interval: float, duration: float, *args, **kwargs) -> None:
    """:see: :py:meth:`~pyglet.clock.Clock.schedule_interval_for_duration`."""
    _default.schedule_interval_for_duration(func, interval, duration, *args, **kwargs)


def schedule_interval_soft(func: Callable, interval: float, *args, **kwargs) -> None:
    """:see: :py:meth:`~pyglet.clock.Clock.schedule_interval_soft`."""
    _default.schedule_interval_soft(func, interval, *args, **kwargs)


def schedule_once(func: Callable, delay: float, *args, **kwargs) -> None:
    """:see: :py:meth:`~pyglet.clock.Clock.schedule_once`."""
    _default.schedule_once(func, delay, *args, **kwargs)


def unschedule(func: Callable) -> None:
    """:see: :py:meth:`~pyglet.clock.Clock.unschedule`."""
    _default.unschedule(func)
