from builtins import str, isinstance
import pytest
from tests import mock
import time

from pyglet.media.sources.procedural import Silence

try:
    from pyglet.media.drivers import openal
except ImportError:
    openal = None


pytestmark = pytest.mark.skipif(openal is None, reason='No OpenAL available.')


def almost_equal(f1, f2, eps=0.0001):
    return abs(f1 - f2) < eps


def almost_equal_coords(c1, c2, eps=0.0001):
    return all(almost_equal(f1, f2, eps) for f1, f2 in zip(c1, c2))



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


@pytest.fixture
def buf():
    return openal.interface.OpenALBuffer.create()


def test_buffer_create_delete(buf):
    assert buf.is_valid
    assert buf.al_buffer is not None
    assert buf.name > 0
    buf.delete()
    assert not buf.is_valid


def test_buffer_data(buf):
    assert buf.is_valid
    audio_source = Silence(1.)
    buf.data(audio_source.get_audio_data(audio_source.audio_format.bytes_per_second),
             audio_source.audio_format)
    assert buf.is_valid
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


def test_source_create_delete(context):
    source = context.create_source()
    assert source.is_initial
    assert not source.is_playing
    assert not source.is_paused
    assert not source.is_stopped
    assert source.buffers_processed == 0
    assert source.byte_offset == 0
    source.delete()


@pytest.fixture
def filled_buffer(buf):
    assert buf.is_valid
    audio_source = Silence(1.)
    buf.data(audio_source.get_audio_data(audio_source.audio_format.bytes_per_second),
             audio_source.audio_format)
    return buf


def test_source_queue_play_unqueue(context, filled_buffer):
    source = context.create_source()

    source.queue_buffer(filled_buffer)
    assert source.is_initial
    assert not source.is_playing
    assert not source.is_paused
    assert not source.is_stopped
    assert source.buffers_processed == 0
    assert source.buffers_queued == 1
    assert source.byte_offset == 0

    source.play()
    assert not source.is_initial
    assert source.is_playing
    assert not source.is_paused
    assert not source.is_stopped
    assert source.byte_offset == 0

    end_time = time.time() + 1.5
    while time.time() < end_time:
        if source.byte_offset > 0:
            break
        time.sleep(.1)
    assert source.byte_offset > 0

    end_time = time.time() + 1.5
    while time.time() < end_time:
        if source.buffers_processed > 0:
            break
        time.sleep(.1)
    assert source.buffers_processed == 1

    source.unqueue_buffers()
    assert source.buffers_processed == 0
    assert source.buffers_queued == 0

    assert not source.is_initial
    assert not source.is_playing
    assert not source.is_paused
    assert source.is_stopped


@pytest.fixture
def filled_source(context, filled_buffer):
    source = context.create_source()
    source.queue_buffer(filled_buffer)
    return source


def test_source_pause_stop(filled_source):
    assert filled_source.is_initial
    assert not filled_source.is_playing
    assert not filled_source.is_paused
    assert not filled_source.is_stopped

    filled_source.play()
    assert not filled_source.is_initial
    assert filled_source.is_playing
    assert not filled_source.is_paused
    assert not filled_source.is_stopped

    filled_source.pause()
    assert not filled_source.is_initial
    assert not filled_source.is_playing
    assert filled_source.is_paused
    assert not filled_source.is_stopped

    filled_source.play()
    assert not filled_source.is_initial
    assert filled_source.is_playing
    assert not filled_source.is_paused
    assert not filled_source.is_stopped

    filled_source.stop()
    assert not filled_source.is_initial
    assert not filled_source.is_playing
    assert not filled_source.is_paused
    assert filled_source.is_stopped


def test_source_prop_position(filled_source):
    assert almost_equal_coords(filled_source.position, (0., 0., 0.))
    filled_source.position = 1., 2., 3.
    assert almost_equal_coords(filled_source.position, (1., 2., 3.))


def test_source_prop_velocity(filled_source):
    assert almost_equal_coords(filled_source.velocity, (0., 0., 0.))
    filled_source.velocity = 1., 2., 3.
    assert almost_equal_coords(filled_source.velocity, (1., 2., 3.))


def test_source_prop_gain(filled_source):
    assert almost_equal(filled_source.gain, 1.)
    filled_source.gain = 8.5
    assert almost_equal(filled_source.gain, 8.5)


def test_source_prop_min_gain(filled_source):
    assert almost_equal(filled_source.min_gain, 0.)
    filled_source.min_gain = .5
    assert almost_equal(filled_source.min_gain, .5)


def test_source_prop_max_gain(filled_source):
    assert almost_equal(filled_source.max_gain, 1.)
    filled_source.max_gain = .8
    assert almost_equal(filled_source.max_gain, .8)


def test_source_prop_reference_distance(filled_source):
    assert almost_equal(filled_source.reference_distance, 1.)
    filled_source.reference_distance = 10.3
    assert almost_equal(filled_source.reference_distance, 10.3)


def test_source_prop_rolloff_factor(filled_source):
    assert almost_equal(filled_source.rolloff_factor, 1.)
    filled_source.rolloff_factor = 4.5
    assert almost_equal(filled_source.rolloff_factor, 4.5)


def test_source_prop_max_distance(filled_source):
    assert filled_source.max_distance > 500.0  # No definition of MAX_FLOAT available, 1000.0 on OSX
    filled_source.max_distance = 500.
    assert almost_equal(filled_source.max_distance, 500.)


def test_source_prop_pitch(filled_source):
    assert almost_equal(filled_source.pitch, 1.)
    filled_source.pitch = 3.14
    assert almost_equal(filled_source.pitch, 3.14)


def test_source_prop_direction(filled_source):
    assert almost_equal_coords(filled_source.direction, (0., 0., 0.))
    filled_source.direction = 1., 2., 3.
    assert almost_equal_coords(filled_source.direction, (1., 2., 3.))


def test_source_prop_cone_inner_angle(filled_source):
    assert almost_equal(filled_source.cone_inner_angle, 360.)
    filled_source.cone_inner_angle = 180.
    assert almost_equal(filled_source.cone_inner_angle, 180.)


def test_source_prop_cone_outer_angle(filled_source):
    assert almost_equal(filled_source.cone_outer_angle, 360.)
    filled_source.cone_outer_angle = 90.
    assert almost_equal(filled_source.cone_outer_angle, 90.)


def test_source_prop_cone_outer_gain(filled_source):
    assert almost_equal(filled_source.cone_outer_gain, 0.)
    filled_source.cone_outer_gain = .6
    assert almost_equal(filled_source.cone_outer_gain, .6)


def test_source_prop_sec_offset(filled_source):
    assert almost_equal(filled_source.sec_offset, 0.)
    filled_source.sec_offset = .1
    assert almost_equal(filled_source.sec_offset, .1)


def test_source_prop_sample_offset(filled_source):
    assert almost_equal(filled_source.sample_offset, 0.)
    filled_source.sample_offset = 5.
    assert almost_equal(filled_source.sample_offset, 5.)


def test_source_prop_byte_offset(filled_source):
    assert almost_equal(filled_source.byte_offset, 0.)
    filled_source.byte_offset = 8.
    assert almost_equal(filled_source.byte_offset, 8.)
