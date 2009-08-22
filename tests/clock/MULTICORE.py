#!/usr/bin/env python

# Contributed by Claudio Canepa
# Integrated by Ben Smith

""" There is the possibility that time.clock be non monotonic in multicore hardware, 
due to the underlaying use of win32 QueryPerformanceCounter.
If your update is seeing a negative dt, then time.clock is probably the culprit.
AMD or Intel Patches for multicore may fix this problem (if you see it at all)"""

__docformat__ = 'restructuredtext'
__version__ = '$Id$'


import time
import unittest

__noninteractive = True


class MULTICORE(unittest.TestCase):
    def test_multicore(self):
        failures = 0
        old_time = time.clock()
        end_time = time.time() + 3
        while time.time() < end_time:
           t = time.clock()
           if t < old_time:
               failures += 1
           old_time = t
           time.sleep(0.001)
        self.assertTrue(failures == 0)
        
if __name__ == '__main__':
    unittest.main()
