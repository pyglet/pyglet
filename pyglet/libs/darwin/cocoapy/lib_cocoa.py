"""macOS only (scheduling)."""
import logging
from ctypes import byref, c_int, c_uint, Structure

import pyglet.lib

logger = logging.getLogger(__name__)

cocoa = pyglet.lib.load_library(framework='Cocoa')

# The following implementation is based on
# https://github.com/histed/PyToolsMH/blob/66867ccfbec8389f8a51665158c7cec1b89d743b/pytoolsMH/macTiming.py

# See thread_policy.h (Darwin)
THREAD_TIME_CONSTRAINT_POLICY = c_int(2)
THREAD_TIME_CONSTRAINT_POLICY_COUNT = c_int(4)

KERNEL_SUCCESS = 0


class TimeConstraintThreadPolicy(Structure):
    _fields_ = [
        ('period', c_uint),
        ('computation', c_uint),
        ('constrain', c_uint),
        ('preemptible', c_int)
    ]


def get_realtime_thread_policy() -> TimeConstraintThreadPolicy | None:
    """Retrieve the default realtime thread policy.

    See https://developer.apple.com/library/archive/documentation/Darwin/Conceptual/KernelProgramming/scheduler/scheduler.html#//apple_ref/doc/uid/TP30000905-CH211-BABHGEFA

    Returns:
        TimeConstraintThreadPolicy if getting the realtime thread policy was successful
        or None if getting the realtime thread policy was not successful.

    """
    timeConstraintThreadPolicy = TimeConstraintThreadPolicy()
    getDefault = c_int(True)  # True to get default thread policy, False to get actual thread policy

    err = cocoa.thread_policy_get(
        cocoa.mach_thread_self(),
        THREAD_TIME_CONSTRAINT_POLICY,
        byref(timeConstraintThreadPolicy),
        byref(THREAD_TIME_CONSTRAINT_POLICY_COUNT),
        byref(getDefault)
    )

    if err != KERNEL_SUCCESS:
        logger.error('Failed to get darwin thread policy with thread_policy_get.')

        return None

    return timeConstraintThreadPolicy


def set_realtime_thread_policy() -> None:
    """Sets the thread policy to realtime behavior.

    See https://developer.apple.com/library/archive/documentation/Darwin/Conceptual/KernelProgramming/scheduler/scheduler.html#//apple_ref/doc/uid/TP30000905-CH211-BABHGEFA
    """
    err = -1
    timeConstraintThreadPolicy = get_realtime_thread_policy()

    if timeConstraintThreadPolicy is not None:
        err = cocoa.thread_policy_set(
            cocoa.mach_thread_self(),
            THREAD_TIME_CONSTRAINT_POLICY,
            byref(timeConstraintThreadPolicy),
            THREAD_TIME_CONSTRAINT_POLICY_COUNT
        )

    if err != KERNEL_SUCCESS or timeConstraintThreadPolicy is None:
        logger.error('Failed to set darwin thread policy with thread_policy_set.')
