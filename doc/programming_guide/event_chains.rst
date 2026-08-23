.. _guide_event_chains:

Event chains
============

Event chains are generator-based coroutines that run on pyglet's clock. They are
useful when an event flow has several timed or callback-driven steps, but you do
not want to split the logic across several scheduled functions.

Event chains live in :py:mod:`pyglet.clock` because they are scheduled work.
They can still wait for dispatcher events through
:py:func:`pyglet.clock.wait_for_event`.

Why event chains
----------------

Normal scheduling via :py:func:`pyglet.clock.schedule_interval` and
:py:func:`pyglet.clock.schedule_once` are simple and easy to use for periodic
updates and simple one-shot callbacks. However, some workflows become awkward
when written only with :py:func:`pyglet.clock.schedule_once`,
:py:func:`pyglet.clock.schedule`, and temporary event handlers:

* A timed sequence needs multiple named callbacks or nested functions.
* Cancellation requires tracking every scheduled callback and temporary event
  handler manually.
* Repeating a multi-step flow requires recreating the whole sequence manually.
* Waiting for an event or callback in the middle of a timed flow splits the
  logic across unrelated handlers.
* No pause or resume behavior.
* Running several flows together, or racing an event against a timeout, requires
  custom bookkeeping.
* Error handling is easy to lose when failures happen inside later scheduled
  callbacks.

Event chains add a small coordination layer over pyglet's existing clock and
event system. They let you write the flow in the order it happens while still
using pyglet's normal single-threaded event loop.

Event chains are not ``asyncio`` coroutines. They do not require ``async`` or
``await`` and they do not run on an asyncio event loop. Instead, a function
decorated with :py:func:`~pyglet.clock.chain` returns a
:py:class:`~pyglet.clock.Chain`, and the chain advances when pyglet's clock
ticks or when a yielded event or callback instruction completes.

The basic rule is that a chain yields one of the following:

* A number (float or int) to wait that many seconds.
* ``None``, to resume on the next clock tick.
* Another :py:class:`~pyglet.clock.Chain` to wait for that child chain.
* A yield instruction created with :py:func:`~pyglet.clock.wait_for_event`,
  :py:func:`~pyglet.clock.yielding_callback`, or
  :py:func:`~pyglet.clock.from_callback`.

A sequence without event chains
-------------------------------

The following example shows a small title flow: fade in, show a title, fade out,
then notify that the sequence is done. With only ``schedule_once``, each step
must be split into a separate function, and the caller needs to track pending
callbacks if the flow should be cancellable::

    import pyglet

    pending_callbacks = []

    def schedule_step(callback, delay):
        pending_callbacks.append(callback)
        pyglet.clock.schedule_once(callback, delay)

    def cancel_title_sequence():
        for callback in pending_callbacks:
            pyglet.clock.unschedule(callback)
        pending_callbacks.clear()
        print('cancelled')

    def start_title_sequence():
        print('fade in')
        schedule_step(show_title, 0.5)

    def show_title(dt):
        pending_callbacks.remove(show_title)
        print('show title')
        schedule_step(fade_out, 2.0)

    def fade_out(dt):
        pending_callbacks.remove(fade_out)
        print('fade out')
        schedule_step(finished, 0.5)

    def finished(dt):
        pending_callbacks.remove(finished)
        print('done')

    start_title_sequence()
    pyglet.app.run()

This is manageable for three steps, but becomes harder to maintain as soon as
the sequence waits for user input, repeats, runs alongside another sequence, or
needs consistent error handling.

The same sequence with event chains
-----------------------------------

With an event chain, the flow is written as one function in the order it
happens::

    import pyglet

    @pyglet.clock.chain
    def title_sequence():
        print('fade in')
        yield 0.5
        print('show title')
        yield 2.0
        print('fade out')
        yield 0.5
        return 'done'

    sequence = title_sequence()
    sequence.add_callbacks(
        on_complete=print,
        on_stop=lambda: print('cancelled'),
    )
    sequence.start()

    pyglet.app.run()

The returned :py:class:`~pyglet.clock.Chain` can be stopped, paused,
resumed, and observed::

    sequence.pause()
    sequence.resume()
    sequence.stop()


Separate clock instances
------------------------

By default, chains use :py:func:`pyglet.clock.get_default` when the chain object
is created::

    @pyglet.clock.chain
    def spawn_wave():
        yield 1.0
        print('spawn')

    spawn_wave().start()

To bind chains to a specific :py:class:`~pyglet.clock.Clock`, decorate from the
clock instance itself::

    game_clock = pyglet.clock.Clock()

    @game_clock.chain
    def spawn_wave():
        yield 1.0
        print('spawn')

    spawn_wave().start()

This is useful when a game has separate clocks for gameplay, UI, or editor
tools. Pausing can be as simple as not ticking the gameplay clock while the UI
clock continues to tick.


Error reporting
---------------

Event chains do not silently hide uncaught exceptions. If a chain raises an
exception, or if a yielded instruction calls ``fail(error)``, the error is
thrown into the waiting chain. If your chain does not catch it, the chain stops,
stores the exception on ``Chain.exception``, finishes as failed, and calls any
callbacks registered with :py:meth:`~pyglet.clock.Chain.add_callbacks`::

    @pyglet.clock.chain
    def failing_sequence():
        yield 0.5
        raise RuntimeError('failed')

    failing_sequence().add_callbacks(on_error=lambda error: print('handled:', error)).start()

If no error callback is registered, pyglet prints the traceback with
``traceback.print_exception`` and still stores the exception on the chain::

    active = failing_sequence().start()

    # After the failure:
    # active.done is True
    # active.exception is the RuntimeError instance


Returning values
----------------

A child chain can return a value to its parent. This makes it possible to write
small reusable event flows::

    @pyglet.clock.chain
    def load_profile(name):
        yield 0.1
        return {'name': name}

    @pyglet.clock.chain
    def show_profile():
        profile = yield load_profile('Ada')
        print(profile['name'])


Stopping child chains
---------------------

Calling :py:meth:`~pyglet.clock.Chain.stop` on a parent stops its active child
chains as well. This is immediate cancellation: the parent generator is closed,
its ``finally`` blocks run, and its ``on_stop`` callbacks are called.

If a child is stopped independently while a parent is waiting for it, pyglet
throws :py:exc:`~pyglet.clock.ChainStopped` at the parent's ``yield``. The
parent can catch this signal and choose how to recover::

    @pyglet.clock.chain
    def load_scene():
        try:
            assets = yield download_assets()
        except pyglet.clock.ChainStopped:
            assets = load_cached_assets()

        yield display_scene(assets)

If the parent does not catch ``ChainStopped``, the parent stops too. It calls
``on_stop``, not ``on_error``, and ``Chain.exception`` remains ``None``. This
keeps cancellation separate from failure while still allowing a parent to
handle child cancellation deliberately.


Parallel work
-------------

Use :py:func:`~pyglet.clock.parallel` when several child chains should run at
the same time and the parent should continue after all of them finish::

    @pyglet.clock.chain
    def prepare_music():
        yield 1.0
        return 'music'

    @pyglet.clock.chain
    def prepare_level():
        yield 2.0
        return 'level'

    @pyglet.clock.chain
    def prepare_game():
        music, level = yield pyglet.clock.parallel(
            prepare_music(),
            prepare_level(),
        )
        print(music, level)

By default, if one child chain stops independently, the parallel group stops
the remaining children and throws :py:exc:`~pyglet.clock.ChainStopped` at the
parent's ``yield``. The parent may catch it; otherwise the parent stops as
described above.

If a stopped child should be treated as missing work and the other children
should continue, pass ``continue_on_stop=True``. The stopped child contributes
:py:data:`~pyglet.clock.STOPPED` to the result tuple, which keeps cancellation
separate from a child that completed with ``return`` or ``return None``::

    results = yield pyglet.clock.parallel(
        prepare_music(),
        prepare_level(),
        continue_on_stop=True,
    )

    if results[0] is pyglet.clock.STOPPED:
        print('music preparation was stopped')


Race and timeout
----------------

:py:func:`~pyglet.clock.race` resumes when the first child chain completes. It
returns ``(index, result)``, where ``index`` is the winning child position. The
remaining children are stopped.

If a race child stops independently before there is a winner, the other
children are stopped and the parent receives
:py:exc:`~pyglet.clock.ChainStopped`. As with a directly yielded child, the
parent may catch the signal; otherwise it stops.

:py:func:`~pyglet.clock.timeout` is a small chain that completes after a delay.
It is most useful when combined with ``race`` to bound how long a flow can wait
for an external event. This keeps prompts, network waits, menu flows, and other
event-driven steps from waiting forever::

    @pyglet.clock.chain
    def wait_for_space():
        symbol, modifiers = yield pyglet.clock.wait_for_event(
            window,
            'on_key_press',
            condition=lambda symbol, modifiers: symbol == key.SPACE,
        )
        return symbol

    @pyglet.clock.chain
    def wait_or_timeout():
        winner, result = yield pyglet.clock.race(
            wait_for_space(),
            pyglet.clock.timeout(5.0),
        )

        if winner == 0:
            print('user responded')
        else:
            print('timed out')

Timeouts can also be used without input events. For example, a status message
can clear itself after a short delay::

    @pyglet.clock.chain
    def show_status(message):
        status_label.text = message
        yield pyglet.clock.timeout(2.0)
        status_label.text = ''

When ``timeout`` wins a race, the other child chains are stopped. If one of
those child chains is waiting on a callback instruction, its cancellation
callback is called during that stop.


Repeating chains
----------------

Repeat helpers accept a factory that creates a fresh chain each time. This is
important because completed chains cannot be restarted::

    @pyglet.clock.chain
    def blink_once():
        print('on')
        yield 0.25
        print('off')
        yield 0.25

    # Run exactly three times.
    yield pyglet.clock.repeat(blink_once, 3)

    # Run until a condition becomes true.
    yield pyglet.clock.repeat_until(blink_once, lambda: game_over)

    # Run until this chain is stopped.
    yield pyglet.clock.repeat_forever(blink_once)

    # Run for a fixed duration.
    yield pyglet.clock.repeat_duration(blink_once, 3.0)


Waiting for events and callbacks
--------------------------------

Most pyglet objects that produce events are
:py:class:`~pyglet.event.EventDispatcher` instances. Use
:py:func:`~pyglet.clock.wait_for_event` to suspend a chain until a dispatcher
emits a matching event. The helper registers and removes the temporary handler
for you::

    from pyglet.window import key

    window = pyglet.window.Window()

    @pyglet.clock.chain
    def prompt():
        print('press Space')
        symbol, modifiers = yield pyglet.clock.wait_for_event(
            window,
            'on_key_press',
            condition=lambda symbol, modifiers: symbol == key.SPACE,
        )
        print('pressed', symbol)

The optional ``condition`` lets you ignore events until the desired one arrives.
The matching event arguments are sent back into the chain. Destructure them the
same way you would in a normal event handler::

    x, y, button, modifiers = yield pyglet.clock.wait_for_event(window, 'on_mouse_press')

``wait_for_event`` is useful for custom dispatchers too. This example does not
depend on windows or graphics::

    class JobQueue(pyglet.event.EventDispatcher):
        def finish_job(self, job_id, status):
            self.dispatch_event('on_job_finished', job_id, status)

    JobQueue.register_event_type('on_job_finished')

    jobs = JobQueue()

    @pyglet.clock.chain
    def wait_for_export():
        job_id, status = yield pyglet.clock.wait_for_event(
            jobs,
            'on_job_finished',
            condition=lambda job_id, status: job_id == 'export',
        )
        print(job_id, 'finished:', status)

Callback-based APIs that are not event dispatchers can be adapted into yield
instructions with :py:func:`~pyglet.clock.yielding_callback`. The decorated
function receives ``complete`` and ``fail`` callbacks and may return a cancellation
callback. Call ``complete(value)`` when the external operation succeeds; that
``value`` becomes the result of ``yield`` in the waiting chain. Call
``fail(error)`` with a :py:class:`BaseException` instance when the external
operation fails; the error is thrown into the waiting chain, and is reported to
the chain's error callbacks if it is not caught. If the starter function raises
an exception before returning, that exception is handled like ``fail(error)``.
For most asynchronous APIs, the starter function only registers callbacks and
returns; ``complete`` or ``fail`` is called later by the external operation::

    class NetworkRequest:
        def send(self, on_success, on_error):
            ...

        def cancel(self):
            ...

    @pyglet.clock.yielding_callback
    def wait_for_network_reply(
        complete: pyglet.clock.CompleteCallback,
        fail: pyglet.clock.ErrorCallback,
        request: NetworkRequest,
    ) -> pyglet.clock.CancelCallback | None:
        request.send(
            on_success=complete,
            on_error=fail,
        )
        return request.cancel

    @pyglet.clock.chain
    def fetch_profile(request):
        try:
            reply = yield wait_for_network_reply(request)
        except OSError as error:
            print('request failed:', error)
            return None

        return reply.json()

    active_request = fetch_profile(NetworkRequest()).start()

If ``fetch_profile`` is stopped before the network request finishes, the cancel
callback returned by ``wait_for_network_reply`` is called. If the external API
calls ``fail(error)``, the ``yield`` raises that error inside ``fetch_profile``.
Errors that are not caught inside the chain are passed to callbacks registered
with :py:meth:`~pyglet.clock.Chain.add_callbacks`::

    fetch_profile(NetworkRequest()).add_callbacks(on_error=print).start()


Chain groups
------------

:py:class:`~pyglet.clock.ChainGroup` tracks related chains so they can be
paused, resumed, or stopped together. A group is not a scheduler; the
:py:class:`~pyglet.clock.Clock` still owns time. The group owns lifecycle.
Adding a chain to a group does not change the clock the chain was created with.

This is useful when an entity starts several independent chains and all of them
must stop when that entity is destroyed::

    class Enemy:
        def __init__(self, game_clock):
            self.chains = pyglet.clock.ChainGroup(clock=game_clock)

        def destroy(self):
            self.chains.clear()
            self.delete_sprites()

        def flash(self):
            self.chains.start(flash_sprite(self.sprite), tag='flash')

Groups can be nested. For example, a scene can own a world group, and the world
group can own entity groups. Clearing the scene group stops every descendant
chain::

    scene_chains = pyglet.clock.ChainGroup(clock=game_clock)
    world_chains = scene_chains.create_group()

    enemy = Enemy(game_clock)
    world_chains.add_group(enemy.chains)

    # Changing scenes:
    scene_chains.clear()

Tags let a group stop one category of work without touching the rest. This is
useful for mutually exclusive flows such as fading in while a fade-out is still
running::

    class Actor:
        def __init__(self, game_clock):
            self.chains = pyglet.clock.ChainGroup(clock=game_clock)
            self.sprites = []

        def fade_in(self):
            self.chains.clear(tag='fade')
            self.chains.start(fade_sprites(self.sprites, target_alpha=255), tag='fade')

        def fade_out_then_destroy(self):
            self.chains.clear(tag='fade')
            chain = self.chains.start(
                fade_sprites(self.sprites, target_alpha=0),
                tag='fade',
            )
            chain.add_callbacks(on_complete=lambda _result: self.destroy())

        def destroy(self):
            self.chains.clear()


Tweening values
---------------

Tweens update a value gradually over time. They are useful for visual changes
such as fading, movement, scaling, or rotation, as well as audio levels,
gameplay parameters, and any other state that changes smoothly. Yielding a
tween keeps the update logic separate from the sequence that should continue
after it finishes.

:py:func:`~pyglet.clock.tween` drives an update callable with normalized
progress over a duration. The callable receives one ``float`` argument. It
can be a function, a lambda, a bound method, or any callable object. The tween
returns a chain that can be yielded like any other child chain::

    class FadeOut:
        def __init__(self, target):
            self.target = target
            self.start_opacity = target.opacity

        def update(self, progress):
            self.target.opacity = self.start_opacity * (1.0 - progress)

    @pyglet.clock.chain
    def remove_sprite(sprite):
        yield pyglet.clock.tween(0.5, FadeOut(sprite).update)
        sprite.delete()

For a one-off update, define a local function instead::

    start_opacity = sprite.opacity

    def update(progress):
        sprite.opacity = start_opacity * (1.0 - progress)

    yield pyglet.clock.tween(0.5, update)

For a compact one-off update, a lambda works too. Capture the starting value
before creating the lambda so that each update is based on the same value::

    start_opacity = sprite.opacity
    yield pyglet.clock.tween(
        0.5,
        lambda progress: setattr(sprite, 'opacity', start_opacity * (1.0 - progress)),
    )

With the default linear easing, the update callable receives ``0.0`` when the
tween starts and ``1.0`` when it finishes. A zero-duration tween applies only
the eased final value. Tweens are chains themselves, so they can be started
directly or composed with :py:func:`~pyglet.clock.parallel` and
:py:func:`~pyglet.clock.race`. They pause, resume, and stop like any other
chain::

    yield pyglet.clock.parallel(
        pyglet.clock.tween(0.5, FadeOut(sprite).update),
        pyglet.clock.tween(0.5, update_position),
    )

Pass an easing function to transform the linear progress. Easing functions
receive a value from ``0.0`` through ``1.0``. Their result is not clamped,
which permits curves that intentionally overshoot::

    yield pyglet.clock.tween(
        0.5,
        FadeOut(sprite).update,
        easing=pyglet.clock.ease_in_out,
    )

The built-in curves are :py:func:`~pyglet.clock.linear`,
:py:func:`~pyglet.clock.ease_in`, :py:func:`~pyglet.clock.ease_out`,
:py:func:`~pyglet.clock.ease_in_out`, and
:py:func:`~pyglet.clock.smoothstep`. Any callable with the same ``float ->
float`` shape can be supplied instead.

Use :py:meth:`~pyglet.clock.Clock.tween` to bind the tween to a custom clock::

    yield game_clock.tween(1.0, update_position, easing=my_easing)

