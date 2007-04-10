#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import ctypes
import math
import sys

from pyglet.media import Sound, Medium
from pyglet.media import lib_openal as al
from pyglet.media import openal
from pyglet.window.carbon import _create_cfstring, _oscheck
from pyglet.window.carbon import carbon, quicktime
from pyglet.window.carbon.constants import _name

BUFFER_SIZE = 8192

quicktime.NewMovieFromDataRef.argtypes = (
    ctypes.POINTER(ctypes.c_void_p),
    ctypes.c_short,
    ctypes.POINTER(ctypes.c_short),
    ctypes.c_void_p,
    ctypes.c_ulong)
    
newMovieActive = 1

kQTPropertyClass_MovieAudioExtraction_Movie = _name('xmov')
kQTPropertyClass_MovieAudioExtraction_Audio = _name('xaud')
kQTMovieAudioExtractionAudioPropertyID_AudioStreamBasicDescription = \
    _name('asbd') # The longest constant name ever.


kAudioFormatFlagIsBigEndian = 1 << 1
kAudioFormatFlagIsSignedInteger = 1 << 2
kAudioFormatFlagIsPacked = 1 << 3
if sys.byteorder == 'big':
    kAudioFormatFlagsNativeEndian = kAudioFormatFlagIsBigEndian
else:
    kAudioFormatFlagsNativeEndian = 0

class AudioStreamBasicDescription(ctypes.Structure):
    _fields_ = [
        ('mSampleRate', ctypes.c_double),
        ('mFormatID', ctypes.c_uint32),
        ('mFormatFlags', ctypes.c_uint32),
        ('mBytesPerPacket', ctypes.c_uint32),
        ('mFramesPerPacket', ctypes.c_uint32),
        ('mBytesPerFrame', ctypes.c_uint32),
        ('mChannelsPerFrame', ctypes.c_uint32),
        ('mBitsPerChannel', ctypes.c_uint32),
        ('mReserved', ctypes.c_uint32),
    ]

class AudioBuffer(ctypes.Structure):
    _fields_ = [
        ('mNumberChannels', ctypes.c_uint32),
        ('mDataByteSize', ctypes.c_uint32),
        ('mData', ctypes.c_void_p),
    ]

class AudioBufferList(ctypes.Structure):
    _fields_ = [
        ('mNumberBuffers', ctypes.c_uint32),
        ('mBuffers', AudioBuffer * 1),
    ]

class ExtractionSession(object):
    def __init__(self, movie):
        self.extraction_session_ref = ctypes.c_void_p()
        result = quicktime.MovieAudioExtractionBegin(
            movie, 0, ctypes.byref(self.extraction_session_ref))
        _oscheck(result)
        

        asbd = AudioStreamBasicDescription()
        result = quicktime.MovieAudioExtractionGetProperty(
            self.extraction_session_ref,
            kQTPropertyClass_MovieAudioExtraction_Audio,
            kQTMovieAudioExtractionAudioPropertyID_AudioStreamBasicDescription,
            ctypes.sizeof(asbd), ctypes.byref(asbd), None)
        _oscheck(result)

        self.channels = asbd.mChannelsPerFrame
        self.sample_rate = asbd.mSampleRate
        
        # Always signed 16-bit interleaved
        asbd.mFormatFlags = kAudioFormatFlagIsSignedInteger | \
                            kAudioFormatFlagIsPacked | \
                            kAudioFormatFlagsNativeEndian
        asbd.mBitsPerChannel = 16
        asbd.mBytesPerFrame = 2 * asbd.mChannelsPerFrame
        asbd.mBytesPerPacket = asbd.mBytesPerFrame
        self.bytes_per_frame = asbd.mBytesPerFrame

        result = quicktime.MovieAudioExtractionSetProperty(
            self.extraction_session_ref,
            kQTPropertyClass_MovieAudioExtraction_Audio,
            kQTMovieAudioExtractionAudioPropertyID_AudioStreamBasicDescription,
            ctypes.sizeof(asbd), ctypes.byref(asbd));
        _oscheck(result)

        if self.channels == 1:
            self.format = al.AL_FORMAT_MONO16
        elif self.channels == 2:
            self.format = al.AL_FORMAT_STEREO16
        else:
            raise NotImplementedError('not mono or stereo')

    def __del__(self):
        try:
            quicktime.MovieAudioExtractionEnd(self.extraction_session_ref)
        except NameError:
            pass

    def get_buffer(self, bytes):
        '''Fill and return an OpenAL buffer'''
        frames = ctypes.c_uint(bytes / self.bytes_per_frame)
        flags = ctypes.c_uint()

        buffer = (ctypes.c_byte * bytes)()

        audio_buffer_list = AudioBufferList()
        audio_buffer_list.mNumberBuffers = 1
        audio_buffer_list.mBuffers[0].mNumberChannels = self.channels
        audio_buffer_list.mBuffers[0].mDataByteSize = bytes
        audio_buffer_list.mBuffers[0].mData = \
            ctypes.cast(buffer, ctypes.c_void_p)

        result = quicktime.MovieAudioExtractionFillBuffer(
            self.extraction_session_ref, 
            ctypes.byref(frames), 
            ctypes.byref(audio_buffer_list),
            ctypes.byref(flags))
        _oscheck(result)

        if frames.value == 0:
            return None

        albuffer = openal.buffer_pool.get()
        al.alBufferData(albuffer, self.format,
            audio_buffer_list.mBuffers[0].mData, 
            audio_buffer_list.mBuffers[0].mDataByteSize,
            int(self.sample_rate))
        return albuffer

    def get_buffers(self, bytes):
        while True:
            buffer = self.get_buffer(bytes)
            if not buffer:
                break
            yield buffer

class QuickTimeStreamingSound(openal.OpenALStreamingSound):
    _buffer_time = .5            # seconds ahead to buffer
    _buffer_size = BUFFER_SIZE   # bytes in each al buffer

    def __init__(self, extraction_session):
        super(QuickTimeStreamingSound, self).__init__()

        self._extraction_session = extraction_session
        time_per_buffer = \
            (self._buffer_size / extraction_session.sample_rate /
             extraction_session.channels / 2)
        self._buffers_ahead = int(math.ceil(
            self._buffer_time / float(time_per_buffer)))

        # Queue up first buffers
        self.dispatch_events()

    def dispatch_events(self):
        super(QuickTimeStreamingSound, self).dispatch_events()

        needed_buffers = max(0, self._buffers_ahead - self._queued_buffers)
        buffers = []
        for i in range(needed_buffers):
            buffer = self._extraction_session.get_buffer(self._buffer_size)
            if not buffer:
                break
            self.finished = False
            buffers.append(buffer)
        buffers = (al.ALuint * len(buffers))(*buffers)
        al.alSourceQueueBuffers(self.source, len(buffers), buffers)

class QuickTimeMedium(Medium):
    def __init__(self, filename, file=None, streaming=None):
        if streaming is None:
            streaming = False # TODO

        self.filename = filename
        self.file = file
        self.streaming = streaming

        if self.streaming:
            self.movie = self._create_movie()
            self.extraction_session = ExtractionSession(self.movie)
            self.channels = self.extraction_session.channels
            self.sample_rate = self.extraction_session.sample_rate
        else:
            movie = self._create_movie()
            extraction_session = ExtractionSession(movie)
            self.channels = extraction_session.channels
            self.sample_rate = extraction_session.sample_rate
            buffers = [b for b in extraction_session.get_buffers(BUFFER_SIZE)]
            self.static_buffers = (al.ALuint * len(buffers))(*buffers)

    def __del__(self):
        if not self.streaming:
            try:
                openal.buffer_pool.replace(self.static_buffers)
            except NameError:
                pass
            
    def get_sound(self):
        if self.streaming:
            extraction_session = self.extraction_session
            if not extraction_session:
                extraction_session = ExtractionSession(self.movie)
            self.extraction_session = None

            sound = QuickTimeStreamingSound(extraction_session)
            sounds.append(sound)
            return sound
        else:
            sound = openal.OpenALStaticSound(self)
            sounds.append(sound)
            al.alSourceQueueBuffers(
                sound.source, len(self.static_buffers), self.static_buffers)
            return sound

    def _create_movie(self):
        if self.file is not None:
            raise NotImplementedError('TODO: file object loading')

        filename = _create_cfstring(self.filename)

        data_ref = ctypes.c_void_p()
        data_ref_type = ctypes.c_ulong()
        result = quicktime.QTNewDataReferenceFromFullPathCFString(filename,
            -1, 0, ctypes.byref(data_ref), ctypes.byref(data_ref_type))
        _oscheck(result) 
        
        movie = ctypes.c_void_p()
        fileid = ctypes.c_short(0)
        result = quicktime.NewMovieFromDataRef(
            ctypes.byref(movie),
            newMovieActive,
            ctypes.byref(fileid),
            data_ref, data_ref_type)
        _oscheck(result)

        carbon.CFRelease(filename)

        return movie

# Device interface
# ----------------------------------------------------------------------------

def load(filename, file=None, streaming=None):
    return QuickTimeMedium(filename, file, streaming)

def dispatch_events():
    global sounds
    for sound in sounds:
        sound.dispatch_events()
    sounds = [sound for sound in sounds if not sound.finished]

openal.init()

sounds = []
