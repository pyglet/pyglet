import ctypes
import numbers
import struct
import pytest
from threading import Timer

import pyglet
pyglet.options.debug_media = False

from pyglet.media.codecs import AudioFormat
from pyglet.media.synthesis import Silence

try:
    from pyglet.media.drivers.pipewire import interface
    from pyglet.media.drivers.pipewire import lib_pipewire as lib
except ImportError:
    interface = None
    lib = None


pytestmark = pytest.mark.skipif(interface is None, reason='requires PipeWire')


@pytest.fixture(scope="module", autouse=True)
def validate_pipewire_audio_driver():
    """Skip this module if PipeWire is importable but not actually usable."""
    mainloop = interface.PipeWireMainloop()
    context = None

    try:
        mainloop.start()
        context = mainloop.create_context()
        context.connect()
    except interface.PipeWireException as exc:
        pytest.skip(f"PipeWire driver is unavailable on this runner: {exc}")
    finally:
        if context is not None:
            with mainloop.lock:
                context.delete()
        mainloop.delete()


@pytest.fixture
def mainloop():
    return interface.PipeWireMainloop()


def test_mainloop_run(mainloop):
    mainloop.start()
    mainloop.delete()


def test_mainloop_lock(mainloop):
    mainloop.start()
    with mainloop.lock:
        pass
    mainloop.delete()


def test_mainloop_signal(mainloop):
    mainloop.start()
    with mainloop.lock:
        mainloop.signal()
    mainloop.delete()


def test_mainloop_wait_signal(mainloop):
    mainloop.start()

    def signal():
        with mainloop.lock:
            mainloop.signal()
    t = Timer(.1, signal)
    t.start()

    with mainloop.lock:
        assert mainloop.timed_wait(1) == 0
    mainloop.delete()


@pytest.fixture
def context(mainloop):
    mainloop.start()
    with mainloop.lock:
        context = mainloop.create_context()
    yield context

    with mainloop.lock:
        context.delete()
    mainloop.delete()


def test_context_connect(context):
    assert context.is_connected == False

    with context.mainloop.lock:
        context.connect()

    assert context.is_connected == True

    with context.mainloop.lock:
        context.delete()

    assert context.is_connected == False


@pytest.fixture
def connected_context(context):
    with context.mainloop.lock:
        context.connect()
    return context


@pytest.fixture
def stream(connected_context):
    audio_format = AudioFormat(1, 16, 44100)
    with connected_context.mainloop.lock:
        stream = connected_context.create_stream(audio_format)
    return stream


def test_stream_create(stream):
    assert stream.state == lib.PW_STREAM_STATE_UNCONNECTED
    assert stream.is_ready == False

    with stream.context.mainloop.lock:
        stream.delete()

    assert stream.state == lib.PW_STREAM_STATE_UNCONNECTED


def test_stream_connect(stream):
    # connect_playback() manages the main-loop lock itself and blocks during
    # negotiation, so it must not be called while holding the lock.
    stream.connect_playback()

    assert stream.is_ready == True
    assert stream.is_paused == True
    assert stream.is_streaming == False
    assert isinstance(stream.get_node_id(), numbers.Integral)

    with stream.context.mainloop.lock:
        stream.delete()


def test_stream_set_active(stream):
    stream.connect_playback()

    assert stream.is_paused

    with stream.context.mainloop.lock:
        stream.set_active(True)
    _wait_for(lambda: stream.is_streaming, stream.context.mainloop)

    with stream.context.mainloop.lock:
        stream.set_active(False)
    _wait_for(lambda: stream.is_paused, stream.context.mainloop)

    with stream.context.mainloop.lock:
        stream.delete()


def test_stream_process_callback(stream):
    stream.connect_playback()

    process_calls = []
    stream.push_handlers(on_process=lambda: process_calls.append(True))

    with stream.context.mainloop.lock:
        stream.set_active(True)
    _wait_for(lambda: process_calls, stream.context.mainloop)

    assert process_calls

    with stream.context.mainloop.lock:
        stream.set_active(False)
    with stream.context.mainloop.lock:
        stream.delete()


@pytest.fixture
def audio_source():
    return Silence(10.0, 44100)


def test_stream_time_info(stream, audio_source):
    stream.connect_playback()

    def fill():
        buffer = stream.dequeue_buffer()
        if buffer is None:
            return
        if buffer.buffer.contents.n_datas > 0:
            data = buffer.buffer.contents.datas[0]
            audio_data = audio_source.get_audio_data(data.maxsize)
            if audio_data is not None:
                nbytes = min(data.maxsize, audio_data.length)
                ctypes.memmove(data.data, audio_data.pointer, nbytes)
                chunk = data.chunk.contents
                chunk.offset = 0
                chunk.stride = 2
                chunk.size = nbytes
                buffer.size = nbytes // 2
        stream.queue_buffer(buffer)

    stream.push_handlers(on_process=fill)

    time_info = None
    with stream.context.mainloop.lock:
        stream.set_active(True)
    _wait_for(lambda: stream.is_streaming, stream.context.mainloop)
    for _ in range(5):
        time_info = stream.get_time()
        if time_info is not None:
            break
        _wait_for(lambda: True, stream.context.mainloop)

    assert time_info is not None

    with stream.context.mainloop.lock:
        stream.set_active(False)
    with stream.context.mainloop.lock:
        stream.delete()


def _wait_for(predicate, mainloop, timeout: float = 10.0):
    """Poll ``predicate`` until it is true, tolerating timed_wait timeouts."""
    import time
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        with mainloop.lock:
            mainloop.timed_wait(1)
    assert predicate(), 'timed out waiting for condition'
    return True


# ---------------------------------------------------------------------------
# SPA POD byte-level regression tests (no daemon required).
# These guard format negotiation: property flags must be NONE, not
# MANDATORY, or the daemon refuses the format ("-95 start failed").
# ---------------------------------------------------------------------------

def _parse_enum_format_pod(pod_bytes: bytes):
    assert len(pod_bytes) >= 16
    pod_size, pod_type, obj_type, obj_id = struct.unpack_from('<IIII', pod_bytes, 0)
    assert pod_type == lib.SPA_TYPE_Object
    assert obj_type == lib.SPA_TYPE_OBJECT_Format
    assert obj_id == lib.SPA_PARAM_EnumFormat
    assert pod_size == len(pod_bytes) - 8

    props = {}
    offset = 16
    while offset < len(pod_bytes):
        key, flags = struct.unpack_from('<II', pod_bytes, offset)
        offset += 8
        value_size, value_type = struct.unpack_from('<II', pod_bytes, offset)
        offset += 8
        if value_type == lib.SPA_TYPE_Id:
            value = struct.unpack_from('<I', pod_bytes, offset)[0]
            offset += 4
        elif value_type == lib.SPA_TYPE_Int:
            value = struct.unpack_from('<i', pod_bytes, offset)[0]
            offset += 4
        elif value_type == lib.SPA_TYPE_Array:
            child_size, child_type = struct.unpack_from('<II', pod_bytes, offset)
            assert child_type == lib.SPA_TYPE_Id
            offset += 8
            n = (value_size - 8) // child_size
            value = list(struct.unpack_from(f'<{n}I', pod_bytes, offset))
            offset += 4 * n
        else:
            raise AssertionError(f'unexpected value type {value_type}')  # noqa: EM102
        offset = (offset + 7) & ~7
        props[key] = (flags, value)

    return props


def test_enum_format_pod_structure():
    pod_bytes = lib._make_enum_format_pod_bytes(lib.SPA_MEDIA_SUBTYPE_raw, lib.SPA_AUDIO_FORMAT_S16_LE, 44100, 2)
    props = _parse_enum_format_pod(pod_bytes)

    assert props[lib.SPA_FORMAT_mediaType][1] == lib.SPA_MEDIA_TYPE_audio
    assert props[lib.SPA_FORMAT_mediaSubtype][1] == lib.SPA_MEDIA_SUBTYPE_raw
    assert props[lib.SPA_FORMAT_AUDIO_format][1] == lib.SPA_AUDIO_FORMAT_S16_LE
    assert props[lib.SPA_FORMAT_AUDIO_rate][1] == 44100
    assert props[lib.SPA_FORMAT_AUDIO_channels][1] == 2
    assert props[lib.SPA_FORMAT_AUDIO_position][1] == [lib.SPA_AUDIO_CHANNEL_FL, lib.SPA_AUDIO_CHANNEL_FR]


def test_enum_format_pod_prop_flags():
    for channels in (1, 2, 6, 7):
        pod_bytes = lib._make_enum_format_pod_bytes(
            lib.SPA_MEDIA_SUBTYPE_raw, lib.SPA_AUDIO_FORMAT_S16_LE, 44100, channels)
        props = _parse_enum_format_pod(pod_bytes)
        for flags, _value in props.values():
            assert flags == lib.SPA_POD_PROP_FLAG_NONE
