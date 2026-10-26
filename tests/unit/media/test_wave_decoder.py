from io import BytesIO
import wave

import pytest

import pyglet.media
from pyglet.media.codecs.wave import WAVEDecodeException, WaveDecoder


@pytest.mark.parametrize("channels", [1, 2])
@pytest.mark.parametrize("sample_width", [1, 2])
@pytest.mark.parametrize("streaming", [False, True])
@pytest.mark.parametrize("frame_count", [0, 2])
def test_wave_decoder_empty_and_nonempty_files(channels, sample_width, streaming, frame_count):
    pcm = bytes(range(channels * sample_width * frame_count))
    audio_file = BytesIO()
    with wave.open(audio_file, "wb") as writer:
        writer.setparams((channels, sample_width, 8000, frame_count, "NONE", "not compressed"))
        writer.writeframes(pcm)
    audio_file.seek(0)

    if frame_count == 0:
        with pytest.raises(WAVEDecodeException, match="no audio frames"):
            pyglet.media.load("audio.wav", audio_file, streaming=streaming, decoder=WaveDecoder())
        return

    source = pyglet.media.load("audio.wav", audio_file, streaming=streaming, decoder=WaveDecoder())

    assert source.duration == frame_count / 8000
    assert source.audio_format.channels == channels
    assert source.audio_format.sample_size == sample_width * 8
    queue_source = source.get_queue_source()
    queue_source.seek(1)
    assert queue_source.get_audio_data(64) is None
    queue_source.seek(0)
    data = queue_source.get_audio_data(64)
    assert data.data == pcm
