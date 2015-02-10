#!/usr/bin/python
# $Id:$

import unittest
import time

class BaseEventSequence(unittest.TestCase):
    next_sequence = 0
    last_sequence = 0
    finished = False
    timeout = 2
    start_time = time.time()

    def check_sequence(self, sequence, name):
        if self.next_sequence == 0 and sequence != 0:
            return
        if sequence == 0:
            self.start_time = time.time()
        if not self.finished:
            if self.next_sequence != sequence:
                print 'ERROR: %s out of order' % name
            else:
                print 'OK: %s' % name
                self.next_sequence += 1
        if self.next_sequence > self.last_sequence:
            self.finished = True

    def check_timeout(self):
        self.assertTrue(time.time() - self.start_time < self.timeout)

