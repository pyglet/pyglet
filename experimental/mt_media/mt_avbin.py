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

'''Use avbin to decode audio and video media.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: avbin.py 2084 2008-05-27 12:42:19Z Alex.Holkner $'

import Queue
import threading
import time

from mt_media import (MediaFormatException, StreamingSource,
                      VideoFormat, AudioFormat, AudioData, MediaEvent,
                      WorkerThread)

import pyglet
from pyglet import gl
from pyglet.gl import gl_info
from pyglet import image
import pyglet.lib

import ctypes

av = pyglet.lib.load_library('avbin', 
                             darwin='/usr/local/lib/libavbin.dylib')

AVBIN_RESULT_ERROR = -1
AVBIN_RESULT_OK = 0
AVbinResult = ctypes.c_int

AVBIN_STREAM_TYPE_UNKNOWN = 0
AVBIN_STREAM_TYPE_VIDEO = 1
AVBIN_STREAM_TYPE_AUDIO = 2
AVbinStreamType = ctypes.c_int

AVBIN_SAMPLE_FORMAT_U8 = 0
AVBIN_SAMPLE_FORMAT_S16 = 1
AVBIN_SAMPLE_FORMAT_S24 = 2
AVBIN_SAMPLE_FORMAT_S32 = 3
AVBIN_SAMPLE_FORMAT_FLOAT = 4
AVbinSampleFormat = ctypes.c_int

AVBIN_LOG_QUIET = -8
AVBIN_LOG_PANIC = 0
AVBIN_LOG_FATAL = 8
AVBIN_LOG_ERROR = 16
AVBIN_LOG_WARNING = 24
AVBIN_LOG_INFO = 32
AVBIN_LOG_VERBOSE = 40
AVBIN_LOG_DEBUG = 48
AVbinLogLevel = ctypes.c_int

AVbinFileP = ctypes.c_void_p
AVbinStreamP = ctypes.c_void_p

Timestamp = ctypes.c_int64

class AVbinFileInfo(ctypes.Structure):
    _fields_ = [
        ('structure_size', ctypes.c_size_t),
        ('n_streams', ctypes.c_int),
        ('start_time', Timestamp),
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

class _AVbinStreamInfoVideo(ctypes.Structure):
    _fields_ = [
        ('width', ctypes.c_uint),
        ('height', ctypes.c_uint),
        ('sample_aspect_num', ctypes.c_int),
        ('sample_aspect_den', ctypes.c_int),
    ]

class _AVbinStreamInfoAudio(ctypes.Structure):
    _fields_ = [
        ('sample_format', ctypes.c_int),
        ('sample_rate', ctypes.c_uint),
        ('sample_bits', ctypes.c_uint),
        ('channels', ctypes.c_uint),
    ]

class _AVbinStreamInfoUnion(ctypes.Union):
    _fields_ = [
        ('video', _AVbinStreamInfoVideo),
        ('audio', _AVbinStreamInfoAudio),
    ]

class AVbinStreamInfo(ctypes.Structure):
    _fields_ = [
        ('structure_size', ctypes.c_size_t),
        ('type', ctypes.c_int),
        ('u', _AVbinStreamInfoUnion)
    ]

class AVbinPacket(ctypes.Structure):
    _fields_ = [
        ('structure_size', ctypes.c_size_t),
        ('timestamp', Timestamp),
        ('stream_index', ctypes.c_int),
        ('data', ctypes.POINTER(ctypes.c_uint8)),
        ('size', ctypes.c_size_t),
    ]

AVbinLogCallback = ctypes.CFUNCTYPE(None,
    ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p)

av.avbin_get_version.restype = ctypes.c_int
av.avbin_get_ffmpeg_revision.restype = ctypes.c_int
av.avbin_get_audio_buffer_size.restype = ctypes.c_size_t
av.avbin_have_feature.restype = ctypes.c_int
av.avbin_have_feature.argtypes = [ctypes.c_char_p]

av.avbin_init.restype = AVbinResult
av.avbin_set_log_level.restype = AVbinResult
av.avbin_set_log_level.argtypes = [AVbinLogLevel]
av.avbin_set_log_callback.argtypes = [AVbinLogCallback]

av.avbin_open_filename.restype = AVbinFileP
av.avbin_open_filename.argtypes = [ctypes.c_char_p]
av.avbin_close_file.argtypes = [AVbinFileP]
av.avbin_seek_file.argtypes = [AVbinFileP, Timestamp]
av.avbin_file_info.argtypes = [AVbinFileP, ctypes.POINTER(AVbinFileInfo)]
av.avbin_stream_info.argtypes = [AVbinFileP, ctypes.c_int,
                                 ctypes.POINTER(AVbinStreamInfo)]

av.avbin_open_stream.restype = ctypes.c_void_p
av.avbin_open_stream.argtypes = [AVbinFileP, ctypes.c_int]
av.avbin_close_stream.argtypes = [AVbinStreamP]

av.avbin_read.argtypes = [AVbinFileP, ctypes.POINTER(AVbinPacket)]
av.avbin_read.restype = AVbinResult
av.avbin_decode_audio.restype = ctypes.c_int
av.avbin_decode_audio.argtypes = [AVbinStreamP, 
    ctypes.c_void_p, ctypes.c_size_t,
    ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
av.avbin_decode_video.restype = ctypes.c_int
av.avbin_decode_video.argtypes = [AVbinStreamP, 
    ctypes.c_void_p, ctypes.c_size_t,
    ctypes.c_void_p]

def get_version():
    return av.avbin_get_version()

class AVbinException(MediaFormatException):
    pass

def timestamp_from_avbin(timestamp):
    return float(timestamp) / 1000000

def timestamp_to_avbin(timestamp):
    return int(timestamp * 1000000)

class VideoPacket(object):
    _next_id = 0

    def __init__(self, packet):
        self.timestamp = timestamp_from_avbin(packet.timestamp)
        self.data = (ctypes.c_uint8 * packet.size)()
        self.size = packet.size
        ctypes.memmove(self.data, packet.data, self.size)

        self.id = self._next_id
        self.__class__._next_id += 1

class BufferedImage(object):
    def __init__(self, image, packet_id):
        self.image = image
        self.id = packet_id

    def __repr__(self):
        return 'BufferedImage(%d)' % self.id

class BufferedImageQueue(object):
    def __init__(self):
        self._queue = []
        self._condition = threading.Condition()
        self._interrupted = False

    def put(self, image):
        self._condition.acquire()
        self._queue.append(image)
        self._interrupted = False
        self._condition.notify()
        self._condition.release()

    def get(self, id):
        item = None

        self._condition.acquire()
        self._interrupted = False
        while not self._interrupted:
            if not self._queue:
                self._condition.wait()

            try:
                if self._queue[0].id == id:
                    # Matching frame at head of queue; return it
                    item = self._queue.pop(0)
                    break
                elif self._queue[0].id > id:
                    # Head of queue is beyond requested frame; requested
                    # frame must have been corrupt or missing; return None
                    break
                elif self._queue[0].id < id:
                    # Head of queue is older than requested frame; throw
                    # it away and keep looking
                    del self._queue[0]
            except IndexError:
                pass
        self._condition.release()

        return item

    def get_first_id(self):
        id = None

        self._condition.acquire()
        if self._queue:
            id = self._queue[0].id
        self._condition.release()
        
        return id

    def clear(self):
        self._condition.acquire()
        self._queue[:] = []
        self._interrupted = True
        self._condition.notify()
        self._condition.release()

class AVbinSource(StreamingSource):
    def __init__(self, filename, file=None):
        if file is not None:
            raise NotImplementedError('TODO: Load from file stream')

        self._file = av.avbin_open_filename(filename)
        if not self._file:
            raise AVbinException('Could not open "%s"' % filename)

        self._video_stream = None
        self._video_stream_index = -1
        self._audio_stream = None
        self._audio_stream_index = -1

        file_info = AVbinFileInfo()
        file_info.structure_size = ctypes.sizeof(file_info)
        av.avbin_file_info(self._file, ctypes.byref(file_info))
        self._duration = timestamp_from_avbin(file_info.duration)

        # Pick the first video and audio streams found, ignore others.
        for i in range(file_info.n_streams):
            info = AVbinStreamInfo()
            info.structure_size = ctypes.sizeof(info)
            av.avbin_stream_info(self._file, i, info)

            if (info.type == AVBIN_STREAM_TYPE_VIDEO and 
                not self._video_stream):

                stream = av.avbin_open_stream(self._file, i)
                if not stream:
                    continue

                self.video_format = VideoFormat(
                    width=info.u.video.width,
                    height=info.u.video.height)
                if info.u.video.sample_aspect_num != 0:
                    self.video_format.sample_aspect = (
                        float(info.u.video.sample_aspect_num) /
                            info.u.video.sample_aspect_den)
                self._video_stream = stream
                self._video_stream_index = i

            elif (info.type == AVBIN_STREAM_TYPE_AUDIO and
                  info.u.audio.sample_bits in (8, 16) and
                  info.u.audio.channels in (1, 2) and 
                  not self._audio_stream):

                stream = av.avbin_open_stream(self._file, i)
                if not stream:
                    continue

                self.audio_format = AudioFormat(
                    channels=info.u.audio.channels,
                    sample_size=info.u.audio.sample_bits,
                    sample_rate=info.u.audio.sample_rate)
                self._audio_stream = stream
                self._audio_stream_index = i

        self._packet = AVbinPacket()
        self._packet.structure_size = ctypes.sizeof(self._packet)
        self._packet.stream_index = -1

        self._events = []
        self._video_images = BufferedImageQueue()

        # Timestamp of last video packet added to decoder queue.
        self._video_timestamp = 0

        if self.audio_format:
            self._audio_buffer = \
                (ctypes.c_uint8 * av.avbin_get_audio_buffer_size())()
            self._buffered_audio_data = []
            
        if self.video_format:
            self._decode_thread = WorkerThread()
            self._decode_thread.start()
            self._requested_video_frame_id = -1
            self._lock = threading.Lock()

    def __del__(self):
        if _debug:
            print 'del avbin source'
        try:
            if self._video_stream:
                av.avbin_close_stream(self._video_stream)
            if self._audio_stream:
                av.avbin_close_stream(self._audio_stream)
            av.avbin_close_file(self._file)
        except:
            pass

    # XXX TODO call this / add to source api
    def delete(self):
        if self.video_format:
            self._decode_thread.stop()

    def seek(self, timestamp):
        if _debug:
            print 'AVbin seek', timestamp
        av.avbin_seek_file(self._file, timestamp_to_avbin(timestamp))

        self._audio_packet_size = 0
        del self._events[:]
        del self._buffered_audio_data[:]

        if self.video_format:
            self._video_timestamp = 0
            self._video_images.clear()

            self._lock.acquire()
            self._requested_video_frame_id = -1
            self._lock.release()

            self._decode_thread.clear_jobs()

    def _queue_video_frame(self):
        # Add the next video frame to the decode queue (may return without
        # adding anything to the queue if eos)
        if _debug:
            print '_single_video_frame'
        while True:
            if not self._get_packet():
                break

            packet_type, packet = self._process_packet()
            if packet_type == 'video':
                return packet.id

    def _get_packet(self):
        # Read a packet into self._packet.  Returns True if OK, False if no
        # more packets are in stream.
        return av.avbin_read(self._file, self._packet) == AVBIN_RESULT_OK

    def _process_packet(self):
        # Returns (packet_type, packet), where packet_type = 'video' or
        # 'audio'; and packet is VideoPacket or AudioData.  In either case,
        # packet is buffered or queued for decoding; no further action is
        # necessary.  Returns (None, None) if packet was neither type.

        if self._packet.stream_index == self._video_stream_index:
            if self._packet.timestamp < 0:
                # XXX TODO
                # AVbin needs hack to decode timestamp for B frames in
                # some containers (OGG?).  See
                # http://www.dranger.com/ffmpeg/tutorial05.html
                # For now we just drop these frames.
                return None, None

            video_packet = VideoPacket(self._packet)

            if _debug:
                print 'Created and queued frame %d (%f)' % \
                    (video_packet.id, video_packet.timestamp)

            self._events.append(MediaEvent(video_packet.timestamp,
                                           'on_video_frame',
                                           video_packet.id))
            self._video_timestamp = max(self._video_timestamp,
                                        video_packet.timestamp)
            self._decode_thread.put_job(
                lambda: self._decode_video_frame(video_packet))

            return 'video', video_packet

        elif self._packet.stream_index == self._audio_stream_index:
            audio_data = self._decode_audio_packet()
            if _debug:
                print 'Got an audio packet at', audio_data.timestamp
            if audio_data:
                self._buffered_audio_data.append(audio_data)
                return 'audio', audio_data

        return None, None

    def _get_audio_data(self, bytes):
        try:
            audio_data = self._buffered_audio_data.pop(0)
            audio_data_timeend = audio_data.timestamp + audio_data.duration
        except IndexError:
            audio_data = None
            audio_data_timeend = self._video_timestamp + 1

        if _debug:
            print '_get_audio_data'

        have_video_work = False

        # Keep reading packets until we have an audio packet and all the
        # associated video packets have been enqueued on the decoder thread.
        while not audio_data or (
            self._video_stream and self._video_timestamp < audio_data_timeend):
            if not self._get_packet():
                break

            packet_type, packet = self._process_packet()

            if packet_type == 'video':
                have_video_work = True
            elif not audio_data and packet_type == 'audio':
                audio_data = self._buffered_audio_data.pop(0)
                if _debug:
                    print 'Got requested audio packet at', audio_data.timestamp
                audio_data_timeend = audio_data.timestamp + audio_data.duration

        if have_video_work:
            # Give decoder thread a chance to run before we return this audio
            # data.
            time.sleep(0)

        if not audio_data:
            if _debug:
                print '_get_audio_data returning None'
            return None

        while self._events and self._events[0].timestamp <= audio_data_timeend:
            event = self._events.pop(0)
            if event.timestamp >= audio_data.timestamp:
                event.timestamp -= audio_data.timestamp
                audio_data.events.append(event)

        if _debug:
            print '_get_audio_data returning ts %f with events' % \
                audio_data.timestamp, audio_data.events
            print 'remaining events are', self._events
        return audio_data

    def _decode_audio_packet(self):
        packet = self._packet
        size_out = ctypes.c_int(len(self._audio_buffer))

        while True:
            audio_packet_ptr = ctypes.cast(packet.data, ctypes.c_void_p)
            audio_packet_size = packet.size

            used = av.avbin_decode_audio(self._audio_stream,
                audio_packet_ptr, audio_packet_size,
                self._audio_buffer, size_out)

            if used < 0:
                self._audio_packet_size = 0
                break

            audio_packet_ptr.value += used
            audio_packet_size -= used

            if size_out.value <= 0:
                continue

            buffer = ctypes.string_at(self._audio_buffer, size_out)
            duration = float(len(buffer)) / self.audio_format.bytes_per_second
            self._audio_packet_timestamp = \
                timestamp = timestamp_from_avbin(packet.timestamp)
            return AudioData(buffer, len(buffer), timestamp, duration, []) 

    def _decode_video_packet(self, packet):
        timestamp = packet.timestamp # XXX unused

        width = self.video_format.width
        height = self.video_format.height
        pitch = width * 3
        buffer = (ctypes.c_uint8 * (pitch * height))()
        result = av.avbin_decode_video(self._video_stream, 
                                       packet.data, packet.size, 
                                       buffer)
        if result < 0:
            image_data = None
        else:
            image_data = image.ImageData(width, height, 'RGB', buffer, pitch)
            
        return BufferedImage(image_data, packet.id)

    def get_next_video_timestamp(self):
        raise TODO
        if not self.video_format:
            return

        try:
            img = self._buffered_images[0]
        except IndexError:
            img = self._next_image()
            self._buffered_images.append(img)
        
        if img:
            return img.timestamp

    def get_next_video_frame(self):
        # See caveat below regarding get_next_video_frame_id
        id = self.get_next_video_frame_id()
        return self.get_video_frame(id)

    def get_next_video_frame_id(self):
        id = self._video_images.get_first_id()
        if id is not None:
            return id

        # Nothing already decoded, let's queue something now and return the
        # id.  (Not perfect, because something might be queued... but we're
        # handling the common case -- seeking)
        id = self._queue_video_frame()
        return id

    def _decode_video_frame(self, packet):
        if _debug:
            print 'decoding video frame', packet.id

        buffered_image = self._decode_video_packet(packet)

        self._lock.acquire()
        requested_video_frame_id = self._requested_video_frame_id
        self._lock.release()

        if packet.id >= requested_video_frame_id:
            self._video_images.put(buffered_image)

        if _debug:
            print 'done decoding video frame', packet.id

    def get_video_frame(self, id):
        if _debug:
            print 'get_video_frame', id
        if not self.video_format:
            return

        if id <= self._requested_video_frame_id:
            return

        self._lock.acquire()
        self._requested_video_frame_id = id
        self._lock.release()
        buffered_image = self._video_images.get(id)
        
        if _debug:
            print 'get_video_frame(%r) -> %r' % (id, buffered_image)
        return buffered_image.image

av.avbin_init()
if pyglet.options['debug_media']:
    _debug = True
    av.avbin_set_log_level(AVBIN_LOG_DEBUG)
else:
    _debug = False
    av.avbin_set_log_level(AVBIN_LOG_QUIET)
