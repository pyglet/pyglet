Keeping track of time
=====================

pyglet's :py:mod:`~pyglet.clock` module allows you to schedule functions
to run periodically, or for one-shot future execution.

.. _guide_calling-functions-periodically:

Scheduling functions
--------------------

As discussed in the :ref:`programming-guide-eventloop` section, pyglet
applications begin execution by entering into an application event loop::

    pyglet.app.run()

Once called, this function doesn't return until the application windows have
been closed.  This may leave you wondering how to execute code while the
application is running.

Typical applications need to execute code in only three circumstances:

* A user input event (such as a mouse movement or key press) has been
  generated.  In this case the appropriate code can be attached as an
  event handler to the window.
* An animation or other time-dependent system needs to update the position
  or parameters of an object.  We'll call this a "periodic" event.
* A certain amount of time has passed, perhaps indicating that an
  operation has timed out, or that a dialog can be automatically dismissed.
  We'll call this a "one-shot" event.

Running on a regular schedule
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Most applications should start with
:py:func:`~pyglet.clock.schedule_interval`. It is well suited to animation,
physics simulation, and game-state updates that should maintain a regular
rate. To call a function once every 0.1 seconds::

    def update(dt):
        # ...

    pyglet.clock.schedule_interval(update, 0.1)

The ``dt``, or *delta time*, parameter gives the number of wall-clock seconds
elapsed since the last call of this function, (or the time the function was
scheduled, if it's the first period). Due to latency, load and timer
imprecision, this might be slightly more or less than the requested interval.
The ``dt`` parameter is always passed to scheduled functions,
so be sure to expect it when writing functions even if you don't need to
use it.

``schedule_interval`` follows the requested series of times. For example, a
callback scheduled every second aims to run at 1, 2, 3, and 4 seconds. If the
2-second call is delayed until 2.1 seconds, the next call still aims for 3
seconds instead of being moved to 3.1 seconds. A late call can therefore be
followed by a slightly shorter gap while the schedule returns to its requested
timing.

If the application is delayed long enough to miss one or more calls, pyglet
does not replay all of them. It calls the function once and chooses a future
time for the next call. When several callbacks are overdue together, their
next times are spread apart to avoid a burst of repeated catch-up work.

For example, most games need no more than 60 updates per second for smooth
animation. A 60 Hz update can be scheduled with::

    pyglet.clock.schedule_interval(update, 1 / 60)

Spreading periodic work
^^^^^^^^^^^^^^^^^^^^^^^

Use :py:func:`~pyglet.clock.schedule_interval_soft` for independent callbacks
that should run regularly but do not need to run at the same moment. It
chooses different starting times for callbacks with similar intervals,
reducing bursts of work::

    pyglet.clock.schedule_interval_soft(update_audio_buffer, 0.1)

This is useful for background work such as updating several audio buffers,
checking independent services, or starting repeated animations at different
points in their cycles. The interval remains the requested average spacing,
but the initial call may occur earlier or later so it does not coincide with
other scheduled work.

Waiting after each call finishes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use :py:func:`~pyglet.clock.schedule_interval_fixed_delay` when there must be
a full delay after one call finishes before the next call can begin::

    pyglet.clock.schedule_interval_fixed_delay(poll_service, 1.0)

If ``poll_service`` takes 0.2 seconds and the delay is 1 second, the next call
starts approximately 1.2 seconds after the previous call started. Delays and
slow callbacks push all future calls later; missed calls are skipped and are
never replayed. This is useful for polling and maintenance work, but its
average call rate will be lower when callbacks take significant time.

Running on every clock tick
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use :py:func:`~pyglet.clock.schedule` when a function should run on every
clock tick rather than at a timed interval. This is mainly useful for
benchmarks and specialized event loops. It can run as frequently as the
application allows and is likely to consume an entire CPU core::

    def benchmark(dt):
        # ...

    pyglet.clock.schedule(benchmark)

.. note:: By default pyglet window buffer swaps are synchronised to the display refresh
          rate, so you may also want to disable vsync if you are running a benchmark.

All clock callbacks run serially on the event-loop thread. No scheduling
method can maintain a requested rate when its callbacks require more total
time than the interval provides. Keep callbacks short, reduce their frequency,
or move blocking work to an appropriate worker thread.

Calling a function once
^^^^^^^^^^^^^^^^^^^^^^^

Use :py:func:`~pyglet.clock.schedule_once` when a function should run once
after a delay::

    def dismiss_dialog(dt):
        # ...

    # Dismiss the dialog after 5 seconds.
    pyglet.clock.schedule_once(dismiss_dialog, 5.0)

Canceling scheduled functions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To stop a scheduled function from being called, including cancelling a
periodic function, use :py:func:`pyglet.clock.unschedule`. This could be
useful if you want to start running a function on schedule when a user provides
a certain input, and then unschedule it when another input is received.


Sprite movement techniques
--------------------------

As mentioned above, every scheduled function receives a `dt` parameter,
giving the actual "wall clock" time that passed since the previous invocation.
This parameter can be used for numerical integration.

For example, a non-accelerating particle with velocity ``v`` will travel
some distance over a change in time ``dt``.  This distance is calculated as
``v * dt``.  Similarly, a particle under constant acceleration ``a`` will have
a change in velocity of ``a * dt``.

The following example demonstrates a simple way to move a sprite across the
screen at exactly 10 pixels per second::

    sprite = pyglet.sprite.Sprite(image)
    sprite.dx = 10.0

    def move_sprite(dt):
        sprite.x += sprite.dx * dt

    pyglet.clock.schedule_interval(move_sprite, 1/60.0)  # update at 60Hz

This is a robust technique for simple sprite movement, as the velocity will
remain constant regardless of the speed or load of the computer.

Some examples of other common animation variables are given in the table
below.

    .. list-table::
        :header-rows: 1

        * - Animation parameter
          - Distance
          - Velocity
        * - Rotation
          - Degrees
          - Degrees per second
        * - Position
          - Pixels
          - Pixels per second
        * - Keyframes
          - Frame number
          - Frames per second


Displaying the frame rate
-------------------------

A simple way to profile your application performance is to display the frame
rate while it is running.  Printing it to the console is not ideal as this
will have a severe impact on performance.  pyglet provides the
:py:class:`~pyglet.window.FPSDisplay` class for displaying the frame rate
with very little effort::

    fps_display = pyglet.window.FPSDisplay(window=window)

    @window.event
    def on_draw():
        window.clear()
        fps_display.draw()

By default the frame rate will be drawn in the bottom-left corner of the
window in a semi-translucent large font.
See the :py:class:`~pyglet.window.FPSDisplay` documentation for details
on how to customise this, or even display another clock value (such as
the current time) altogether.


User-defined clocks
-------------------

The default clock used by pyglet uses the system clock to determine the time
(i.e., ``time.time()``).  Separate clocks can be created, however, allowing
you to use another time source.  This can be useful for implementing a
separate "game time" to the real-world time, or for synchronising to a network
time source or a sound device.

Each of the ``clock_*`` functions are aliases for the methods on a global
instance of :py:class:`~pyglet.clock.Clock`. You can construct or subclass
your own :py:class:`~pyglet.clock.Clock`, which can then maintain its own
schedule and framerate calculation.
See the class documentation for more details.
