from future.standard_library import install_aliases
install_aliases()

from builtins import object
import queue
import unittest
import time

from pyglet import window


class EventSequenceFixture(object):
    def __init__(self, event_loop):
        self.event_loop = event_loop
        self.listen_events = []
        self.received_events = queue.Queue()

    def create_window(self, **kwargs):
        w = event_loop.create_window(**kwargs)
        w.push_handlers(self)
        return w

    def wait_for_events(self, expected_events, incorrect_events):
        if isinstance(expected_events, (tuple, list)):
            self.listen_events = expected_events
        else:
            self.listen_events = [expected_events]

        while True:
            # check events
            self.event_loop.run_event_loop()

    def __getattr__(self, name):
        if name.startswith('on_'):
            return self._handle_event
        else:
            raise AttributeError()

    def _handle_event(self, name, *args, **kwargs):
        if name in self.listen_events:
            q.put((name, args, kwargs))
            self.event_loop.interrupt_event_loop()


class EventSequenceTest(object):
    """Base for testing event sequences on a window."""
    next_sequence = 0
    last_sequence = 0
    finished = False
    timeout = 2
    start_time = time.time()

    def check_sequence(self, sequence, name):
        if self.next_sequence == 0 and sequence != 0:
            print('received event before test start:', name)
            return
        if sequence == 0:
            self.start_time = time.time()
        if not self.finished:
            if self.next_sequence != sequence:
                self.failed = 'ERROR: %s out of order' % name
            else:
                self.next_sequence += 1
        if self.next_sequence > self.last_sequence:
            self.finished = True

    def check(self):
        self.assertTrue(time.time() - self.start_time < self.timeout,
                        'Did not receive next expected event: %d' % self.next_sequence)
        failed = getattr(self, 'failed', None)
        if failed:
            self.fail(failed)


class WindowShowEventSequenceTest(EventSequenceTest, unittest.TestCase):
    """Event sequence when hidden window is set to visible."""
    last_sequence = 3

    def on_resize(self, width, height):
        self.check_sequence(1, 'on_resize')

    def on_show(self):
        self.check_sequence(2, 'on_show')

    def on_expose(self):
        self.check_sequence(3, 'on_expose')

    def test_method(self):
        window.Window._enable_event_queue = True
        win = window.Window(visible=False)
        try:
            win.dispatch_events()
            win.push_handlers(self)

            win.set_visible(True)
            self.check_sequence(0, 'begin')
            while not win.has_exit and not self.finished:
                win.dispatch_events()
                self.check()
        finally:
            win.close()


class WindowCreateEventSequenceTest(EventSequenceTest, unittest.TestCase):
    last_sequence = 3

    def on_resize(self, width, height):
        self.check_sequence(1, 'on_resize')

    def on_show(self):
        self.check_sequence(2, 'on_show')

    def on_expose(self):
        self.check_sequence(3, 'on_expose')

    def test_method(self):
        window.Window._enable_event_queue = True
        win = window.Window()
        try:
            win.push_handlers(self)
            self.check_sequence(0, 'begin')
            while not win.has_exit and not self.finished:
                win.dispatch_events()
                self.check()
        finally:
            win.close()


class WindowCreateFullScreenEventSequenceTest(EventSequenceTest, unittest.TestCase):
    last_sequence = 3

    def on_resize(self, width, height):
        self.check_sequence(1, 'on_resize')

    def on_show(self):
        self.check_sequence(2, 'on_show')

    def on_expose(self):
        self.check_sequence(3, 'on_expose')

    def test_method(self):
        window.Window._enable_event_queue = True
        win = window.Window(fullscreen=True)
        try:
            win.push_handlers(self)
            self.check_sequence(0, 'begin')
            while not win.has_exit and not self.finished:
                win.dispatch_events()
                self.check()
        finally:
            win.close()


class WindowSetFullScreenEventSequenceTest(EventSequenceTest, unittest.TestCase):
    last_sequence = 2

    def on_resize(self, width, height):
        self.check_sequence(1, 'on_resize')

    def on_expose(self):
        self.check_sequence(2, 'on_expose')

    def test_method(self):
        window.Window._enable_event_queue = True
        win = window.Window()
        try:
            win.dispatch_events()

            win.push_handlers(self)
            win.set_fullscreen()
            self.check_sequence(0, 'begin')
            while not win.has_exit and not self.finished:
                win.dispatch_events()
                self.check()
        finally:
            win.close()


class WindowUnsetFullScreenEventSequenceTest(EventSequenceTest, unittest.TestCase):
    last_sequence = 2

    def on_resize(self, width, height):
        self.check_sequence(1, 'on_resize')

    def on_expose(self):
        self.check_sequence(2, 'on_expose')

    def test_method(self):
        window.Window._enable_event_queue = True
        win = window.Window(fullscreen=True)
        try:
            win.dispatch_events()
            win.push_handlers(self)

            win.set_fullscreen(False)
            self.check_sequence(0, 'begin')
            while not win.has_exit and not self.finished:
                win.dispatch_events()
                self.check()
        finally:
            win.close()
