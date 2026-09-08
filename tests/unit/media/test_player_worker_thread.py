from __future__ import annotations

import sys
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from pyglet.media.player_worker_thread import PlayerWorkerThread


pytestmark = pytest.mark.skipif(
    sys.platform == "emscripten",
    reason="PlayerWorkerThread requires native Python threads.",
)


class _ContendedSet(set):
    """Make the old check-then-remove implementation race deterministically."""

    def __init__(self, values) -> None:
        super().__init__(values)
        self.barrier = threading.Barrier(2)

    def __contains__(self, value) -> bool:
        self.barrier.wait(timeout=1)
        return super().__contains__(value)


def test_concurrent_remove_is_idempotent() -> None:
    worker = PlayerWorkerThread()
    player = object()
    worker.players = _ContendedSet((player,))
    start = threading.Barrier(2)

    def remove_player() -> None:
        start.wait(timeout=1)
        worker.remove(player)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(remove_player) for _ in range(2)]
        for future in futures:
            future.result(timeout=1)

    assert not worker.players


def test_remove_waits_for_in_flight_work() -> None:
    """Backends may only free native resources after remove() returns."""
    worker = PlayerWorkerThread()
    work_started = threading.Event()
    allow_work_to_finish = threading.Event()
    work_finished = threading.Event()

    class BlockingPlayer:
        def work(self) -> None:
            work_started.set()
            assert allow_work_to_finish.wait(1)
            work_finished.set()

    player = BlockingPlayer()
    worker.start()
    worker.add(player)
    assert work_started.wait(1)

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            remove_future = executor.submit(worker.remove, player)
            assert not remove_future.done()

            allow_work_to_finish.set()
            remove_future.result(timeout=1)

        assert work_finished.is_set()
        assert player not in worker.players
    finally:
        allow_work_to_finish.set()
        worker.stop()


def test_notify_wakes_active_worker_without_waiting_for_poll_interval() -> None:
    """Callback notifications must not wait for the normal refill poll."""
    worker = PlayerWorkerThread()
    worker._nap_time = 1.0
    calls = threading.Event()
    call_count = 0
    call_count_lock = threading.Lock()

    class ProbePlayer:
        def work(self) -> None:
            nonlocal call_count
            with call_count_lock:
                call_count += 1
            calls.set()

    player = ProbePlayer()
    worker.start()
    worker.add(player)
    assert calls.wait(1)

    try:
        calls.clear()
        worker.notify()
        assert calls.wait(0.2)
        with call_count_lock:
            assert call_count >= 2
    finally:
        worker.remove(player)
        worker.stop()


def test_concurrent_add_remove_stress() -> None:
    """Registration remains safe while multiple application threads churn players."""
    worker = PlayerWorkerThread()

    class ProbePlayer:
        def work(self) -> None:
            pass

    players = [ProbePlayer() for _ in range(8)]
    start = threading.Barrier(8)

    def churn(player_offset: int) -> None:
        start.wait(timeout=1)
        for index in range(200):
            player = players[(player_offset + index) % len(players)]
            worker.add(player)
            worker.notify()
            worker.remove(player)

    worker.start()
    try:
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(churn, offset) for offset in range(8)]
            for future in futures:
                future.result(timeout=5)

        assert not worker.players
    finally:
        for player in players:
            worker.remove(player)
        worker.stop()
