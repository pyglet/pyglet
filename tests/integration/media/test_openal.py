import pytest
from tests import mock
import time

try:
    from pyglet.media.drivers import openal
except ImportError:
    openal = None


pytestmark = pytest.mark.skipif(openal is None, reason='No OpenAL available.')


def test_worker_add_remove_players():
    worker = openal.OpenALWorker()
    player1 = mock.MagicMock()
    player2 = mock.MagicMock()

    worker.start()
    try:
        worker.add(player1)
        worker.add(player2)
        worker.remove(player1)
        worker.remove(player2)
        worker.remove(player2)
    finally:
        worker.stop()


def test_worker_refill_player():
    worker = openal.OpenALWorker()
    worker.start()

    try:
        player = mock.MagicMock()
        player.get_write_size.return_value = 1024
        worker.add(player)

        for _ in range(10):
            if player.get_write_size.called:
                break
            time.sleep(.1)

        worker.remove(player)
        player.refill.assert_called_with(1024)

    finally:
        worker.stop()


def test_worker_do_not_refill_player():
    worker = openal.OpenALWorker()
    worker.start()

    try:
        player = mock.MagicMock()
        player.get_write_size.return_value = 104
        worker.add(player)

        for _ in range(10):
            if player.get_write_size.called:
                break
            time.sleep(.1)

        worker.remove(player)
        assert not player.refill.called

    finally:
        worker.stop()


def test_worker_refill_multiple_players_refill_largest():
    worker = openal.OpenALWorker()
    worker.start()

    try:
        player1 = mock.MagicMock()
        player1.get_write_size.return_value = 1024
        worker.add(player1)

        player2 = mock.MagicMock()
        player2.get_write_size.return_value = 768
        worker.add(player2)

        for _ in range(10):
            if player1.get_write_size.called:
                break
            time.sleep(.1)

        player1.refill.assert_called_with(1024)
        assert not player2.called

    finally:
        worker.stop()


