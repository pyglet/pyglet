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

class VideoPacket(object):
    _next_id = 0

    def __init__(self, packet):
        self.timestamp = timestamp_from_ffmpeg(packet.timestamp)
        self.data = (ctypes.c_uint8 * packet.size)()
        self.size = packet.size
        ctypes.memmove(self.data, packet.data, self.size)

        # Decoded image.  0 == not decoded yet; None == Error or discarded
        self.image = 0

        self.id = self._next_id
        self.__class__._next_id += 1

class FFmpegSource(StreamingSource):
    def __init__(self, filename, file=None):
        if file is not None:
            raise NotImplementedError('Loading from file stream is not supported')

        self._file = av.ffmpeg_open_filename(asbytes_filename(filename))
        if not self._file:
            raise FFmpegException('Could not open "%s"' % filename)

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
                not self._video_stream):

                stream = av.ffmpeg_open_stream(self._file, i)
                if not stream:
                    continue

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
                  not self._audio_stream):

                stream = av.ffmpeg_open_stream(self._file, i)
                if not stream:
                    continue

                self.audio_format = AudioFormat(
                    channels=min(2, info.u.audio.channels),
                    sample_size=info.u.audio.sample_bits,
                    sample_rate=info.u.audio.sample_rate)
                self._audio_stream = stream
                self._audio_stream_index = i

        self._packet = FFmpegPacket()
        self._packet.stream_index = -1

        self._events = [] # They don't seem to be used!

        # Timestamp of last video packet added to decoder queue.
        self._video_timestamp = 0
        self._buffered_audio_data = deque()
        if self.audio_format:
            self._audio_buffer = \
                (ctypes.c_uint8 * av.ffmpeg_get_audio_buffer_size())()
        
        if self.video_format:
            self._video_packets = deque()
            # self._decode_thread = WorkerThread()
            # self._decode_thread.start()
            self._condition = threading.Condition()

    def __del__(self):
        if _debug:
            print('del ffmpeg source')
        try:
            if self._video_stream:
                av.ffmpeg_close_stream(self._video_stream)
            if self._audio_stream:
                av.ffmpeg_close_stream(self._audio_stream)
            av.ffmpeg_close_file(self._file)
        except:
            pass

    def delete(self):
        # if self.video_format:
        #     self._decode_thread.stop()
        pass

    def seek(self, timestamp):
        if _debug:
            print('FFmpeg seek', timestamp)
        
        av.ffmpeg_seek_file(self._file, timestamp_to_ffmpeg(timestamp))

        self._audio_packet_size = 0
        del self._events[:]
        self._buffered_audio_data.clear()


        if self.video_format:
            self._video_timestamp = 0
            with self._condition:
                for packet in self._video_packets:
                    packet.image = None
                self._condition.notify()
            self._video_packets.clear()
            # self._decode_thread.clear_jobs()

    def _get_packet(self):
        # Read a packet into self._packet.  Returns True if OK, False if no
        # more packets are in stream.
        return av.ffmpeg_read(self._file, self._packet) == FFMPEG_RESULT_OK

    def _process_packet(self, compensation_time=0.0):
        # Returns (packet_type, packet), where packet_type = 'video' or
        # 'audio'; and packet is VideoPacket or AudioData.  In either case,
        # packet is buffered or queued for decoding; no further action is
        # necessary.  Returns (None, None) if packet was neither type.
        if self._packet.stream_index == self._video_stream_index:
            if self._packet.timestamp < 0:
                # XXX TODO
                # FFmpeg needs hack to decode timestamp for B frames in
                # some containers (OGG?).  See
                # http://www.dranger.com/ffmpeg/tutorial05.html
                # For now we just drop these frames.
                return None, None

            video_packet = VideoPacket(self._packet)

            if _debug:
                print('Created and queued frame %d (%f)' % \
                    (video_packet.id, video_packet.timestamp))

            self._video_timestamp = max(self._video_timestamp,
                                        video_packet.timestamp)
            self._video_packets.append(video_packet)
            return 'video', video_packet

        elif self._packet.stream_index == self._audio_stream_index:
            audio_data = self._decode_audio_packet(compensation_time)
            if audio_data:
                if _debug:
                    print('Got an audio packet at', audio_data.timestamp)
                self._buffered_audio_data.append(audio_data)
                return 'audio', audio_data

        return None, None

    def get_audio_data(self, bytes, compensation_time=0.0):
        try:
            audio_data = self._buffered_audio_data.popleft()
            audio_data_timeend = audio_data.timestamp + audio_data.duration
        except IndexError:
            audio_data = None
            audio_data_timeend = self._video_timestamp + 1

        if _debug:
            print('get_audio_data')

        # Keep reading packets until we have an audio packet and all the
        # associated video packets have been enqueued on the decoder thread.
        while not audio_data or (
            self._video_stream and self._video_timestamp < audio_data_timeend):
            if not self._get_packet():
                break

            packet_type, packet = self._process_packet(compensation_time)

            if not audio_data and packet_type == 'audio':
                audio_data = self._buffered_audio_data.popleft()
                if _debug:
                    print('Got requested audio packet at', audio_data.timestamp)
                audio_data_timeend = audio_data.timestamp + audio_data.duration

        if not audio_data:
            if _debug:
                print('get_audio_data returning None')
            return None

        while self._events and self._events[0].timestamp <= audio_data_timeend:
            event = self._events.pop(0)
            if event.timestamp >= audio_data.timestamp:
                event.timestamp -= audio_data.timestamp
                audio_data.events.append(event)

        if _debug:
            print('get_audio_data returning ts %f with events' % \
                audio_data.timestamp, audio_data.events)
            print('remaining events are', self._events)
        return audio_data

    def _decode_audio_packet(self, compensation_time):
        packet = self._packet
        size_out = ctypes.c_int(len(self._audio_buffer))

        while True:
            audio_packet_ptr = ctypes.cast(packet.data, ctypes.c_void_p)
            audio_packet_size = packet.size

            try:
                used = av.ffmpeg_decode_audio(self._audio_stream,
                                    audio_packet_ptr, audio_packet_size,
                                    self._audio_buffer, size_out,
                                    compensation_time)
            except FFmpegException:
                self._audio_packet_size = 0
                break

            audio_packet_ptr.value += used
            audio_packet_size -= used

            if size_out.value <= 0:
                break

            # XXX how did this ever work?  replaced with copy below
            # buffer = ctypes.string_at(self._audio_buffer, size_out)

            # XXX to actually copy the data.. but it never used to crash, so
            # maybe I'm  missing something
            
            buffer = ctypes.create_string_buffer(size_out.value)
            ctypes.memmove(buffer, self._audio_buffer, len(buffer))
            buffer = buffer.raw

            duration = float(len(buffer)) / self.audio_format.bytes_per_second
            self._audio_packet_timestamp = \
                timestamp = timestamp_from_ffmpeg(packet.timestamp)
            return AudioData(buffer, len(buffer), timestamp, duration, []) 

    def _decode_video_packet(self, packet):
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
                                           packet.data, packet.size, 
                                           buffer)
        except FFmpegException:
            image_data = None
        else:
            image_data = image.ImageData(width, height, 'RGB', buffer, pitch)
            
        packet.image = image_data

        if _debug:
            print('Decoding video packet at timestamp', packet.timestamp)

        # t2 = clock.time()
        # pr.disable()
        # print("Time in _decode_video_packet: {:.4f} s for timestamp {} s".format(t2-t0, packet.timestamp))
        # if t2-t0 > 0.01:
        #     import pstats
        #     ps = pstats.Stats(pr).sort_stats("cumulative")
        #     ps.print_stats()

    def _ensure_video_packets(self):
        """Process packets until a video packet has been queued (and begun
        decoding).  Return False if EOS.
        """
        if not self._video_packets:
            if _debug:
                print('No video packets...')
            # Read ahead until we have another video packet but quit reading
            # after 15 frames, in case there is no more video packets
            for i in range(15):
                if not self._get_packet():
                    return False
                packet_type, _ = self._process_packet()
                if packet_type and packet_type == 'video':
                    break
            if packet_type is None or packet_type == 'audio':
                return False

            if _debug:
                print('Queued packet', _)
        return True

    def get_next_video_timestamp(self):
        if not self.video_format:
            return

        if self._ensure_video_packets():
            if _debug:
                print('Next video timestamp is', self._video_packets[0].timestamp)
            return self._video_packets[0].timestamp

    def get_next_video_frame(self):
        if not self.video_format:
            return

        if self._ensure_video_packets():
            packet = self._video_packets.popleft()
            if _debug:
                print('Waiting for', packet)

            self._decode_video_packet(packet)

            if _debug:
                print('Returning', packet)
            return packet.image

av.ffmpeg_init()
if pyglet.options['debug_media']:
    _debug = True
else:
    _debug = False
