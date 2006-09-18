#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import time
from ctypes import *

clib = cdll.LoadLibrary('libc.so.6')
clib.usleep.argtypes = [c_ulong]

class Clock:
    last_ts = None
    calibration = 0

    @classmethod
    def calibrate(cls, time=time.time):
        test = cls().set_fps
        s = time()
        for i in xrange(100): test(100)
        d = time() - s - 1
        cls.calibration = d/100
        print 'CALIBRATION = %f'%cls.calibration

    def set_fps(self, fps, time=time.time, usleep=clib.usleep):
        delay = 1. / fps
        ts = time()
        if self.last_ts is None:
            self.last_ts = ts
            return 0
        self.last_ts = ts
        actual = ts - self.last_ts
        sleeptime = (delay - actual) - self.calibration
        if sleeptime > 0:
            usleep(int(sleeptime * 1000000))
            return delay
        else:
            return actual

if __name__ == '__main__':
    Clock.calibrate()
    s = time.time()
    c = Clock()
    for i in xrange(100):
        c.set_fps(50)
    print time.time() - s

