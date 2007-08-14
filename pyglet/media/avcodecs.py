#!/usr/bin/env python
# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2007 Alex Holkner
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
#  * Neither the name of the pyglet nor the names of its
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

'''Use avcodecs to decode audio and video media.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from pyglet.media import (MediaFormatException, StreamingSource, 
                          VideoFormat, AudioFormat, AudioData)
#import pyglet.lib
#av = pyglet.lib.load_library('/home/alex/projects/avcodecs/libavcodecs.so.1.0')

from pyglet import gl
from pyglet.gl import gl_info
from pyglet import image

import ctypes
av = ctypes.cdll.LoadLibrary('/home/alex/projects/avcodecs/libavcodecs.so.1')

Timestamp = ctypes.c_int64


AVCODECS_STREAM_TYPE_UNKNOWN = 0
AVCODECS_STREAM_TYPE_VIDEO = 1
AVCODECS_STREAM_TYPE_AUDIO = 2

AVCODECS_SAMPLE_FORMAT_U8 = 0
AVCODECS_SAMPLE_FORMAT_S16 = 1
AVCODECS_SAMPLE_FORMAT_S24 = 2
AVCODECS_SAMPLE_FORMAT_S32 = 3
AVCODECS_SAMPLE_FORMAT_FLOAT = 4

class AvcodecsFileInfo(ctypes.Structure):
    _fields_ = [
        ('structure_size', ctypes.c_size_t),
        ('streams', ctypes.c_int),
        ('duration', Timestamp),
        ('title', ctypes.c_char * 512),
        ('author', ctypes.c_char * 512),
        ('copyright', ctypes.c_char * 512),
        ('comment', ctypes.c_char * 512),
        ('album', ctypes.c_char * 512),
        ('year', ctypes.c_int),
        ('track', ctypes.c_int),
        ('genre', ctypes.c_char * 32),
    ]

class _AvcodecsStreamInfoVideo(ctypes.Structure):
    _fields_ = [
        ('width', ctypes.c_uint),
        ('height', ctypes.c_uint),
        ('sample_aspect_num', ctypes.c_int),
        ('sample_aspect_den', ctypes.c_int),
    ]

class _AvcodecsStreamInfoAudio(ctypes.Structure):
    _fields_ = [
        ('sample_rate', ctypes.c_uint),
        ('channels', ctypes.c_uint),
        ('sample_size', ctypes.c_uint),
        ('sample_format', ctypes.c_int),
    ]

class _AvcodecsStreamInfoUnion(ctypes.Union):
    _fields_ = [
        ('video', _AvcodecsStreamInfoVideo),
        ('audio', _AvcodecsStreamInfoAudio),
    ]

class AvcodecsStreamInfo(ctypes.Structure):
    _fields_ = [
        ('structure_size', ctypes.c_size_t),
        ('type', ctypes.c_int),
        ('u', _AvcodecsStreamInfoUnion)
    ]

class AvcodecsPacket(ctypes.Structure):
    _fields_ = [
        ('structure_size', ctypes.c_size_t),
        ('has_timestamp', ctypes.c_int),
        ('timestamp', Timestamp),
        ('stream', ctypes.c_int),
        ('data', ctypes.POINTER(ctypes.c_uint8)),
        ('size', ctypes.c_size_t),
    ]

av.avcodecs_open_filename.restype = ctypes.c_void_p
av.avcodecs_open_filename.argtypes = [ctypes.c_char_p]
av.avcodecs_seek_file.argtypes = [ctypes.c_void_p, Timestamp]
av.avcodecs_open_stream.restype = ctypes.c_void_p

av.avcodecs_read.argtypes = [ctypes.c_void_p, ctypes.POINTER(AvcodecsPacket)]
av.avcodecs_decode_audio.argtypes = [ctypes.c_void_p, 
    ctypes.c_void_p, ctypes.c_size_t,
    ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
av.avcodecs_decode_video.argtypes = [ctypes.c_void_p, 
    ctypes.c_void_p, ctypes.c_size_t,
    ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]

def get_version():
    return av.avcodecs_get_version()

class AvcodecsException(MediaFormatException):
    pass

def timestamp_from_avcodecs(timestamp):
    return float(timestamp) / 1000000

def timestamp_to_avcodecs(timestamp):
    return int(timestamp * 1000000)

class BufferedPacket(object):
    def __init__(self, packet):
        self.timestamp = packet.timestamp
        self.stream = packet.stream
        self.data = (ctypes.c_uint8 * packet.size)()
        self.size = packet.size
        ctypes.memmove(self.data, packet.data, self.size)

class AvcodecsSource(StreamingSource):
    def __init__(self, filename, file=None):
        if file is not None:
            raise NotImplementedError('TODO: Load from file stream')

        self._file = av.avcodecs_open_filename(filename)
        if not self._file:
            raise AvcodecsException('Could not open "%s"' % filename)

        self._video_stream = None
        self._audio_stream = None

        file_info = AvcodecsFileInfo()
        file_info.structure_size = ctypes.sizeof(file_info)
        av.avcodecs_file_info(self._file, ctypes.byref(file_info))
        self._duration = timestamp_from_avcodecs(file_info.duration)

        # Pick the first video and audio streams found, ignore others.
        for i in range(file_info.streams):
            stream = av.avcodecs_open_stream(self._file, i)
            if not stream:
                # Not decodable
                continue

            info = AvcodecsStreamInfo()
            info.structure_size = ctypes.sizeof(info)
            av.avcodecs_stream_info(stream, ctypes.byref(info))

            if (info.type == AVCODECS_STREAM_TYPE_VIDEO and 
                not self._video_stream):
                self.video_format = VideoFormat(
                    width=info.u.video.width,
                    height=info.u.video.height)
                if info.u.video.sample_aspect_num != 0:
                    self.video_format.sample_aspect = (
                        float(info.u.video.sample_aspect_num) /
                            info.u.video.sample_aspect_den)
                self._video_stream = stream
                self._video_stream_index = i

            elif (info.type == AVCODECS_STREAM_TYPE_AUDIO and
                  info.u.audio.sample_size in (8, 16) and
                  info.u.audio.channels in (1, 2) and 
                  not self._audio_stream):
                self.audio_format = AudioFormat(
                    channels=info.u.audio.channels,
                    sample_size=info.u.audio.sample_size,
                    sample_rate=info.u.audio.sample_rate)
                self._audio_stream = stream
                self._audio_stream_index = i
            else:
                av.avcodecs_close_stream(stream)

        self._packet = AvcodecsPacket()
        self._packet.structure_size = ctypes.sizeof(self._packet)
        self._packet.stream = -1
        self._buffered_packets = []

        self._buffer_streams = []
        if self.audio_format:
            self._audio_packet_ptr = 0
            self._audio_packet_size = 0
            self._audio_packet_timestamp = 0
            self._audio_buffer = \
                (ctypes.c_uint8 * av.avcodecs_audio_buffer_size())()
            self._buffer_streams.append(self._audio_stream_index)
            self._next_audio_data = self._get_next_audio_data()
            
        if self.video_format:
            self._buffer_streams.append(self._video_stream_index)
            self._next_video_image = None
            self._next_video_timestamp = -1
            self._force_next_video_image = True

    def __del__(self):
        try:
            if self._video_stream:
                av.avcodecs_close_stream(self._video_stream)
            if self._audio_stream:
                av.avcodecs_close_stream(self._audio_stream)
            av.avcodecs_close_file(self._file)
        except (NameError, AttributeError):
            pass

    def _seek(self, timestamp):
        av.avcodecs_seek_file(self._file, timestamp_to_avcodecs(timestamp))
        self._buffered_packets = []
        self._next_video_image = None
        self._force_next_video_image = True

    def _get_packet_for_stream(self, stream_index):
        # See if a packet has already been buffered
        for packet in self._buffered_packets:
            if packet.stream == stream_index:
                self._buffered_packets.remove(packet)
                return packet

        # Read more packets, buffering each interesting one until we get to 
        # the one we want or reach end of file.
        while True: 
            if av.avcodecs_read(self._file, self._packet) != 0:
                return None
            elif self._packet.stream == stream_index:
                return self._packet
            elif self._packet.stream in self._buffer_streams:
                self._buffered_packets.append(BufferedPacket(self._packet))

    def _get_next_audio_data(self):
        while True:
            while self._audio_packet_size > 0:
                size_out = ctypes.c_int(len(self._audio_buffer))

                used = av.avcodecs_decode_audio(self._audio_stream,
                    self._audio_packet_ptr, self._audio_packet_size,
                    self._audio_buffer, size_out)

                if used < 0:
                    self._audio_packet_size = 0
                    break

                self._audio_packet_ptr.value += used
                self._audio_packet_size -= used

                if size_out.value <= 0:
                    continue

                buffer = ctypes.string_at(self._audio_buffer, size_out)
                duration = \
                    float(len(buffer)) / self.audio_format.bytes_per_second
                timestamp = self._audio_packet_timestamp
                self._audio_packet_timestamp += duration
                return AudioData(buffer, len(buffer),
                                 timestamp, duration, False)

            packet = self._get_packet_for_stream(self._audio_stream_index)
            if not packet:
                return None

            self._audio_packet_timestamp = \
                timestamp_from_avcodecs(packet.timestamp)
            self._audio_packet_ptr = ctypes.cast(packet.data,
                                                 ctypes.c_void_p)
            self._audio_packet_size = packet.size

    def _get_audio_data(self, bytes):
        # XXX bytes currently ignored

        if not self._next_audio_data:
            return None

        audio_data = self._next_audio_data
        self._next_audio_data = self._get_next_audio_data()

        if not self._next_audio_data:
            audio_data.is_eos = True

        return audio_data

    def _init_texture(self, player):
        if not self.video_format:
            return

        width = self.video_format.width
        height = self.video_format.height
        if gl_info.have_extension('GL_ARB_texture_rectangle'):
            texture = image.Texture.create_for_size(
                gl.GL_TEXTURE_RECTANGLE_ARB, width, height,
                internalformat=gl.GL_RGB)
        else:
            texture = image.Texture.create_for_size(
                gl.GL_TEXTURE_2D, width, height, internalformat=gl.GL_RGB)
            if texture.width != width or texture.height != height:
                texture = texture.get_region(0, 0, width, height)
        player._texture = texture

        # Flip texture coords (good enough for simple apps).
        bl, br, tr, tl = player._texture.tex_coords
        player._texture.tex_coords = tl, tr, br, bl

        # XXX HACK Change texture size to account for sample aspect
        if self.video_format.sample_aspect > 1.0:
            player._texture.width *= self.video_format.sample_aspect
        elif self.video_format.sample_aspect < 1.0:
            player._texture.height /= self.video_format.sample_aspect
        print player._texture.width, player._texture.height

    def _update_texture(self, player, timestamp):
        if not self.video_format:
            return

        if self._next_video_image:
            # A frame is ready, is it time to show?
            if timestamp >= self._next_video_timestamp:
                player._texture.blit_into(self._next_video_image, 0, 0, 0)
                self._next_video_image = None
            else:
                return

        packet = self._get_packet_for_stream(self._video_stream_index)
        if not packet:
            return
        # TODO what if no timestamp?
        self._next_video_timestamp = timestamp_from_avcodecs(packet.timestamp)

        width = self.video_format.width
        height = self.video_format.height
        pitch = ctypes.c_int()
        buffer = (ctypes.c_uint8 * (width * height * 3))()
        result = av.avcodecs_decode_video(self._video_stream, 
                                          packet.data, packet.size, 
                                          buffer, pitch)
        if result < 0:
            return

        self._next_video_image = \
            image.ImageData(width, height, 'RGB', buffer, pitch.value)
        if (timestamp >= self._next_video_timestamp or
            self._force_next_video_image):
            player._texture.blit_into(self._next_video_image, 0, 0, 0)
            self._next_video_image = None
            self._force_next_video_image = False

    def _release_texture(self, player):
        if player._texture:
            player._texture.delete()
        player._texture = None

av.avcodecs_init()
