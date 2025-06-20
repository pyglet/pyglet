"""Decoder for RIFF Wave files, using the standard library wave module.
"""

import wave

from pyglet.util import DecodeException
from .base import StreamingSource, AudioData, AudioFormat, StaticSource
from . import MediaEncoder, MediaDecoder


class WAVEDecodeException(DecodeException):
    pass


class WaveSource(StreamingSource):
    def __init__(self, filename, file=None):
        if file is None:
            file = open(filename, 'rb')
            self._file = file

        try:
            self._wave = wave.open(file)
        except wave.Error as e:
            raise WAVEDecodeException(e)

        nchannels, sampwidth, framerate, nframes, comptype, compname = self._wave.getparams()

        if nchannels not in (1, 2):
            raise WAVEDecodeException(f"incompatible channel count {nchannels}")

        if sampwidth not in (1, 2):
            raise WAVEDecodeException(f"incompatible sample width {sampwidth}")

        self.audio_format = AudioFormat(channels=nchannels, sample_size=sampwidth * 8, sample_rate=framerate)

        self._bytes_per_frame = nchannels * sampwidth
        self._duration = nframes / framerate
        self._duration_per_frame = self._duration / nframes
        self._num_frames = nframes

        self._wave.rewind()

    def __del__(self):
        if hasattr(self, '_file'):
            self._file.close()

    def get_audio_data(self, num_bytes, compensation_time=0.0):
        num_frames = max(1, num_bytes // self._bytes_per_frame)

        data = self._wave.readframes(num_frames)
        if not data:
            return None

        timestamp = self._wave.tell() / self.audio_format.sample_rate
        duration = num_frames / self.audio_format.sample_rate
        return AudioData(data, len(data), timestamp, duration, [])

    def seek(self, timestamp):
        timestamp = max(0.0, min(timestamp, self._duration))
        position = int(timestamp / self._duration_per_frame)
        self._wave.setpos(position)


#########################################
#   Decoder class:
#########################################

class WaveDecoder(MediaDecoder):

    def get_file_extensions(self):
        return '.wav', '.wave', '.riff'

    def decode(self, filename, file, streaming=True):
        if streaming:
            return WaveSource(filename, file)
        else:
            return StaticSource(WaveSource(filename, file))


class WaveEncoder(MediaEncoder):

    def get_file_extensions(self):
        return '.wav', '.wave', '.riff'

    def encode(self, source, filename, file):
        """Save the Source to disk as a standard RIFF Wave.

        A standard RIFF wave header will be added to the raw PCM
        audio data when it is saved to disk.

        :Parameters:
            `filename` : str
                The file name to save as.
            `file` : file-like object
                A file-like object, opened with mode 'wb'.

        """
        opened_file = None
        if file is None:
            file = open(filename, 'wb')
            opened_file = True

        source.seek(0)
        wave_writer = wave.open(file, mode='wb')
        wave_writer.setnchannels(source.audio_format.channels)
        wave_writer.setsampwidth(source.audio_format.bytes_per_sample)
        wave_writer.setframerate(source.audio_format.sample_rate)
        # Save the data in 1-second chunks:
        chunksize = source.audio_format.bytes_per_second
        audiodata = source.get_audio_data(chunksize)
        while audiodata:
            wave_writer.writeframes(audiodata.data)
            audiodata = source.get_audio_data(chunksize)
        else:
            wave_writer.close()
            if opened_file:
                file.close()


def get_decoders():
    return [WaveDecoder()]


def get_encoders():
    return [WaveEncoder()]
