"""
Test internals of the DirectSound media driver.
"""

import ctypes
import math
import pytest
import random
import time

from pyglet.media.sources import AudioFormat

try:
    from pyglet.media.drivers import directsound
    from pyglet.media.drivers.directsound.interface import DirectSoundDriver, DirectSoundBuffer
    from pyglet.media.drivers.directsound.adaptation import _gain2db, _db2gain
except ImportError:
    directsound = None

import pytest
pytestmark = pytest.mark.skipif(directsound is None, reason='No DirectSound available.')

def almost_equal(a, b, e=0.0001):
    assert abs(a-b) <= e
    return True


def iter_almost_equal(a, b, e=0.0001):
    for x, y in zip(a, b):
        assert abs(x-y) <= e
    return True

def random_normalized_vector():
    vector = [random.uniform(-1.0, 1.0) for _ in range(3)]

    length = math.sqrt(sum(x**2 for x in vector))
    return [x/length for x in vector]

def test_gain2db_gain_convert():
    assert _gain2db(0.0) == -10000
    assert almost_equal(_db2gain(-10000), 0.0)

    assert _gain2db(1.0) == 0
    assert almost_equal(_db2gain(0), 1.0)

    assert _gain2db(-0.1) == -10000
    assert _gain2db(1.1) == 0

    x = 0.0
    while (x <= 1.0):
        assert almost_equal(_db2gain(_gain2db(x)), x, 0.01)
        x += 0.01

    y = -10000
    while (y <= 0):
        assert almost_equal(_gain2db(_db2gain(y)), y, 1)
        y += 10


@pytest.fixture
def driver():
    return DirectSoundDriver()


@pytest.fixture(params=[(1, 8, 22050),
                        (2, 8, 22050),
                        (1, 16, 22050),
                        (2, 16, 22050),
                        (1, 16, 44100),
                        (2, 16, 44100)])
def audio_format(request):
    return AudioFormat(*request.param)


@pytest.fixture(params=[(1, 8, 22050),
                        (1, 16, 22050),
                        (1, 16, 44100)])
def audio_format_3d(request):
    return AudioFormat(*request.param)


@pytest.fixture
def buffer_(driver, audio_format):
    return driver.create_buffer(audio_format)


@pytest.fixture
def buffer_3d(driver, audio_format_3d):
    buf = driver.create_buffer(audio_format_3d)
    assert buf.is3d
    return buf


@pytest.fixture
def filled_buffer(audio_format, buffer_):
    pointer = buffer_.lock(0, 1024)
    if audio_format.sample_size == 8:
        c = 0x80
    else:
        c = 0x00
    ctypes.memset(pointer.audio_ptr_1, c, pointer.audio_length_1.value)
    if pointer.audio_length_2.value > 0:
        ctypes.memset(pointer.audio_ptr_2, c, pointer.audio_length_2.value)

    return buffer_


@pytest.fixture
def listener(driver):
    return driver.create_listener()


def test_driver_create():
    driver = DirectSoundDriver()
    del driver


def test_create_buffer(driver, audio_format):
    buf = driver.create_buffer(audio_format)
    del buf


def test_buffer_volume(buffer_):
    vol = 0.0
    while vol <= 1.0:
        listener.volume = _gain2db(vol)
        assert almost_equal(listener.volume, _gain2db(vol), 0.05)
        vol += 0.05


def test_buffer_current_position_empty_buffer(buffer_):
    buffer_.current_position = 0
    assert buffer_.current_position == (0, 0)


def test_buffer_current_position_filled_buffer(filled_buffer):
    filled_buffer.current_position = 512
    assert filled_buffer.current_position == (512, 512)


def test_buffer_is3d(audio_format, buffer_):
    assert buffer_.is3d == (audio_format.channels == 1)


def test_buffer_position(buffer_):
    for _ in range(10):
        position = [random.uniform(-10.0, 10.0) for _ in range(3)]
        buffer_.position = position
        if buffer_.is3d:
            assert iter_almost_equal(buffer_.position, position)
        else:
            assert buffer_.position == (0, 0, 0)


def test_buffer_min_distance(buffer_):
    for _ in range(10):
        distance = random.uniform(0.0, 100.0)
        buffer_.min_distance = distance
        if buffer_.is3d:
            assert almost_equal(buffer_.min_distance, distance)
        else:
            assert buffer_.min_distance == 0


def test_buffer_max_distance(buffer_):
    for _ in range(10):
        distance = random.uniform(0.0, 100.0)
        buffer_.max_distance = distance
        if buffer_.is3d:
            assert almost_equal(buffer_.max_distance, distance)
        else:
            assert buffer_.max_distance == 0


def test_buffer_cone_orienation(buffer_):
    for _ in range(10):
        orientation = random_normalized_vector()
        buffer_.cone_orientation = orientation
        if buffer_.is3d:
            assert iter_almost_equal(buffer_.cone_orientation, orientation)
        else:
            assert buffer_.cone_orientation == (0, 0, 0)


def test_buffer_cone_angles(buffer_):
    for _ in range(10):
        angle1 = random.randint(0, 360)
        angle2 = random.randint(0, 360)
        inside = min(angle1, angle2)
        outside = max(angle1, angle2)
        buffer_.set_cone_angles(inside, outside)
        result = buffer_.cone_angles
        if buffer_.is3d:
            assert result.inside == inside
            assert result.outside == outside
        else:
            assert result.inside == 0
            assert result.outside == 0


def test_buffer_cone_outside_volume(buffer_):
    for _ in range(10):
        volume = _gain2db(random.uniform(0.0, 1.0))
        buffer_.cone_outside_volume = volume
        if buffer_.is3d:
            assert almost_equal(buffer_.cone_outside_volume, volume)
        else:
            assert buffer_.cone_outside_volume == 0


def test_buffer_frequency(buffer_):
    for _ in range(10):
        freq = random.randint(100, 100000)
        buffer_.frequency = freq
        assert buffer_.frequency == freq


def test_buffer_lock_unlock(buffer_):
    size = 1024
    pointer = buffer_.lock(0, size)
    assert pointer.audio_length_1.value + pointer.audio_length_2.value == size
    buffer_.unlock(pointer)


def test_buffer_play_stop(filled_buffer):
    assert filled_buffer.current_position[0] == 0
    filled_buffer.play()
    for _ in range(100):
        assert filled_buffer.is_playing
        if filled_buffer.current_position[0] > 0:
            break
        else:
            time.sleep(0.001)
    else:
        pytest.fail("Did not advance position in buffer while playing.")

    filled_buffer.stop()
    assert not filled_buffer.is_playing
    pos = filled_buffer.current_position
    for _ in range(10):
        assert filled_buffer.current_position == pos
        time.sleep(0.001)


def test_create_listener(driver):
    listener = driver.create_listener()
    del listener


def test_listener_position(listener):
    for _ in range(10):
        position = [random.uniform(-10.0, 10.0) for _ in range(3)]
        listener.position = position
        assert iter_almost_equal(listener.position, position)


def test_listener_orientation(listener):
    for _ in range(10):
        front = random_normalized_vector()
        top = random_normalized_vector()
        orientation = front + top

        listener.orientation = orientation
        # Only testing first 3, as random values might be adjusted by DS to be correct angles
        assert iter_almost_equal(listener.orientation[:3], orientation[:3])

