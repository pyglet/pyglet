"""Small, dependency-free benchmarks for pyglet.clock scheduling paths.

Useful for determining regressions in clock performance.
"""

# ruff: noqa: INP001, T201

from __future__ import annotations

import argparse
import gc
import sys
import statistics
import time
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pyglet.clock import Clock

if TYPE_CHECKING:
    from collections.abc import Callable


def _measure(workload: Callable[[], None], repeat: int) -> float:
    samples = []
    for _ in range(repeat):
        gc.collect()
        start = time.perf_counter()
        workload()
        samples.append(time.perf_counter() - start)
    return statistics.median(samples)


def _soft_schedule(count: int) -> None:
    clock = Clock(lambda: 0.0)
    for _ in range(count):
        clock.schedule_interval_soft(None, 1.0)


def _one_shot_schedule(count: int) -> None:
    clock = Clock(lambda: 0.0)

    def callback(_dt: float) -> None:
        pass

    for _ in range(count):
        clock.schedule_once(callback, 3600.0)


def _interval_schedule(count: int) -> None:
    clock = Clock(lambda: 0.0)

    def callback(_dt: float) -> None:
        pass

    for _ in range(count):
        clock.schedule_interval(callback, 3600.0)


def _equal_deadline_dispatch(count: int) -> None:
    now = [0.0]
    clock = Clock(lambda: now[0])

    def callback(_dt: float) -> None:
        pass

    for _ in range(count):
        clock.schedule_once(callback, 1.0)
    now[0] = 1.0
    clock.tick()


def _steady_interval_dispatch(count: int) -> None:
    now = [0.0]
    clock = Clock(lambda: now[0])

    def callback(_dt: float) -> None:
        pass

    for _ in range(count):
        clock.schedule_interval(callback, 1.0)
    for frame in range(1, 11):
        now[0] = float(frame)
        clock.tick()


def _overdue_interval_recovery(count: int) -> None:
    now = [0.0]
    clock = Clock(lambda: now[0])

    def callback(_dt: float) -> None:
        pass

    for _ in range(count):
        clock.schedule_interval(callback, 1.0)
    now[0] = 2.0
    clock.tick()


def _fixed_delay_dispatch(count: int) -> None:
    now = [0.0]
    clock = Clock(lambda: now[0])

    def callback(_dt: float) -> None:
        now[0] += 0.000_001

    for _ in range(count):
        clock.schedule_interval_fixed_delay(callback, 1.0)
    now[0] = 1.0
    clock.tick()


def _staggered_one_shot_schedule(count: int) -> None:
    clock = Clock(lambda: 0.0)

    def callback(_dt: float) -> None:
        pass

    for delay in range(count, 0, -1):
        clock.schedule_once(callback, float(delay))


def _cancel_unique_timers(count: int) -> None:
    clock = Clock(lambda: 0.0)
    callbacks = [lambda _dt, value=value: value for value in range(count)]
    for callback in callbacks:
        clock.schedule_once(callback, 3600.0)
    for callback in callbacks:
        clock.unschedule(callback)


def main() -> None:
    """Run the clock benchmarks and enforce an optional broad time ceiling."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--count', type=int, default=1_000)
    parser.add_argument('--repeat', type=int, default=7)
    parser.add_argument(
        '--max-seconds',
        type=float,
        help='Fail if the median of any benchmark exceeds this broad regression ceiling.',
    )
    args = parser.parse_args()

    benchmarks = (
        ('one-shot schedule', _one_shot_schedule),
        ('interval schedule', _interval_schedule),
        ('soft schedule', _soft_schedule),
        ('equal-deadline dispatch', _equal_deadline_dispatch),
        ('steady interval dispatch', _steady_interval_dispatch),
        ('overdue interval recovery', _overdue_interval_recovery),
        ('fixed-delay dispatch', _fixed_delay_dispatch),
        ('staggered one-shot schedule', _staggered_one_shot_schedule),
        ('cancel unique timers', _cancel_unique_timers),
    )

    print(f'Clock benchmark: {args.count} items, median of {args.repeat} runs')
    regressions = []
    for name, workload in benchmarks:
        duration = _measure(partial(workload, args.count), args.repeat)
        print(f'{name:28}: {duration * 1_000:9.3f} ms')
        if args.max_seconds is not None and duration > args.max_seconds:
            regressions.append((name, duration))

    if regressions:
        details = ', '.join(f'{name}={duration:.3f}s' for name, duration in regressions)
        message = f'Clock benchmark ceiling exceeded: {details}'
        raise SystemExit(message)


if __name__ == '__main__':
    main()
