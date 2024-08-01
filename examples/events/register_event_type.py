"""
This example demonstrates an alternative way to register an event type.
The original way looks like this:

    class Foo(EventDispatcher):
        # ...


    Foo.register_event_type('bar')

Instead of calling the classmethod register_event_type() below the implementation of your dispatcher,
you can decorate the latter with the function decorator:

    @register_event_type('bar')
    class Foo(EventDispatcher):
        # ...

All in one place.
"""

import pyglet
from pyglet.event import EventDispatcher


def register_event_type(name):
    def _reg_evt_type(cls):
        assert issubclass(cls, EventDispatcher), "Event types can only be registered on EventDispatcher subclasses"
        if not hasattr(cls, 'event_types'):
            cls.event_types = []

        cls.event_types.append(name)
        return cls

    return _reg_evt_type


def create_alarm(dt):
    alarms.dispatch_event('on_wake_up', dt)


@register_event_type('on_wake_up')
class Alarms(EventDispatcher):
    def on_wake_up(self, dt):
        print(f'Yet another {dt} seconds wasted! Wake up!')


alarms = Alarms()
pyglet.clock.schedule_interval(create_alarm, 30)
pyglet.app.run()
