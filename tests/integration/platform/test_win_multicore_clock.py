#!/usr/bin/env python

# Contributed by Claudio Canepa
# Integrated by Ben Smith

""" There is the possibility that time.clock be non monotonic in multicore hardware, 
due to the underlaying use of win32 QueryPerformanceCounter.
If your update is seeing a negative dt, then time.clock is probably the culprit.
AMD or Intel Patches for multicore may fix this problem (if you see it at all)"""
import time
import sys
from tests.annotations import require_platform, Platform
import unittest

# PYTHON2 - This entire test may no longer be necessary,
#           thanks to Python time module updates.
if sys.version_info[:2] < (3, 5):
    clock = time.clock
else:
    clock = time.perf_counter


@require_platform(Platform.WINDOWS)
class WindowsMulticoreClockTestCase(unittest.TestCase):
    def test_multicore(self):
        failures = 0
        old_time = clock()
        end_time = time.time() + 3
        while time.time() < end_time:
            t = clock()
            if t < old_time:
                failures += 1
            old_time = t
            time.sleep(0.001)
        self.assertTrue(failures == 0)
