from ..sources.riff import WaveSource
from ..sources import StaticSource


class WaveDecoder(object):

    def get_file_extensions(self):
        return ['.wav', '.wave']

    def decode(self, file, filename, streaming):
        if streaming:
            return WaveSource(filename, file)
        else:
            return StaticSource(WaveSource(filename, file))


def get_decoders():
    return [WaveDecoder()]


def get_encoders():
    return []
