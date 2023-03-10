import time
import atexit
import threading

import pyglet

from pyglet.util import debug_print


_debug = debug_print('debug_media')


class MediaThread:
    """A thread that cleanly exits on interpreter shutdown, and provides
    a sleep method that can be interrupted and a termination method.

    :Ivariables:
        `_condition` : threading.Condition
            Lock _condition on all instance variables.
        `_stopped` : bool
            True if `stop` has been called.

    """
    _threads = set()
    _threads_lock = threading.Lock()

    def __init__(self):
        self._thread = threading.Thread(target=self._thread_run, daemon=True)
        self._condition = threading.Condition()
        self._stopped = False

    def run(self):
        raise NotImplementedError

    def _thread_run(self):
        if pyglet.options['debug_trace']:
            pyglet._install_trace()

        with self._threads_lock:
            self._threads.add(self)
        self.run()
        with self._threads_lock:
            self._threads.remove(self)

    def start(self):
        self._thread.start()

    def stop(self):
        """Stop the thread and wait for it to terminate.

        The `stop` instance variable is set to ``True`` and the condition is
        notified.  It is the responsibility of the `run` method to check
        the value of `stop` after each sleep or wait and to return if set.
        """
        assert _debug('MediaThread.stop()')
        with self._condition:
            self._stopped = True
            self._condition.notify()
        self._thread.join()

    def sleep(self, timeout):
        """Wait for some amount of time, or until notified.

        :Parameters:
            `timeout` : float
                Time to wait, in seconds.

        """
        assert _debug(f'MediaThread.sleep({timeout!r})')
        with self._condition:
            if not self._stopped:
                self._condition.wait(timeout)

    def notify(self):
        """Interrupt the current sleep operation.

        If the thread is currently sleeping, it will be woken immediately,
        instead of waiting the full duration of the timeout.
        """
        assert _debug('MediaThread.notify()')
        with self._condition:
            self._condition.notify()

    @classmethod
    def atexit(cls):
        with cls._threads_lock:
            threads = list(cls._threads)
        for thread in threads:
            thread.stop()


atexit.register(MediaThread.atexit)


class PlayerWorkerThread(MediaThread):
    """Worker thread for refilling players."""

    # Time to wait if there are players, but they're all full:
    _nap_time = 0.05

    def __init__(self):
        super().__init__()
        self.players = set()

    def run(self):
        while True:
            # This is a big lock, but ensures a player is not deleted while
            # we're processing it -- this saves on extra checks in the
            # player's methods that would otherwise have to check that it's
            # still alive.
            with self._condition:
                assert _debug('PlayerWorkerThread: woke up @{}'.format(time.time()))
                if self._stopped:
                    break
                sleep_time = -1

                if self.players:
                    filled = False
                    for player in list(self.players):
                        filled = player.refill_buffer()
                    if not filled:
                        sleep_time = self._nap_time
                else:
                    assert _debug('PlayerWorkerThread: No active players')
                    sleep_time = None   # sleep until a player is added

                if sleep_time != -1:
                    self.sleep(sleep_time)
                else:
                    # We MUST sleep, or we will starve pyglet's main loop.  It
                    # also looks like if we don't sleep enough, we'll starve out
                    # various updates that stop us from properly removing players
                    # that should be removed.
                    self.sleep(self._nap_time)

    def add(self, player):
        assert player is not None
        assert _debug('PlayerWorkerThread: player added')
        with self._condition:
            self.players.add(player)
            self._condition.notify()

    def remove(self, player):
        assert _debug('PlayerWorkerThread: player removed')
        with self._condition:
            if player in self.players:
                self.players.remove(player)
            self._condition.notify()
