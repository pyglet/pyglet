import os

import pytest
import pyglet


pytestmark = pytest.mark.skipif(not pyglet.media.have_ffmpeg(), reason="FFmpeg not available.")

test_data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))


def get_test_data_file(path, file_name):
    """Get a file from the test data directory."""
    return os.path.join(test_data_path, path, file_name)


def test_ffmpeg_decoder_load_audio_from_filename():
    from pyglet.media.codecs.ffmpeg import FFmpegDecoder

    file_path = get_test_data_file("media", "alert.wav")
    source = pyglet.media.load_audio(file_path, streaming=False, decoder=FFmpegDecoder())

    assert source.audio_format is not None
    assert source.duration > 0


def test_ffmpeg_decoder_load_audio_from_open_file_object():
    from pyglet.media.codecs.ffmpeg import FFmpegDecoder

    file_path = get_test_data_file("media", "alert.wav")
    with open(file_path, "rb") as file_object:
        source = pyglet.media.load_audio(file_path, file=file_object, streaming=False, decoder=FFmpegDecoder())

    assert source.audio_format is not None
    assert source.duration > 0


def test_ffmpeg_decoder_is_last_audio_decoder_in_registry():
    from pyglet.media.codecs.ffmpeg import FFmpegDecoder
    from pyglet.media import codecs as media_codecs

    audio_decoders = media_codecs.get_decoders(media_capabilities="audio")
    assert audio_decoders
    assert any(isinstance(decoder, FFmpegDecoder) for decoder in audio_decoders)
    assert isinstance(audio_decoders[-1], FFmpegDecoder)
