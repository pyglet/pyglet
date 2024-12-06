"""Use ffmpeg to decode audio and video media."""
from __future__ import annotations

import sys
from collections import deque
from ctypes import (
    POINTER,
    Array,
    Structure,
    addressof,
    byref,
    c_char_p,
    c_int,
    c_int32,
    c_uint8,
    cast,
    create_string_buffer,
    memmove,
)
from dataclasses import dataclass
from typing import BinaryIO, TYPE_CHECKING, Iterator, Sequence

from _ctypes import _Pointer

import pyglet
import pyglet.lib
from pyglet import image
from pyglet.util import asbytes, asstr
from . import MediaDecoder
from .base import AudioData, AudioFormat, SourceInfo, StaticSource, StreamingSource, VideoFormat
from .ffmpeg_lib import (
    AV_CODEC_ID_VP8,
    AV_CODEC_ID_VP9,
    FF_INPUT_BUFFER_PADDING_SIZE,
    SWS_FAST_BILINEAR,
    AVPacket,
    SwrContext,
    SwsContext,
    avcodec,
    libavformat,
    libavutil,
    swscale,
)
from .ffmpeg_lib.libavformat import AVCodecContext, AVFormatContext, avformat, avformat_version
from .ffmpeg_lib.libavutil import (
    AV_NOPTS_VALUE,
    AV_PIX_FMT_RGBA,
    AV_SAMPLE_FMT_FLT,
    AV_SAMPLE_FMT_FLTP,
    AV_SAMPLE_FMT_S16,
    AV_SAMPLE_FMT_S16P,
    AV_SAMPLE_FMT_S32,
    AV_SAMPLE_FMT_S32P,
    AV_SAMPLE_FMT_U8,
    AV_SAMPLE_FMT_U8P,
    AV_TIME_BASE,
    AV_TIME_BASE_Q,
    AVMEDIA_TYPE_AUDIO,
    AVMEDIA_TYPE_VIDEO,
    AVChannelLayout,
    AVFrame,
    AVRational,
    avutil,
)
from .ffmpeg_lib.libswresample import swresample, swresample_version
from ..exceptions import MediaFormatException

if TYPE_CHECKING:
    from .ffmpeg_lib.libavformat import AVStream


class FileInfo:
    def __init__(self):
        self.n_streams = None
        self.start_time = None
        self.duration = None
        self.title = ""
        self.author = ""
        self.copyright = ""
        self.comment = ""
        self.album = ""
        self.year = None
        self.track = ""
        self.genre = ""


@dataclass
class StreamVideoInfo:
    width: int
    height: int
    sample_aspect_num: int
    sample_aspect_den: int
    frame_rate_num: int
    frame_rate_den: int
    codec_id: int


@dataclass
class StreamAudioInfo:
    sample_format: int
    sample_rate: int
    channels: int
    sample_bits: int | None = None


class FFmpegFile(Structure):
    _fields_ = [
        ('context', POINTER(AVFormatContext)),
    ]


class FFmpegStream(Structure):
    _fields_ = [
        ('type', c_int32),
        ('format_context', POINTER(AVFormatContext)),
        ('codec_context', POINTER(AVCodecContext)),
        ('frame', POINTER(AVFrame)),
        ('time_base', AVRational),
    ]


class FFmpegException(MediaFormatException):
    pass


def ffmpeg_get_audio_buffer_size(audio_format):
    """Return the audio buffer size

    Buffer size can accomodate 1 sec of audio data.
    """
    return audio_format.bytes_per_second + FF_INPUT_BUFFER_PADDING_SIZE


def ffmpeg_init():
    """Initialize libavformat and register all the muxers, demuxers and protocols."""


class MemoryFileObject:
    """A class to manage reading and seeking of a ffmpeg file object."""
    buffer_size = 32768

    def __init__(self, file: BinaryIO) -> None:
        self.file = file
        self.fmt_context = None
        self.buffer = None

        if not getattr(self.file, 'seek', None) or not getattr(self.file, 'tell', None):
            raise Exception("File object does not support seeking.")

        # Seek to end of file to get the filesize.
        self.file.seek(0, 2)
        self.file_size = self.file.tell()
        self.file.seek(0)  # Put cursor back at the beginning.

        def read_data_cb(_, buff: bytes, buf_size: int) -> int:
            data = self.file.read(buf_size)
            read_size = len(data)
            memmove(buff, data, read_size)
            return read_size

        def seek_data_cb(_, offset: int, whence: int) -> int:
            if whence == libavformat.AVSEEK_SIZE:
                return self.file_size

            pos = self.file.seek(offset, whence)
            return pos

        self.read_func = libavformat.ffmpeg_read_func(read_data_cb)
        self.seek_func = libavformat.ffmpeg_seek_func(seek_data_cb)

    def __del__(self) -> None:
        """These are usually freed when the source is, but no guarantee."""
        if self.buffer:
            try:
                avutil.av_freep(self.buffer)
            except OSError:
                pass

        if self.fmt_context:
            try:
                avutil.av_freep(self.fmt_context)
            except OSError:
                pass


def ffmpeg_open_memory_file(filename: bytes, file_object: BinaryIO) -> tuple[FFmpegFile, MemoryFileObject]:
    """Open a media file from a file-like object.

    Returns:
        The structure containing all the information for the media and the memory file object.
    """
    file = FFmpegFile()

    file.context = libavformat.avformat.avformat_alloc_context()
    file.context.contents.seekable = 1

    memory_file = MemoryFileObject(file_object)

    av_buf = libavutil.avutil.av_malloc(memory_file.buffer_size)
    memory_file.buffer = cast(av_buf, c_char_p)

    ptr = create_string_buffer(memory_file.buffer_size)

    memory_file.fmt_context = libavformat.avformat.avio_alloc_context(
        memory_file.buffer,
        memory_file.buffer_size,
        0,
        ptr,
        memory_file.read_func,
        None,
        memory_file.seek_func,
    )

    file.context.contents.pb = memory_file.fmt_context
    file.context.contents.flags |= libavformat.AVFMT_FLAG_CUSTOM_IO

    result = avformat.avformat_open_input(byref(file.context), filename, None, None)

    if result != 0:
        raise FFmpegException('avformat_open_input in ffmpeg_open_filename returned an error opening file '
                              + filename.decode("utf8")
                              + ' Error code: ' + str(result))

    result = avformat.avformat_find_stream_info(file.context, None)
    if result < 0:
        raise FFmpegException('Could not find stream info')

    return file, memory_file


def ffmpeg_open_filename(filename: bytes) -> FFmpegFile:
    """Open the media file.

    Returns:
        The structure containing all the information for the media.
    """
    file = FFmpegFile()  # TODO: delete this structure and use directly AVFormatContext
    result = avformat.avformat_open_input(byref(file.context),
                                          filename,
                                          None,
                                          None)

    if result != 0:
        raise FFmpegException('avformat_open_input in ffmpeg_open_filename returned an error opening file '
                              + filename.decode("utf8")
                              + ' Error code: ' + str(result))

    result = avformat.avformat_find_stream_info(file.context, None)
    if result < 0:
        raise FFmpegException('Could not find stream info')

    return file


def ffmpeg_close_file(file: FFmpegFile):
    """Close the media file and free resources."""
    avformat.avformat_close_input(byref(file.context))


def ffmpeg_file_info(file: FFmpegFile) -> FileInfo:
    """Get information on the file:

        - number of streams
        - duration
        - artist
        - album
        - date
        - track

    Returns:
        The file info instance containing all the meta information.
    """
    info = FileInfo()
    info.n_streams = file.context.contents.nb_streams
    info.start_time = file.context.contents.start_time
    info.duration = file.context.contents.duration

    entry = avutil.av_dict_get(file.context.contents.metadata, asbytes('title'), None, 0)
    if entry:
        info.title = asstr(entry.contents.value)

    entry = avutil.av_dict_get(file.context.contents.metadata, asbytes('artist'), None, 0) \
        or avutil.av_dict_get(file.context.contents.metadata, asbytes('album_artist'), None, 0)
    if entry:
        info.author = asstr(entry.contents.value)

    entry = avutil.av_dict_get(file.context.contents.metadata, asbytes('copyright'), None, 0)
    if entry:
        info.copyright = asstr(entry.contents.value)

    entry = avutil.av_dict_get(file.context.contents.metadata, asbytes('comment'), None, 0)
    if entry:
        info.comment = asstr(entry.contents.value)

    entry = avutil.av_dict_get(file.context.contents.metadata, asbytes('album'), None, 0)
    if entry:
        info.album = asstr(entry.contents.value)

    entry = avutil.av_dict_get(file.context.contents.metadata, asbytes('date'), None, 0)
    if entry:
        info.year = asstr(entry.contents.value)

    entry = avutil.av_dict_get(file.context.contents.metadata, asbytes('track'), None, 0)
    if entry:
        info.track = asstr(entry.contents.value)

    entry = avutil.av_dict_get(file.context.contents.metadata, asbytes('genre'), None, 0)
    if entry:
        info.genre = asstr(entry.contents.value)

    return info


def ffmpeg_stream_info(file: FFmpegFile, stream_index: int) -> StreamAudioInfo | StreamVideoInfo | None:
    """Open the stream and retrieve information about it."""
    av_stream = file.context.contents.streams[stream_index].contents

    context = av_stream.codecpar.contents

    if context.codec_type == AVMEDIA_TYPE_VIDEO:
        if _debug:
            print(" codec_type=", context.codec_type)
            print(" codec_id=", context.codec_id)
            print(" codec name=", avcodec.avcodec_get_name(context.codec_id).decode('utf-8'))
            print(" codec_tag=", context.codec_tag)
            print(" extradata=", context.extradata)
            print(" extradata_size=", context.extradata_size)
            print(" format=", context.format)
            print(" bit_rate=", context.bit_rate)
            print(" bits_per_coded_sample=", context.bits_per_coded_sample)
            print(" bits_per_raw_sample=", context.bits_per_raw_sample)
            print(" profile=", context.profile)
            print(" level=", context.level)
            print(" width=", context.width)
            print(" height=", context.height)
            print(" sample_aspect_ratio=", context.sample_aspect_ratio.num, context.sample_aspect_ratio.den)
            print(" field_order=", context.field_order)
            print(" color_range=", context.color_range)
            print(" color_primaries=", context.color_primaries)
            print(" color_trc=", context.color_trc)
            print(" color_space=", context.color_space)
            print(" chroma_location=", context.chroma_location)
            print(" video_delay=", context.video_delay)
            if avformat_version >= 61:
                print(" channel_layout=", context.ch_layout)
            else:
                print(" channel_layout=", context.channel_layout)
                print(" channels=", context.channels)
            print(" sample_rate=", context.sample_rate)
            print(" block_align=", context.block_align)
            print(" frame_size=", context.frame_size)
            print(" initial_padding=", context.initial_padding)
            print(" trailing_padding=", context.trailing_padding)
            print(" seek_preroll=", context.seek_preroll)
        #
        frame_rate = avformat.av_guess_frame_rate(file.context, av_stream, None)

        info = StreamVideoInfo(
            context.width,
            context.height,
            context.sample_aspect_ratio.num,
            context.sample_aspect_ratio.den,
            frame_rate.num,
            frame_rate.den,
            context.codec_id,
        )
    elif context.codec_type == AVMEDIA_TYPE_AUDIO:
        # Format changed in 7.x
        if avformat_version >= 61:
            channel_count = context.ch_layout.nb_channels
        else:
            channel_count = context.channels

        if _debug:
            print(" codec_type=", context.codec_type)
            print(" codec_id=", context.codec_id)
            print(" codec name=", avcodec.avcodec_get_name(context.codec_id).decode('utf-8'))
            print(" format=", context.format)
            print(" bit_rate=", context.bit_rate)
            print(" sample_rate=", context.sample_rate)
            print(" channel_count=", channel_count)

        info = StreamAudioInfo(
            context.format,
            context.sample_rate,
            channel_count,
        )
        if context.format in (AV_SAMPLE_FMT_U8, AV_SAMPLE_FMT_U8P):
            info.sample_bits = 8
        elif context.format in (AV_SAMPLE_FMT_S16, AV_SAMPLE_FMT_S16P,
                                AV_SAMPLE_FMT_FLT, AV_SAMPLE_FMT_FLTP):
            info.sample_bits = 16
        elif context.format in (AV_SAMPLE_FMT_S32, AV_SAMPLE_FMT_S32P):
            info.sample_bits = 32
        else:
            info.sample_format = None
            info.sample_bits = None
    else:
        return None
    return info


def ffmpeg_open_stream(file: FFmpegFile, index: int) -> FFmpegStream:
    if not 0 <= index < file.context.contents.nb_streams:
        raise FFmpegException(f'index out of range. Only {file.context.contents.nb_streams} streams.')
    codec_context = avcodec.avcodec_alloc_context3(None)
    if not codec_context:
        raise MemoryError('Could not allocate Codec Context.')
    result = avcodec.avcodec_parameters_to_context(
        codec_context,
        file.context.contents.streams[index].contents.codecpar)
    if result < 0:
        avcodec.avcodec_free_context(byref(codec_context))
        raise FFmpegException('Could not copy the AVCodecContext.')
    codec_id = codec_context.contents.codec_id
    codec = avcodec.avcodec_find_decoder(codec_id)
    if _debug:
        print("Found Codec=", codec_id, "=", codec.contents.long_name.decode())

    # VP8 and VP9 default codec don't support alpha transparency.
    # Force libvpx codec in this case.
    if codec_id == AV_CODEC_ID_VP9:
        newcodec = avcodec.avcodec_find_decoder_by_name(b"libvpx-vp9")
        codec = newcodec or codec

    if codec_id == AV_CODEC_ID_VP8:
        newcodec = avcodec.avcodec_find_decoder_by_name(b"libvpx")
        codec = newcodec or codec

    if not codec:
        raise FFmpegException('No codec found for this media. '
                              f'codecID={codec_id}')

    codec_id = codec.contents.id
    if _debug:
        print("Loaded codec: ", codec.contents.long_name.decode())

    result = avcodec.avcodec_open2(codec_context, codec, None)
    if result < 0:
        raise FFmpegException('Could not open the media with the codec.')

    stream = FFmpegStream()
    stream.format_context = file.context
    stream.codec_context = codec_context
    stream.type = codec_context.contents.codec_type
    stream.frame = avutil.av_frame_alloc()
    stream.time_base = file.context.contents.streams[index].contents.time_base

    return stream


def ffmpeg_close_stream(stream: FFmpegStream) -> None:
    if stream.frame:
        avutil.av_frame_free(byref(stream.frame))
    avcodec.avcodec_free_context(byref(stream.codec_context))


def ffmpeg_seek_file(file: FFmpegFile, timestamp: float) -> None:
    flags = 0
    max_ts = file.context.contents.duration * AV_TIME_BASE
    result = avformat.avformat_seek_file(
        file.context, -1, 0,
        timestamp, timestamp, flags,
    )
    if result < 0:
        buf = create_string_buffer(128)
        avutil.av_strerror(result, buf, 128)
        descr = buf.value
        raise FFmpegException('Error occured while seeking. ' +
                              descr.decode())


def ffmpeg_read(file: FFmpegFile, packet: _Pointer[AVPacket]) -> bool:
    """Read from the stream a packet.

    Returns:
        True if the packet was correctly read. False if the end of stream was reached, or an error occurred.
    """
    avcodec.av_packet_unref(packet)
    result = avformat.av_read_frame(file.context, packet)
    if result < 0:
        return False

    return True


def ffmpeg_get_packet_pts(file: FFmpegFile, packet: _Pointer[AVPacket]) -> float:
    if packet.contents.dts != AV_NOPTS_VALUE:
        pts = packet.contents.dts
    else:
        pts = 0

    timestamp = avutil.av_rescale_q(pts,
                                    file.context.contents.streams[
                                        packet.contents.stream_index].contents.time_base,
                                    AV_TIME_BASE_Q)
    return timestamp


def ffmpeg_get_frame_ts(stream: FFmpegStream) -> float:
    ts = stream.frame.contents.best_effort_timestamp
    timestamp = avutil.av_rescale_q(ts,
                                    stream.time_base,
                                    AV_TIME_BASE_Q)
    return timestamp


def ffmpeg_init_packet() -> _Pointer[AVPacket]:
    p = avcodec.av_packet_alloc()
    if not p:
        raise MemoryError("Could not allocate AVPacket.")
    return p


def ffmpeg_free_packet(packet):
    avcodec.av_packet_free(byref(packet))


def ffmpeg_unref_packet(packet):
    avcodec.av_packet_unref(byref(packet))


def ffmpeg_transfer_packet(dst, src):
    avcodec.av_packet_move_ref(dst, src)


def get_version():
    """Return an informative version string of FFmpeg"""
    return avutil.av_version_info().decode()


def timestamp_from_ffmpeg(timestamp):
    return float(timestamp) / 1000000


def timestamp_to_ffmpeg(timestamp):
    return int(timestamp * 1000000)


class _Packet:
    packet: AVPacket
    timestamp: float

    __slots__ = ['packet', 'timestamp']

    def __init__(self, packet, timestamp):
        self.packet = AVPacket()
        ffmpeg_transfer_packet(byref(self.packet), packet)
        self.timestamp = timestamp

    def __del__(self):
        if ffmpeg_unref_packet is not None:
            ffmpeg_unref_packet(self.packet)


class VideoPacket(_Packet):
    id: int
    image: int
    _next_id = 0

    def __init__(self, packet, timestamp):
        super().__init__(packet, timestamp)
        # Decoded image.  0 == not decoded yet; None == Error or discarded
        self.image = 0
        self.id = self._next_id
        VideoPacket._next_id += 1


class AudioPacket(_Packet):
    pass


class FFmpegSource(StreamingSource):
    # Max increase/decrease of original sample size
    SAMPLE_CORRECTION_PERCENT_MAX = 10

    # Maximum amount of packets to create for video and audio queues.
    MAX_QUEUE_SIZE = 100

    def __init__(self, filename: str, file: BinaryIO | None=None):
        self._packet = None
        self._video_stream = None
        self._audio_stream = None
        self._stream_end = False
        self._file = None
        self._memory_file = None

        encoded_filename = filename.encode(sys.getfilesystemencoding())

        if file:
            self._file, self._memory_file = ffmpeg_open_memory_file(encoded_filename, file)
        else:
            self._file = ffmpeg_open_filename(encoded_filename)

        if not self._file:
            raise FFmpegException(f'Could not open "{filename}"')

        self._video_stream_index = None
        self._audio_stream_index = None
        self._audio_format = None

        self.img_convert_ctx = POINTER(SwsContext)()
        self.audio_convert_ctx = None

        file_info = ffmpeg_file_info(self._file)

        self.info = SourceInfo()
        self.info.title = file_info.title
        self.info.author = file_info.author
        self.info.copyright = file_info.copyright
        self.info.comment = file_info.comment
        self.info.album = file_info.album
        self.info.year = file_info.year
        self.info.track = file_info.track
        self.info.genre = file_info.genre

        # Pick the first video and audio streams found, ignore others.
        for i in range(file_info.n_streams):
            info = ffmpeg_stream_info(self._file, i)

            if isinstance(info, StreamVideoInfo) and self._video_stream is None:
                stream = ffmpeg_open_stream(self._file, i)

                self.video_format = VideoFormat(
                    width=info.width,
                    height=info.height)
                if info.sample_aspect_num != 0:
                    self.video_format.sample_aspect = (
                            float(info.sample_aspect_num) /
                            info.sample_aspect_den)
                self.video_format.frame_rate = (
                        float(info.frame_rate_num) /
                        info.frame_rate_den)
                self._video_stream = stream
                self._video_stream_index = i

            elif isinstance(info, StreamAudioInfo) and info.sample_bits in (8, 16, 24) and self._audio_stream is None:
                stream = ffmpeg_open_stream(self._file, i)

                self.audio_format = AudioFormat(
                    channels=min(2, info.channels),
                    sample_size=info.sample_bits,
                    sample_rate=info.sample_rate)
                self._audio_stream = stream
                self._audio_stream_index = i

                channel_input = self._get_default_channel_layout(info.channels)
                channels_out = min(2, info.channels)
                channel_output = self._get_default_channel_layout(channels_out)

                sample_rate = stream.codec_context.contents.sample_rate
                sample_format = stream.codec_context.contents.sample_fmt

                if sample_format in (AV_SAMPLE_FMT_U8, AV_SAMPLE_FMT_U8P):
                    self.tgt_format = AV_SAMPLE_FMT_U8
                elif sample_format in (AV_SAMPLE_FMT_S16, AV_SAMPLE_FMT_S16P):
                    self.tgt_format = AV_SAMPLE_FMT_S16
                elif sample_format in (AV_SAMPLE_FMT_S32, AV_SAMPLE_FMT_S32P):
                    self.tgt_format = AV_SAMPLE_FMT_S32
                elif sample_format in (AV_SAMPLE_FMT_FLT, AV_SAMPLE_FMT_FLTP):
                    self.tgt_format = AV_SAMPLE_FMT_S16
                else:
                    raise FFmpegException('Audio format not supported.')

                self.audio_convert_ctx = self.get_formatted_swr_context(channel_output, sample_rate, channel_input, sample_format)
                if not self.audio_convert_ctx:
                    swresample.swr_free(self.audio_convert_ctx)
                    raise FFmpegException('Cannot create sample rate converter.')

                result = swresample.swr_init(self.audio_convert_ctx)
                if result < 0:
                    swresample.swr_free(self.audio_convert_ctx)
                    raise FFmpegException('Cannot create sample rate converter.', result)

        self._packet = ffmpeg_init_packet()
        self._events = []  # They don't seem to be used!

        self.audioq = deque()
        # Make queue big enough to accomodate 1.2 sec?
        self._max_len_audioq = self.MAX_QUEUE_SIZE  # Need to figure out a correct amount
        if self.audio_format:
             # Buffer 1 sec worth of audio
             nbytes = ffmpeg_get_audio_buffer_size(self.audio_format)
             self._audio_buffer = (c_uint8 * nbytes)()

        self.videoq: deque[VideoPacket] = deque()
        self._max_len_videoq = self.MAX_QUEUE_SIZE  # Need to figure out a correct amount

        self.start_time = self._get_start_time()
        self._duration = timestamp_from_ffmpeg(file_info.duration)
        self._duration -= self.start_time

        # Flag to determine if the _fillq method was already scheduled
        self._fillq_scheduled = False
        self._fillq()
        # Don't understand why, but some files show that seeking without
        # reading the first few packets results in a seeking where we lose
        # many packets at the beginning.
        # We only seek back to 0 for media which have a start_time > 0
        if self.start_time > 0:
            self.seek(0.0)

    def get_formatted_swr_context(self, channel_output: AVChannelLayout | int, sample_rate: int,
                                  channel_input: AVChannelLayout | int, sample_format: int) -> int | SwrContext:
        # Newer FFmpeg versions use the AVChannelLayout
        if swresample_version < 5:
            return swresample.swr_alloc_set_opts(None,
                                          channel_output, self.tgt_format, sample_rate,
                                          channel_input, sample_format, sample_rate,
                                          0, None)
        else:
            swr_ctx = swresample.swr_alloc()
            if not swr_ctx:
                raise RuntimeError("Could not allocate SwrContext")

            if swresample.swr_alloc_set_opts2(byref(swr_ctx),
                                              channel_output, self.tgt_format, sample_rate,
                                              channel_input, sample_format, sample_rate,
                                              0, None) < 0:
                raise Exception("Could not set sample rate context values.")
            return swr_ctx

    @staticmethod
    def _get_default_channel_layout(channels: int) -> int | AVChannelLayout:
        if swresample_version < 5:
            return avutil.av_get_default_channel_layout(channels)
        else:
            layout = AVChannelLayout()
            avutil.av_channel_layout_default(byref(layout), channels)
            return layout

    def __del__(self) -> None:
        if self._packet and ffmpeg_free_packet is not None:
            ffmpeg_free_packet(self._packet)
        if self._video_stream and swscale is not None:
            swscale.sws_freeContext(self.img_convert_ctx)
            ffmpeg_close_stream(self._video_stream)
        if self._audio_stream:
            if swresample:
                swresample.swr_free(self.audio_convert_ctx)
                ffmpeg_close_stream(self._audio_stream)
        if self._file and ffmpeg_close_file is not None:
            ffmpeg_close_file(self._file)

    def seek(self, timestamp: float) -> None:
        if _debug:
            print('FFmpeg seek', timestamp)

        ffmpeg_seek_file(
            self._file,
            timestamp_to_ffmpeg(timestamp + self.start_time),
        )
        del self._events[:]
        self._stream_end = False
        self._clear_video_audio_queues()
        self._fillq()

        # Consume video and audio packets until we arrive at the correct
        # timestamp location
        if not self.audio_format:
            while len(self.videoq) > 1:
                # We only advance if there is at least 2 packets in the queue
                # The queue is only left with 1 packet if we have reached the
                #  end of the stream.
                if timestamp < self.videoq[1].timestamp:
                    break
                else:
                    self.get_next_video_frame(skip_empty_frame=False)

        elif not self.video_format:
            while len(self.audioq) > 1:
                # We only advance if there is at least 2 packets in the queue
                # The queue is only left with 1 packet if we have reached the
                #  end of the stream.
                if timestamp < self.audioq[1].timestamp:
                    break
                else:
                    self._get_audio_packet()

        else:
            while len(self.audioq) > 1 and len(self.videoq) > 1:
                # We only advance if there is at least 2 packets in the queue
                # The queue is only left with 1 packet if we have reached the
                #  end of the stream.
                audioq_is_first = self.audioq[0].timestamp < self.videoq[0].timestamp
                correct_audio_pos = timestamp < self.audioq[1].timestamp
                correct_video_pos = timestamp < self.videoq[1].timestamp
                if audioq_is_first and not correct_audio_pos:
                    self._get_audio_packet()

                elif not correct_video_pos:
                    self.get_next_video_frame(skip_empty_frame=False)

                else:
                    break

    def _get_audio_packet(self) -> AudioPacket:
        """Take an audio packet from the queue.

        This function will schedule its `_fillq` function to fill up
        the queues if space is available. Multiple calls to this method will
        only result in one scheduled call to `_fillq`.
        """
        audio_data = self.audioq.popleft()
        low_lvl = self._check_low_level()
        if not low_lvl and not self._fillq_scheduled:
            pyglet.clock.schedule_once(lambda dt: self._fillq(), 0)
            self._fillq_scheduled = True

        return audio_data

    def _get_video_packet(self) -> VideoPacket | None:
        """Take a video packet from the queue.

        This function will schedule its `_fillq` function to fill up
        the queues if space is available. Multiple calls to this method will
        only result in one scheduled call to `_fillq`.
        """
        if not self.videoq:
            return None
        video_packet = self.videoq.popleft()
        low_lvl = self._check_low_level()
        if not low_lvl and not self._fillq_scheduled:
            pyglet.clock.schedule_once(lambda dt: self._fillq(), 0)
            self._fillq_scheduled = True
        return video_packet

    def _clear_video_audio_queues(self) -> None:
        """Empty both audio and video queues."""
        self.audioq.clear()
        self.videoq.clear()

    def _fillq(self) -> None:
        """Fill up both Audio and Video queues if space is available in both"""
        # We clear our flag.
        self._fillq_scheduled = False
        while (len(self.audioq) < self._max_len_audioq and
               len(self.videoq) < self._max_len_videoq):
            if self._get_packet():
                self._process_packet()
            else:
                self._stream_end = True
                break

    def _check_low_level(self) -> bool:
        """Check if both audio and video queues are getting very low.

        If one of them has less than 2 elements, we fill the queue immediately
        with new packets. We don't wait for a scheduled call because we need
        them immediately.

        This would normally happens only during seek operations where we
        consume many packets to find the correct timestamp.
        """
        if len(self.audioq) < 2 or len(self.videoq) < 2:
            if len(self.audioq) < self._max_len_audioq and len(self.videoq) < self._max_len_videoq:
                self._fillq()
            return True
        return False

    def _get_packet(self) -> bool:
        # Read a packet into self._packet. Returns True if OK, False if no
        # more packets are in stream.
        return ffmpeg_read(self._file, self._packet)

    def _process_packet(self) -> AudioPacket | VideoPacket:
        """Process the packet that has been just read.

        Determines whether it's a video or audio packet and queue it in the
        appropriate queue.
        """
        timestamp = ffmpeg_get_packet_pts(self._file, self._packet)
        timestamp = timestamp_from_ffmpeg(timestamp)
        timestamp -= self.start_time

        if self._packet.contents.stream_index == self._video_stream_index:
            video_packet = VideoPacket(self._packet, timestamp)

            if _debug:
                print('Created and queued packet %d (%f)' % (video_packet.id, video_packet.timestamp))

            self.videoq.append(video_packet)
            return video_packet

        elif self.audio_format and self._packet.contents.stream_index == self._audio_stream_index:
            audio_packet = AudioPacket(self._packet, timestamp)

            self.audioq.append(audio_packet)
            return audio_packet

    def get_audio_data(self, num_bytes: int, compensation_time: float=0.0) -> AudioData | None:
        data = b''
        timestamp = duration = 0

        while len(data) < num_bytes:
            if not self.audioq:
                break

            audio_packet = self._get_audio_packet()
            buffer, timestamp, duration = self._decode_audio_packet(audio_packet, compensation_time)

            if not buffer:
                break
            data += buffer

        # No data and no audio queue left
        if not data and not self.audioq:
            if not self._stream_end:
                # No more audio data in queue, but we haven't hit the stream end.
                if _debug:
                    print("Audio queue was starved by the audio driver.")

            return None

        audio_data = AudioData(data, len(data), timestamp, duration, [])

        while self._events and self._events[0].timestamp <= (timestamp + duration):
            event = self._events.pop(0)
            if event.timestamp >= timestamp:
                event.timestamp -= timestamp
                audio_data.events.append(event)

        if _debug:
            print(f'get_audio_data returning ts {audio_data.timestamp} with events {audio_data.events}')
            print('remaining events are', self._events)

        return audio_data

    def _decode_audio_packet(self, audio_packet: AudioPacket, compensation_time: float) -> tuple[bytes | None, float, float]:
        while True:
            try:
                size_out = self._ffmpeg_decode_audio(
                    audio_packet.packet,
                    self._audio_buffer,
                    compensation_time)
            except FFmpegException:
                break

            if size_out <= 0:
                break

            buffer = create_string_buffer(size_out)
            memmove(buffer, self._audio_buffer, len(buffer))
            buffer = buffer.raw

            duration = float(len(buffer)) / self.audio_format.bytes_per_second
            timestamp = ffmpeg_get_frame_ts(self._audio_stream)
            timestamp = timestamp_from_ffmpeg(timestamp)
            return buffer, timestamp, duration

        return None, 0, 0

    def _ffmpeg_decode_audio(self, packet: AVPacket, data_out: Array[c_uint8], compensation_time: float) -> int:
        stream = self._audio_stream

        if stream.type != AVMEDIA_TYPE_AUDIO:
            raise FFmpegException('Trying to decode audio on a non-audio stream.')

        sent_result = avcodec.avcodec_send_packet(
            stream.codec_context,
            packet,
        )

        if sent_result < 0:
            buf = create_string_buffer(128)
            avutil.av_strerror(sent_result, buf, 128)
            descr = buf.value
            raise FFmpegException(f'Error occurred sending packet to decoder. {descr.decode()}')

        receive_result = avcodec.avcodec_receive_frame(
            stream.codec_context,
            stream.frame,
        )

        if receive_result < 0:
            buf = create_string_buffer(128)
            avutil.av_strerror(receive_result, buf, 128)
            descr = buf.value
            raise FFmpegException(f'Error occurred receiving frame. {descr.decode()}')

        plane_size = c_int(0)

        if avformat_version >= 61:
            channel_count = stream.codec_context.contents.ch_layout.nb_channels
        else:
            channel_count = stream.codec_context.contents.channels

        data_size = avutil.av_samples_get_buffer_size(
            byref(plane_size),
            channel_count,
            stream.frame.contents.nb_samples,
            stream.codec_context.contents.sample_fmt,
            1)

        if data_size < 0:
            raise FFmpegException('Error in av_samples_get_buffer_size')
        if len(self._audio_buffer) < data_size:
            raise FFmpegException('Output audio buffer is too small for current audio frame!')

        nb_samples = stream.frame.contents.nb_samples
        sample_rate = stream.codec_context.contents.sample_rate
        bytes_per_sample = avutil.av_get_bytes_per_sample(self.tgt_format)
        channels_out = min(2, self.audio_format.channels)

        wanted_nb_samples = nb_samples + compensation_time * sample_rate
        min_nb_samples = (nb_samples * (100 - self.SAMPLE_CORRECTION_PERCENT_MAX) / 100)
        max_nb_samples = (nb_samples * (100 + self.SAMPLE_CORRECTION_PERCENT_MAX) / 100)
        wanted_nb_samples = min(max(wanted_nb_samples, min_nb_samples), max_nb_samples)
        wanted_nb_samples = int(wanted_nb_samples)

        if wanted_nb_samples != nb_samples:
            res = swresample.swr_set_compensation(
                self.audio_convert_ctx,
                (wanted_nb_samples - nb_samples),
                wanted_nb_samples,
            )

            if res < 0:
                raise FFmpegException('swr_set_compensation failed.')

        data_in = stream.frame.contents.extended_data
        p_data_out = cast(data_out, POINTER(c_uint8))

        out_samples = swresample.swr_get_out_samples(self.audio_convert_ctx, nb_samples)
        total_samples_out = swresample.swr_convert(self.audio_convert_ctx,
                                                   byref(p_data_out), out_samples,
                                                   data_in, nb_samples)
        while True:
            # We loop because there could be some more samples buffered in
            # SwrContext. We advance the pointer where we write our samples.
            offset = (total_samples_out * channels_out * bytes_per_sample)
            p_data_offset = cast(
                addressof(p_data_out.contents) + offset,
                POINTER(c_uint8),
            )

            samples_out = swresample.swr_convert(self.audio_convert_ctx,
                                                 byref(p_data_offset),
                                                 out_samples - total_samples_out, None, 0)
            if samples_out == 0:
                # No more samples. We can continue.
                break
            total_samples_out += samples_out

        size_out = (total_samples_out * channels_out * bytes_per_sample)

        return size_out

    def _decode_video_packet(self, video_packet: VideoPacket) -> None:
        # # Some timing and profiling
        # pr = cProfile.Profile()
        # pr.enable()
        # clock = pyglet.clock.get_default()
        # t0 = clock.time()

        width = self.video_format.width
        height = self.video_format.height
        pitch = width * 4
        # https://ffmpeg.org/doxygen/3.3/group__lavc__decoding.html#ga8f5b632a03ce83ac8e025894b1fc307a
        nbytes = (pitch * height + FF_INPUT_BUFFER_PADDING_SIZE)
        buffer = (c_uint8 * nbytes)()
        try:
            result = self._ffmpeg_decode_video(video_packet.packet, buffer)
        except FFmpegException:
            image_data = None
        else:
            image_data = image.ImageData(width, height, 'RGBA', buffer, pitch)
            timestamp = ffmpeg_get_frame_ts(self._video_stream)
            timestamp = timestamp_from_ffmpeg(timestamp)
            video_packet.timestamp = timestamp - self.start_time

        video_packet.image = image_data

        if _debug:
            print('Decoding video packet at timestamp', video_packet, video_packet.timestamp)

            # t2 = clock.time()
            # pr.disable()
            # print("Time in _decode_video_packet: {:.4f} s for timestamp {} s".format(t2-t0, packet.timestamp))
            # if t2-t0 > 0.01:
            #     import pstats
            #     ps = pstats.Stats(pr).sort_stats("cumulative")
            #     ps.print_stats()

    def _ffmpeg_decode_video(self, packet: AVPacket, data_out: Array[c_uint8]) -> int:
        stream = self._video_stream
        rgba_ptrs = (POINTER(c_uint8) * 4)()
        rgba_stride = (c_int * 4)()
        width = stream.codec_context.contents.width
        height = stream.codec_context.contents.height
        if stream.type != AVMEDIA_TYPE_VIDEO:
            raise FFmpegException('Trying to decode video on a non-video stream.')

        sent_result = avcodec.avcodec_send_packet(
            stream.codec_context,
            packet,
        )

        if sent_result < 0:
            buf = create_string_buffer(128)
            avutil.av_strerror(sent_result, buf, 128)
            descr = buf.value
            raise FFmpegException(f'Video: Error occurred sending packet to decoder. {descr.decode()}')

        receive_result = avcodec.avcodec_receive_frame(
            stream.codec_context,
            stream.frame,
        )

        if receive_result < 0:
            buf = create_string_buffer(128)
            avutil.av_strerror(receive_result, buf, 128)
            descr = buf.value
            raise FFmpegException(f'Video: Error occurred receiving frame. {descr.decode()}')

        avutil.av_image_fill_arrays(rgba_ptrs, rgba_stride, data_out,
                                    AV_PIX_FMT_RGBA, width, height, 1)

        self.img_convert_ctx = swscale.sws_getCachedContext(
            self.img_convert_ctx,
            width, height, stream.codec_context.contents.pix_fmt,
            width, height, AV_PIX_FMT_RGBA,
            SWS_FAST_BILINEAR, None, None, None)

        swscale.sws_scale(self.img_convert_ctx,
                          cast(stream.frame.contents.data,
                               POINTER(POINTER(c_uint8))),
                          stream.frame.contents.linesize,
                          0,
                          height,
                          rgba_ptrs,
                          rgba_stride)
        return receive_result

    def get_next_video_timestamp(self) -> int | None:
        if not self.video_format:
            return None

        ts = None

        if self.videoq:
            while True:
                # We skip video packets which are not video frames
                # This happens in mkv files for the first few frames.
                try:
                    video_packet = self.videoq.popleft()
                except IndexError:
                    break
                if video_packet.image == 0:
                    self._decode_video_packet(video_packet)
                if video_packet.image is not None:
                    ts = video_packet.timestamp
                    self.videoq.appendleft(video_packet)  # put it back
                    break
                self._get_video_packet()
        else:
            ts = None

        if _debug:
            print('Next video timestamp is', ts)
        return ts

    def get_next_video_frame(self, skip_empty_frame: bool=True) -> int | None:
        if not self.video_format:
            return None

        while True:
            # We skip video packets which are not video frames
            # This happens in mkv files for the first few frames.
            video_packet = self._get_video_packet()
            if not video_packet:
                return None
            if video_packet.image == 0:
                self._decode_video_packet(video_packet)
            if video_packet.image is not None or not skip_empty_frame:
                break

        if _debug:
            print('Returning', video_packet)

        return video_packet.image

    def _get_start_time(self) -> int:
        def streams() -> Iterator[AVStream]:
            format_context = self._file.context
            for idx in (self._video_stream_index, self._audio_stream_index):
                if idx is None:
                    continue
                stream = format_context.contents.streams[idx].contents
                yield stream

        def start_times(streams) -> Iterator[int]:
            yield 0
            for stream in streams:
                start = stream.start_time
                if start == AV_NOPTS_VALUE:
                    yield 0
                start_time = avutil.av_rescale_q(start,
                                                 stream.time_base,
                                                 AV_TIME_BASE_Q)
                start_time = timestamp_from_ffmpeg(start_time)
                yield start_time

        return max(start_times(streams()))

    @property
    def audio_format(self) -> AudioFormat:
        return self._audio_format

    @audio_format.setter
    def audio_format(self, value: AudioFormat) -> None:
        self._audio_format = value
        if value is None:
            self.audioq.clear()


ffmpeg_init()
if pyglet.options['debug_media']:
    _debug = True
else:
    _debug = False
    avutil.av_log_set_level(8)


#########################################
#   Decoder class:
#########################################

class FFmpegDecoder(MediaDecoder):

    def get_file_extensions(self) -> Sequence[str]:
        return '.mp3', '.ogg'

    def decode(self, filename: str, file: BinaryIO | None, streaming: bool=True) -> FFmpegSource | StaticSource:
        if streaming:
            return FFmpegSource(filename, file)
        else:
            return StaticSource(FFmpegSource(filename, file))


def get_decoders() -> list[FFmpegDecoder]:
    return [FFmpegDecoder()]


def get_encoders() -> list:
    return []
