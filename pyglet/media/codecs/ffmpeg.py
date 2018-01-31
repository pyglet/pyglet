from ..sources.ffmpeg import FFmpegSource
from ..sources import StaticSource


class FFmpegDecoder(object):

    def get_file_extensions(self):
        return ['.mp3', '.ogg']

    def decode(self, file, filename, streaming):
        if streaming:
            return FFmpegSource(filename, file)
        else:
            return StaticSource(FFmpegSource(filename, file))


def get_decoders():
    return [FFmpegDecoder()]


def get_encoders():
    return []
