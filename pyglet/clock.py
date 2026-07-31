"""Precise framerate calculation function scheduling.

The :py:mod:`~pyglet.clock` module allows you to schedule functions
to run periodically, or for one-shot future execution. pyglet's default
event loop (:py:func:`~pyglet.app.run`) keeps an internal instance of
a :py:class:`~pyglet.clock.Clock`, which is ticked automatically.

.. note:: Some internal modules will schedule items on the clock. If you
          are using a custom event loop, always remember to `tick` the clock!

Scheduling
==========

You can schedule a function to be called every time the clock is ticked::

    def callback(dt):
        print(f"{dt} seconds since last callback")

    clock.schedule(callback)

The `schedule_interval` method causes a function to be called every "n"
seconds::

    clock.schedule_interval(callback, 0.5)   # called twice a second

The `schedule_once` method causes a function to be called once "n" seconds
in the future::

    clock.schedule_once(callback, 5)        # called in 5 seconds

All the `schedule` methods will pass on any additional args or keyword args
you specify to the callback function::

    def move(dt, velocity, sprite):
        sprite.position += dt * velocity

    clock.schedule(move, velocity=5.0, sprite=alien)

You can cancel a function scheduled with any of these methods using
`unschedule`::

    clock.unschedule(move)

Using multiple clocks
=====================

The clock functions are all relayed to an instance of
:py:class:`~pyglet.clock.Clock` which is initialised with the module.  You can
get this instance to use directly::

    clk = pyglet.clock.get_default()

You can also replace the default clock with your own:

    myclk = pyglet.clock.Clock()
    pyglet.clock.set_default(myclk)

Each clock maintains its own set of scheduled functions and frequency
measurement.  Each clock must be "ticked" separately.

Multiple and derived clocks potentially allow you to separate "game-time" and
"wall-time", or to synchronise your clock to an audio or video stream instead
of the system clock.
"""
from __future__ import annotations

import time as _time
import inspect
import traceback

from bisect import bisect_left as _bisect_left
from bisect import insort_right as _insort_right
from typing import Any, Callable
from collections.abc import Generator, Iterable
from functools import wraps
from typing import Any, Callable, Protocol, TypeAlias, TypeVar, cast

from heapq import heappop as _heappop
from heapq import heappush as _heappush
from heapq import heappushpop as _heappushpop
from collections import deque as _deque

from pyglet.event import EVENT_HANDLED, EVENT_UNHANDLED, EventDispatcher

T = TypeVar('T')
CancelCallback: TypeAlias = Callable[[], None]
CompleteCallback: TypeAlias = Callable[[Any], None]
ErrorCallback: TypeAlias = Callable[[BaseException], None]
EasingFunction: TypeAlias = Callable[[float], float]
TweenUpdateFunction: TypeAlias = Callable[[float], Any]


def linear(progress: float) -> float:
    """Return unchanged progress for constant-speed interpolation."""
    return progress


def ease_in(progress: float) -> float:
    """Accelerate from rest using quadratic easing."""
    return progress * progress


def ease_out(progress: float) -> float:
    """Decelerate to rest using quadratic easing."""
    return 1.0 - (1.0 - progress) ** 2


def ease_in_out(progress: float) -> float:
    """Accelerate and then decelerate using quadratic easing."""
    if progress < 0.5:
        return 2.0 * progress * progress
    return 1.0 - ((-2.0 * progress + 2.0) ** 2) / 2.0


def smoothstep(progress: float) -> float:
    """Interpolate with zero first derivatives at both endpoints."""
    return progress * progress * (3.0 - 2.0 * progress)


class _StoppedResult:
    """Sentinel returned by composition helpers for a stopped child chain."""

    def __repr__(self) -> str:
        return 'STOPPED'


STOPPED = _StoppedResult()
"""Used when something continues after a stop."""


class ChainStopped(Exception):  # noqa: N818
    """Raised in a waiting chain when one of its child chains stops."""


class YieldingOperation(Protocol):
    """A yield instruction that can wake a suspended chain."""

    def start(
        self,
        complete: CompleteCallback,
        fail: ErrorCallback,
    ) -> CancelCallback | None:
        ...


class YieldInstruction:
    """Adapt a callback-driven API into a yield instruction."""

    def __init__(
        self,
        starter: Callable[
            [CompleteCallback, ErrorCallback],
            CancelCallback | None,
        ],
    ) -> None:
        """Initialize the operation with a callback starter."""
        self._starter = starter

    def start(
        self,
        complete: CompleteCallback,
        fail: ErrorCallback,
    ) -> CancelCallback | None:
        return self._starter(complete, fail)


class _ChainOperation:
    """Shared lifecycle behavior for operations composed of child chains."""
    _finished: bool
    _running: bool
    _clock: Clock
    _chains: tuple[Chain, ...]

    def __init__(
        self,
        chains: tuple[Chain, ...],
        *,
        clock: Clock | None = None,
    ) -> None:
        self._chains = chains
        self._clock: Clock = clock or _default
        self._running = False
        self._finished = False

    def stop(self) -> None:
        if not self._running:
            return

        self._running = False
        for child in self._chains:
            if not child.done:
                child.stop()

    def pause(self) -> None:
        if not self._running:
            return

        for child in self._chains:
            child.pause()

    def resume(self) -> None:
        if not self._running:
            return

        for child in self._chains:
            child.resume()


class _ParallelOperation(_ChainOperation):
    """Run several chains concurrently and complete when all are done."""
    _continue_on_stop: bool

    def __init__(
        self,
        chains: tuple[Chain, ...],
        *,
        continue_on_stop: bool = False,
        clock: Clock | None = None,
    ) -> None:
        """Initialize the operation with child chains."""
        super().__init__(chains, clock=clock)
        self._continue_on_stop = continue_on_stop

    def start(
        self,
        complete: CompleteCallback,
        fail: ErrorCallback,
    ) -> CancelCallback | None:
        self._running = True
        if not self._chains:
            complete(())
            self._finished = True
            self._running = False
            return None

        remaining = len(self._chains)
        results: list[Any] = [None] * remaining

        def finish_child(idx: int, result: Any) -> None:
            nonlocal remaining
            if not self._running:
                return

            results[idx] = result
            remaining -= 1
            if remaining:
                return

            self._finished = True
            self._running = False
            complete(tuple(results))

        def fail_child(error: BaseException) -> None:
            if not self._running:
                return

            # A parallel operation has one failure outcome.  Stop unfinished
            # siblings before reporting it so they cannot keep changing state.
            self.stop()
            self._finished = True
            fail(error)

        def stop_child(idx: int) -> None:
            if not self._running:
                return

            if self._continue_on_stop:
                finish_child(idx, STOPPED)
            else:
                fail_child(ChainStopped("A parallel child chain stopped."))

        for child_index, child in enumerate(self._chains):
            child.add_callbacks(
                on_complete=lambda result, current_index=child_index: finish_child(current_index, result),
                on_error=fail_child,
                on_stop=lambda current_index=child_index: stop_child(current_index),
            )

        try:
            for child_index, child in enumerate(self._chains):
                if child.stopped:
                    stop_child(child_index)
                else:
                    child.start()
                if not self._running:
                    break
        except Exception as exc:  # noqa: BLE001
            fail_child(exc)

        if self._finished:
            return None

        return self.stop

class _RaceOperation(_ChainOperation):
    """Run several chains concurrently and complete with the first result."""
    def __init__(self, chains: tuple[Chain, ...], *, clock: Clock | None = None) -> None:
        """Initialize the operation with child chains."""
        if not chains:
            raise ValueError("race requires at least one child chain")
        super().__init__(chains, clock=clock)

    def start(
        self,
        complete: CompleteCallback,
        fail: ErrorCallback,
    ) -> CancelCallback | None:
        self._running = True
        def finish_child(idx: int, result: Any) -> None:
            if not self._running:
                return

            self._finished = True
            self._running = False
            # A race consumes the first completion, then cancels all others.
            for child_chain in self._chains:
                if not child_chain.done:
                    child_chain.stop()
            complete((idx, result))

        def fail_child(error: BaseException) -> None:
            if not self._running:
                return

            self.stop()
            self._finished = True
            fail(error)

        def stop_child() -> None:
            if self._running:
                fail_child(ChainStopped("A race child chain stopped."))

        for child_idx, child in enumerate(self._chains):
            child.add_callbacks(
                on_complete=lambda result, current_idx=child_idx: finish_child(current_idx, result),
                on_error=fail_child,
                on_stop=stop_child,
            )

        try:
            for child in self._chains:
                if child.stopped:
                    stop_child()
                else:
                    child.start()
                if not self._running:
                    break
        except Exception as exc:  # noqa: BLE001
            fail_child(exc)

        if self._finished:
            return None

        return self.stop


class _TweenManager:
    """Update every tween on one clock from a single scheduled callback.

    This is mostly for improved performance, since unscheduling rebuilds
    the scheduler list.
    """

    def __init__(self, clock: Clock) -> None:
        self._clock = clock
        self._operations: dict[_TweenOperation, None] = {}

    def add(self, operation: _TweenOperation) -> None:
        if not self._operations:
            self._clock.schedule(self._tick)
        self._operations[operation] = None

    def remove(self, operation: _TweenOperation) -> None:
        self._operations.pop(operation, None)
        if not self._operations:
            self._clock.unschedule(self._tick)

    def _tick(self, _dt: float) -> None:
        now = self._clock.time()
        for operation in tuple(self._operations):
            operation._tick(now)  # noqa: SLF001


class _TweenOperation:
    """Drive an update callback with eased progress over a duration."""

    def __init__(
        self,
        duration: float,
        update: TweenUpdateFunction,
        *,
        easing: EasingFunction = linear,
        clock: Clock | None = None,
    ) -> None:
        """Initialize a tween with its duration, update, easing, and clock."""
        if duration < 0:
            raise ValueError("Tween duration cannot be negative.")
        if not callable(update):
            raise TypeError("Tween update must be callable.")
        if not callable(easing):
            raise TypeError("Tween easing must be callable.")

        self.duration = float(duration)
        self.update = update
        self.easing = easing
        self._clock: Clock = clock or _default
        self._manager = self._clock._get_tween_manager()  # noqa: SLF001
        self._elapsed = 0.0
        self._last_time: float | None = None
        self._running = False
        self._paused = False
        self._finished = False
        self._complete: CompleteCallback | None = None
        self._fail: ErrorCallback | None = None

    def start(
        self,
        complete: CompleteCallback,
        fail: ErrorCallback,
    ) -> CancelCallback | None:
        """Start updating and return a callback that cancels the tween."""
        if self._running or self._finished:
            raise RuntimeError("A tween operation can only be started once.")

        self._running = True
        self._complete = complete
        self._fail = fail

        if self.duration == 0.0:
            if self._apply(1.0):
                self._finish()
            return None

        if not self._apply(0.0):
            return None

        self._last_time = self._clock.time()
        self._manager.add(self)
        return self.stop

    def _tick(self, now: float) -> None:
        if not self._running or self._paused or self._last_time is None:
            return

        self._elapsed += max(now - self._last_time, 0.0)
        self._last_time = now
        progress = min(self._elapsed / self.duration, 1.0)
        if not self._apply(progress):
            return
        if progress >= 1.0:
            self._finish()

    def _apply(self, progress: float) -> bool:
        try:
            self.update(self.easing(progress))
        except Exception as exc:  # noqa: BLE001
            self._finish(exc)
            return False
        return True

    def _finish(self, error: BaseException | None = None) -> None:
        self._manager.remove(self)
        self._running = False
        self._paused = False
        self._finished = True
        self._last_time = None

        complete, fail = self._complete, self._fail
        self._complete = None
        self._fail = None
        if error is None:
            if complete is not None:
                complete(None)
        elif fail is not None:
            fail(error)

    def stop(self) -> None:
        """Cancel the tween without completing its waiting chain."""
        if not self._running:
            return

        self._manager.remove(self)
        self._running = False
        self._paused = False
        self._finished = True
        self._last_time = None
        self._complete = None
        self._fail = None

    def pause(self) -> None:
        """Pause the tween without consuming clock time."""
        if not self._running or self._paused:
            return

        self._paused = True
        self._last_time = None
        self._manager.remove(self)

    def resume(self) -> None:
        """Resume a paused tween from its current progress."""
        if not self._running or not self._paused:
            return

        self._paused = False
        self._last_time = self._clock.time()
        self._manager.add(self)


def from_callback(
    starter: Callable[
        [CompleteCallback, ErrorCallback],
        CancelCallback | None,
    ],
) -> YieldInstruction:
    """Create a yield instruction from a callback-based function."""
    return YieldInstruction(starter)


def wait_for_event(
    dispatcher: EventDispatcher,
    event_type: str,
    *,
    condition: Callable[..., bool] | None = None,
    consume: bool = False,
) -> YieldInstruction:
    """Create a yield instruction that completes on a dispatcher event.

    The temporary handler is removed when the event matches or when the
    waiting chain is stopped.
    """
    def starter(complete: CompleteCallback, _fail: ErrorCallback) -> CancelCallback:
        def handler(*args: Any) -> bool | None:
            if condition is not None and not condition(*args):
                return EVENT_UNHANDLED

            dispatcher.remove_handlers(**{event_type: handler})
            if not args:
                complete(None)
            elif len(args) == 1:
                complete(args[0])
            else:
                complete(args)

            return EVENT_HANDLED if consume else EVENT_UNHANDLED

        dispatcher.push_handlers(**{event_type: handler})
        return lambda: dispatcher.remove_handlers(**{event_type: handler})

    return from_callback(starter)


def parallel(*chains: Chain, continue_on_stop: bool = False) -> _ParallelOperation:
    """Run child chains concurrently and resume with their ordered results."""
    return _ParallelOperation(chains, continue_on_stop=continue_on_stop)


def race(*chains: Chain) -> _RaceOperation:
    """Run child chains concurrently and resume with the first result."""
    return _RaceOperation(chains)


YieldValue: TypeAlias = 'float | int | Chain | YieldingOperation | None'
ChainGenerator: TypeAlias = Generator[YieldValue, Any, T]
ChainTag: TypeAlias = str
_MISSING = object()


class Chain:
    """Run generator-based sequences on a pyglet clock.

    Chains yield delays, child chains, callback operations, or ``None``. They can
    be stopped as a group and exposes callbacks.
    """
    _callback_names = frozenset(('on_complete', 'on_stop', 'on_pause', 'on_resume', 'on_error'))
    on_complete: Callable[[Any], Any] | None
    on_stop: Callable[[], Any] | None
    on_pause: Callable[[], Any] | None
    on_resume: Callable[[], Any] | None
    on_error: Callable[[BaseException], Any] | None

    _callbacks: dict[str, list[Callable[..., Any]]]

    def __init__(self, generator: ChainGenerator[Any], clock: Clock | None = None) -> None:
        """Initialize the chain with a generator."""
        self._generator = generator
        self._clock: Clock = clock or _default
        self._callbacks = {
            name: [] for name in self._callback_names
        }
        self._running = False
        self._paused = False
        self._finished = False
        self._stopped = False
        self._child: Chain | None = None
        self._operation: YieldingOperation | None = None
        self._cancel_operation: CancelCallback | None = None
        self._scheduled_callback: Callable[[float], None] | None = None
        self._scheduled_remaining: float | None = None
        self._scheduled_started_at: float | None = None
        self._pending_advance: tuple[Any, BaseException | None] | None = None

        # Stale guard prevents old callbacks from resuming.
        self._wait_token: object | None = None

        self.result: Any = None
        self.exception: BaseException | None = None

    @property
    def running(self) -> bool:
        return self._running and not self._paused

    @property
    def paused(self) -> bool:
        return self._paused

    @property
    def done(self) -> bool:
        return self._finished

    @property
    def completed(self) -> bool:
        return self._finished and not self._stopped and self.exception is None

    @property
    def stopped(self) -> bool:
        return self._stopped

    @property
    def failed(self) -> bool:
        return self.exception is not None

    @property
    def clock(self) -> Clock:
        return self._clock

    def start(self) -> Chain:
        if self._finished:
            raise RuntimeError("A completed or stopped chain cannot be restarted")
        if not self._running:
            self._running = True
            self._advance(0.0)
        return self

    def _advance(
        self,
        _dt: float,
        value: Any = _MISSING,
        error: BaseException | None = None,
    ) -> None:
        if not self._running:
            return

        self._scheduled_callback = None
        self._scheduled_remaining = None
        self._scheduled_started_at = None
        self._wait_token = None

        if self._paused:
            self._pending_advance = (value, error)
            return

        try:
            # Resume the generator using the outcome of its previous yield:
            # a yielded child or operation sends a value, while its failure is
            # thrown back into the generator for ordinary try/except handling.
            if error is not None:
                yielded = self._generator.throw(error)
            elif value is _MISSING:
                yielded = next(self._generator)
            else:
                yielded = self._generator.send(value)
        except StopIteration as completed:
            self._finish(completed.value)
            return
        except ChainStopped:
            self.stop()
            return
        except Exception as exc:  # noqa: BLE001
            self._fail(exc)
            return

        if isinstance(yielded, Chain):
            self._wait_for_child(yielded)
        elif isinstance(yielded, (int, float)):
            delay = float(yielded)
            if delay < 0:
                self._fail(ValueError("A chain cannot yield a negative delay"))
            else:
                self._schedule_advance(delay)
        elif yielded is None:
            self._schedule_advance(0.0)
        elif hasattr(yielded, "start") and callable(yielded.start):
            self._wait_for_operation(cast("YieldingOperation", yielded))
        else:
            self._fail(
                TypeError(
                    "A chain must yield a delay, another Chain, "
                    "a callback operation, or None; "
                    f"received {yielded}",
                ),
            )

    def _wait_for_child(self, child: Chain) -> None:
        self._child = child
        token = self._new_wait_token()

        # Child results and errors resume this chain. A stopped child throws a
        # catchable ChainStopped signal into the generator; if it remains
        # unhandled, _advance stops this waiting parent.
        child.add_callbacks(
            on_complete=lambda result: self._resume_if_current(token, value=result),
            on_error=lambda error: self._resume_if_current(token, error=error),
            on_stop=lambda: self._resume_if_current(
                token,
                error=ChainStopped("A child chain stopped."),
            ),
        )

        if child.stopped:
            self._resume_if_current(token, error=ChainStopped("A child chain stopped."))
            return

        try:
            child.start()
        except Exception as exc:  # noqa: BLE001
            self._resume_if_current(token, error=exc)

    def _wait_for_operation(self, operation: YieldingOperation) -> None:
        token = self._new_wait_token()

        def complete(result: Any = None) -> None:
            self._resume_if_current(token, value=result)

        def fail(error: BaseException) -> None:
            self._resume_if_current(token, error=error)

        try:
            cancel = operation.start(complete, fail)
            # A starter may call complete or fail before returning.  Only keep
            # its cancellation callback if this is still the active wait.
            if self._wait_token is token:
                self._operation = operation
                self._cancel_operation = cancel
        except Exception as exc:  # noqa: BLE001
            fail(exc)

    def _new_wait_token(self) -> object:
        # Callback-based operations can complete after cancellation.
        # Gives each wait a distinct identity so a late callback cannot resume a chain
        # that has already advanced, stopped, or started another wait.
        token = object()
        self._wait_token = token
        return token

    def _resume_if_current(
        self,
        token: object,
        *,
        value: Any = _MISSING,
        error: BaseException | None = None,
    ) -> None:
        # This is the single gate used by child and callback-operation results.
        if not self._running or self._wait_token is not token:
            return
        self._wait_token = None
        self._cancel_operation = None
        self._operation = None
        self._child = None
        if self._paused:
            self._pending_advance = (value, error)
            return
        self._schedule_advance(0.0, value=value, error=error)

    def _schedule_advance(
        self,
        delay: float,
        *,
        value: Any = _MISSING,
        error: BaseException | None = None,
    ) -> None:
        if not self._running:
            return

        def callback(dt: float) -> None:
            if not self._running:
                return

            # Zero-delay advances use ``schedule`` to preserve next-tick
            # behavior, so they must remove themselves. Positive delays are
            # one-shot items and have already been removed by the scheduler.
            if self._scheduled_started_at is None:
                self._clock.unschedule(callback)
            self._advance(dt, value, error)

        self._scheduled_callback = callback
        self._scheduled_remaining = delay
        if delay > 0.0:
            self._scheduled_started_at = self._clock.time()
            self._clock.schedule_once(callback, delay)
        else:
            self._scheduled_started_at = None
            self._clock.schedule(callback)

    def stop(self) -> None:
        """Stops the chain from running."""
        if not self._running:
            return

        self._running = False
        self._paused = False
        self._finished = True
        self._stopped = True
        self._pending_advance = None
        self._wait_token = None

        if self._scheduled_callback is not None:
            self._clock.unschedule(self._scheduled_callback)
            self._scheduled_callback = None
            self._scheduled_remaining = None
            self._scheduled_started_at = None

        if self._child is not None:
            child, self._child = self._child, None
            child.stop()

        if self._cancel_operation is not None:
            cancel, self._cancel_operation = self._cancel_operation, None
            self._operation = None
            cancel()

        self._generator.close()
        self._dispatch_callbacks('on_stop')

    def pause(self) -> Chain:
        """Pauses the chain, with the intention to either resume or stop in the future.

        Cannot resume if chain was stopped.
        """
        if not self._running or self._paused or self._finished:
            return self

        self._paused = True

        if self._scheduled_callback is not None:
            # Calculate remaining for when unpausing.
            if self._scheduled_started_at is not None and self._scheduled_remaining is not None:
                elapsed = max(self._clock.time() - self._scheduled_started_at, 0.0)
                self._scheduled_remaining = max(self._scheduled_remaining - elapsed, 0.0)
            self._clock.unschedule(self._scheduled_callback)
            self._scheduled_started_at = None

        if self._child is not None:
            self._child.pause()
        elif self._operation is not None and hasattr(self._operation, 'pause'):
            self._operation.pause()

        self._dispatch_callbacks('on_pause')

        return self

    def resume(self) -> Chain:
        """Resumes the chain if it was paused.

        Cannot resume if chain was stopped.
        """
        if not self._running or not self._paused or self._finished:
            return self

        self._paused = False

        if self._child is not None:
            self._child.resume()
        elif self._operation is not None and hasattr(self._operation, 'resume'):
            self._operation.resume()
        elif self._pending_advance is not None:
            value, error = self._pending_advance
            self._pending_advance = None
            self._schedule_advance(0.0, value=value, error=error)
        elif self._scheduled_callback is not None:
            remaining = self._scheduled_remaining or 0.0
            if remaining > 0.0:
                self._scheduled_started_at = self._clock.time()
                self._clock.schedule_once(self._scheduled_callback, remaining)
            else:
                self._clock.schedule(self._scheduled_callback)

        self._dispatch_callbacks('on_resume')

        return self

    def _finish(self, result: Any) -> None:
        self._running = False
        self._paused = False
        self._finished = True
        self.result = result
        self._dispatch_callbacks('on_complete', result)

    def _fail(self, error: BaseException) -> None:
        self._running = False
        self._paused = False
        self._finished = True
        self.exception = error
        if not self._dispatch_callbacks('on_error', error):
            traceback.print_exception(error)

    def add_callbacks(self, **callbacks: Callable[..., Any]) -> Chain:
        """Register strongly referenced callbacks and return this chain.

        Accepted names are ``on_complete``, ``on_stop``, ``on_pause``,
        ``on_resume``, and ``on_error``.
        """
        for name, callback in callbacks.items():
            if name not in self._callback_names:
                msg = f"Unknown chain callback {name!r}"
                raise ValueError(msg)
            if not callable(callback):
                msg = f"Chain callback {name!r} must be callable"
                raise TypeError(msg)
            self._callbacks[name].append(callback)

        return self

    def _dispatch_callbacks(self, name: str, *args: Any) -> bool:
        """Invoke registered callbacks and an optional directly assigned callback.

        Returns:
            True if callback was called.
        """
        invoked = False
        for callback in tuple(self._callbacks[name]):
            invoked = True
            callback(*args)
        return invoked


class ChainGroup:
    """Track related chains and child groups for lifecycle control."""

    def __init__(self, clock: Clock | None = None) -> None:
        """Initialize the group with an optional clock for unbound chains."""
        self._clock: Clock = clock or _default
        self._chains: dict[Chain, frozenset[ChainTag]] = {}
        self._groups: set[ChainGroup] = set()
        self._paused = False

    @property
    def clock(self) -> Clock:
        return self._clock

    @property
    def paused(self) -> bool:
        return self._paused

    @property
    def chains(self) -> tuple[Chain, ...]:
        return tuple(self._chains)

    @property
    def groups(self) -> tuple[ChainGroup, ...]:
        return tuple(self._groups)

    def add_group(self, group: ChainGroup) -> ChainGroup:
        """Add an existing child group and return it."""
        if group is self:
            raise ValueError("A chain group cannot contain itself")

        self._groups.add(group)
        if self._paused:
            group.pause()
        return group

    def create_group(self, clock: Clock | None = None) -> ChainGroup:
        """Create, add, and return a child group."""
        return self.add_group(ChainGroup(clock=clock or self._clock))

    def add(
        self,
        chain: Chain,
        *,
        tag: ChainTag | None = None,
        tags: Iterable[ChainTag] = (),
    ) -> Chain:
        """Track a chain without starting it."""
        if chain.done:
            return chain

        chain_tags = self._normalize_tags(tag, tags)
        self._chains[chain] = chain_tags

        def remove_chain(_result: Any = None) -> None:
            self._chains.pop(chain, None)

        chain.add_callbacks(
            on_complete=remove_chain,
            on_stop=remove_chain,
            on_error=remove_chain,
        )

        if self._paused and chain.running:
            chain.pause()

        return chain

    def start(
        self,
        chain: Chain,
        *,
        tag: ChainTag | None = None,
        tags: Iterable[ChainTag] = (),
    ) -> Chain:
        """Track and start a chain, or return it unchanged if already done."""
        self.add(chain, tag=tag, tags=tags)
        if chain.done:
            return chain

        chain.start()
        if self._paused and chain.running:
            chain.pause()
        return chain

    def clear(
        self,
        *,
        tag: ChainTag | None = None,
        tags: Iterable[ChainTag] = (),
    ) -> ChainGroup:
        """Stop and forget tracked chains, optionally filtered by tag."""
        tag_filter = self._normalize_tags(tag, tags)

        # Groups form a lifecycle tree.  Apply the same filter to children
        # before removing this group's unfiltered child-group references.
        for child_group in tuple(self._groups):
            child_group.clear(tags=tag_filter)

        for chain, chain_tags in tuple(self._chains.items()):
            if tag_filter and chain_tags.isdisjoint(tag_filter):
                continue

            self._chains.pop(chain, None)
            chain.stop()

        if not tag_filter:
            self._groups.clear()

        return self

    def stop(
        self,
        *,
        tag: ChainTag | None = None,
        tags: Iterable[ChainTag] = (),
    ) -> ChainGroup:
        """Alias for :py:meth:`clear`."""
        return self.clear(tag=tag, tags=tags)

    def pause(
        self,
        *,
        tag: ChainTag | None = None,
        tags: Iterable[ChainTag] = (),
    ) -> ChainGroup:
        """Pause tracked chains and child groups, optionally filtered by tag."""
        tag_filter = self._normalize_tags(tag, tags)

        if not tag_filter:
            self._paused = True

        for child_group in tuple(self._groups):
            child_group.pause(tags=tag_filter)

        for chain, chain_tags in tuple(self._chains.items()):
            if tag_filter and chain_tags.isdisjoint(tag_filter):
                continue
            chain.pause()

        return self

    def resume(
        self,
        *,
        tag: ChainTag | None = None,
        tags: Iterable[ChainTag] = (),
    ) -> ChainGroup:
        """Resume tracked chains and child groups, optionally filtered by tag."""
        tag_filter = self._normalize_tags(tag, tags)

        if not tag_filter:
            self._paused = False

        for child_group in tuple(self._groups):
            child_group.resume(tags=tag_filter)

        for chain, chain_tags in tuple(self._chains.items()):
            if tag_filter and chain_tags.isdisjoint(tag_filter):
                continue
            chain.resume()

        return self

    @staticmethod
    def _normalize_tags(
        tag: ChainTag | None,
        tags: Iterable[ChainTag],
    ) -> frozenset[ChainTag]:
        normalized = set(tags)
        if tag is not None:
            normalized.add(tag)
        return frozenset(normalized)

def chain(
    function: Callable[..., ChainGenerator[T]],
    *,
    clock: Clock | None = None,
) -> Callable[..., Chain]:
    """Decorate a generator function so it returns a ``Chain``."""

    @wraps(function)
    def wrapper(*args: Any, **kwargs: Any) -> Chain:
        generator = function(*args, **kwargs)
        if not inspect.isgenerator(generator):
            msg = (
                f"{function.__qualname__} must be a generator function "
                "and contain at least one yield"
            )
            raise TypeError(
                msg,
            )
        return Chain(generator, clock=clock)

    return wrapper


def tween(
    duration: float,
    update: TweenUpdateFunction,
    *,
    easing: EasingFunction = linear,
    clock: Clock | None = None,
) -> Chain:
    """Create a tween chain that updates eased progress over a duration."""
    bound_clock = clock or _default
    operation = _TweenOperation(duration, update, easing=easing, clock=bound_clock)

    def _tween() -> ChainGenerator[None]:
        yield operation

    return Chain(_tween(), clock=bound_clock)


def yielding_callback(
    function: Callable[..., CancelCallback | None],
) -> Callable[..., YieldInstruction]:
    """Decorate a callback starter so it can be yielded from a chain."""

    @wraps(function)
    def wrapper(*args: Any, **kwargs: Any) -> YieldInstruction:
        def start(
            complete: CompleteCallback,
            fail: ErrorCallback,
        ) -> CancelCallback | None:
            return function(complete, fail, *args, **kwargs)

        return YieldInstruction(start)

    return wrapper


def timeout(delay: float, *, clock: Clock | None = None) -> Chain:
    """Create a chain that completes after ``delay`` seconds."""
    if delay < 0:
        raise ValueError("Timeout delay cannot be negative.")

    def _timeout() -> ChainGenerator[None]:
        yield delay

    return chain(_timeout, clock=clock)()


def repeat(factory: Callable[[], Chain], count: int, *, clock: Clock | None = None) -> Chain:
    """Create a chain that runs a child-chain factory ``count`` times."""
    if count < 0:
        raise ValueError("Repeat count cannot be negative.")

    def _repeat() -> ChainGenerator[tuple[Any, ...]]:
        results = []
        for _ in range(count):
            results.append((yield factory()))  # noqa: PERF401
        return tuple(results)

    return chain(_repeat, clock=clock)()


def repeat_until(
    factory: Callable[[], Chain],
    condition: Callable[[], bool],
    *,
    clock: Clock | None = None,
) -> Chain:
    """Create a chain that repeats child chains until ``condition`` is true."""

    def _repeat_until() -> ChainGenerator[tuple[Any, ...]]:
        results = []
        while not condition():
            results.append((yield factory()))
        return tuple(results)

    return chain(_repeat_until, clock=clock)()


def repeat_forever(factory: Callable[[], Chain], *, clock: Clock | None = None) -> Chain:
    """Create a chain that repeats child chains until stopped."""

    def _repeat_forever() -> ChainGenerator[None]:
        while True:
            yield factory()

    return chain(_repeat_forever, clock=clock)()


def repeat_duration(factory: Callable[[], Chain], duration: float, *, clock: Clock | None = None) -> Chain:
    """Create a chain that repeats child chains until ``duration`` elapses."""
    if duration < 0:
        raise ValueError("Repeat duration cannot be negative.")

    def _repeat_duration() -> ChainGenerator[Any]:
        winner_index, result = yield race(
            repeat_forever(factory, clock=clock),
            timeout(duration, clock=clock),
        )
        return result if winner_index == 0 else None

    return chain(_repeat_duration, clock=clock)()


class _ScheduledItem:
    __slots__ = ['args', 'func', 'kwargs']

    def __init__(self, func: Callable, args: Any, kwargs: Any) -> None:
        self.func = func
        self.args = args
        self.kwargs = kwargs


class _ScheduledIntervalItem:
    __slots__ = ['args', 'func', 'interval', 'kwargs', 'last_ts', 'next_ts']

    def __init__(self, func: Callable, interval: float, last_ts: float, next_ts: float, args: Any, kwargs: Any) -> None:
        self.func = func
        self.interval = interval
        self.last_ts = last_ts
        self.next_ts = next_ts
        self.args = args
        self.kwargs = kwargs

    def __lt__(self, other: _ScheduledIntervalItem) -> bool:
        return self.next_ts < other.next_ts


class _ScheduledFixedDelayItem(_ScheduledIntervalItem):
    """Marker type for intervals rescheduled from callback completion."""

    __slots__ = ()


class Clock:
    """Schedule callbacks and chains against a single time source.

    Each clock maintains its own scheduled callbacks, chain state, and
    frequency measurements. Custom clocks can be ticked independently to
    separate gameplay time, UI time, or other application timelines.
    """

    # List of functions to call every tick.
    _schedule_items: list

    # List of schedule interval items kept in sort order.
    _schedule_interval_items: list

    # Lazily-built sorted deadline cache used by the soft scheduler.
    # Creation of soft schedule and recovery of timers is faster.
    _schedule_interval_timestamps: list[float] | None

    # If True, a sleep(0) is inserted on every tick.
    _force_sleep: bool = False

    def __init__(self, time_function: Callable = _time.perf_counter) -> None:
        """Initialize a Clock, with optional custom time function.

        You can provide a custom time function to return the elapsed
        time of the application, in seconds. Defaults to ``time.perf_counter``,
        but can be replaced to allow for easy time dilation effects or game
        pausing.
        """
        self.time = time_function
        self.last_ts = None
        self.next_ts = self.time()

        # Used by self.get_frequency to show update frequency
        self.times: _deque = _deque()
        self.cumulative_time = 0.0
        self.window_size = 60

        self._schedule_items = []
        self._schedule_interval_items = []
        self._schedule_interval_timestamps = None
        self._current_interval_item = None
        self._tween_manager: _TweenManager | None = None

    def chain(self, function: Callable[..., ChainGenerator[T]]) -> Callable[..., Chain]:
        """Decorate a generator function so returned chains use this clock."""
        return chain(function, clock=self)

    def timeout(self, delay: float) -> Chain:
        """Create a chain on this clock that completes after ``delay`` seconds."""
        return timeout(delay, clock=self)

    def parallel(self, *chains: Chain, continue_on_stop: bool = False) -> _ParallelOperation:
        """Run child chains on this clock and resume with their ordered results."""
        return _ParallelOperation(chains, continue_on_stop=continue_on_stop, clock=self)

    def race(self, *chains: Chain) -> _RaceOperation:
        """Run child chains on this clock and resume with the first result."""
        return _RaceOperation(chains, clock=self)

    def repeat(self, factory: Callable[[], Chain], count: int) -> Chain:
        """Create a repeat chain on this clock."""
        return repeat(factory, count, clock=self)

    def repeat_until(self, factory: Callable[[], Chain], condition: Callable[[], bool]) -> Chain:
        """Create a repeat-until chain on this clock."""
        return repeat_until(factory, condition, clock=self)

    def repeat_forever(self, factory: Callable[[], Chain]) -> Chain:
        """Create an indefinite repeat chain on this clock."""
        return repeat_forever(factory, clock=self)

    def repeat_duration(self, factory: Callable[[], Chain], duration: float) -> Chain:
        """Create a duration-limited repeat chain on this clock."""
        return repeat_duration(factory, duration, clock=self)

    def tween(
        self,
        duration: float,
        update: TweenUpdateFunction,
        *,
        easing: EasingFunction = linear,
    ) -> Chain:
        """Create a tween chain driven by this clock."""
        return tween(duration, update, easing=easing, clock=self)

    def _get_tween_manager(self) -> _TweenManager:
        if self._tween_manager is None:
            self._tween_manager = _TweenManager(self)
        return self._tween_manager

    def create_group(self) -> ChainGroup:
        """Create a chain group bound to this clock."""
        return ChainGroup(clock=self)

    @staticmethod
    def sleep(microseconds: float) -> None:
        _time.sleep(microseconds * 1e-6)

    def update_time(self) -> float:
        """Get the elapsed time since the last call to `update_time`.

        This updates the clock's internal measure of time and returns
        the difference (in seconds) since the last time it was called.
        The first call of this method always returns 0.
        """
        ts = self.time()
        if self.last_ts is None:
            delta_t = 0.0
        else:
            delta_t = ts - self.last_ts
            self.times.appendleft(delta_t)
            if len(self.times) > self.window_size:
                self.cumulative_time -= self.times.pop()
        self.cumulative_time += delta_t
        self.last_ts = ts

        return delta_t

    def call_scheduled_functions(self, dt: float) -> bool:
        """Call scheduled functions that elapsed on the last `update_time`.

        This method is called automatically when the clock is ticked
        (see :py:meth:`~pyglet.clock.tick`), so you need not call it
        yourself in most cases.

        Args:
            dt:
                The elapsed time since the last update to pass to each
                scheduled function. This is *not* used to calculate which
                functions have elapsed.

        Returns: ``True`` if any functions were called, else ``False``.
        """
        now = self.last_ts or self.time()
        result = False  # flag indicates if any function was called

        # handle items scheduled for every tick
        if self._schedule_items:
            result = True
            # duplicate list in case event unschedules itself
            for item in list(self._schedule_items):
                item.func(dt, *item.args, **item.kwargs)

        # check the next scheduled item that is not called each tick
        # if it is scheduled in the future, then exit
        interval_items = self._schedule_interval_items
        try:
            if interval_items[0].next_ts > now:
                return result
        except IndexError:
            # The interval_items list is empty
            return result

        # Ordinary heap dispatch does not need the soft scheduler's sorted
        # deadline view. Invalidate it up front; a recovery batch will rebuild
        # it once and keep it synchronized for the rest of that batch.
        self._schedule_interval_timestamps = None

        # NOTE: there is no special handling required to manage things
        #       that are scheduled during this loop, due to the heap
        self._current_interval_item = item = None
        get_soft_next_ts = self._get_soft_next_ts
        while interval_items:

            # the scheduler will hold onto a reference to an item in
            # case it needs to be rescheduled.  it is more efficient
            # to push and pop the heap at once rather than two operations
            if item is None:
                item = _heappop(interval_items)
                timestamps = self._schedule_interval_timestamps
                if timestamps is not None:
                    index = _bisect_left(timestamps, item.next_ts)
                    timestamps.pop(index)
            else:
                if self._schedule_interval_timestamps is None:
                    item = _heappushpop(interval_items, item)
                else:
                    item = self._pushpop_interval_item(item)

            # a scheduled function may try to unschedule itself,
            # so we need to keep a reference to the current
            # item no longer on heap to be able to check
            self._current_interval_item = item

            # if next item is scheduled in the future then break
            if item.next_ts > now:
                break

            scheduled_ts = item.next_ts
            if isinstance(item, _ScheduledFixedDelayItem):
                # Fixed-delay callbacks use their actual start and completion
                # timestamps. Eligibility remains bounded by ``now`` above, so
                # callback runtime cannot pull more timers into this dispatch.
                callback_ts = self.time()
                item.func(callback_ts - item.last_ts, *item.args, **item.kwargs)
                finished_ts = self.time()
                if item.interval:
                    item.last_ts = callback_ts
                    item.next_ts = finished_ts + item.interval
                else:
                    # The callback unscheduled itself while it was executing.
                    self._current_interval_item = item = None
            else:
                # Phase-based callbacks share the clock tick's timestamp.
                item.func(now - item.last_ts, *item.args, **item.kwargs)
                if item.interval:
                    item.last_ts = now
                    # Keep the requested series of deadlines while the next
                    # one is still in the future. If a complete call was
                    # missed, coalesce it and spread recovery deadlines.
                    item.next_ts = scheduled_ts + item.interval
                    if item.next_ts <= now:
                        item.next_ts = get_soft_next_ts(now, item.interval)
                else:
                    # The callback unscheduled itself while it was executing.
                    self._current_interval_item = item = None

        if item is not None:
            if self._schedule_interval_timestamps is None:
                _heappush(interval_items, item)
            else:
                self._push_interval_item(item, preserve_timestamps=True)

        return True

    def tick(self, poll: bool = False) -> float:
        """Signify that one frame has passed.

        This will call any scheduled functions that have elapsed,
        and returns the number of seconds since the last time this
        method has been called. The first time this method is called,
        0 is returned.

        Args:
            poll:
                If True, the function will call any scheduled functions
                but will not sleep or busy-wait for any reason.  Recommended
                for advanced applications managing their own sleep timers
                only.
        """
        if not poll and self._force_sleep:
            self.sleep(0)

        delta_t = self.update_time()
        self.call_scheduled_functions(delta_t)
        return delta_t

    def get_sleep_time(self, sleep_idle: bool) -> float | None:
        """Get the time until the next item is scheduled, if any.

        Applications can choose to continue receiving updates at the
        maximum framerate during idle time (when no functions are scheduled),
        or they can sleep through their idle time and allow the CPU to
        switch to other processes or run in low-power mode.

        If ``sleep_idle`` is ``True`` the latter behaviour is selected, and
        ``None`` will be returned if there are no scheduled items.

        Otherwise, if ``sleep_idle`` is ``False``, or if any scheduled items
        exist, a value of 0 is returned.

        Args:
            sleep_idle:
                If True, the application intends to sleep through its idle
                time; otherwise it will continue ticking at the maximum
                frame rate allowed.
        """
        if self._schedule_items or not sleep_idle:
            return 0.0

        if self._schedule_interval_items:
            return max(self._schedule_interval_items[0].next_ts - self.time(), 0.0)

        return None

    def get_frequency(self) -> float:
        """Get the average clock update frequency of recent history.

        The result is the average of a sliding window of the last "n" updates,
        where "n" is some number designed to cover approximately 1 second.
        This is the clock frequency, **not** the Window redraw rate (fps).
        """
        if not self.cumulative_time:
            return 0
        return len(self.times) / self.cumulative_time

    def _get_nearest_ts(self) -> float:
        """Get the nearest timestamp.

        Schedule from now, unless now is sufficiently close to last_ts, in
        which case use last_ts.  This clusters together scheduled items that
        probably want to be scheduled together.
        """
        last_ts = self.last_ts or self.next_ts
        ts = self.time()
        if ts - last_ts > 0.2:
            return ts
        return last_ts

    def _push_interval_item(
        self,
        item: _ScheduledIntervalItem,
        *,
        preserve_timestamps: bool = False,
    ) -> None:
        """Push an interval item and update or invalidate the timestamp cache."""
        _heappush(self._schedule_interval_items, item)
        if preserve_timestamps and self._schedule_interval_timestamps is not None:
            _insort_right(self._schedule_interval_timestamps, item.next_ts)
        else:
            self._schedule_interval_timestamps = None

    def _pushpop_interval_item(self, item: _ScheduledIntervalItem) -> _ScheduledIntervalItem:
        """Push and pop an interval item while keeping a timestamp cache synchronized."""
        timestamps = self._schedule_interval_timestamps
        if timestamps is not None:
            _insort_right(timestamps, item.next_ts)
        popped_item = _heappushpop(self._schedule_interval_items, item)
        if timestamps is not None:
            index = _bisect_left(timestamps, popped_item.next_ts)
            timestamps.pop(index)
        return popped_item

    def _get_soft_next_ts(self, last_ts: float, interval: float) -> float:
        timestamps = self._schedule_interval_timestamps
        if timestamps is None:
            timestamps = sorted(item.next_ts for item in self._schedule_interval_items)
            self._schedule_interval_timestamps = timestamps

        def taken(ts: float, e: float) -> bool:
            """Check if `ts` has already got an item scheduled nearby."""
            # The first timestamp >= ts - e is in range when it is <= ts + e.
            index = _bisect_left(timestamps, ts - e)
            return index < len(timestamps) and timestamps[index] <= ts + e

        # Binary division over interval:
        #
        # 0                          interval
        # |--------------------------|
        #   5  3   6   2   7  4  8   1          Order of search
        #
        # i.e., first scheduled at interval,
        #       then at            interval/2
        #       then at            interval/4
        #       then at            interval*3/4
        #       then at            ...
        #
        # Schedule is hopefully then evenly distributed for any interval,
        # and any number of scheduled functions.

        next_ts = last_ts + interval
        if not taken(next_ts, interval / 4):
            return next_ts

        dt = interval
        divs = 1
        while True:
            next_ts = last_ts
            for _ in range(divs - 1):
                next_ts += dt
                if not taken(next_ts, dt / 4):
                    return next_ts
            dt /= 2
            divs *= 2

            # Avoid infinite loop in pathological case
            if divs > 16:
                return next_ts

    def schedule(self, func: Callable, *args: Any, **kwargs: Any) -> None:
        """Schedule a function to be called every tick.

        The scheduled function should have a prototype that includes ``dt``
        as the first argument, which gives the elapsed time in seconds since
        the last clock tick. Any additional args or kwargs given to this
        method are passed on to the callback::

            def callback(dt, *args, **kwargs):
                pass


        .. note:: Functions scheduled using this method will be called
                  every tick by the default pyglet event loop, which can
                  lead to high CPU usage. It is usually better to use
                  :py:meth:`~pyglet.clock.schedule_interval` unless
                  this is desired.
        """
        item = _ScheduledItem(func, args, kwargs)
        self._schedule_items.append(item)

    def schedule_once(self, func: Callable, delay: float, *args: Any, **kwargs: Any) -> None:
        """Schedule a function to be called once after ``delay`` seconds.

        The callback function prototype is the same as for
        :py:meth:`~pyglet.clock.Clock.schedule`.
        """
        last_ts = self._get_nearest_ts()
        next_ts = last_ts + delay
        item = _ScheduledIntervalItem(func, 0, last_ts, next_ts, args, kwargs)
        _heappush(self._schedule_interval_items, item)
        if self._schedule_interval_timestamps is not None:
            self._schedule_interval_timestamps = None

    def schedule_interval(self, func: Callable, interval: float, *args: Any, **kwargs: Any) -> None:
        """Schedule a function to be called every ``interval`` seconds.

        To schedule a function to be called at 60Hz (60fps), you would use ``1/60``
        for the interval, and so on. The clock follows the requested series of
        times. If a callback is late but its following time has not passed, that
        following time is kept. A late callback can therefore be followed by a
        shorter gap.

        If pyglet misses one or more complete calls, those calls are skipped
        rather than replayed. The next times of callbacks that are overdue
        together are spread apart to avoid a burst of catch-up work. Delays can
        occur when the main thread is overloaded or blocked.

        The callback function prototype is the same as for
        :py:meth:`~pyglet.clock.Clock.schedule`.

        .. note:: Specifying an interval of ``0`` will prevent the function from
                  being called again. If you want to schedule a function to be called
                  as often as possible, see :py:meth:`~pyglet.clock.Clock.schedule`.
        """
        last_ts = self._get_nearest_ts()
        next_ts = last_ts + interval
        item = _ScheduledIntervalItem(func, interval, last_ts, next_ts, args, kwargs)
        _heappush(self._schedule_interval_items, item)
        if self._schedule_interval_timestamps is not None:
            self._schedule_interval_timestamps = None

    def schedule_interval_fixed_delay(
        self,
        func: Callable,
        interval: float,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Schedule a function with a fixed delay after each completed call.

        Unlike :py:meth:`~pyglet.clock.Clock.schedule_interval`, the next
        deadline is calculated from the time the callback finishes. This
        prevents a long-running callback from immediately becoming due again.
        Callbacks initially due together can acquire different next times
        according to when each one finishes.

        The time from the start of one call to the next is approximately the
        callback's runtime plus ``interval``. Missed calls are never accumulated,
        and callback runtime does not expand the set of callbacks eligible in
        the current clock tick.

        This is useful for polling and maintenance work where the delay between
        completed operations matters more than maintaining the original series
        of requested times.

        .. note:: Specifying an interval of ``0`` will prevent the function from
                  being called again.

        .. note:: This is not a fixed time step implementation.
        """
        last_ts = self._get_nearest_ts()
        next_ts = last_ts + interval
        item = _ScheduledFixedDelayItem(
            func,
            interval,
            last_ts,
            next_ts,
            args,
            kwargs,
        )
        _heappush(self._schedule_interval_items, item)
        if self._schedule_interval_timestamps is not None:
            self._schedule_interval_timestamps = None

    def schedule_interval_for_duration(self, func: Callable, interval: float,
                                       duration: float, *args: Any, **kwargs: Any) -> None:
        """Temporarily schedule a function to be called every ``interval`` seconds.

        This method will schedule a function to be called every ``interval``
        seconds (see  :py:meth:`~pyglet.clock.Clock.schedule_interval`), but
        will automatically unschedule it after ``duration`` seconds.

        The callback function prototype is the same as for
        :py:meth:`~pyglet.clock.Clock.schedule`.

        :Args:
            func:
                The function to call when the timer lapses.
            interval:
                The number of seconds to wait between each call.
            duration:
                The number of seconds for which the function is scheduled.
        """
        # NOTE: unschedule wrapper that takes `dt` argument
        def _unschedule(_dt: float, _func: Callable) -> None:
            self.unschedule(_func)

        self.schedule_interval(func, interval, *args, **kwargs)
        self.schedule_once(_unschedule, duration, func)

    def schedule_interval_soft(self, func: Callable, interval: float, *args: Any, **kwargs: Any) -> None:
        """Schedule a function to be called approximately every ``interval`` seconds.

        This method is similar to :py:meth:`~pyglet.clock.Clock.schedule_interval`,
        except that the clock chooses a different starting time from nearby
        scheduled functions in order to distribute CPU load more evenly.

        This is useful for functions that need to be called regularly,
        but not relative to the initial start time.  :py:mod:`pyglet.media`
        does this for scheduling audio buffer updates, which need to occur
        regularly -- if all audio updates are scheduled at the same time
        (for example, mixing several tracks of a music score, or playing
        multiple videos back simultaneously), the resulting load on the
        CPU is excessive for those intervals but idle outside.  Using
        the soft interval scheduling, the load is more evenly distributed.

        Soft interval scheduling can also start repeating animations at
        different points in their cycles; for example, multiple flags waving
        in the wind.
        """
        next_ts = self._get_soft_next_ts(self._get_nearest_ts(), interval)
        last_ts = next_ts - interval
        item = _ScheduledIntervalItem(func, interval, last_ts, next_ts, args, kwargs)
        self._push_interval_item(item, preserve_timestamps=True)

    def unschedule(self, func: Callable) -> None:
        """Remove a function from the schedule.

        If the function appears in the schedule more than once, all occurrences
        are removed.  If the function was not scheduled, no error is raised.
        """
        # clever remove item without disturbing the heap:
        # 1. set function to an empty lambda -- original function is not called
        # 2. set interval to 0               -- item will be removed from heap eventually
        valid_items = {item for item in self._schedule_interval_items if item.func == func}

        if self._current_interval_item and self._current_interval_item.func == func:
            valid_items.add(self._current_interval_item)

        for item in valid_items:
            item.interval = 0
            item.func = lambda x, *args, **kwargs: x

        self._schedule_items = [i for i in self._schedule_items if i.func != func]


# Default clock.
_default = Clock()


def set_default(default: Clock) -> None:
    """Set the default clock to use for all module-level functions.

    By default, an instance of :py:class:`~pyglet.clock.Clock` is used.
    """
    global _default
    _default = default


def get_default() -> Clock:
    """Get the pyglet default Clock.

    Return the :py:class:`~pyglet.clock.Clock` instance that is used by all
    module-level clock functions.
    """
    return _default


def tick(poll: bool = False) -> float:
    """:see: :py:meth:`~pyglet.clock.Clock.tick`."""
    return _default.tick(poll)


def get_sleep_time(sleep_idle: bool) -> float | None:
    """:see: :py:meth:`~pyglet.clock.Clock.get_sleep_time`."""
    return _default.get_sleep_time(sleep_idle)


def get_frequency() -> float:
    """:see: :py:meth:`~pyglet.clock.Clock.get_frequency`."""
    return _default.get_frequency()


def schedule(func: Callable, *args: Any, **kwargs: Any) -> None:
    """:see: :py:meth:`~pyglet.clock.Clock.schedule`."""
    _default.schedule(func, *args, **kwargs)


def schedule_interval(func: Callable, interval: float, *args: Any, **kwargs: Any) -> None:
    """:see: :py:meth:`~pyglet.clock.Clock.schedule_interval`."""
    _default.schedule_interval(func, interval, *args, **kwargs)


def schedule_interval_fixed_delay(func: Callable, interval: float, *args: Any, **kwargs: Any) -> None:
    """:see: :py:meth:`~pyglet.clock.Clock.schedule_interval_fixed_delay`."""
    _default.schedule_interval_fixed_delay(func, interval, *args, **kwargs)


def schedule_interval_for_duration(func: Callable, interval: float, duration: float, *args, **kwargs) -> None:
    """:see: :py:meth:`~pyglet.clock.Clock.schedule_interval_for_duration`."""
    _default.schedule_interval_for_duration(func, interval, duration, *args, **kwargs)


def schedule_interval_soft(func: Callable, interval: float, *args, **kwargs) -> None:
    """:see: :py:meth:`~pyglet.clock.Clock.schedule_interval_soft`."""
    _default.schedule_interval_soft(func, interval, *args, **kwargs)


def schedule_once(func: Callable, delay: float, *args, **kwargs) -> None:
    """:see: :py:meth:`~pyglet.clock.Clock.schedule_once`."""
    _default.schedule_once(func, delay, *args, **kwargs)


def unschedule(func: Callable) -> None:
    """:see: :py:meth:`~pyglet.clock.Clock.unschedule`."""
    _default.unschedule(func)
