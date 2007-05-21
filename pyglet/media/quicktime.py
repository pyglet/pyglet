#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import ctypes
import math
import sys
import re

from pyglet.gl import *
from pyglet import image
from pyglet.media import Sound, Medium, Video
from pyglet.media import lib_openal as al
from pyglet.media import openal
from pyglet.window.carbon import _create_cfstring, _oscheck
from pyglet.window.carbon import carbon, quicktime
from pyglet.window.carbon.constants import _name, noErr

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

kMovieLoadStateError          = -1
kMovieLoadStateLoading        = 1000
kMovieLoadStateLoaded         = 2000
kMovieLoadStatePlayable       = 10000
kMovieLoadStatePlaythroughOK  = 20000
kMovieLoadStateComplete       = 100000

k16BE555PixelFormat = 0x00000010
k32ARGBPixelFormat = 0x00000020

quicktime.GetMovieTime.restype = ctypes.c_long
quicktime.GetMovieDuration.restype = ctypes.c_long
quicktime.NewPtrClear.restype = ctypes.c_void_p

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

class Rect(ctypes.Structure):
    _fields_ = [
        ('top', ctypes.c_short),   
        ('left', ctypes.c_short),   
        ('bottom', ctypes.c_short),   
        ('right', ctypes.c_short),   
    ]

    def __str__(self):
        return '<Rect tl=%d,%d br=%d,%d>'%(self.top, self.left,
            self.bottom, self.right)

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

        # For calculating timestamps
        self.seconds_per_byte = 1. / self.sample_rate / self.channels / 2
        self.time = 0.

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

        size = audio_buffer_list.mBuffers[0].mDataByteSize
        albuffer = openal.buffer_pool.get(self.time)
        al.alBufferData(albuffer, self.format,
            audio_buffer_list.mBuffers[0].mData, size,
            int(self.sample_rate))

        self.time += self.seconds_per_byte * size
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

class QuickTimeStreamingVideo(Video):
    sound = None
    finished = False

    def __init__(self, movie):    # XXX sound?
        self.movie = movie
        self._duration = quicktime.GetMovieDuration(self.movie)

        quicktime.EnterMovies()

        # determine dimensions of video
        r = Rect()
        quicktime.GetMovieBox(movie, ctypes.byref(r))

        # XXX this is the only way I can think to detect absence of video
        if r.top == r.left == r.bottom == r.right == 0:
            self.has_video = False
            return
        
        # now handle the video
        quicktime.OffsetRect(ctypes.byref(r), -r.left, -r.top)
        quicktime.SetMovieBox(movie, ctypes.byref(r))

        # save off current GWorld
        origDevice = ctypes.c_void_p()
        origPort = ctypes.c_void_p()
        quicktime.GetGWorld(ctypes.byref(origPort), ctypes.byref(origDevice))

        self.width = r.right - r.left
        self.height = r.bottom - r.top
        self.rect = Rect(0, 0, self.width, self.height)

        # TODO sanity check size? QT can scale for us
        self.texture = image.Texture.create_for_size(image.GL_TEXTURE_2D,
            self.width, self.height, image.GL_RGB)
        tw = self.texture.width
        th = self.texture.height

        # create "graphics world" for QT to render to
        buf = quicktime.NewPtrClear(4 * self.width * self.height)
        self.buffer_type = c_char * (4 * self.width * self.height)
        self.gworld = ctypes.c_void_p() #GWorldPtr()
        err = quicktime.QTNewGWorldFromPtr(ctypes.byref(self.gworld),
            k32ARGBPixelFormat, ctypes.byref(self.rect), 0, 0, 0, buf,
            4*self.width)
        assert err == noErr, 'An error was raised!'
        assert self.gworld != 0, 'Could not allocate GWorld'
        quicktime.SetGWorld(self.gworld, 0)
        quicktime.SetMovieGWorld(movie, self.gworld, 0)

        # pull out the buffer address and row stride from the pixmap
        # (just in case...)
        pixmap = quicktime.GetGWorldPixMap(self.gworld)
        assert pixmap != 0, 'Could not GetGWorldPixMap'
        if not quicktime.LockPixels(pixmap):
            raise ValueError, 'Could not lock PixMap'
        self.gp_buffer = quicktime.GetPixBaseAddr(pixmap)
        self.gp_row_stride = quicktime.GetPixRowBytes(pixmap)
        print self.gp_buffer

        # restore old GWorld
        quicktime.SetGWorld(origPort, origDevice)

        # right, now start playing at start of movie
        self._playMovie(0)

    def _playMovie(self, timestamp):
        print '_playMovie', timestamp
        if not timestamp:
            quicktime.GoToBeginningOfMovie(self.movie)
            print '> to beginning'
        elif timestamp > self._duration:
            quicktime.SetMovieTimeValue(self.movie, self._duration)
            print '> set to end'
        else:
            quicktime.SetMovieTimeValue(self.movie, timestamp)
            print '> set to timestamp'

        # now force redraw and processing of first frame
        err = quicktime.GetMoviesError()
        if err == noErr:
            err = quicktime.UpdateMovie(self.movie)         # force redraw
            print '> update movie'
        if err == noErr:
            quicktime.MoviesTask(self.movie, 0)             # process movie
            print '> movies task'
            err = quicktime.GetMoviesError()
        assert err == noErr, 'An error was raised!'
        print 'done'

    __paused = False
    def play(self):
        if not self.__paused:
            quicktime.GoToBeginningOfMovie(self.movie)
        quicktime.StartMovie(self.movie)

    def pause(self):
        if self.__paused:
            quicktime.StartMovie(self.movie)
        else:
            quicktime.StopMovie(self.movie)
        self.__paused = not self.__paused

    def stop(self):
        self.__paused = False
        quicktime.GoToBeginningOfMovie(self.movie)
        quicktime.StopMovie(self.movie)

    def _get_time(self):
        return quicktime.GetMovieTime(self.movie, 0)

    def dispatch_events(self):
        ''' draw to the texture '''
        quicktime.MoviesTask(self.movie, 0)
        err = quicktime.GetMoviesError()
        assert err == noErr, 'An error was raised!'

        # Create an intermediate ImageData and use it to update the
        # texture, as it does a good job of swizzling ARGB to RGB in the
        # most efficient way.
        texture = self.texture
        glBindTexture(texture.target, texture.id)
        imagedata = image.ImageData(self.width, self.height, 'ARGB',
            self.gp_buffer)
        imagedata.blit_to_texture(texture.target, 0, 0, 0, 0)

        self.finished = quicktime.IsMovieDone(self.movie)

        if self.finished:
            # examples nudge one last time to make sure last frame is drawn
            self._playMovie(self.movie, quicktime.GetMovieTime(self.movie, 0))

    def __del__(self):
        try:
            quicktime.DisposeGWorld(self.gworld)
        except NameError, name:
            pass


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
            self.movie = self._create_movie()
            extraction_session = ExtractionSession(self.movie)
            self.channels = extraction_session.channels
            self.sample_rate = extraction_session.sample_rate
            buffers = [b for b in extraction_session.get_buffers(BUFFER_SIZE)]
            self.static_buffers = (al.ALuint * len(buffers))(*buffers)

        self._duration = quicktime.GetMovieDuration(self.movie)

        # copy flags
        self.has_audio = True       # XXX can't figure how to detect this

        # XXX this is the only way I can think to detect absence of video
        r = Rect()
        quicktime.GetMovieBox(self.movie, ctypes.byref(r))
        self.has_video = not (r.top == r.left == r.bottom == r.right == 0)

    def __del__(self):
        if self.streaming:
            pass
            # XXX this disposes the movie from underneath the video playing
            #try:
            #    quicktime.DisposeMovie(self.movie)
            #except NameError:
            #    pass
        else:
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

    def get_video(self):
        video = QuickTimeStreamingVideo(self.movie)
        videos.append(video)
        return video

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
    global videos
    for sound in sounds:
        sound.dispatch_events()
    sounds = [sound for sound in sounds if not sound.finished]
    for video in videos:
        video.dispatch_events()
    videos = [video for video in videos if not video.finished]

def init():
    openal.init()

def cleanup():
    pass

listener = openal.OpenALListener()

sounds = []
videos = []
