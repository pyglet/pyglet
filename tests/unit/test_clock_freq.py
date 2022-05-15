"""Tests clock timing between frames and estimations
of frames per second.
"""
import time
import pytest

from pyglet import clock

from ..annotations import skip_if_continuous_integration


def sleep(seconds):
    """Busy sleep on the CPU which is very precise"""
    start = time.perf_counter()
    while time.perf_counter() - start < seconds:
        pass


@pytest.fixture
def newclock():
    clock.set_default(clock.Clock())
    yield clock


def test_first_tick_is_delta_zero(newclock):
    """
    Tests that the first tick is dt = 0.
    """
    dt = newclock.tick()
    assert dt == 0


def test_start_at_zero_fps(newclock):
    """
    Tests that the default clock starts
    with zero fps.
    """
    fps = newclock.get_frequency()
    assert fps == 0


@skip_if_continuous_integration()
def test_elapsed_time_between_tick():
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
    sleep(sleep_time)
    delta_time_1 = clock.tick()

    # test between non-initialization tick and next tick
    sleep(sleep_time)
    delta_time_2 = clock.tick()

    assert delta_time_1 == pytest.approx(sleep_time, rel=0.01*sleep_time)
    assert delta_time_2 == pytest.approx(sleep_time, rel=0.01*sleep_time)


@skip_if_continuous_integration()
def test_compute_fps():
    """
    Test that the clock computes a reasonable value of
    frames per second when simulated for 120 ticks at 60 frames per second.

    Because sleep is not very precise and fps are unbounded, we
    expect a moderate error (10%) from the expected value.
    """
    ticks = 120  # for averaging
    expected_fps = 60
    seconds_per_tick = 1./expected_fps

    for i in range(ticks):
        time.sleep(seconds_per_tick)
        clock.tick()
    computed_fps = clock.get_frequency()

    assert computed_fps == pytest.approx(expected_fps, rel=0.1*expected_fps)
