import pytest

import pyglet
from pyglet import clock


@pytest.fixture
def event_loop():
    return EventLoopFixture()


class EventLoopFixture(object):
    def run_event_loop(self, duration=None):
        if duration:
            clock.schedule_once(self.interrupt_event_loop, duration)
        pyglet.app.run()

    def interrupt_event_loop(self, *args, **kwargs):
        pyglet.app.exit()

    @staticmethod
    def schedule_once(callback, dt=.1):
        clock.schedule_once(callback, dt)
