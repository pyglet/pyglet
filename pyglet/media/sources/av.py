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
"""Wrap FFmpeg using ctypes and provide a similar API to AVbin which is now
unmaintained.
"""
from ctypes import (c_int, c_uint16, c_int32, c_int64, c_uint32, c_uint64, 
    c_uint8, c_uint, c_double, c_float, c_ubyte, c_size_t, c_char, c_char_p, 
    c_void_p, addressof, byref, cast, POINTER, CFUNCTYPE, Structure, Union, 
    create_string_buffer, memmove)

import pyglet.lib
from pyglet.media.exceptions import MediaFormatException
from pyglet.compat import asbytes
from pyglet.media.sources.ffmpeg import *

AVBIN_RESULT_ERROR = -1
AVBIN_RESULT_OK = 0
AVbinResult = c_int

AVBIN_STREAM_TYPE_UNKNOWN = 0
AVBIN_STREAM_TYPE_VIDEO = 1
AVBIN_STREAM_TYPE_AUDIO = 2
AVbinStreamType = c_int

AVBIN_SAMPLE_FORMAT_U8 = 0
AVBIN_SAMPLE_FORMAT_S16 = 1
AVBIN_SAMPLE_FORMAT_S32 = 2
AVBIN_SAMPLE_FORMAT_FLOAT = 3
AVBIN_SAMPLE_FORMAT_DOUBLE = 4
AVBIN_SAMPLE_FORMAT_U8P = 5
AVBIN_SAMPLE_FORMAT_S16P = 6
AVBIN_SAMPLE_FORMAT_S32P = 7
AVBIN_SAMPLE_FORMAT_FLTP = 8
AVBIN_SAMPLE_FORMAT_DBLP = 9
AVBIN_SAMPLE_FORMAT_S64 = 10
AVBIN_SAMPLE_FORMAT_S64P = 11
AVbinSampleFormat = c_int

AVBIN_LOG_QUIET = -8
AVBIN_LOG_PANIC = 0
AVBIN_LOG_FATAL = 8
AVBIN_LOG_ERROR = 16
AVBIN_LOG_WARNING = 24
AVBIN_LOG_INFO = 32
AVBIN_LOG_VERBOSE = 40
AVBIN_LOG_DEBUG = 48
AVbinLogLevel = c_int

AVbinFileP = c_void_p
AVbinStreamP = c_void_p

Timestamp = c_int64

INT64_MIN = -2**63+1
INT64_MAX = 0x7FFFFFFFFFFFFFFF

class AVbinFileInfo(Structure):
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

class _AVbinStreamInfoVideo8(Structure):
    _fields_ = [
        ('width', c_uint),
        ('height', c_uint),
        ('sample_aspect_num', c_uint),
        ('sample_aspect_den', c_uint),
        ('frame_rate_num', c_uint),
        ('frame_rate_den', c_uint),
    ]

class _AVbinStreamInfoAudio8(Structure):
    _fields_ = [
        ('sample_format', c_int),
        ('sample_rate', c_uint),
        ('sample_bits', c_uint),
        ('channels', c_uint),
    ]

class _AVbinStreamInfoUnion8(Union):
    _fields_ = [
        ('video', _AVbinStreamInfoVideo8),
        ('audio', _AVbinStreamInfoAudio8),
    ]

class AVbinStreamInfo8(Structure):
    _fields_ = [
        ('type', c_int),
        ('u', _AVbinStreamInfoUnion8)
    ]

class AVbinPacket(Structure):
    _fields_ = [
        ('timestamp', Timestamp),
        ('stream_index', c_int),
        ('data', POINTER(c_uint8)),
        ('size', c_size_t),
    ]

class AVbinFile(Structure):
    _fields_ = [
        ('context', POINTER(AVFormatContext)),
        ('packet', POINTER(AVPacket))
    ]

class AVbinStream(Structure):
    _fields_ = [
        ('type', c_int32),
        ('format_context', POINTER(AVFormatContext)),
        ('codec_context', POINTER(AVCodecContext)),
        ('frame', POINTER(AVFrame)),
    ]


###################

class FFmpegException(MediaFormatException):
    pass

def avbin_get_version():
    '''Return an informative version string of FFmpeg'''
    return avutil.av_version_info().decode()

def avbin_get_audio_buffer_size():
    '''Return the audio buffer size'''
    # TODO: Should be determined by code. See ffplay.c in FFmpeg to get some
    # ideas how to do that.
    return 192000

# This AVbin function seems useless to me with the current wrapping we are 
# doing. I leave it here for reference.

# def avbin_have_feature(feature):
#     if feature == 'frame_rate':
#         # See note on avbin_have_feature() in avbin.h
#         return False
#     elif feature == 'options':
#         return True
#     elif feature == 'info':
#         return True
#     return False

def avbin_init():
    '''Initialize libavformat and register all the muxers, demuxers and 
    protocols.'''
    avformat.av_register_all()

def avbin_open_filename(filename):
    '''Open the media file.

    :rtype: AVbinFile
        :return: The structure containing all the information for the media.
    '''
    file = AVbinFile()
    result = avformat.avformat_open_input(byref(file.context), 
                                          filename, 
                                          None, 
                                          None)
    if result != 0:
        raise FFmpegException('Error opening file ' + filename)

    result = avformat.avformat_find_stream_info(file.context, None)
    if result < 0:
        raise FFmpegException('Could not find stream info')

    return file

def avbin_close_file(file):
    '''Close the media file and free resources.'''
    if file.packet:
        avcodec.av_packet_unref(file.packet)
    avformat.avformat_close_input(byref(file.context))

def avbin_file_info(file):
    '''Get information on the file:

        - number of streams
        - duration
        - artist
        - album
        - date
        - track

    :rtype: AVbinFileInfo
        :return: The structure containing all the meta information.
    '''
    info = AVbinFileInfo()
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

def avbin_stream_info(file, stream_index):
    '''Open the stream 
    '''
    info = AVbinStreamInfo8()
    av_stream = file.context.contents.streams[stream_index].contents
    context = av_stream.codecpar.contents
    if context.codec_type == AVMEDIA_TYPE_VIDEO:
        info.type = AVBIN_STREAM_TYPE_VIDEO
        info.u.video.width = context.width
        info.u.video.height = context.height
        info.u.video.sample_aspect_num = context.sample_aspect_ratio.num
        info.u.video.sample_aspect_den = context.sample_aspect_ratio.den
        info.u.video.frame_rate_num = av_stream.avg_frame_rate.num
        info.u.video.frame_rate_den = av_stream.avg_frame_rate.den
    elif context.codec_type == AVMEDIA_TYPE_AUDIO:
        info.type = AVBIN_STREAM_TYPE_AUDIO
        info.u.audio.sample_rate = context.sample_rate
        info.u.audio.channels = context.channels
        if context.format == AV_SAMPLE_FMT_U8:
            info.u.audio.sample_format = AVBIN_SAMPLE_FORMAT_U8
            info.u.audio.sample_bits = 8
        elif context.format == AV_SAMPLE_FMT_U8P:
            info.u.audio.sample_format = AVBIN_SAMPLE_FORMAT_U8P
            info.u.audio.sample_bits = 8
        elif context.format == AV_SAMPLE_FMT_S16:
            info.u.audio.sample_format = AVBIN_SAMPLE_FORMAT_S16
            info.u.audio.sample_bits = 16
        elif context.format == AV_SAMPLE_FMT_S16P:
            info.u.audio.sample_format = AVBIN_SAMPLE_FORMAT_S16P
            info.u.audio.sample_bits = 16
        elif context.format == AV_SAMPLE_FMT_S32:
            info.u.audio.sample_format = AVBIN_SAMPLE_FORMAT_S32
            info.u.audio.sample_bits = 32
        elif context.format == AV_SAMPLE_FMT_S32P:
            info.u.audio.sample_format = AVBIN_SAMPLE_FORMAT_S32P
            info.u.audio.sample_bits = 32
        elif context.format == AV_SAMPLE_FMT_FLT:
            info.u.audio.sample_format = AVBIN_SAMPLE_FORMAT_FLOAT
            info.u.audio.sample_bits = 16
        elif context.format == AV_SAMPLE_FMT_FLTP:
            info.u.audio.sample_format = AVBIN_SAMPLE_FORMAT_FLTP
            info.u.audio.sample_bits = 16
        else:
            info.u.audio.sample_format = -1
            info.u.audio.sample_bits = -1
    else:
        info.type = AVBIN_STREAM_TYPE_UNKNOWN
    return info

def avbin_open_stream(file, index):
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
    stream = AVbinStream()
    stream.format_context = file.context
    stream.codec_context = codec_context
    stream.type = codec_context.contents.codec_type
    stream.frame = avutil.av_frame_alloc()

    return stream

def avbin_close_stream(stream):
    if stream.frame:
        avutil.av_frame_free(addressof(stream.frame))
    avcodec.avcodec_free_context(addressof(stream.codec_context))

def avbin_seek_file(file, timestamp):
    flags = AVSEEK_FLAG_BACKWARD
    max_ts = file.context.contents.duration * AV_TIME_BASE
    result = avformat.avformat_seek_file(file.context, -1, 0, timestamp, max_ts, flags)
    if result < 0:
        # buf = create_string_buffer(128)
        # avutil.av_strerror(result, buf, 128)
        # descr = buf.value
        # raise FFmpegException('Error occured while seeking. ' +
        #                       descr.decode())
        return AVBIN_RESULT_ERROR

    for i in range(file.context.contents.nb_streams):   
        codec_context = file.context.contents.streams[i].contents.codec
        if codec_context and codec_context.contents.codec:
            avcodec.avcodec_flush_buffers(codec_context)
    
    return AVBIN_RESULT_OK

def avbin_read(file, packet):
    if file.packet:
        avcodec.av_packet_unref(file.packet) # Is it the right way to free it?
    else:
        file.packet = avcodec.av_packet_alloc()
    result = avformat.av_read_frame(file.context, file.packet)
    if result < 0:
        return AVBIN_RESULT_ERROR
    
    packet.timestamp = avutil.av_rescale_q(file.packet.contents.dts,
        file.context.contents.streams[file.packet.contents.stream_index].contents.time_base,
        AV_TIME_BASE_Q)
    tb = file.context.contents.streams[file.packet.contents.stream_index].contents.time_base
    packet.stream_index = file.packet.contents.stream_index
    packet.data = file.packet.contents.data
    packet.size = file.packet.contents.size
    return AVBIN_RESULT_OK

def avbin_decode_audio(stream, data_in, size_in, data_out, size_out):
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
            raise FFmpegException('Audi format not supported.')

        swr_ctx = swresample.swr_alloc_set_opts(None, 
            channel_output, tgt_format,  sample_rate,
            channel_input, sample_format, sample_rate,
            0, None)
        if not swr_ctx or swresample.swr_init(swr_ctx) < 0:
            swresample.swr_free(swr_ctx)
            raise FFmpegException('Cannot create sample rate converter.')

        data_in = stream.frame.contents.extended_data
        p_data_out = cast(data_out, POINTER(c_uint8))
        len_data = swresample.swr_convert(swr_ctx, 
            byref(p_data_out), data_size, 
            data_in, stream.frame.contents.nb_samples)
        size_out.value = (len_data * 
                          channels_out * 
                          avutil.av_get_bytes_per_sample(tgt_format))
        swresample.swr_free(swr_ctx)
    else:
        size_out.value = 0
    return bytes_used



def avbin_decode_video(stream, data_in, size_in, data_out):
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

def avbin_set_log_level(dummy):
    pass
