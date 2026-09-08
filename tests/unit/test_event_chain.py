from __future__ import annotations

import pytest

import pyglet.clock
import pyglet.event


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.scheduled = []
        self.scheduled_once = []

    def schedule_once(self, func, delay):
        self.scheduled_once.append([func, delay])

    def schedule(self, func):
        self.scheduled.append(func)

    def unschedule(self, func):
        self.scheduled = [callback for callback in self.scheduled if callback != func]
        self.scheduled_once = [item for item in self.scheduled_once if item[0] != func]

    def time(self):
        return self.now

    def tick(self, dt=0.0):
        pending_once = list(self.scheduled_once)
        self.now += dt
        for callback in list(self.scheduled):
            callback(dt)
        for item in pending_once:
            if item not in self.scheduled_once:
                continue
            item[1] -= dt
            if item[1] <= 1e-12:
                self.scheduled_once.remove(item)
                item[0](dt)

    def run_once(self):
        callback, delay = self.scheduled_once.pop(0)
        self.now += delay
        callback(delay)


@pytest.fixture
def fake_clock():
    clock = FakeClock()
    default_clock = pyglet.clock.get_default()
    pyglet.clock.set_default(clock)
    try:
        yield clock
    finally:
        pyglet.clock.set_default(default_clock)


def test_chain_yields_delay_and_completes(fake_clock):
    events = []

    @pyglet.clock.chain
    def sequence():
        events.append('started')
        yield 0.25
        events.append('finished')
        return 'done'

    chain = sequence().add_callbacks(on_complete=events.append).start()

    assert chain.clock is fake_clock
    assert chain.running
    assert not chain.done
    assert events == ['started']
    assert fake_clock.scheduled == []
    assert len(fake_clock.scheduled_once) == 1

    fake_clock.tick(0.24)

    assert not chain.done

    fake_clock.tick(0.01)

    assert not chain.running
    assert chain.done
    assert chain.completed
    assert not chain.stopped
    assert not chain.failed
    assert chain.result == 'done'
    assert events == ['started', 'finished', 'done']


def test_chain_callbacks_support_builtin_bound_methods(fake_clock):
    # Should pass on normal pythons to may pypy happy.
    events = []

    @pyglet.clock.chain
    def sequence():
        yield 0
        return 'done'

    sequence().add_callbacks(on_complete=events.append).start()
    fake_clock.tick()

    assert events == ['done']


def test_chain_invokes_lifecycle_callbacks(fake_clock):
    events = []

    @pyglet.clock.chain
    def sequence():
        yield 0.5
        return 'done'

    chain = sequence()
    chain.add_callbacks(
        on_pause=lambda: events.append('paused'),
        on_resume=lambda: events.append('resumed'),
        on_complete=lambda result: events.append(result),
    )
    chain.start()
    chain.pause()
    chain.resume()
    fake_clock.tick(0.5)

    assert events == ['paused', 'resumed', 'done']


def test_chain_invokes_all_completion_callbacks_in_registration_order(fake_clock):
    events = []

    @pyglet.clock.chain
    def sequence():
        yield 0
        return 'done'

    def first(result):
        events.append(('first', result))
        return True

    chain = sequence()
    chain.add_callbacks(on_complete=first)
    chain.add_callbacks(on_complete=lambda result: events.append(('second', result)))
    chain.start()
    fake_clock.tick()

    assert events == [('first', 'done'), ('second', 'done')]


def test_chain_allows_default_lifecycle_event_handlers(fake_clock):
    events = []

    @pyglet.clock.chain
    def sequence():
        yield 0.5
        return 'done'

    chain = sequence()
    chain.add_callbacks(on_complete=events.append)
    chain.start()
    fake_clock.tick(0.5)

    assert events == ['done']


def test_chain_can_be_created_for_explicit_clock(fake_clock):
    events = []
    game_time = [0.0]
    game_clock = pyglet.clock.Clock(lambda: game_time[0])

    @game_clock.chain
    def sequence():
        yield 0.5
        events.append('game clock')

    chain = sequence().start()

    assert chain.clock is game_clock
    assert fake_clock.scheduled == []

    game_clock.tick(poll=True)
    game_time[0] = 0.5
    game_clock.tick(poll=True)

    assert events == ['game clock']


def test_clock_instance_chain_binds_to_that_clock(fake_clock):
    events = []
    game_time = [0.0]
    game_clock = pyglet.clock.Clock(lambda: game_time[0])

    @game_clock.chain
    def sequence():
        yield 0.5
        events.append('bound clock')

    chain = sequence().start()

    assert chain.clock is game_clock
    assert fake_clock.scheduled == []

    game_clock.tick(poll=True)
    game_time[0] = 0.5
    game_clock.tick(poll=True)

    assert events == ['bound clock']


def test_clock_instance_parallel_binds_children_to_that_clock(fake_clock):
    events = []
    game_time = [0.0]
    game_clock = pyglet.clock.Clock(lambda: game_time[0])

    @game_clock.chain
    def child(name):
        yield 0.5
        return name

    @game_clock.chain
    def parent():
        results = yield game_clock.parallel(child('first'), child('second'))
        events.append(results)

    parent().start()

    assert fake_clock.scheduled == []

    game_clock.tick(poll=True)
    game_time[0] = 0.5
    game_clock.tick(poll=True)
    game_clock.tick(poll=True)

    assert events == [('first', 'second')]


def test_chain_group_tracks_and_removes_completed_chains(fake_clock):
    events = []
    group = pyglet.clock.ChainGroup()

    assert group.clock is fake_clock

    @pyglet.clock.chain
    def sequence():
        yield 0.1
        events.append('finished')
        return 'done'

    chain = group.start(sequence(), tag='fade')

    assert group.chains == (chain,)

    fake_clock.tick(0.1)

    assert group.chains == ()
    assert chain.completed
    assert events == ['finished']


def test_chain_group_start_ignores_already_done_chains(fake_clock):
    group = pyglet.clock.ChainGroup()

    @pyglet.clock.chain
    def completes_immediately():
        if False:
            yield

    @pyglet.clock.chain
    def waits():
        yield 1.0

    completed = completes_immediately().start()
    stopped = waits().start()
    stopped.stop()

    assert group.start(completed) is completed
    assert group.start(stopped) is stopped
    assert group.chains == ()
    assert fake_clock.scheduled == []
    assert fake_clock.scheduled_once == []


def test_chain_group_clear_stops_tracked_chains(fake_clock):
    events = []
    group = pyglet.clock.ChainGroup()

    @pyglet.clock.chain
    def sequence(name):
        try:
            yield 1.0
        finally:
            events.append(f'{name} stopped')

    group.start(sequence('fade'), tag='fade')
    group.start(sequence('move'), tag='move')

    group.clear()

    assert group.chains == ()
    assert fake_clock.scheduled == []
    assert events == ['fade stopped', 'move stopped']


def test_chain_group_clear_can_filter_by_tag(fake_clock):
    events = []
    group = pyglet.clock.ChainGroup()

    @pyglet.clock.chain
    def sequence(name):
        try:
            yield 1.0
            events.append(f'{name} finished')
        finally:
            events.append(f'{name} stopped')

    fade = group.start(sequence('fade'), tag='fade')
    move = group.start(sequence('move'), tag='move')

    group.clear(tag='fade')

    assert group.chains == (move,)
    assert fade.stopped
    assert not move.done
    assert events == ['fade stopped']

    fake_clock.tick(1.0)

    assert group.chains == ()
    assert events == ['fade stopped', 'move finished', 'move stopped']


def test_chain_group_clear_recurses_into_child_groups(fake_clock):
    events = []
    scene_group = pyglet.clock.ChainGroup()
    entity_group = scene_group.create_group()

    @pyglet.clock.chain
    def sequence():
        try:
            yield 1.0
        finally:
            events.append('entity stopped')

    entity_group.start(sequence(), tag='fade')

    scene_group.clear()

    assert scene_group.groups == ()
    assert entity_group.chains == ()
    assert fake_clock.scheduled == []
    assert events == ['entity stopped']


def test_chain_group_tagged_clear_recurses_without_removing_child_groups(fake_clock):
    events = []
    scene_group = pyglet.clock.ChainGroup()
    entity_group = scene_group.create_group()

    @pyglet.clock.chain
    def sequence(name):
        try:
            yield 1.0
        finally:
            events.append(f'{name} stopped')

    fade = entity_group.start(sequence('fade'), tag='fade')
    move = entity_group.start(sequence('move'), tag='move')

    scene_group.clear(tag='fade')

    assert scene_group.groups == (entity_group,)
    assert entity_group.chains == (move,)
    assert fade.stopped
    assert not move.done
    assert events == ['fade stopped']


def test_chain_group_pause_and_resume(fake_clock):
    events = []
    group = pyglet.clock.ChainGroup()

    @pyglet.clock.chain
    def sequence():
        yield 1.0
        events.append('finished')

    group.start(sequence())
    group.pause()

    fake_clock.tick(1.0)

    assert events == []

    group.resume()
    fake_clock.tick(1.0)

    assert events == ['finished']


def test_clock_create_group_binds_started_chains_to_that_clock(fake_clock):
    events = []
    game_time = [0.0]
    game_clock = pyglet.clock.Clock(lambda: game_time[0])
    group = game_clock.create_group()

    @game_clock.chain
    def sequence():
        yield 0.5
        events.append('game clock')

    chain = group.start(sequence())

    assert chain.clock is game_clock
    assert fake_clock.scheduled == []

    game_clock.tick(poll=True)
    game_time[0] = 0.5
    game_clock.tick(poll=True)

    assert events == ['game clock']


def test_chain_yields_none_to_resume_on_next_clock_tick(fake_clock):
    events = []

    @pyglet.clock.chain
    def sequence():
        events.append('started')
        yield None
        events.append('resumed')

    sequence().start()

    assert events == ['started']
    assert len(fake_clock.scheduled) == 1

    fake_clock.tick()

    assert events == ['started', 'resumed']


def test_consecutive_zero_delays_each_resume_on_a_separate_tick(fake_clock):
    events = []

    @pyglet.clock.chain
    def sequence():
        events.append(0)
        yield None
        events.append(1)
        yield 0
        events.append(2)

    sequence().start()

    fake_clock.tick()
    assert events == [0, 1]

    fake_clock.tick()
    assert events == [0, 1, 2]


def test_chain_stop_unschedules_pending_work_and_closes_generator(fake_clock):
    events = []

    @pyglet.clock.chain
    def sequence():
        try:
            yield 5.0
        finally:
            events.append('closed')

    chain = sequence().add_callbacks(on_stop=lambda: events.append('stopped')).start()

    chain.stop()

    assert chain.done
    assert not chain.completed
    assert chain.stopped
    assert not chain.failed
    assert not chain.running
    assert fake_clock.scheduled == []
    assert events == ['closed', 'stopped']


def test_wait_for_event_completes_on_dispatcher_event(fake_clock):
    class Dispatcher(pyglet.event.EventDispatcher):
        pass

    Dispatcher.register_event_type('on_value')
    dispatcher = Dispatcher()

    @pyglet.clock.chain
    def sequence():
        value = yield pyglet.clock.wait_for_event(dispatcher, 'on_value')
        return value

    chain = sequence().start()

    dispatcher.dispatch_event('on_value', 42)
    fake_clock.tick()

    assert chain.done
    assert chain.result == 42
    assert dispatcher.dispatch_event('on_value', 99) is False


def test_wait_for_event_can_filter_with_condition(fake_clock):
    class Dispatcher(pyglet.event.EventDispatcher):
        pass

    Dispatcher.register_event_type('on_value')
    dispatcher = Dispatcher()

    @pyglet.clock.chain
    def sequence():
        value = yield pyglet.clock.wait_for_event(
            dispatcher,
            'on_value',
            condition=lambda value: value > 1,
        )
        return value

    chain = sequence().start()

    dispatcher.dispatch_event('on_value', 1)
    fake_clock.tick()

    assert not chain.done

    dispatcher.dispatch_event('on_value', 2)
    fake_clock.tick()

    assert chain.done
    assert chain.result == 2


def test_wait_for_event_can_consume_matching_event(fake_clock):
    class Dispatcher(pyglet.event.EventDispatcher):
        pass

    Dispatcher.register_event_type('on_value')
    dispatcher = Dispatcher()

    @pyglet.clock.chain
    def sequence():
        yield pyglet.clock.wait_for_event(dispatcher, 'on_value', consume=True)

    sequence().start()

    assert dispatcher.dispatch_event('on_value') == pyglet.event.EVENT_HANDLED


def test_wait_for_event_stop_removes_handler(fake_clock):
    class Dispatcher(pyglet.event.EventDispatcher):
        pass

    Dispatcher.register_event_type('on_value')
    dispatcher = Dispatcher()

    @pyglet.clock.chain
    def sequence():
        yield pyglet.clock.wait_for_event(dispatcher, 'on_value')

    chain = sequence().start()

    chain.stop()

    assert dispatcher.dispatch_event('on_value') is False


def test_chain_pause_unschedules_and_resume_continues_remaining_delay(fake_clock):
    events = []

    @pyglet.clock.chain
    def sequence():
        events.append('started')
        yield 1.0
        events.append('finished')

    chain = sequence()
    chain.add_callbacks(
        on_pause=lambda: events.append('paused'),
        on_resume=lambda: events.append('resumed'),
    )
    chain.start()

    fake_clock.tick(0.4)
    chain.pause()

    assert chain.paused
    assert not chain.running
    assert fake_clock.scheduled == []
    assert fake_clock.scheduled_once == []
    assert events == ['started', 'paused']

    # Time spent paused must not consume the delay.
    fake_clock.tick(5.0)
    chain.resume()

    assert chain.running
    assert not chain.paused
    assert events == ['started', 'paused', 'resumed']

    fake_clock.tick(0.59)

    assert not chain.done

    fake_clock.tick(0.01)

    assert chain.done
    assert events == ['started', 'paused', 'resumed', 'finished']


def test_paused_chain_defers_callback_operation_completion(fake_clock):
    complete_callback = None
    events = []

    @pyglet.clock.yielding_callback
    def wait_for_message(complete, fail):
        nonlocal complete_callback
        complete_callback = complete

    @pyglet.clock.chain
    def sequence():
        events.append('waiting')
        message = yield wait_for_message()
        events.append(message)

    chain = sequence().start()
    chain.pause()

    assert complete_callback is not None
    complete_callback('arrived')

    assert fake_clock.scheduled == []
    assert events == ['waiting']

    chain.resume()
    fake_clock.tick()

    assert chain.done
    assert events == ['waiting', 'arrived']


def test_chain_waits_for_child_chain_result(fake_clock):
    @pyglet.clock.chain
    def child():
        yield 0.1
        return 21

    @pyglet.clock.chain
    def parent():
        result = yield child()
        return result * 2

    chain = parent().start()

    fake_clock.tick(0.1)
    fake_clock.tick()

    assert chain.done
    assert chain.result == 42


def test_stopped_child_stops_waiting_parent(fake_clock):
    events = []

    @pyglet.clock.chain
    def child():
        yield 1.0

    child_chain = child()

    @pyglet.clock.chain
    def parent():
        yield child_chain

    chain = parent().add_callbacks(on_stop=lambda: events.append('parent stopped')).start()

    child_chain.stop()
    fake_clock.tick()

    assert chain.stopped
    assert not chain.failed
    assert events == ['parent stopped']


def test_parent_can_catch_stopped_child(fake_clock):
    events = []

    @pyglet.clock.chain
    def child():
        yield 1.0

    child_chain = child()

    @pyglet.clock.chain
    def parent():
        try:
            yield child_chain
        except pyglet.clock.ChainStopped as exc:
            events.append(str(exc))
        return 'recovered'

    chain = parent().start()

    child_chain.stop()
    fake_clock.tick()

    assert chain.completed
    assert chain.result == 'recovered'
    assert events == ['A child chain stopped.']


def test_parent_can_catch_child_stopped_before_yield(fake_clock):
    @pyglet.clock.chain
    def child():
        yield 1.0

    child_chain = child().start()
    child_chain.stop()

    @pyglet.clock.chain
    def parent():
        try:
            yield child_chain
        except pyglet.clock.ChainStopped:
            return 'recovered'

    chain = parent().start()
    fake_clock.tick()

    assert chain.completed
    assert chain.result == 'recovered'


def test_pause_and_resume_propagates_to_child_chain(fake_clock):
    events = []

    @pyglet.clock.chain
    def child():
        events.append('child started')
        yield 1.0
        events.append('child finished')
        return 'child result'

    @pyglet.clock.chain
    def parent():
        result = yield child()
        events.append(result)

    chain = parent().start()

    fake_clock.tick(0.25)
    chain.pause()

    assert chain.paused
    assert fake_clock.scheduled == []

    chain.resume()

    fake_clock.tick(0.74)

    assert not chain.done

    fake_clock.tick(0.01)
    fake_clock.tick()

    assert chain.done
    assert events == ['child started', 'child finished', 'child result']


def test_parallel_runs_child_chains_together_and_returns_ordered_results(fake_clock):
    events = []

    @pyglet.clock.chain
    def child(name, delay):
        events.append(f'{name} started')
        yield delay
        events.append(f'{name} finished')
        return name

    @pyglet.clock.chain
    def parent():
        results = yield pyglet.clock.parallel(
            child('first', 0.2),
            child('second', 0.4),
        )
        events.append(results)

    chain = parent().start()

    assert events == ['first started', 'second started']

    fake_clock.tick(0.2)

    assert not chain.done
    assert events == ['first started', 'second started', 'first finished']

    fake_clock.tick(0.2)
    fake_clock.tick()

    assert chain.done
    assert events == ['first started', 'second started', 'first finished', 'second finished', ('first', 'second')]


def test_parallel_stop_stops_running_child_chains(fake_clock):
    events = []

    @pyglet.clock.chain
    def child(name):
        try:
            yield 1.0
        finally:
            events.append(f'{name} stopped')

    @pyglet.clock.chain
    def parent():
        yield pyglet.clock.parallel(child('first'), child('second'))

    chain = parent().start()

    chain.stop()

    assert chain.done
    assert fake_clock.scheduled == []
    assert events == ['first stopped', 'second stopped']


def test_parallel_child_stop_stops_remaining_children_and_parent_by_default(fake_clock):
    events = []

    @pyglet.clock.chain
    def child(name):
        try:
            yield 1.0
        finally:
            events.append(f'{name} stopped')

    first = child('first')
    second = child('second')

    @pyglet.clock.chain
    def parent():
        yield pyglet.clock.parallel(first, second)

    chain = parent().add_callbacks(on_stop=lambda: events.append('parent stopped')).start()

    first.stop()

    assert not chain.done

    fake_clock.tick()

    assert chain.done
    assert chain.stopped
    assert not chain.failed
    assert fake_clock.scheduled == []
    assert events == ['first stopped', 'second stopped', 'parent stopped']


def test_parallel_child_stop_can_be_caught_by_parent(fake_clock):
    events = []

    @pyglet.clock.chain
    def child(name):
        try:
            yield 1.0
        finally:
            events.append(f'{name} stopped')

    first = child('first')
    second = child('second')

    @pyglet.clock.chain
    def parent():
        try:
            yield pyglet.clock.parallel(first, second)
        except pyglet.clock.ChainStopped:
            events.append('recovered')
        return 'done'

    chain = parent().start()

    first.stop()
    fake_clock.tick()

    assert chain.completed
    assert chain.result == 'done'
    assert events == ['first stopped', 'second stopped', 'recovered']


def test_parallel_can_continue_when_child_chain_stops(fake_clock):
    events = []

    @pyglet.clock.chain
    def child(name):
        try:
            yield 1.0
            events.append(f'{name} finished')
            return name
        finally:
            events.append(f'{name} stopped')

    first = child('first')
    second = child('second')

    @pyglet.clock.chain
    def parent():
        results = yield pyglet.clock.parallel(first, second, continue_on_stop=True)
        events.append(results)

    chain = parent().start()

    first.stop()

    assert not chain.done
    assert events == ['first stopped']

    fake_clock.tick(1.0)
    fake_clock.tick()

    assert chain.done
    assert events == [
        'first stopped',
        'second finished',
        'second stopped',
        (pyglet.clock.STOPPED, 'second'),
    ]


def test_parallel_pause_and_resume_propagates_to_children(fake_clock):
    events = []

    @pyglet.clock.chain
    def child(name):
        yield 1.0
        events.append(f'{name} finished')
        return name

    @pyglet.clock.chain
    def parent():
        results = yield pyglet.clock.parallel(child('first'), child('second'))
        events.append(results)

    chain = parent().start()

    fake_clock.tick(0.3)
    chain.pause()

    assert chain.paused
    assert fake_clock.scheduled == []

    chain.resume()
    fake_clock.tick(0.69)

    assert not chain.done

    fake_clock.tick(0.01)
    fake_clock.tick()

    assert chain.done
    assert events == ['first finished', 'second finished', ('first', 'second')]


def test_parallel_child_error_stops_remaining_children(fake_clock):
    error = ValueError('failed child')
    events = []
    captured = []

    @pyglet.clock.chain
    def failing_child():
        yield 0.2
        raise error

    @pyglet.clock.chain
    def long_child():
        try:
            yield 1.0
        finally:
            events.append('long child stopped')

    @pyglet.clock.chain
    def parent():
        yield pyglet.clock.parallel(failing_child(), long_child())

    chain = parent().add_callbacks(on_error=captured.append).start()

    fake_clock.tick(0.2)
    fake_clock.tick()

    assert chain.done
    assert not chain.completed
    assert not chain.stopped
    assert chain.failed
    assert chain.exception is error
    assert captured == [error]
    assert events == ['long child stopped']


def test_race_completes_with_first_child_result_and_stops_losers(fake_clock):
    events = []

    @pyglet.clock.chain
    def child(name, delay):
        try:
            yield delay
            return name
        finally:
            events.append(f'{name} stopped')

    @pyglet.clock.chain
    def parent():
        result = yield pyglet.clock.race(
            child('first', 0.2),
            child('second', 0.5),
        )
        events.append(result)

    chain = parent().start()

    fake_clock.tick(0.2)
    fake_clock.tick()

    assert chain.done
    assert events == ['first stopped', 'second stopped', (0, 'first')]


def test_race_child_stop_stops_remaining_children_and_parent(fake_clock):
    events = []

    @pyglet.clock.chain
    def child(name):
        try:
            yield 1.0
        finally:
            events.append(f'{name} stopped')

    first = child('first')
    second = child('second')

    @pyglet.clock.chain
    def parent():
        yield pyglet.clock.race(first, second)

    chain = parent().add_callbacks(on_stop=lambda: events.append('parent stopped')).start()

    first.stop()
    fake_clock.tick()

    assert chain.stopped
    assert not chain.failed
    assert fake_clock.scheduled == []
    assert events == ['first stopped', 'second stopped', 'parent stopped']


def test_race_child_error_stops_losers_and_errors_parent(fake_clock):
    error = ValueError('race failed')
    events = []
    captured = []

    @pyglet.clock.chain
    def failing_child():
        yield 0.2
        raise error

    @pyglet.clock.chain
    def long_child():
        try:
            yield 1.0
        finally:
            events.append('long child stopped')

    @pyglet.clock.chain
    def parent():
        yield pyglet.clock.race(failing_child(), long_child())

    chain = parent().add_callbacks(on_error=captured.append).start()

    fake_clock.tick(0.2)
    fake_clock.tick()

    assert chain.done
    assert not chain.completed
    assert not chain.stopped
    assert chain.failed
    assert chain.exception is error
    assert captured == [error]
    assert events == ['long child stopped']


def test_timeout_completes_after_delay(fake_clock):
    events = []

    pyglet.clock.timeout(0.5).add_callbacks(on_complete=lambda result: events.append(result)).start()

    fake_clock.tick(0.49)

    assert events == []

    fake_clock.tick(0.01)

    assert events == [None]


def test_repeat_runs_factory_count_times(fake_clock):
    events = []

    @pyglet.clock.chain
    def child():
        events.append('started')
        yield 0.1
        return len(events)

    chain = pyglet.clock.repeat(child, 3).start()

    for _ in range(3):
        fake_clock.tick(0.1)
        fake_clock.tick()

    assert chain.done
    assert chain.result == (1, 2, 3)
    assert events == ['started', 'started', 'started']


def test_repeat_until_runs_until_condition_is_true(fake_clock):
    events = []

    @pyglet.clock.chain
    def child():
        events.append('started')
        yield 0.1
        return len(events)

    chain = pyglet.clock.repeat_until(child, lambda: len(events) == 2).start()

    for _ in range(2):
        fake_clock.tick(0.1)
        fake_clock.tick()

    assert chain.done
    assert chain.result == (1, 2)


def test_repeat_forever_runs_until_stopped(fake_clock):
    events = []

    @pyglet.clock.chain
    def child():
        try:
            events.append('started')
            yield 0.1
            events.append('finished')
        finally:
            events.append('stopped')

    chain = pyglet.clock.repeat_forever(child).start()

    for _ in range(3):
        fake_clock.tick(0.1)
        fake_clock.tick()

    chain.stop()

    assert chain.stopped
    assert events == [
        'started', 'finished', 'stopped',
        'started', 'finished', 'stopped',
        'started', 'finished', 'stopped',
        'started', 'stopped',
    ]


def test_clock_repeat_forever_uses_clock_instance():
    clock = pyglet.clock.Clock(time_function=lambda: 0.0)

    @clock.chain
    def child():
        yield 0.1

    chain = clock.repeat_forever(child)

    assert chain.clock is clock


def test_repeat_duration_stops_repeating_when_duration_elapses(fake_clock):
    events = []

    @pyglet.clock.chain
    def child():
        try:
            events.append('started')
            yield 0.3
            events.append('finished')
        finally:
            events.append('stopped')

    chain = pyglet.clock.repeat_duration(child, 0.75).start()

    fake_clock.tick(0.3)
    fake_clock.tick()
    fake_clock.tick(0.3)
    fake_clock.tick()
    fake_clock.tick(0.15)
    fake_clock.tick()

    assert chain.done
    assert events == ['started', 'finished', 'stopped', 'started', 'finished', 'stopped', 'started', 'stopped']


def test_repeat_duration_zero_completes_without_repeating(fake_clock):
    events = []

    @pyglet.clock.chain
    def child():
        events.append('started')
        yield 0.1

    chain = pyglet.clock.repeat_duration(child, 0).start()

    fake_clock.tick()
    fake_clock.tick()

    assert chain.done
    assert events == ['started']


def test_chain_waits_for_callback_operation(fake_clock):
    complete_callback = None

    @pyglet.clock.yielding_callback
    def wait_for_message(complete, fail):
        nonlocal complete_callback
        complete_callback = complete

    @pyglet.clock.chain
    def sequence():
        message = yield wait_for_message()
        return message.upper()

    chain = sequence().start()

    assert complete_callback is not None
    complete_callback('arrived')
    fake_clock.tick()

    assert chain.done
    assert chain.result == 'ARRIVED'


def test_chain_stop_cancels_callback_operation(fake_clock):
    events = []

    @pyglet.clock.yielding_callback
    def wait_forever(complete, fail):
        return lambda: events.append('cancelled')

    @pyglet.clock.chain
    def sequence():
        yield wait_forever()

    chain = sequence().add_callbacks(on_stop=lambda: events.append('stopped')).start()

    chain.stop()

    assert events == ['cancelled', 'stopped']


def test_chain_reports_operation_errors(fake_clock):
    error = ValueError('bad event')
    captured = []

    @pyglet.clock.yielding_callback
    def fail_later(complete, fail):
        fail(error)

    @pyglet.clock.chain
    def sequence():
        yield fail_later()

    chain = sequence().add_callbacks(on_error=captured.append).start()

    fake_clock.tick()

    assert chain.done
    assert not chain.completed
    assert not chain.stopped
    assert chain.failed
    assert chain.exception is error
    assert captured == [error]


def test_chain_rejects_negative_delay(fake_clock):
    captured = []

    @pyglet.clock.chain
    def sequence():
        yield -1

    chain = sequence().add_callbacks(on_error=captured.append).start()

    assert chain.done
    assert isinstance(chain.exception, ValueError)
    assert captured == [chain.exception]

