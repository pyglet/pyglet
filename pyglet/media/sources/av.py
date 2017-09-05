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
"""Wrap FFmpeg using ctypes and provide a similar API to FFmpeg which is now
unmaintained.
"""
from ctypes import (c_int, c_uint16, c_int32, c_int64, c_uint32, c_uint64, 
    c_uint8, c_uint, c_double, c_float, c_ubyte, c_size_t, c_char, c_char_p, 
    c_void_p, addressof, byref, cast, POINTER, CFUNCTYPE, Structure, Union, 
    create_string_buffer, memmove)

import pyglet.lib
from pyglet.media.exceptions import MediaFormatException
from pyglet.compat import asbytes
from pyglet.media.sources.ffmpeg_lib import *

FFMPEG_RESULT_ERROR = -1
FFMPEG_RESULT_OK = 0
FFmpegResult = c_int

FFMPEG_STREAM_TYPE_UNKNOWN = 0
FFMPEG_STREAM_TYPE_VIDEO = 1
FFMPEG_STREAM_TYPE_AUDIO = 2
FFmpegStreamType = c_int

FFMPEG_SAMPLE_FORMAT_U8 = 0
FFMPEG_SAMPLE_FORMAT_S16 = 1
FFMPEG_SAMPLE_FORMAT_S32 = 2
FFMPEG_SAMPLE_FORMAT_FLOAT = 3
FFMPEG_SAMPLE_FORMAT_DOUBLE = 4
FFMPEG_SAMPLE_FORMAT_U8P = 5
FFMPEG_SAMPLE_FORMAT_S16P = 6
FFMPEG_SAMPLE_FORMAT_S32P = 7
FFMPEG_SAMPLE_FORMAT_FLTP = 8
FFMPEG_SAMPLE_FORMAT_DBLP = 9
FFMPEG_SAMPLE_FORMAT_S64 = 10
FFMPEG_SAMPLE_FORMAT_S64P = 11
FFmpegSampleFormat = c_int

FFMPEG_LOG_QUIET = -8
FFMPEG_LOG_PANIC = 0
FFMPEG_LOG_FATAL = 8
FFMPEG_LOG_ERROR = 16
FFMPEG_LOG_WARNING = 24
FFMPEG_LOG_INFO = 32
FFMPEG_LOG_VERBOSE = 40
FFMPEG_LOG_DEBUG = 48
FFmpegLogLevel = c_int

FFmpegFileP = c_void_p
FFmpegStreamP = c_void_p

Timestamp = c_int64

INT64_MIN = -2**63+1
INT64_MAX = 0x7FFFFFFFFFFFFFFF

# Max increase/decrease of original sample size
SAMPLE_CORRECTION_PERCENT_MAX = 10

class FFmpegFileInfo(Structure):
    _fields_ = [
        ('n_streams', c_int),
        ('start_time', Timestamp),
        ('duration', Timestamp),
        ('title', c_char * 512),
        ('author', c_char * 512),
        ('copyright', c_char * 512),
        ('comment', c_char * 512),
        ('album', c_char * 512),
        ('year', c_int),
        ('track', c_char * 32),
        ('genre', c_char * 32),
    ]

class _FFmpegStreamInfoVideo8(Structure):
    _fields_ = [
        ('width', c_uint),
        ('height', c_uint),
        ('sample_aspect_num', c_uint),
        ('sample_aspect_den', c_uint),
        ('frame_rate_num', c_uint),
        ('frame_rate_den', c_uint),
    ]

class _FFmpegStreamInfoAudio8(Structure):
    _fields_ = [
        ('sample_format', c_int),
        ('sample_rate', c_uint),
        ('sample_bits', c_uint),
        ('channels', c_uint),
    ]

class _FFmpegStreamInfoUnion8(Union):
    _fields_ = [
        ('video', _FFmpegStreamInfoVideo8),
        ('audio', _FFmpegStreamInfoAudio8),
    ]

class FFmpegStreamInfo8(Structure):
    _fields_ = [
        ('type', c_int),
        ('u', _FFmpegStreamInfoUnion8)
    ]

class FFmpegPacket(Structure):
    _fields_ = [
        ('timestamp', Timestamp),
        ('stream_index', c_int),
        ('data', POINTER(c_uint8)),
        ('size', c_size_t),
    ]

class FFmpegFile(Structure):
    _fields_ = [
        ('context', POINTER(AVFormatContext)),
        ('packet', POINTER(AVPacket))
    ]

class FFmpegStream(Structure):
    _fields_ = [
        ('type', c_int32),
        ('format_context', POINTER(AVFormatContext)),
        ('codec_context', POINTER(AVCodecContext)),
        ('frame', POINTER(AVFrame)),
    ]


###################

class FFmpegException(MediaFormatException):
    pass

def ffmpeg_get_version():
    '''Return an informative version string of FFmpeg'''
    return avutil.av_version_info().decode()

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
    file = FFmpegFile()
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
    if file.packet:
        avcodec.av_packet_unref(file.packet)
    avformat.avformat_close_input(byref(file.context))

def ffmpeg_file_info(file):
    '''Get information on the file:

        - number of streams
        - duration
        - artist
        - album
        - date
        - track

    :rtype: FFmpegFileInfo
        :return: The structure containing all the meta information.
    '''
    info = FFmpegFileInfo()
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
    info = FFmpegStreamInfo8()
    av_stream = file.context.contents.streams[stream_index].contents
    context = av_stream.codecpar.contents
    if context.codec_type == AVMEDIA_TYPE_VIDEO:
        info.type = FFMPEG_STREAM_TYPE_VIDEO
        info.u.video.width = context.width
        info.u.video.height = context.height
        info.u.video.sample_aspect_num = context.sample_aspect_ratio.num
        info.u.video.sample_aspect_den = context.sample_aspect_ratio.den
        info.u.video.frame_rate_num = av_stream.avg_frame_rate.num
        info.u.video.frame_rate_den = av_stream.avg_frame_rate.den
    elif context.codec_type == AVMEDIA_TYPE_AUDIO:
        info.type = FFMPEG_STREAM_TYPE_AUDIO
        info.u.audio.sample_rate = context.sample_rate
        info.u.audio.channels = context.channels
        if context.format == AV_SAMPLE_FMT_U8:
            info.u.audio.sample_format = FFMPEG_SAMPLE_FORMAT_U8
            info.u.audio.sample_bits = 8
        elif context.format == AV_SAMPLE_FMT_U8P:
            info.u.audio.sample_format = FFMPEG_SAMPLE_FORMAT_U8P
            info.u.audio.sample_bits = 8
        elif context.format == AV_SAMPLE_FMT_S16:
            info.u.audio.sample_format = FFMPEG_SAMPLE_FORMAT_S16
            info.u.audio.sample_bits = 16
        elif context.format == AV_SAMPLE_FMT_S16P:
            info.u.audio.sample_format = FFMPEG_SAMPLE_FORMAT_S16P
            info.u.audio.sample_bits = 16
        elif context.format == AV_SAMPLE_FMT_S32:
            info.u.audio.sample_format = FFMPEG_SAMPLE_FORMAT_S32
            info.u.audio.sample_bits = 32
        elif context.format == AV_SAMPLE_FMT_S32P:
            info.u.audio.sample_format = FFMPEG_SAMPLE_FORMAT_S32P
            info.u.audio.sample_bits = 32
        elif context.format == AV_SAMPLE_FMT_FLT:
            info.u.audio.sample_format = FFMPEG_SAMPLE_FORMAT_FLOAT
            info.u.audio.sample_bits = 16
        elif context.format == AV_SAMPLE_FMT_FLTP:
            info.u.audio.sample_format = FFMPEG_SAMPLE_FORMAT_FLTP
            info.u.audio.sample_bits = 16
        else:
            info.u.audio.sample_format = -1
            info.u.audio.sample_bits = -1
    else:
        info.type = FFMPEG_STREAM_TYPE_UNKNOWN
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
        avcodec.avcodec_free_context(addressof(codec_context))
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

    return stream

def ffmpeg_close_stream(stream):
    if stream.frame:
        avutil.av_frame_free(addressof(stream.frame))
    avcodec.avcodec_free_context(addressof(stream.codec_context))

def ffmpeg_seek_file(file, timestamp):
    flags = AVSEEK_FLAG_BACKWARD
    max_ts = file.context.contents.duration * AV_TIME_BASE

    result = avformat.avformat_seek_file(file.context, -1, 0, timestamp, timestamp, flags)
    if result < 0:
        buf = create_string_buffer(128)
        avutil.av_strerror(result, buf, 128)
        descr = buf.value
        raise FFmpegException('Error occured while seeking. ' +
                              descr.decode())

def ffmpeg_read(file, packet):
    if file.packet:
        avcodec.av_packet_unref(file.packet) # Is it the right way to free it?
    else:
        file.packet = avcodec.av_packet_alloc()
    result = avformat.av_read_frame(file.context, file.packet)
    if result < 0:
        return FFMPEG_RESULT_ERROR
    
    if file.packet.contents.dts != AV_NOPTS_VALUE:
        pts = file.packet.contents.dts
    else:
        pts = 0

    packet.timestamp = avutil.av_rescale_q(pts,
        file.context.contents.streams[file.packet.contents.stream_index].contents.time_base,
        AV_TIME_BASE_Q)
    tb = file.context.contents.streams[file.packet.contents.stream_index].contents.time_base
    packet.stream_index = file.packet.contents.stream_index
    packet.data = file.packet.contents.data
    packet.size = file.packet.contents.size
    return FFMPEG_RESULT_OK

def ffmpeg_decode_audio(stream, data_in, size_in, data_out, size_out, compensation_time):
    if stream.type != AVMEDIA_TYPE_AUDIO:
        raise FFmpegException('Trying to decode audio on a non-audio stream.')
    inbuf = create_string_buffer(size_in + FF_INPUT_BUFFER_PADDING_SIZE)
    memmove(inbuf, data_in, size_in)
    
    packet = AVPacket()
    avcodec.av_init_packet(byref(packet))
    packet.data.contents = inbuf
    packet.size = size_in

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
        if size_out.value < data_size:
            raise FFmpegException('Output audio buffer is too small for current audio frame!')

        nb_samples = stream.frame.contents.nb_samples
        channels = stream.codec_context.contents.channels
        channel_input = avutil.av_get_default_channel_layout(channels)
        channels_out = min(2, channels)
        channel_output = avutil.av_get_default_channel_layout(channels_out)

        sample_rate = stream.codec_context.contents.sample_rate
        sample_format = stream.frame.contents.format
        if sample_format in (AV_SAMPLE_FMT_U8, AV_SAMPLE_FMT_U8P):
            tgt_format = AV_SAMPLE_FMT_U8
        elif sample_format in (AV_SAMPLE_FMT_S16, AV_SAMPLE_FMT_S16P):
            tgt_format = AV_SAMPLE_FMT_S16
        elif sample_format in (AV_SAMPLE_FMT_S32, AV_SAMPLE_FMT_S32P):
            tgt_format = AV_SAMPLE_FMT_S32
        elif sample_format in (AV_SAMPLE_FMT_FLT, AV_SAMPLE_FMT_FLTP):
            tgt_format = AV_SAMPLE_FMT_S16
        else:
            raise FFmpegException('Audio format not supported.')

        bytes_per_sample = avutil.av_get_bytes_per_sample(tgt_format)

        wanted_nb_samples = nb_samples + compensation_time * sample_rate
        min_nb_samples = (nb_samples * (100 - SAMPLE_CORRECTION_PERCENT_MAX) / 100)
        max_nb_samples = (nb_samples * (100 + SAMPLE_CORRECTION_PERCENT_MAX) / 100)
        wanted_nb_samples = min(max(wanted_nb_samples, min_nb_samples), max_nb_samples)
        wanted_nb_samples = int(wanted_nb_samples)

        swr_ctx = swresample.swr_alloc_set_opts(None, 
            channel_output, tgt_format,  sample_rate,
            channel_input, sample_format, sample_rate,
            0, None)
        if not swr_ctx or swresample.swr_init(swr_ctx) < 0:
            swresample.swr_free(swr_ctx)
            raise FFmpegException('Cannot create sample rate converter.')

        if wanted_nb_samples != nb_samples:
            res = swresample.swr_set_compensation(
                swr_ctx,
                (wanted_nb_samples - nb_samples),
                wanted_nb_samples
            )
            if res < 0:
                raise FFmpegException('swr_set_compensation failed.')

        data_in = stream.frame.contents.extended_data
        p_data_out = cast(data_out, POINTER(c_uint8))

        out_samples = swresample.swr_get_out_samples(swr_ctx, nb_samples)
        total_samples_out = swresample.swr_convert(swr_ctx, 
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
            samples_out = swresample.swr_convert(swr_ctx, 
                byref(p_data_offset), out_samples-total_samples_out, None, 0)
            if samples_out == 0:
                # No more samples. We can continue.
                break
            total_samples_out += samples_out

        size_out.value = (total_samples_out * channels_out * bytes_per_sample)
        swresample.swr_free(swr_ctx)
    else:
        size_out.value = 0
    return bytes_used



def ffmpeg_decode_video(stream, data_in, size_in, data_out):
    picture_rgb = AVPicture()
    width = stream.codec_context.contents.width
    height = stream.codec_context.contents.height
    if stream.type != AVMEDIA_TYPE_VIDEO:
        raise FFmpegException('Trying to decode video on a non-video stream.')
    inbuf = create_string_buffer(size_in + FF_INPUT_BUFFER_PADDING_SIZE)
    memmove(inbuf, data_in, size_in)
    packet = AVPacket()
    avcodec.av_init_packet(byref(packet))
    packet.data.contents = inbuf
    packet.size = size_in
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
    
    # A bit useless as it is. Should make a class with img_convert_ctx as
    # attribute. Would just need to call sws_getCachedContext on it.
    # Once instance is deleted, should call sws_freeContext
    img_convert_ctx = POINTER(SwsContext)() 
    img_convert_ctx = swscale.sws_getCachedContext(img_convert_ctx,
        width, height, stream.codec_context.contents.pix_fmt,
        width, height, AV_PIX_FMT_RGB24, SWS_FAST_BILINEAR, None, None, None)

    swscale.sws_scale(img_convert_ctx, 
                      cast(stream.frame.contents.data, 
                                  POINTER(POINTER(c_uint8))), 
                      stream.frame.contents.linesize,
                      0, 
                      height, 
                      picture_rgb.data, 
                      picture_rgb.linesize)
    swscale.sws_freeContext(img_convert_ctx)
    return bytes_used

def ffmpeg_set_log_level(dummy):
    pass
