import os
from unittest import mock

import pyglet


test_data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))


def get_test_data_file(path, file_name):
    """Get a file from the test data directory in an OS independent way."""
    return os.path.join(test_data_path, path, file_name)


def test_load_audio_from_disk_path():
    file_path = get_test_data_file("media", "alert.wav")
    source = pyglet.media.load_audio(file_path, streaming=False)

    assert source.audio_format is not None
    assert source.duration > 0


def test_load_audio_from_open_file_object():
    file_path = get_test_data_file("media", "alert.wav")
    with open(file_path, "rb") as file_object:
        source = pyglet.media.load_audio(file_path, file=file_object, streaming=False)

    assert source.audio_format is not None
    assert source.duration > 0


def test_wav_uses_wave_decoder():
    from pyglet.media import codecs as media_codecs
    from pyglet.media.codecs.wave import WaveDecoder

    file_path = get_test_data_file("media", "alert.wav")
    decoder = next(
        decoder
        for decoder in media_codecs.get_decoders(file_path, media_capabilities="audio")
        if isinstance(decoder, WaveDecoder)
    )

    with mock.patch.object(decoder, "decode", wraps=decoder.decode) as decode_mock:
        source = pyglet.media.load_audio(file_path, streaming=False)

    decode_mock.assert_called_once()
    assert source.audio_format is not None
    assert source.duration > 0
