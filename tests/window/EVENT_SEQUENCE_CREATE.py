#!/usr/bin/env python
# $Id: $

import unittest

from pyglet import window

import base_event_sequence

__noninteractive = True

class TEST_CLASS(base_event_sequence.BaseEventSequence):
    def on_resize(self, width, height):
        self.check_sequence(1, 'on_resize')

    def on_show(self):
        self.check_sequence(2, 'on_show')

    def on_expose(self):
        self.check_sequence(3, 'on_expose')
        self.finished = True

    def test_method(self):
        win = window.Window()
        win.push_handlers(self)
        self.check_sequence(0, 'begin')
        while not win.has_exit and not self.finished:
            win.dispatch_events()
            self.check_timeout()

if __name__ == '__main__':
    unittest.main()
