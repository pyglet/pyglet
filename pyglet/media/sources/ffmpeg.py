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
import ctypes
import threading
import time
from collections import deque

import pyglet
from pyglet import image
import pyglet.lib
from pyglet.media.sources.base import \
    StreamingSource, VideoFormat, AudioFormat, \
    AudioData, SourceInfo
from pyglet.media.events import MediaEvent
from pyglet.media.exceptions import MediaFormatException
from pyglet.media.threads import WorkerThread
from pyglet.compat import asbytes, asbytes_filename

from pyglet.media.sources import av
from pyglet.media.sources.av import (
    FFmpegException,
    FFMPEG_STREAM_TYPE_UNKNOWN,
    FFMPEG_STREAM_TYPE_VIDEO,
    FFMPEG_STREAM_TYPE_AUDIO,
    FFmpegPacket,
    FFMPEG_RESULT_OK,
    FFMPEG_RESULT_ERROR
    )

# import cProfile

if False:
    # XXX lock all ffmpeg calls.  not clear from ffmpeg documentation if this
    # is necessary.  leaving it on while debugging to rule out the possiblity
    # of a problem.
    def synchronize(func, lock):
        def f(*args):
            with lock:
                result = func(*args)
            return result
        return f 

    _ffmpeg_lock = threading.Lock()
    for name in dir(av):
        if name.startswith('ffmpeg_'):
            setattr(av, name, synchronize(getattr(av, name), _ffmpeg_lock))

def get_version():
    return av.ffmpeg_get_version()

def timestamp_from_ffmpeg(timestamp):
    return float(timestamp) / 1000000

def timestamp_to_ffmpeg(timestamp):
    return int(timestamp * 1000000)

class _Packet(object):
    def __init__(self, packet, timestamp):
        self.packet = av.AVPacket()
        av.ffmpeg_transfer_packet(ctypes.byref(self.packet), packet)        
        self.timestamp = timestamp

    def __del__(self):
        av.ffmpeg_unref_packet(self.packet)


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
    def __init__(self, filename, file=None):
        if file is not None:
            raise NotImplementedError('Loading from file stream is not supported')

        self._file = av.ffmpeg_open_filename(asbytes_filename(filename))
        if not self._file:
            raise FFmpegException('Could not open "{0}"'.format(filename))

        self._video_stream = None
        self._video_stream_index = -1
        self._audio_stream = None
        self._audio_stream_index = -1

        file_info = av.ffmpeg_file_info(self._file)
        self._duration = timestamp_from_ffmpeg(file_info.duration)

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
            info = av.ffmpeg_stream_info(self._file, i)

            if (info.type == FFMPEG_STREAM_TYPE_VIDEO and 
                self._video_stream is None):

                stream = av.ffmpeg_open_stream(self._file, i)

                self.video_format = VideoFormat(
                    width=info.u.video.width,
                    height=info.u.video.height)
                if info.u.video.sample_aspect_num != 0:
                    self.video_format.sample_aspect = (
                        float(info.u.video.sample_aspect_num) /
                            info.u.video.sample_aspect_den)
                self.video_format.frame_rate = (
                    float(info.u.video.frame_rate_num) / 
                        info.u.video.frame_rate_den)
                self._video_stream = stream
                self._video_stream_index = i

            elif (info.type == FFMPEG_STREAM_TYPE_AUDIO and
                  info.u.audio.sample_bits in (8, 16) and
                  self._audio_stream is None):

                stream = av.ffmpeg_open_stream(self._file, i)

                self.audio_format = AudioFormat(
                    channels=min(2, info.u.audio.channels),
                    sample_size=info.u.audio.sample_bits,
                    sample_rate=info.u.audio.sample_rate)
                self._audio_stream = stream
                self._audio_stream_index = i

        self._packet = av.ffmpeg_init_packet()
        self._events = [] # They don't seem to be used!

        if self.audio_format:
            self.audioq = deque()        
            # Make queue big enough to accomodate 1.2 sec?
            self._max_len_audioq = 50 # Need to figure out a correct amount
            # Buffer 1 sec worth of audio
            self._audio_buffer = \
                (ctypes.c_uint8 * av.ffmpeg_get_audio_buffer_size(self.audio_format))()
        
        if self.video_format:
            self.videoq = deque()
            self._max_len_videoq = 50 # Need to figure out a correct amount
        
        # Flag to determine if the _fillq method was already scheduled
        self._fillq_scheduled = False
        self._fillq()

    def __del__(self):
        if _debug:
            print('del ffmpeg source')

        av.ffmpeg_free_packet(self._packet)
        if self._video_stream:
            av.ffmpeg_close_stream(self._video_stream)
        if self._audio_stream:
            av.ffmpeg_close_stream(self._audio_stream)
        av.ffmpeg_close_file(self._file)

    def seek(self, timestamp):
        if _debug:
            print('FFmpeg seek', timestamp)
        
        av.ffmpeg_seek_file(self._file, timestamp_to_ffmpeg(timestamp))
        del self._events[:]
        self._clear_video_audio_queues()
        self._fillq()
        # Consume video and audio packets until we arrive at the correct
        # timestamp location
        while True:
            if self.audioq[0].timestamp < self.videoq[0].timestamp:
                if self.audioq[0].timestamp <= timestamp < self.audioq[1].timestamp:
                    break
                else:
                    self._get_audio_packet()
            else:
                if self.videoq[0].timestamp <= timestamp < self.videoq[1].timestamp:
                    break
                else:
                    self.get_next_video_frame()
            if len(self.audioq) == 1 or len(self.videoq) == 1:
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
        """Take an video packet from the queue.

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
            assert len(self.videoq) < self._max_len_audioq
            self._fillq()
            return True
        return False

    def _get_packet(self):
        # Read a packet into self._packet. Returns True if OK, False if no
        # more packets are in stream.
        return av.ffmpeg_read(self._file, self._packet) == FFMPEG_RESULT_OK

    def _process_packet(self):
        """Process the packet that has been just read.

        Determines whether it's a video or audio packet and queue it in the
        appropriate queue.
        """
        timestamp = av.ffmpeg_get_packet_pts(self._file, self._packet)
        timestamp = timestamp_from_ffmpeg(timestamp)

        if self._packet.contents.stream_index == self._video_stream_index:
            video_packet = VideoPacket(self._packet, timestamp)

            if _debug:
                print('Created and queued packet %d (%f)' % \
                    (video_packet.id, video_packet.timestamp))

            self._append_video_packet(video_packet)
            return video_packet

        elif self._packet.contents.stream_index == self._audio_stream_index:
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
        size_out = ctypes.c_int(len(self._audio_buffer))

        while True:
            try:
                used = av.ffmpeg_decode_audio(self._audio_stream,
                                    audio_packet.packet,
                                    self._audio_buffer, size_out,
                                    compensation_time)
            except FFmpegException:
                break

            if size_out.value <= 0:
                break
            
            buffer = ctypes.create_string_buffer(size_out.value)
            ctypes.memmove(buffer, self._audio_buffer, len(buffer))
            buffer = buffer.raw

            duration = float(len(buffer)) / self.audio_format.bytes_per_second
            timestamp = av.ffmpeg_get_frame_ts(self._audio_stream)
            timestamp = timestamp_from_ffmpeg(timestamp)
            return AudioData(buffer, len(buffer), timestamp, duration, [])
        
        return AudioData(b"", 0, 0, 0, []) 

    def _decode_video_packet(self, video_packet):
        # # Some timing and profiling
        # pr = cProfile.Profile()
        # pr.enable()
        # clock = pyglet.clock.get_default()
        # t0 = clock.time()

        width = self.video_format.width
        height = self.video_format.height
        pitch = width * 3
        buffer = (ctypes.c_uint8 * (pitch * height))()
        try:
            result = av.ffmpeg_decode_video(self._video_stream, 
                                           video_packet.packet,
                                           # packet.data, packet.size, 
                                           buffer)
        except FFmpegException:
            image_data = None
        else:
            image_data = image.ImageData(width, height, 'RGB', buffer, pitch)
            timestamp = av.ffmpeg_get_frame_ts(self._video_stream)            
            video_packet.timestamp = timestamp_from_ffmpeg(timestamp)
            
        video_packet.image = image_data

        if _debug:
            print('Decoding video packet at timestamp', packet.timestamp)

        # t2 = clock.time()
        # pr.disable()
        # print("Time in _decode_video_packet: {:.4f} s for timestamp {} s".format(t2-t0, packet.timestamp))
        # if t2-t0 > 0.01:
        #     import pstats
        #     ps = pstats.Stats(pr).sort_stats("cumulative")
        #     ps.print_stats()

    def get_next_video_timestamp(self):
        if not self.video_format:
            return

        if self.videoq:
            video_packet = self.videoq[0]
            if video_packet.image == 0:
                self._decode_video_packet(video_packet)    
            ts = video_packet.timestamp
        else:
            ts = None

        if _debug:
            print('Next video timestamp is', ts)
        return ts

    def get_next_video_frame(self):
        if not self.video_format:
            return

        video_packet = self._get_video_packet()
        if video_packet.image == 0:
            self._decode_video_packet(video_packet)

        if _debug:
            print('Returning', video_packet)

        return video_packet.image

av.ffmpeg_init()
if pyglet.options['debug_media']:
    _debug = True
else:
    _debug = False
