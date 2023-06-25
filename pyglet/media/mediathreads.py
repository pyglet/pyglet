import time
import atexit
import threading

import pyglet

from pyglet.util import debug_print


_debug = debug_print('debug_media')


class PlayerWorkerThread(threading.Thread):
    """Worker thread for refilling players. Exits on interpreter shutdown,
    provides a notify method to interrupt it as well as a termination method.
    """

    _threads = set()

    # Time to wait if there are players, but they're all full:
    _nap_time = 0.05

    def __init__(self):
        super().__init__(daemon=True)

        self._rest_event = threading.Event()
        # A lock that should be held as long as consistency of `self.players` is required.
        self._operation_lock = threading.Lock()
        self._stopped = False
        self.players = set()

    def run(self):
        if pyglet.options['debug_trace']:
            pyglet._install_trace()

        self._threads.add(self)

        sleep_time = None

        while True:
            assert _debug(
                'PlayerWorkerThread: Going to sleep ' +
                ('indefinitely; no active players' if sleep_time is None else f'for {sleep_time}')
            )
            self._rest_event.wait(sleep_time)
            self._rest_event.clear()

            assert _debug(f'PlayerWorkerThread: woke up @{time.time()}')
            if self._stopped:
                break

            with self._operation_lock:
                if self.players:
                    sleep_time = self._nap_time
                    for player in self.players:
                        player.refill_buffer()
                else:
                    # sleep until a player is added
                    sleep_time = None

        self._threads.remove(self)

    def stop(self):
        """Stop the thread and wait for it to terminate.

        The `stop` instance variable is set to ``True`` and the rest event
        is set.  It is the responsibility of the `run` method to check
        the value of `_stopped` after each sleep or wait and to return if
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

    def notify(self):
        """Interrupt the current sleep operation.

        If the thread is currently sleeping, it will be woken immediately,
        instead of waiting the full duration of the timeout.
        If the thread is not sleeping, it will run again as soon as it is
        done with its operation.
        """
        assert _debug('PlayerWorkerThread.notify()')
        self._rest_event.set()

    def add(self, player):
        """
        Add a player to the PlayerWorkerThread; which will call
        `refill_buffer` on it regularly. Notify the thread as well.

        Do not call this method from within the thread, as it will deadlock.
        """
        assert player is not None
        assert _debug('PlayerWorkerThread: player added')

        with self._operation_lock:
            self.players.add(player)

        self.notify()

    def remove(self, player):
        """
        Remove a player from the PlayerWorkerThread, or ignore if it does
        not exist.

        Do not call this method from within the thread, as it may deadlock.
        """
        assert _debug('PlayerWorkerThread: player removed')

        if player in self.players:
            with self._operation_lock:
                self.players.remove(player)

            # self.notify()

    @classmethod
    def atexit(cls):
        for thread in list(cls._threads):
            thread.stop()
        # Can't be 100% sure that all threads are stopped here as it is technically possible that
        # a thread may just have removed itself from cls._threads as the last action in `run()`
        # and then was unscheduled; But it will definitely finish very soon after anyways

atexit.register(PlayerWorkerThread.atexit)
