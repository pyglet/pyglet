from __future__ import unicode_literals

from builtins import str
import numbers
import pytest
from threading import Timer

import pyglet
pyglet.options['debug_media'] = False

from pyglet.media.codecs import AudioFormat
from pyglet.media.procedural import Silence

try:
    from pyglet.media.drivers.pulse import interface
except ImportError:
    interface = None


pytestmark = pytest.mark.skipif(interface is None, reason='requires PulseAudio')


@pytest.fixture
def mainloop():
    return interface.PulseAudioMainLoop()


def test_mainloop_run(mainloop):
    mainloop.start()
    mainloop.delete()


def test_mainloop_lock(mainloop):
    mainloop.start()
    mainloop.lock()
    mainloop.unlock()
    mainloop.delete()


def test_mainloop_signal(mainloop):
    mainloop.start()
    with mainloop:
        mainloop.signal()
    mainloop.delete()


def test_mainloop_wait_signal(mainloop):
    mainloop.start()

    def signal():
        with mainloop:
            mainloop.signal()
    t = Timer(.1, signal)
    t.start()

    with mainloop:
        mainloop.wait()
    mainloop.delete()


@pytest.fixture
def context(mainloop):
    mainloop.start()
    with mainloop:
        context = mainloop.create_context()
    yield context

    with context:
        context.delete()
    mainloop.delete()


def test_context_not_connected(context):
    assert context.is_ready == False
    assert context.is_failed == False
    assert context.is_terminated == False
    assert context.server == None
    assert isinstance(context.protocol_version, numbers.Integral)
    assert context.server_protocol_version == None
    assert context.is_local == None

    with context:
        context.delete()

    assert context.is_ready == False
    assert context.is_failed == False
    assert context.is_terminated == False  # Never connected, so state is not set yet
    assert context.server == None
    assert context.protocol_version == None
    assert context.server_protocol_version == None
    assert context.is_local == None


def test_context_connect(context):
    assert context.is_ready == False
    assert context.is_failed == False
    assert context.is_terminated == False
    assert context.server == None
    assert isinstance(context.protocol_version, numbers.Integral)
    assert context.server_protocol_version == None
    assert context.is_local == None

    context.connect()

    assert context.is_ready == True
    assert context.is_failed == False
    assert context.is_terminated == False
    assert isinstance(context.server, str)
    assert isinstance(context.protocol_version, numbers.Integral)
    assert isinstance(context.server_protocol_version, numbers.Integral)
    assert context.is_local == True

    with context:
        context.delete()

    assert context.is_ready == False
    assert context.is_failed == False
    assert context.is_terminated == True
    assert context.server == None
    assert context.protocol_version == None
    assert context.server_protocol_version == None
    assert context.is_local == None


@pytest.fixture
def stream(context):
    context.connect()
    audio_format = AudioFormat(1, 16, 44100)
    with context:
        stream = context.create_stream(audio_format)
    return stream


@pytest.fixture
def audio_source():
    return Silence(10.0, 44100, 16)


@pytest.fixture
def filled_stream(stream, audio_source):
    with stream:
        stream.connect_playback()

    assert stream.is_ready
    assert stream.writable_size > 0

    nbytes = min(1024, stream.writable_size)
    audio_data = audio_source.get_audio_data(nbytes)
    with stream:
        stream.write(audio_data)

    assert stream.is_ready
    return stream


def test_stream_create(stream):
    assert stream.is_unconnected == True
    assert stream.is_creating == False
    assert stream.is_ready == False
    assert stream.is_failed == False
    assert stream.is_terminated == False

    with stream:
        stream.delete()

    assert stream.is_unconnected == True
    assert stream.is_creating == False
    assert stream.is_ready == False
    assert stream.is_failed == False
    assert stream.is_terminated == False


def test_stream_connect(stream):
    assert stream.is_unconnected == True
    assert stream.is_creating == False
    assert stream.is_ready == False
    assert stream.is_failed == False
    assert stream.is_terminated == False
    assert isinstance(stream.index, numbers.Integral)

    with stream:
        stream.connect_playback()

    assert stream.is_unconnected == False
    assert stream.is_creating == False
    assert stream.is_ready == True
    assert stream.is_failed == False
    assert stream.is_terminated == False
    assert isinstance(stream.index, numbers.Integral)

    with stream:
        stream.delete()

    assert stream.is_unconnected == False
    assert stream.is_creating == False
    assert stream.is_ready == False
    assert stream.is_failed == False
    assert stream.is_terminated == True



def test_stream_write(stream, audio_source):
    with stream:
        stream.connect_playback()

    assert stream.is_ready
    assert stream.writable_size > 0

    nbytes = min(1024, stream.writable_size)
    audio_data = audio_source.get_audio_data(nbytes)
    with stream:
        written = stream.write(audio_data)
    assert written == nbytes

    assert stream.is_ready

    with stream:
        stream.delete()

    assert stream.is_terminated



def test_stream_timing_info(filled_stream):
    with filled_stream:
        op = filled_stream.update_timing_info()
        op.wait()
    assert op.is_done
    info = filled_stream.get_timing_info()
    assert info is not None

    with filled_stream:
        op.delete()


def test_stream_trigger(filled_stream):
    with filled_stream:
        op = filled_stream.trigger()
        op.wait()
    assert op.is_done

    with filled_stream:
        op.delete()


def test_stream_prebuf(filled_stream):
    with filled_stream:
        op = filled_stream.prebuf()
        op.wait()
    assert op.is_done

    with filled_stream:
        op.delete()


def test_stream_cork(filled_stream):
    assert filled_stream.is_corked

    with filled_stream:
        op = filled_stream.resume()
        op.wait()
    assert op.is_done
    assert not filled_stream.is_corked

    with filled_stream:
        op.delete()
        op = filled_stream.pause()
        op.wait()
    assert op.is_done
    assert filled_stream.is_corked

    with filled_stream:
        op.delete()


def test_stream_update_sample_rate(filled_stream):
    with filled_stream:
        op = filled_stream.update_sample_rate(44100)
        op.wait()
    assert op.is_done

    with filled_stream:
        op.delete()


def test_stream_write_needed(stream, audio_source, event_loop):
    with stream:
        stream.connect_playback()

    assert stream.is_ready
    assert stream.writable_size > 0

    @stream.event
    def on_write_needed(nbytes, underflow):
        on_write_needed.nbytes = nbytes
        on_write_needed.underflow = underflow
        if underflow is True:
            event_loop.interrupt_event_loop()
        return pyglet.event.EVENT_HANDLED

    on_write_needed.nbytes = None
    on_write_needed.underflow = None

    audio_data = audio_source.get_audio_data(stream.writable_size)
    with stream:
        stream.write(audio_data)
    assert stream.is_ready
    assert not stream.underflow
    with stream:
        stream.resume().wait().delete()

    event_loop.run_event_loop(duration=0.1)

    assert on_write_needed.nbytes > 0
    assert on_write_needed.underflow == False
    assert not stream.underflow

    on_write_needed.nbytes = None
    on_write_needed.underflow = None

    event_loop.run_event_loop(duration=5.0)
    assert on_write_needed.nbytes > 0
    assert on_write_needed.underflow == True
    assert stream.underflow

