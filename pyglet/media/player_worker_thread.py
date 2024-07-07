from __future__ import annotations

import time
import threading

from typing import TYPE_CHECKING, Set

import pyglet

from pyglet.util import debug_print

if TYPE_CHECKING:
    from pyglet.media.drivers.base import AbstractAudioPlayer


_debug = debug_print('debug_media')


class PlayerWorkerThread(threading.Thread):
    """Worker thread for refilling audio players.

    This thread manages calling the ``work`` method on low level AudioPlayer
    instances (not the high level Player instances). This allows the players
    to keep their buffers filled (and perform event dispatching tasks), but
    does not block the main thread.

    This thread will sleep for a small period betwen updates, but provides a
    :py:meth:`~notify` method to allow waking it immediately. A :py:meth:`~stop`
    method is provided to terminate the thread, but under normal operation it
    will exit cleanly on interpreter shutdown.
    """

    # Run every 20ms; accurate enough for event dispatching while not hogging too much
    # time updating the players
    _nap_time = 0.020

    def __init__(self) -> None:
        super().__init__(daemon=True)

        self._rest_event = threading.Event()
        # A lock that should be held as long as consistency of `self.players` is required.
        self._operation_lock = threading.Lock()
        self._stopped = False
        self.players: Set[AbstractAudioPlayer] = set()

    def run(self) -> None:
        if pyglet.options['debug_trace']:
            pyglet._install_trace()

        sleep_time = None

        while True:
            assert _debug(f"PlayerWorkerThread.run: Going to sleep "
                          f"{'indefinitely; no active players' if sleep_time is None else f'for {sleep_time}'}")
            self._rest_event.wait(sleep_time)
            self._rest_event.clear()

            assert _debug(f'PlayerWorkerThread.run: woke up @{time.time()}')
            if self._stopped:
                break

            with self._operation_lock:
                if self.players:
                    sleep_time = self._nap_time
                    for player in self.players:
                        player.work()
                else:
                    # sleep until a player is added
                    sleep_time = None

        assert _debug(f'PlayerWorkerThread.run: exiting')

    def stop(self) -> None:
        """Stop the thread and wait for it to terminate.

        The ``stop`` instance variable is set to ``True`` and the rest event
        is set.  It is the responsibility of the ``run`` method to check
        the value of ``_stopped`` after each sleep or wait and to return if
        set.
        """
        assert _debug('PlayerWorkerThread.stop()')
        self._stopped = True
        self._rest_event.set()
        try:
            self.join()
        except RuntimeError:
            # Ignore on unclean shutdown
            pass

    def notify(self) -> None:
        """Interrupt the current sleep operation.

        If the thread is currently sleeping, it will be woken immediately
        instead of waiting the full duration of the timeout.
        If the thread is not sleeping, it will run again as soon as it is
        done with its operation.
        """
        assert _debug('PlayerWorkerThread.notify()')
        self._rest_event.set()

    def add(self, player: AbstractAudioPlayer) -> None:
        """Add a player to the PlayerWorkerThread, and call :py:meth:`~notify`.

        When a player is added, it's ``work`` method will be called regularly.

        .. note:: Do not call this method from within the thread, as it will deadlock.
        """
        assert player is not None
        assert _debug('PlayerWorkerThread: player added')

        with self._operation_lock:
            self.players.add(player)

        self.notify()

    def remove(self, player: AbstractAudioPlayer) -> None:
        """Remove a player from the PlayerWorkerThread.

        This call has no effect if the player does not exist.

        .. note:: Do not call this method from within the thread, as it will deadlock.
        """
        assert _debug('PlayerWorkerThread: player removed')

        if player in self.players:
            with self._operation_lock:
                self.players.remove(player)
