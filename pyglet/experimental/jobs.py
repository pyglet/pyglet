"""Experimental multithreaded Job system.

This module provides the `JobExecutor` class, which allows submitting
batches of highly parallizable work in the form of functions and arguments.
This is commonly known as "task-based multithreading" or a "multithreaded
job system".

..note:: This module is only really useful with the recent Python 3.13
         releases that are built with experimental free-threading support.
         With typical Python releases that contain a GIL, this is not of
         much practical use.
"""

from __future__ import annotations

import os

from queue import Queue
from threading import Event, Thread
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Callable, Any


class _Worker(Thread):
    """A worker thread to pop and run jobs."""
    def __init__(self, workqueue: Queue, exitevent: Event, index: int) -> None:
        super().__init__(daemon=True)
        self._queue = workqueue
        self._exit = exitevent
        self._index = index
        self.start()

    def run(self) -> None:
        """Parallel thread of execution."""
        _exit = self._exit
        _queue = self._queue
        while not _exit.is_set():
            func, args = _queue.get()
            func(*args)
            _queue.task_done()

    def __repr__(self) -> str:
        return f"{self.name}(id={self.native_id})"


class JobExecutor:
    """A light-weight multithreaded job system.

    A JobExecutor loosely mimics the design of the Executor classes from the
    `concurrent.futures` module, but does not share any code with those classes.
    Instead, it is a more light-weight implementation intended for execution of
    highly parallizable functions (jobs). A key difference is that JobExecutor
    does not return `Futures`. Submitted jobs must be self-contained, or handle
    returning values by other mechanisms. The :py:meth:`~sync` method can be
    used to wait for all currently submitted jobs to complete.
    """

    def __init__(self, max_workers: int | None = None) -> None:
        """Create an instance of a JobExecutor.

        Args:
            max_workers: The number of threads to use. If `None`, will
                         create half as many threads as reported CPU cores.
        """
        self._max_workers = max_workers or os.cpu_count() // 2
        self._exitevent = Event()
        self._queue = Queue()
        self._threads = [_Worker(self._queue, self._exitevent, i) for i in range(self._max_workers)]

    def submit(self, func: Callable, *args: Any) -> None:
        """Submit a job to be executed on .

        A "job" consists of a function to be called, alone with any arguments
        that should be passed to it. Jobs are automatically executed by the next
        free worker thread. No values are returned when jobs are submitted,
        and the functions should also not return any values; return values are
        lost.

        Args:
            func: A function to execute.
            *args: Any arguments to pass to the function.
        """
        try:
            self._queue.put((func, args))
        except AttributeError:
            raise RuntimeError("cannot submit new tasks after shutdown")

    def shutdown(self) -> None:
        """Shut down the JobExecutor, terminating all worker threads.

        All JobExecutor workers are Daemon Threads, so it is not strictly
        necessary to call shutdown() at program termination. However, if
        it is no longer needed, shutdown() can be called ot free up the
        thread resources.
        """
        if not self._queue:
            return
        self._exitevent.set()
        for _ in range(self._max_workers):
            self.submit(lambda: None)
        self._threads.clear()
        self._exitevent = None
        self._queue = None

    def sync(self) -> None:
        """Wait for all currently submitted jobs to complete.

        This method will wait until the internal queue is empty, AND all
        currently submitted jobs have completed execution. It can be used
        to fence between separate batches of jobs that should not be run
        at the same time. For example::

            for chunk in worklist:
                executor.submit(some_function, chunk)

            executor.sync()

            window.draw()

        """
        self._queue.join()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(workers={self._threads})"
