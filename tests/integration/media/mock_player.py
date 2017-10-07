from __future__ import absolute_import, print_function
import pyglet
_debug = False


class MockPlayer(object):
    def __init__(self, event_loop):
        self.event_loop = event_loop
        self.events = []
        self.pyclock = pyglet.clock.get_default()
        super(MockPlayer, self).__init__()

    def dispatch_event(self, event_type, *args):
        super(MockPlayer, self).dispatch_event(event_type, *args)
        if _debug:
            print('{}: event {} received @ {}'.format(self.__class__.__name__,
            	event_type, self.pyclock.time()))
        self.events.append((event_type, args))
        pyglet.clock.unschedule(self.event_loop.interrupt_event_loop)
        self.event_loop.interrupt_event_loop()

    def wait_for_event(self, timeout, *event_types):
        end_time = self.pyclock.time() + timeout

        while self.pyclock.time() < end_time:
            if _debug:
                print('{}: run for {} sec @ {}'.format(self.__class__.__name__,
                	end_time-self.pyclock.time(), self.pyclock.time()))
            self.event_loop.run_event_loop(duration=end_time-self.pyclock.time())
            if not self.events:
                continue
            event_type, args = self.events.pop()
            if event_type in event_types:
                return event_type, args
        return None, None

    def wait_for_all_events(self, timeout, *expected_events):
        now = self.pyclock.time()
        if _debug:
            print('Wait for events @ {}'.format(now))
        end_time = self.pyclock.time() + timeout
        expected_events = list(expected_events)
        received_events = []
        while expected_events:
            event_type, args = self.wait_for_event(timeout, *expected_events)
            if _debug:
                print('{}: got event {} @ {}'.format(self.__class__.__name__,
                	event_type, self.pyclock.time()))
            if event_type is None and self.pyclock.time() >= end_time:
                pytest.fail('Timeout before all events have been received. Still waiting for: '
                        + ','.join(expected_events))
            elif event_type is not None:
                if event_type in expected_events:
                    expected_events.remove(event_type)
                received_events.append((event_type, args))
        return received_events

    def wait(self, timeout):
        now = self.pyclock.time()
        end_time = now + timeout
        while now - end_time < -0.005:
            duration = max(.01, end_time-now)
            self.event_loop.run_event_loop(duration=duration)
            now = self.pyclock.time()