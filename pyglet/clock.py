#!/usr/bin/env python

'''Precise framerate calculation and framerate limiting.

General use::

    >>> clock = Clock()
    >>> while True:
    ...     dt = clock.tick()
    ...     # (update, render)
    ...     print 'FPS is %f' % clock.get_fps()
    >>>

The `dt` value returned gives the number of seconds (as a float) since the
last "tick".  You can also limit the framerate::

    >>> clock = Clock(20)       # limits to 20 FPS
    >>>

The implementation uses platform-dependent high-resolution sleep functions
to achieve better accuracy with busy-waiting than would be possible using
just the `time` module.  

The `get_fps` function averages the framerate over a sliding window of
approximately 1 second.  (You can calculate the absolute framerate by taking
the reciprocal of `dt`).

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import time
import sys
import operator
import ctypes
import ctypes.util

if sys.platform in ('win32', 'cygwin'):
    # Win32 Sleep function is only 10-millisecond resolution, so instead
    # use a waitable timer object, which has up to 100-nanosecond resolution
    # (hardware and implementation dependent, of course).
    _kernel32 = ctypes.windll.kernel32
    class _ClockBase(object):
        def __init__(self):
            self._timer = _kernel32.CreateWaitableTimerA(ctypes.c_void_p(), 
                True, ctypes.c_void_p())

        def sleep(self, microseconds):
            delay = ctypes.c_longlong(int(-microseconds * 10))
            _kernel32.SetWaitableTimer(self._timer, ctypes.byref(delay), 
                0, ctypes.c_void_p(), ctypes.c_void_p(), False)
            _kernel32.WaitForSingleObject(self._timer, 0xffffffff)

else:
    path = ctypes.util.find_library('c')
    if not path:
        raise ImportError('libc not found')
    _c = ctypes.cdll.LoadLibrary(path)
    _c.usleep.argtypes = [ctypes.c_ulong]

    class _ClockBase(object):
        def sleep(self, microseconds):
            _c.usleep(int(microseconds))

class Clock(_ClockBase):
    '''Class for calculating and limiting framerate.  See the module
    docstring for usage.
    '''

    # No attempt to sleep will be made for less than this time.  Setting
    # high will increase accuracy and CPU burn.  Setting low reduces accuracy
    # but ensures more sleeping takes place rather than busy-loop.
    MIN_SLEEP = 0.005

    # Sleep by the desired amount minus this bit.  This is to compensate
    # for operating systems being a bit lazy in returning control.
    SLEEP_UNDERSHOOT = MIN_SLEEP - 0.001

    def __init__(self, fps_limit=None, time_function=time.time):
        '''Initialise a Clock, with optional framerate limit and custom
        time function.

        :Parameters:
            `fps_limit` : float
                If not None, the maximum allowable framerate.  Defaults
                to None.
            `time_function` : function
                Function to return the elapsed time of the application, 
                in seconds.  Defaults to time.time, but can be replaced
                to allow for easy time dilation effects or game pausing.

        '''

        super(Clock, self).__init__()
        self.time = time_function
        self.next_ts = self.time()
        self.last_ts = None
        self.times = []

        self.set_fps_limit(fps_limit)
        self.cumulative_time = 0

    def tick(self):
        '''Signify that one frame has passed.

        :return: The number of seconds (as a float) since the last `tick`,
            or 0 if this was the first frame.

        '''
        if self.period_limit:
            self.limit()

        ts = self.time()
        if self.last_ts is None: 
            delta_t = 0
        else:
            delta_t = ts - self.last_ts
            self.times.insert(0, delta_t)
            if len(self.times) > self.window_size:
                self.cumulative_time -= self.times.pop()
        self.cumulative_time += delta_t
        self.last_ts = ts

        return delta_t

    def limit(self):
        '''Sleep until the next frame is due.  Called automatically by
        `tick` if a framerate limit has been set.

        This method uses several heuristics to determine whether to
        sleep or busy-wait (or both).
        '''
        ts = self.time()
        # Sleep to just before the desired time
        sleeptime = self.next_ts - self.time()
        while sleeptime - self.SLEEP_UNDERSHOOT > self.MIN_SLEEP:
            self.sleep(1000000 * (sleeptime - self.SLEEP_UNDERSHOOT))
            sleeptime = self.next_ts - self.time()

        # Busy-loop CPU to get closest to the mark
        sleeptime = self.next_ts - self.time()
        while sleeptime > 0:
            sleeptime = self.next_ts - self.time()

        if sleeptime < -2 * self.period_limit:
            # Missed the time by a long shot, let's reset the clock
            # print >> sys.stderr, 'Step %f' % -sleeptime
            self.next_ts = ts + 2 * self.period_limit
        else:
            # Otherwise keep the clock steady
            self.next_ts = self.next_ts + self.period_limit

    def set_fps_limit(self, fps_limit):
        '''Set the framerate limit.

        :Parameters:
            `fps_limit` : float
                Maximum frames per second allowed, or None to disable
                limiting.

        '''
        if not fps_limit:
            self.period_limit = None
        else:
            self.period_limit = 1. / fps_limit
        self.window_size = fps_limit or 60

    def get_fps_limit(self):
        '''Get the framerate limit.

        :return: The framerate limit previously set in the constructor or
            `set_fps_limit`, or None if no limit was set.

        '''
        if self.period_limit:
            return 1. / self.period_limit
        else:
            return 0

    def get_fps(self):
        '''Get the average FPS of recent history, as a float.  The result
        is the average of a sliding window of the last `n` frames, where
        `n` is some number designed to cover approximately 1 second.

        :return: The measured frames per second.
        '''
        if not self.times: 
            return 0
        return len(self.times) / self.cumulative_time

if __name__ == '__main__':
    import sys
    import getopt
    test_seconds = 1 
    test_fps = 60
    show_fps = False
    options, args = getopt.getopt(sys.argv[1:], 'vht:f:', 
        ['time=', 'fps=', 'help'])
    for key, value in options:
        if key in ('-t', '--time'):
            test_seconds = float(value)
        elif key in ('-f', '--fps'):
            test_fps = float(value)
        elif key in ('-v'):
            show_fps = True
        elif key in ('-h', '--help'):
            print ('Usage: clock.py <options>\n'
                   '\n'
                   'Options:\n'
                   '  -t   --time       Number of seconds to run for.\n'
                   '  -f   --fps        Target FPS.\n'
                   '\n'
                   'Tests the clock module by measuring how close we can\n'
                   'get to the desired FPS by sleeping and busy-waiting.')
            sys.exit(0) 

    c = Clock(test_fps)
    start = time.time()

    # Add one because first frame has no update interval.
    n_frames = int(test_seconds * test_fps + 1)

    print 'Testing %f FPS for %f seconds...' % (test_fps, test_seconds)
    for i in xrange(n_frames):
        c.tick()
        if show_fps:
            print c.get_fps()
    total_time = time.time() - start
    total_error = total_time - test_seconds
    print 'Total clock error: %f secs' % total_error
    print 'Total clock error / secs: %f secs/secs' % \
        (total_error / test_seconds)

    # Not fair to add the extra frame in this calc, since no-one's interested
    # in the startup situation.
    print 'Average FPS: %f' % ((n_frames - 1) / total_time)

