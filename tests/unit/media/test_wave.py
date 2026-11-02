from io import BytesIO
import wave

import pytest

from pyglet.media.codecs.wave import WaveEncoder, WaveSource


@pytest.mark.parametrize("channels", [1, 2])
@pytest.mark.parametrize("sample_width", [1, 2])
def test_wave_export_preserves_sample_format(channels, sample_width):
    pcm = bytes(range(channels * sample_width * 8))
    original = BytesIO()
    with wave.open(original, "wb") as writer:
        writer.setparams((channels, sample_width, 8000, 8, "NONE", "not compressed"))
        writer.writeframes(pcm)
    original.seek(0)
    source = WaveSource("original.wav", original)
    exported = BytesIO()

    source.save("exported.wav", exported, encoder=WaveEncoder())

    exported.seek(0)
    with wave.open(exported, "rb") as reader:
        assert reader.getnchannels() == channels
        assert reader.getsampwidth() == sample_width
        assert reader.getframerate() == 8000
        assert reader.getnframes() == 8
        assert reader.readframes(8) == pcm
