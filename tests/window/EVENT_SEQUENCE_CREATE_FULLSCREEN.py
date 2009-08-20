#!/usr/bin/env python
# $Id: $

import unittest

from pyglet import window

import base_event_sequence

__noninteractive = True

class TEST_CLASS(base_event_sequence.BaseEventSequence):
    last_sequence = 3

    def on_resize(self, width, height):
        self.check_sequence(1, 'on_resize')

    def on_show(self):
        self.check_sequence(2, 'on_show')

    def on_expose(self):
        self.check_sequence(3, 'on_expose')

    def test_method(self):
        win = window.Window(fullscreen=True)
        win.push_handlers(self)
        self.check_sequence(0, 'begin')
        while not win.has_exit and not self.finished:
            win.dispatch_events()
            self.check_timeout()
        win.close()
if __name__ == '__main__':
    unittest.main()
