# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions 
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright 
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

"""Use ffmpeg to decode audio and video media.
"""
from __future__ import print_function
from __future__ import division
from builtins import range
from builtins import object

import struct
from ctypes import (c_int, c_uint16, c_int32, c_int64, c_uint32, c_uint64, 
    c_uint8, c_uint, c_double, c_float, c_ubyte, c_size_t, c_char, c_char_p, 
    c_void_p, addressof, byref, cast, POINTER, CFUNCTYPE, Structure, Union, 
    create_string_buffer, memmove)
from collections import deque

import pyglet
from pyglet import image
import pyglet.lib
from pyglet.media.sources.base import \
    StreamingSource, VideoFormat, AudioFormat, \
    AudioData, SourceInfo
from pyglet.media.events import MediaEvent
from pyglet.media.exceptions import MediaFormatException
from pyglet.compat import asbytes, asbytes_filename
from pyglet.media.sources.ffmpeg_lib import *

# import cProfile

class FileInfo(object):
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


class StreamVideoInfo(object):
    def __init__(self, width, height, sample_aspect_num, sample_aspect_den,
                 frame_rate_num, frame_rate_den):
        self.width = width
        self.height = height
        self.sample_aspect_num = sample_aspect_num
        self.sample_aspect_den = sample_aspect_den
        self.frame_rate_num = frame_rate_num
        self.frame_rate_den = frame_rate_den


class StreamAudioInfo(object):
    def __init__(self, sample_format, sample_rate, channels):
        self.sample_format = sample_format
        self.sample_rate = sample_rate
        self.sample_bits = None
        self.channels = channels


class FFmpegFile(Structure):
    _fields_ = [
        ('context', POINTER(AVFormatContext))
    ]


class FFmpegStream(Structure):
    _fields_ = [
        ('type', c_int32),
        ('format_context', POINTER(AVFormatContext)),
        ('codec_context', POINTER(AVCodecContext)),
        ('frame', POINTER(AVFrame)),
        ('time_base', AVRational)
    ]


class FFmpegException(MediaFormatException):
    pass


def ffmpeg_get_audio_buffer_size(audio_format):
    '''Return the audio buffer size

    Buffer size can accomodate 1 sec of audio data.
    '''
    return audio_format.bytes_per_second

def ffmpeg_init():
    '''Initialize libavformat and register all the muxers, demuxers and 
    protocols.'''
    avformat.av_register_all()

def ffmpeg_open_filename(filename):
    '''Open the media file.

    :rtype: FFmpegFile
        :return: The structure containing all the information for the media.
    '''
    file = FFmpegFile() # TODO: delete this structure and use directly AVFormatContext
    result = avformat.avformat_open_input(byref(file.context), 
                                          filename, 
                                          None, 
                                          None)
    if result != 0:
        raise FFmpegException('Error opening file ' + filename.decode("utf8"))

    result = avformat.avformat_find_stream_info(file.context, None)
    if result < 0:
        raise FFmpegException('Could not find stream info')

    return file

def ffmpeg_close_file(file):
    '''Close the media file and free resources.'''
    avformat.avformat_close_input(byref(file.context))

def ffmpeg_file_info(file):
    '''Get information on the file:

        - number of streams
        - duration
        - artist
        - album
        - date
        - track

    :rtype: FileInfo
        :return: The file info instance containing all the meta information.
    '''
    info = FileInfo()
    info.n_streams = file.context.contents.nb_streams
    info.start_time = file.context.contents.start_time
    info.duration = file.context.contents.duration

    entry = avutil.av_dict_get(file.context.contents.metadata, asbytes('title'), None, 0)
    if entry:
        info.title = entry.contents.value 

    entry = avutil.av_dict_get(file.context.contents.metadata, 
                               asbytes('artist'), 
                               None, 
                               0) \
            or \
            avutil.av_dict_get(file.context.contents.metadata, 
                               asbytes('album_artist'), 
                               None, 
                               0)
    if entry:
        info.author = entry.contents.value

    entry = avutil.av_dict_get(file.context.contents.metadata, asbytes('copyright'), None, 0)
    if entry:
        info.copyright = entry.contents.value
    
    entry = avutil.av_dict_get(file.context.contents.metadata, asbytes('comment'), None, 0)
    if entry:
        info.comment = entry.contents.value
    
    entry = avutil.av_dict_get(file.context.contents.metadata, asbytes('album'), None, 0)
    if entry:
        info.album = entry.contents.value
    
    entry = avutil.av_dict_get(file.context.contents.metadata, asbytes('date'), None, 0)
    if entry:
        info.year = int(entry.contents.value)
    
    entry = avutil.av_dict_get(file.context.contents.metadata, asbytes('track'), None, 0)
    if entry:
        info.track = entry.contents.value
    
    entry = avutil.av_dict_get(file.context.contents.metadata, asbytes('genre'), None, 0)
    if entry:
        info.genre = entry.contents.value

    return info

def ffmpeg_stream_info(file, stream_index):
    '''Open the stream 
    '''
    av_stream = file.context.contents.streams[stream_index].contents
    context = av_stream.codecpar.contents
    if context.codec_type == AVMEDIA_TYPE_VIDEO:
        frame_rate = avformat.av_guess_frame_rate(file.context, av_stream, None)
        info = StreamVideoInfo(
            context.width,
            context.height,
            context.sample_aspect_ratio.num,
            context.sample_aspect_ratio.den,
            frame_rate.num,
            frame_rate.den
            )
    elif context.codec_type == AVMEDIA_TYPE_AUDIO:
        info = StreamAudioInfo(
            context.format,
            context.sample_rate,
            context.channels
            )
        if context.format in (AV_SAMPLE_FMT_U8, AV_SAMPLE_FMT_U8P):
            info.sample_bits = 8
        elif context.format in (AV_SAMPLE_FMT_S16, AV_SAMPLE_FMT_S16P,
                                AV_SAMPLE_FMT_FLT, AV_SAMPLE_FMT_FLTP):
            info.sample_bits = 16
        elif context.format in (AV_SAMPLE_FMT_S32, FFMPEG_SAMPLE_FORMAT_S32P):
            info.sample_bits = 32
        else:
            info.sample_format = None
            info.sample_bits = None
    else:
        return None
    return info

def ffmpeg_open_stream(file, index):
    if not 0 <= index < file.context.contents.nb_streams:
        raise FFmpegException('index out of range. '
            'Only {} streams.'.format(file.context.contents.nb_streams))
    codec_context = avcodec.avcodec_alloc_context3(None)
    if not codec_context:
        raise MemoryError('Could not allocate Codec Context.')
    result = avcodec.avcodec_parameters_to_context(
        codec_context,
        file.context.contents.streams[index].contents.codecpar)
    if result < 0:
        avcodec.avcodec_free_context(byref(codec_context))
        raise FFmpegException('Could not copy the AVCodecContext.')
    codec = avcodec.avcodec_find_decoder(codec_context.contents.codec_id)
    if not codec:
        raise FFmpegException('No codec found for this media.')
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

def ffmpeg_close_stream(stream):
    if stream.frame:
        avutil.av_frame_free(byref(stream.frame))
    avcodec.avcodec_free_context(byref(stream.codec_context))

def ffmpeg_seek_file(file, timestamp,):
    flags = 0
    max_ts = file.context.contents.duration * AV_TIME_BASE
    result = avformat.avformat_seek_file(
        file.context, -1 , 0,
        timestamp, timestamp, flags
    )
    if result < 0:
        buf = create_string_buffer(128)
        avutil.av_strerror(result, buf, 128)
        descr = buf.value
        raise FFmpegException('Error occured while seeking. ' +
                              descr.decode())

def ffmpeg_read(file, packet):
    """Read from the stream a packet.

    :rtype: bool
    :return: True if the packet was correctly read. False if the end of stream
        was reached or an error occured.
    """
    avcodec.av_packet_unref(packet)
    result = avformat.av_read_frame(file.context, packet)
    if result < 0:
        return False

    return True

def ffmpeg_get_packet_pts(file, packet):
    if packet.contents.dts != AV_NOPTS_VALUE:
        pts = packet.contents.dts
    else:
        pts = 0

    timestamp = avutil.av_rescale_q(pts,
        file.context.contents.streams[packet.contents.stream_index].contents.time_base,
        AV_TIME_BASE_Q)
    return timestamp

def ffmpeg_get_frame_ts(stream):
    ts = avutil.av_frame_get_best_effort_timestamp(stream.frame)
    timestamp = avutil.av_rescale_q(ts,
        stream.time_base,
        AV_TIME_BASE_Q)
    return timestamp

def ffmpeg_init_packet():
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
    '''Return an informative version string of FFmpeg'''
    return avutil.av_version_info().decode()

def timestamp_from_ffmpeg(timestamp):
    return float(timestamp) / 1000000

def timestamp_to_ffmpeg(timestamp):
    return int(timestamp * 1000000)

class _Packet(object):
    def __init__(self, packet, timestamp):
        self.packet = AVPacket()
        ffmpeg_transfer_packet(byref(self.packet), packet)        
        self.timestamp = timestamp

    def __del__(self):
        ffmpeg_unref_packet(self.packet)


class VideoPacket(_Packet):
    _next_id = 0

    def __init__(self, packet, timestamp):
        super(VideoPacket, self).__init__(packet, timestamp)

        # Decoded image.  0 == not decoded yet; None == Error or discarded
        self.image = 0
        self.id = self._next_id
        VideoPacket._next_id += 1


class AudioPacket(_Packet):
    pass


class FFmpegSource(StreamingSource):
    # Max increase/decrease of original sample size
    SAMPLE_CORRECTION_PERCENT_MAX = 10
    
    def __init__(self, filename, file=None):
        if file is not None:
            raise NotImplementedError('Loading from file stream is not supported')

        self._file = ffmpeg_open_filename(asbytes_filename(filename))
        if not self._file:
            raise FFmpegException('Could not open "{0}"'.format(filename))

        self._video_stream = None
        self._video_stream_index = -1
        self._audio_stream = None
        self._audio_stream_index = -1
        self._audio_format = None

        self.img_convert_ctx = POINTER(SwsContext)()
        self.audio_convert_ctx = POINTER(SwrContext)()

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

            if (isinstance(info, StreamVideoInfo) and 
                self._video_stream is None):

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

            elif (isinstance(info, StreamAudioInfo) and
                  info.sample_bits in (8, 16) and
                  self._audio_stream is None):

                stream = ffmpeg_open_stream(self._file, i)

                self.audio_format = AudioFormat(
                    channels=min(2, info.channels),
                    sample_size=info.sample_bits,
                    sample_rate=info.sample_rate)
                self._audio_stream = stream
                self._audio_stream_index = i

                channel_input = avutil.av_get_default_channel_layout(info.channels)
                channels_out = min(2, info.channels)
                channel_output = avutil.av_get_default_channel_layout(channels_out)

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

                self.audio_convert_ctx = swresample.swr_alloc_set_opts(None, 
                    channel_output, self.tgt_format,  sample_rate,
                    channel_input, sample_format, sample_rate,
                    0, None)
                if (not self.audio_convert_ctx or 
                        swresample.swr_init(self.audio_convert_ctx) < 0):
                    swresample.swr_free(self.audio_convert_ctx)
                    raise FFmpegException('Cannot create sample rate converter.')

        self._packet = ffmpeg_init_packet()
        self._events = [] # They don't seem to be used!

        self.audioq = deque()        
        # Make queue big enough to accomodate 1.2 sec?
        self._max_len_audioq = 50 # Need to figure out a correct amount
        if self.audio_format:
            # Buffer 1 sec worth of audio
            self._audio_buffer = \
                (c_uint8 * ffmpeg_get_audio_buffer_size(self.audio_format))()
        
        self.videoq = deque()
        self._max_len_videoq = 50 # Need to figure out a correct amount
        
        self.start_time = self._get_start_time()
        self._duration = timestamp_from_ffmpeg(file_info.duration)
        self._duration -= self.start_time

        # Flag to determine if the _fillq method was already scheduled
        self._fillq_scheduled = False
        self.seek(0)

    def __del__(self):
        if _debug:
            print('del ffmpeg source')

        ffmpeg_free_packet(self._packet)
        if self._video_stream:
            swscale.sws_freeContext(self.img_convert_ctx)
            ffmpeg_close_stream(self._video_stream)
        if self._audio_stream:
            swresample.swr_free(self.audio_convert_ctx)
            ffmpeg_close_stream(self._audio_stream)
        ffmpeg_close_file(self._file)

    def seek(self, timestamp):
        if _debug:
            print('FFmpeg seek', timestamp)
        ffmpeg_seek_file(
            self._file, 
            timestamp_to_ffmpeg(timestamp+self.start_time)
        )
        del self._events[:]
        self._clear_video_audio_queues()
        self._fillq()

        # Consume video and audio packets until we arrive at the correct
        # timestamp location
        while True:
            if self.audio_format and self.audioq[0].timestamp < self.videoq[0].timestamp:
                if self.audioq[0].timestamp <= timestamp < self.audioq[1].timestamp:
                    break
                else:
                    self._get_audio_packet()
            else:
                if self.videoq[0].timestamp <= timestamp < self.videoq[1].timestamp:
                    break
                else:
                    self.get_next_video_frame()
            if (self.audio_format and len(self.audioq) == 1) or len(self.videoq) == 1:
                # No more packets to read.
                # The queues are only left with 1 packet each because we have
                # reached then end of the stream.
                break

    def _append_audio_data(self, audio_data):
        self.audioq.append(audio_data)
        assert len(self.audioq) <= self._max_len_audioq

    def _append_video_packet(self, video_packet):
        self.videoq.append(video_packet)
        assert len(self.videoq) <= self._max_len_audioq

    def _get_audio_packet(self):
        """Take an audio packet from the queue.

        This function will schedule its `_fillq` function to fill up
        the queues if space is available. Multiple calls to this method will
        only result in one scheduled call to `_fillq`.
        """
        audio_data = self.audioq.popleft()
        low_lvl = self._check_low_level()
        if not low_lvl and not self._fillq_scheduled:
            pyglet.clock.schedule_once(lambda dt:self._fillq(), 0)
            self._fillq_scheduled = True
        return audio_data

    def _get_video_packet(self):
        """Take a video packet from the queue.

        This function will schedule its `_fillq` function to fill up
        the queues if space is available. Multiple calls to this method will
        only result in one scheduled call to `_fillq`.
        """
        video_packet = self.videoq.popleft()
        low_lvl = self._check_low_level()
        if not low_lvl and not self._fillq_scheduled:
            pyglet.clock.schedule_once(lambda dt:self._fillq(), 0)
            self._fillq_scheduled = True
        return video_packet

    def _clear_video_audio_queues(self):
        "Empty both audio and video queues."
        self.audioq.clear()
        self.videoq.clear()

    def _fillq(self):
        "Fill up both Audio and Video queues if space is available in both"
        # We clear our flag.
        self._fillq_scheduled = False
        while (len(self.audioq) < self._max_len_audioq and
               len(self.videoq) < self._max_len_videoq):
            if self._get_packet():
                self._process_packet()
            else:
                break
            # Should maybe record that end of stream is reached in an
            # instance member.

    def _check_low_level(self):
        """Check if both audio and video queues are getting very low.

        If one of them has less than 2 elements, we fill the queue immediately
        with new packets. We don't wait for a scheduled call because we need
        them immediately.

        This would normally happens only during seek operations where we
        consume many packets to find the correct timestamp.
        """
        if len(self.audioq) < 2 or len(self.videoq) < 2:
            assert len(self.audioq) < self._max_len_audioq
            assert len(self.videoq) < self._max_len_videoq
            self._fillq()
            return True
        return False

    def _get_packet(self):
        # Read a packet into self._packet. Returns True if OK, False if no
        # more packets are in stream.
        return ffmpeg_read(self._file, self._packet)

    def _process_packet(self):
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
                print('Created and queued packet %d (%f)' % \
                    (video_packet.id, video_packet.timestamp))

            self._append_video_packet(video_packet)
            return video_packet

        elif (self.audio_format and
              self._packet.contents.stream_index == self._audio_stream_index):
            audio_packet = AudioPacket(self._packet, timestamp)
            self._append_audio_data(audio_packet)
            return audio_packet
          
    def get_audio_data(self, bytes, compensation_time=0.0):
        if self.audioq:
            audio_packet = self._get_audio_packet()
            audio_data = self._decode_audio_packet(audio_packet, compensation_time)
            audio_data_timeend = audio_data.timestamp + audio_data.duration
        else:
            audio_data = None
            audio_data_timeend = None

        if _debug:
            print('get_audio_data')

        if audio_data is None:
            if _debug:
                print('No more audio data. get_audio_data returning None')
            return None

        while self._events and self._events[0].timestamp <= audio_data_timeend:
            event = self._events.pop(0)
            if event.timestamp >= audio_data.timestamp:
                event.timestamp -= audio_data.timestamp
                audio_data.events.append(event)

        if _debug:
            print('get_audio_data returning ts {0} with events {1}'.format(
                audio_data.timestamp, audio_data.events))
            print('remaining events are', self._events)
        return audio_data

    def _decode_audio_packet(self, audio_packet, compensation_time):

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
            return AudioData(buffer, len(buffer), timestamp, duration, [])
        
        return AudioData(b"", 0, 0, 0, []) 

    def _ffmpeg_decode_audio(self, packet, data_out, compensation_time):
        stream = self._audio_stream
        data_in = packet.data
        size_in = packet.size
        if stream.type != AVMEDIA_TYPE_AUDIO:
            raise FFmpegException('Trying to decode audio on a non-audio stream.')

        got_frame = c_int(0)
        bytes_used = avcodec.avcodec_decode_audio4(
            stream.codec_context, 
            stream.frame, 
            byref(got_frame), 
            byref(packet))
        if (bytes_used < 0):
            buf = create_string_buffer(128)
            avutil.av_strerror(bytes_used, buf, 128)
            descr = buf.value
            raise FFmpegException('Error occured while decoding audio. ' +
                                  descr.decode())
        plane_size = c_int(0)
        if got_frame:
            data_size = avutil.av_samples_get_buffer_size(
                byref(plane_size),
                stream.codec_context.contents.channels,
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
                    wanted_nb_samples
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
                    POINTER(c_uint8)
                    )
                samples_out = swresample.swr_convert(self.audio_convert_ctx, 
                    byref(p_data_offset), out_samples-total_samples_out, None, 0)
                if samples_out == 0:
                    # No more samples. We can continue.
                    break
                total_samples_out += samples_out

            size_out = (total_samples_out * channels_out * bytes_per_sample)
        else:
            size_out = 0
        return size_out

    def _decode_video_packet(self, video_packet):
        # # Some timing and profiling
        # pr = cProfile.Profile()
        # pr.enable()
        # clock = pyglet.clock.get_default()
        # t0 = clock.time()

        width = self.video_format.width
        height = self.video_format.height
        pitch = width * 3
        buffer = (c_uint8 * (pitch * height))()
        try:
            result = self._ffmpeg_decode_video(video_packet.packet,
                                               buffer)
        except FFmpegException:
            image_data = None
        else:
            image_data = image.ImageData(width, height, 'RGB', buffer, pitch)
            timestamp = ffmpeg_get_frame_ts(self._video_stream)            
            timestamp = timestamp_from_ffmpeg(timestamp)
            video_packet.timestamp = timestamp - self.start_time
            
        video_packet.image = image_data

        if _debug:
            print('Decoding video packet at timestamp', video_packet.timestamp)

        # t2 = clock.time()
        # pr.disable()
        # print("Time in _decode_video_packet: {:.4f} s for timestamp {} s".format(t2-t0, packet.timestamp))
        # if t2-t0 > 0.01:
        #     import pstats
        #     ps = pstats.Stats(pr).sort_stats("cumulative")
        #     ps.print_stats()

    def _ffmpeg_decode_video(self, packet, data_out):
        stream = self._video_stream
        picture_rgb = AVPicture()
        width = stream.codec_context.contents.width
        height = stream.codec_context.contents.height
        if stream.type != AVMEDIA_TYPE_VIDEO:
            raise FFmpegException('Trying to decode video on a non-video stream.')
        
        got_picture = c_int(0)
        bytes_used = avcodec.avcodec_decode_video2(
            stream.codec_context, 
            stream.frame, 
            byref(got_picture), 
            byref(packet))
        if bytes_used < 0:
            raise FFmpegException('Error decoding a video packet.')
        if not got_picture:
            raise FFmpegException('No frame could be decompressed')
        
        avcodec.avpicture_fill(byref(picture_rgb), data_out, AV_PIX_FMT_RGB24,
            width, height)
        
        self.img_convert_ctx = swscale.sws_getCachedContext(
            self.img_convert_ctx,
            width, height, stream.codec_context.contents.pix_fmt,
            width, height, AV_PIX_FMT_RGB24, 
            SWS_FAST_BILINEAR, None, None, None)

        swscale.sws_scale(self.img_convert_ctx, 
                          cast(stream.frame.contents.data, 
                                      POINTER(POINTER(c_uint8))), 
                          stream.frame.contents.linesize,
                          0, 
                          height, 
                          picture_rgb.data, 
                          picture_rgb.linesize)
        return bytes_used

    def get_next_video_timestamp(self):
        if not self.video_format:
            return

        if self.videoq:
            while True:
                # We skip video packets which are not video frames
                # This happens in mkv files for the first few frames.
                video_packet = self.videoq[0]
                if video_packet.image == 0:
                    self._decode_video_packet(video_packet)
                if video_packet.image is not None:
                    break
                self._get_video_packet()

            ts = video_packet.timestamp
        else:
            ts = None

        if _debug:
            print('Next video timestamp is', ts)
        return ts

    def get_next_video_frame(self):
        if not self.video_format:
            return

        while True:
            # We skip video packets which are not video frames
            # This happens in mkv files for the first few frames.
            video_packet = self._get_video_packet()
            if video_packet.image == 0:
                self._decode_video_packet(video_packet)
            if video_packet.image is not None:
                    break

        if _debug:
            print('Returning', video_packet)

        return video_packet.image

    def _get_start_time(self):
        def streams():
            format_context = self._file.context
            for idx in (self._video_stream_index, self._audio_stream_index):
                if idx is None:
                    continue
                stream = format_context.contents.streams[idx].contents
                yield stream
        
        def start_times(streams):
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
    def audio_format(self):
        return self._audio_format

    @audio_format.setter
    def audio_format(self, value):
        self._audio_format = value
        if value is None:
            self.audioq.clear()


ffmpeg_init()
if pyglet.options['debug_media']:
    _debug = True
else:
    _debug = False



