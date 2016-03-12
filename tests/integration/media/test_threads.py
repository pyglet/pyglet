from tests import mock
import time

from pyglet.media.threads import PlayerWorker


def test_worker_add_remove_players():
    worker = PlayerWorker()
    player1 = mock.MagicMock()
    player1.get_write_size.return_value = 0
    type(player1).min_buffer_size = mock.PropertyMock(return_value=512)
    player2 = mock.MagicMock()
    player2.get_write_size.return_value = 0
    type(player2).min_buffer_size = mock.PropertyMock(return_value=512)

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
    worker = PlayerWorker()
    worker.start()

    try:
        player = mock.MagicMock()
        player.get_write_size.return_value = 1024
        type(player).min_buffer_size = mock.PropertyMock(return_value=512)
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
    worker = PlayerWorker()
    worker.start()

    try:
        player = mock.MagicMock()
        player.get_write_size.return_value = 104
        type(player).min_buffer_size = mock.PropertyMock(return_value=512)
        worker.add(player)

        for _ in range(10):
            if player.get_write_size.called:
                break
            time.sleep(.1)

        worker.remove(player)
        assert not player.refill.called

    finally:
        worker.stop()


def test_worker_refill_multiple_players_refill_multiple():
    worker = PlayerWorker()
    worker.start()

    try:
        player1 = mock.MagicMock()
        player1.get_write_size.return_value = 1024
        type(player1).min_buffer_size = mock.PropertyMock(return_value=512)
        worker.add(player1)

        player2 = mock.MagicMock()
        player2.get_write_size.return_value = 768
        type(player2).min_buffer_size = mock.PropertyMock(return_value=512)
        worker.add(player2)

        for _ in range(10):
            if player1.get_write_size.called and player2.get_write_size.called:
                break
            time.sleep(.1)

        player1.refill.assert_called_with(1024)
        player2.refill.assert_called_with(768)

    finally:
        worker.stop()

