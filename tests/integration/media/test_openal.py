from builtins import str, isinstance
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


@pytest.fixture
def device():
    return openal.interface.OpenALDevice()


def test_device_create_delete(device):
    assert device.is_ready
    device.delete()
    assert not device.is_ready


def test_device_version(device):
    major, minor = device.get_version()
    assert major > 0
    assert minor > 0


def test_device_extensions(device):
    extensions = device.get_extensions()
    assert len(extensions) > 0
    for ext in extensions:
        assert isinstance(ext, str)


def test_context_create_delete(device):
    context = device.create_context()
    assert context is not None
    context.delete()


@pytest.fixture
def context(device):
    return device.create_context()


def test_context_make_current(context):
    context.make_current()


def test_source_create_delete(context):
    source = context.create_source()
    assert not source.is_playing
    assert source.buffers_processed == 0
    assert source.byte_offset == 0
    source.delete()


def test_buffer_create_delete(context):
    buf = openal.interface.OpenALBuffer.create()
    assert buf.is_valid
    assert buf.al_buffer is not None
    buf.delete()
    assert not buf.is_valid


@pytest.fixture
def buffer_pool():
    return openal.interface.OpenALBufferPool()

def test_bufferpool_get_single_buffer(buffer_pool):
    assert len(buffer_pool) == 0

    buf = buffer_pool.get_buffer()
    assert buf is not None
    assert buf.is_valid
    assert len(buffer_pool) == 0


def test_bufferpool_return_valid_buffer(buffer_pool):
    buf = buffer_pool.get_buffer()
    assert buf is not None
    assert buf.is_valid
    assert len(buffer_pool) == 0

    buffer_pool.unqueue_buffer(buf)
    assert len(buffer_pool) == 1

    buf = buffer_pool.get_buffer()
    assert buf is not None
    assert buf.is_valid
    assert len(buffer_pool) == 0


def test_bufferpool_get_multiple_buffers(buffer_pool):
    bufs = buffer_pool.get_buffers(3)
    assert bufs is not None
    assert len(bufs) == 3
    for buf in bufs:
        assert buf.is_valid
    assert len(buffer_pool) == 0


def test_bufferpool_return_multiple_valid_buffers(buffer_pool):
    bufs = buffer_pool.get_buffers(3)
    assert bufs is not None
    assert len(bufs) == 3
    for buf in bufs:
        assert buf.is_valid
    assert len(buffer_pool) == 0

    return_count = 0
    for buf in bufs:
        buffer_pool.unqueue_buffer(buf)
        return_count += 1
        assert len(buffer_pool) == return_count

    buf = buffer_pool.get_buffer()
    assert buf is not None
    assert buf.is_valid
    assert len(buffer_pool) == 2


def test_bufferpool_return_invalid_buffer(buffer_pool):
    buf = buffer_pool.get_buffer()
    assert buf is not None
    assert buf.is_valid
    assert len(buffer_pool) == 0

    buf.delete()
    assert not buf.is_valid
    buffer_pool.unqueue_buffer(buf)
    assert len(buffer_pool) == 0

    buf = buffer_pool.get_buffer()
    assert buf is not None
    assert buf.is_valid
    assert len(buffer_pool) == 0


def test_bufferpool_invalidate_buffer_in_pool(buffer_pool):
    buf = buffer_pool.get_buffer()
    assert buf is not None
    assert buf.is_valid
    assert len(buffer_pool) == 0

    buffer_pool.unqueue_buffer(buf)
    assert len(buffer_pool) == 1

    buf.delete()
    assert not buf.is_valid

    buf = buffer_pool.get_buffer()
    assert buf is not None
    assert buf.is_valid
    assert len(buffer_pool) == 0

