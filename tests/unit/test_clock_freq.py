"""Tests for clock tick timing and frequency estimation."""

import pytest

from pyglet.clock import Clock


@pytest.fixture
def timed_clock():
    now = [0.0]
    return Clock(time_function=lambda: now[0]), now


def test_first_tick_has_zero_delta(timed_clock):
    clock, _ = timed_clock

    assert clock.tick() == 0


def test_frequency_starts_at_zero(timed_clock):
    clock, _ = timed_clock

    assert clock.get_frequency() == 0


def test_tick_returns_elapsed_time(timed_clock):
    clock, now = timed_clock
    clock.tick()

    now[0] = 1.0
    assert clock.tick() == 1.0

    now[0] = 3.0
    assert clock.tick() == 2.0


def test_compute_frequency(timed_clock):
    clock, now = timed_clock
    expected_frequency = 60
    seconds_per_tick = 1 / expected_frequency
    clock.tick()

    for tick in range(1, 121):
        now[0] = tick * seconds_per_tick
        clock.tick()

    assert clock.get_frequency() == pytest.approx(expected_frequency)
