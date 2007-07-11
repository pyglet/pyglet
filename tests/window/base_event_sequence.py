#!/usr/bin/python
# $Id:$

import unittest
import time

class BaseEventSequence(unittest.TestCase):
    next_sequence = 0
    finished = False
    timeout = 2
    start_time = time.time()

    def check_sequence(self, sequence, name):
        if not self.finished:
            self.assertTrue(self.next_sequence == sequence,
                            '%s out of order' % name)
            print 'OK: %s' % name
            self.next_sequence += 1

    def check_timeout(self):
        self.assertTrue(time.time() - self.start_time < self.timeout)

