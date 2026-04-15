from __future__ import annotations

import os
import subprocess
from typing import Union

from pytest import LogCaptureFixture

import pyglet
from tests.annotations import Platform, require_platform

pytestmark = require_platform(Platform.OSX)

if pyglet.compat_platform in Platform.OSX:
    from pyglet.libs.darwin.cocoapy import (
        TimeConstraintThreadPolicy,
        get_realtime_thread_policy,
        set_realtime_thread_policy,
    )


def _get_current_process_thread_priority() -> int | None:
    """Using commandline `ps` retrieves the priority of the current process thread.

    Returns:
        Priority of current process thread or None if there was an error.
    """
    output = subprocess.check_output(["ps", "-o", "pid,pri"]).decode("utf-8")

    pids_to_priorities = [
        line.split()
        for line in output.splitlines()[
            1:
        ]  # Skip the headers that contain 'PID' and 'PRI'
    ]
    priority = None
    for pid_to_priority in pids_to_priorities:
        if int(pid_to_priority[0]) == os.getpid():
            priority = int(pid_to_priority[1])

    return priority


def test_get_realtime_thread_policy__call_success__TimeConstraintThreadPolicy_with_values_returned(
    caplog: LogCaptureFixture,
):
    caplog.set_level(logging.ERROR)
    actual_time_constraint_thread_policy: TimeConstraintThreadPolicy = (
        get_realtime_thread_policy()
    )

    assert not any(
        record.levelname == "ERROR" for record in caplog.records
    ), "Error was logged, call failed"

    # The actual values may differ depending on what version of MacOS
    # the test is running on, so we are checking that the values are
    # in an expected range after population.
    assert actual_time_constraint_thread_policy.period >= 0
    assert actual_time_constraint_thread_policy.constrain > 0
    assert actual_time_constraint_thread_policy.computation > 0
    assert (
        actual_time_constraint_thread_policy.preemptible == 0
        or actual_time_constraint_thread_policy.preemptible == 1
    )


def test_set_realtime_thread_policy__call_success__current_thread_set_to_realtime_priority(
    caplog: LogCaptureFixture,
):
    caplog.set_level(logging.ERROR)

    set_realtime_thread_policy()

    thread_priority = _get_current_process_thread_priority()

    assert not any(
        record.levelname == "ERROR" for record in caplog.records
    ), "Error was logged, call failed"

    # A previous iteration of this test retrieved the thread priority
    # before calling `set_realtime_thread_policy` to compare that value
    # with the value after the call. Unfortunately, other tests run
    # code paths that call `set_realtime_thread_policy` before this
    # test is run, so we're only checking that the thread priority
    # is a number indicating realtime behavior.
    assert thread_priority > 90
