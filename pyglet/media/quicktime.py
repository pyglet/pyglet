#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import ctypes
import math
import sys
import re
import atexit

from pyglet import image
from pyglet.media import Sound, Video, Medium, MediaException
from pyglet.media import lib_openal as al
from pyglet.media import openal
from pyglet import window
from pyglet.window.carbon import _create_cfstring, _oscheck
from pyglet.window.carbon import carbon, quicktime, _get_framework
from pyglet.window.carbon.constants import _name, noErr
from pyglet.window.carbon.types import Rect, Boolean

from pyglet.gl import *
from pyglet import gl
from pyglet.gl import agl
from pyglet.gl import gl_info

try:
    corevideo = _get_framework('CoreVideo')
except ImportError:
    corevideo = None

BUFFER_SIZE = 8192

Movie = ctypes.c_void_p

quicktime.NewMovieFromDataRef.argtypes = (
    ctypes.POINTER(Movie),
    ctypes.c_short,
    ctypes.POINTER(ctypes.c_short),
    ctypes.c_void_p,
    ctypes.c_ulong)

CVDisplayLinkOutputCallback = CFUNCTYPE(c_int, c_void_p, c_void_p, c_void_p,
    c_uint64, c_void_p, c_void_p)

ItemCount = ctypes.c_uint32
OSStatus = ctypes.c_int32
FourCharCode = ctypes.c_uint32
OSType = FourCharCode
QTPropertyClass = OSType
QTPropertyID = OSType
ByteCount = ctypes.c_uint32
QTPropertyValuePtr = ctypes.c_void_p
QTVisualContextRef = ctypes.c_void_p
CFStringRef = ctypes.c_void_p

class QTNewMoviePropertyElement(ctypes.Structure):
     _fields_ = [('propClass', QTPropertyClass),
                 ('propID', QTPropertyID),
                 ('propValueSize', ByteCount),
                 ('propValueAddress', QTPropertyValuePtr),
                 ('propStatus',OSStatus)]

class CVSMPTETime(ctypes.Structure):
    _fields_ = [
        ('subframes', ctypes.c_int16),
        ('subframeDivisor', ctypes.c_int16),
        ('counter', ctypes.c_uint32),
        ('type', ctypes.c_uint32),
        ('flags', ctypes.c_uint32),
        ('hours', ctypes.c_int16),
        ('minutes', ctypes.c_int16),
        ('seconds', ctypes.c_int16),
        ('frames', ctypes.c_int16),
    ]

class CVTimeStamp(ctypes.Structure):
    _fields_ = [
        ('version', ctypes.c_uint32),
        ('videoTimeScale', ctypes.c_int32),
        ('videoTime', ctypes.c_int64),
        ('hostTime', ctypes.c_uint64),
        ('rateScalar', ctypes.c_double),
        ('videoRefreshPeriod', ctypes.c_int64),
        ('smpteTime', CVSMPTETime),
        ('flags', ctypes.c_uint64),
        ('reserved', ctypes.c_uint64),
    ]

kQTPropertyClass_DataLocation = _name('dloc')
kQTDataLocationPropertyID_CFStringPosixPath = _name('cfpp')

kQTPropertyClass_Context = _name('ctxt')
kQTContextPropertyID_VisualContext = _name('visu')

kQTPropertyClass_MovieInstantiation = _name('mins')
kQTMovieInstantiationPropertyID_DontAskUnresolvedDataRefs = _name('aurn')

kQTPropertyClass_NewMovieProperty = _name('mprp')
kQTNewMoviePropertyID_Active = _name('actv')
kQTNewMoviePropertyID_DontInteractWithUser = _name('intn')

quicktime.NewMovieFromProperties.restype = _oscheck
quicktime.NewMovieFromProperties.argtypes = (
    ItemCount,
    ctypes.POINTER(QTNewMoviePropertyElement),
    ItemCount,
    ctypes.POINTER(QTNewMoviePropertyElement),
    ctypes.POINTER(Movie))

newMovieActive = 1

movieTrackMediaType = 1 << 0
movieTrackCharacteristic = 1 << 1
movieTrackEnabledOnly = 1 << 2
VisualMediaCharacteristic = _name('eyes')
AudioMediaCharacteristic = _name('ears')

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
        if not self.channels or not self.sample_rate:
            raise MediaException('No audio in media file')
        
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
            if quicktime.MovieAudioExtractionEnd is not None:
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

    def play(self):
        instances.append(self)
        super(QuickTimeStreamingSound, self).play()

    def stop(self):
        instances.remove(self)
        super(QuickTimeStreamingSound, self).stop()

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

class QuickTimeCoreVideoStreamingVideo(Video):
    '''A streaming video implementation using Core Video to draw
    directly into an OpenGL texture.

    http://developer.apple.com/documentation/QuickTime/Conceptual/QT7UpdateGuide/Chapter02/chapter_2_section_7.html#//apple_ref/doc/uid/TP40001163-CH313-BBCFCEII
    '''
    context = None
    def __init__(self, sound, medium):
        self._medium = medium
        self._movie = medium.movie
        self.sound = sound

        # Get CGL context and pixel format (the long, convoluted way) 
        agl_context = window.get_current_context()._context
        agl_pixelformat = window.get_current_context()._pixelformat
        cgl_context = ctypes.c_void_p()
        agl.aglGetCGLContext(agl_context, ctypes.byref(cgl_context))
        cgl_pixelformat = ctypes.c_void_p()
        agl.aglGetCGLPixelFormat(
            agl_pixelformat, ctypes.byref(cgl_pixelformat))

        # XXX 10 points for the person who can find what the attributes are
        # that we are allowed / able to pass here
        textureContextAttributes = None

        '''
        # TODO match colorspace

        ... Other keys? Except these are "CV" not "QT" keys....
        kCVImageBufferDisplayWidthKey?
        kCVImageBufferDisplayHeightKey?

        keys = (CFTypeRef*1)(kQTVisualContextWorkingColorSpaceKey)
        colorSpace = quicktime.CGColorSpaceCreateDeviceRGB()
        textureContextAttributes = CFDictionaryCreate(
           carbon.CFAllocatorGetDefault(),
           keys, ctypes.byref(colorSpace), len(keys),
           ctypes.byref(quicktime.kCFTypeDictionaryKeyCallBacks),
           ctypes.byref(quicktime.kCFTypeDictionaryValueCallBacks)
        )
        '''

        # Create texture context for QuickTime to render into.
        self.context = ctypes.c_void_p()
        r = quicktime.QTOpenGLTextureContextCreate(
            carbon.CFAllocatorGetDefault(),
            cgl_context,
            cgl_pixelformat, 
            textureContextAttributes,
            ctypes.byref(self.context))
        _oscheck(r)

        if textureContextAttributes:
            quicktime.CFRelease(textureContextAttributes)

        # Get dimensions of video
        rect = Rect()
        quicktime.GetMovieBox(self._movie, ctypes.byref(rect))
        self.width = rect.right - rect.left
        self.height = rect.bottom - rect.top

        quicktime.SetMovieVisualContext(self._movie, self.context)

        # create a Texture that we can use for rendering
        self._texture = image.Texture.create_for_size(GL_TEXTURE_2D,
            self.width, self.height).get_region(0, 0, self.width, self.height)

        # create display link
        self.display_link = ctypes.c_void_p()
        main_display = quicktime.CGMainDisplayID()
        result = corevideo.CVDisplayLinkCreateWithCGDisplay(main_display,
            ctypes.byref(self.display_link))
        _oscheck(result)

        # now, er call another function with the same two arguments, reversed!
        result = corevideo.CVDisplayLinkSetCurrentCGDisplay(self.display_link,
            main_display)
        _oscheck(result)

        # set the output callback
        self._callback = CVDisplayLinkOutputCallback(self.output_callback)
        result = corevideo.CVDisplayLinkSetOutputCallback(self.display_link,
            self._callback, None)
        _oscheck(result)

        # ensure the display link is closed down nicely on program exit
        atexit.register(self.cleanup)

        # create our drawing mutext
        self.draw_lock = quicktime.QTMLCreateMutex()
        self._ts = 0

        self.latest_texture = c_void_p(0)

    def cleanup(self):
        '''On interpreter exit stop the display link thread.'''
        if corevideo.CVDisplayLinkIsRunning(self.display_link):
            corevideo.CVDisplayLinkStop(self.display_link)

    # XXX need a better way to do this
    def get_texture(self):
        '''Wrap the texture so calls to blit() will lock the draw mutex.
        '''
        class TextureProxy(object):
            def __init__(self, obj):
                self.obj = obj
            def blit(self, *args, **kw):
                quicktime.QTMLGrabMutex(self.obj.draw_lock)
                self.obj._texture.blit(*args, **kw)
                quicktime.QTMLReturnMutex(self.obj.draw_lock)
        return TextureProxy(self)
    texture = property(get_texture)

    def _get_time(self):
        t = quicktime.GetMovieTime(self._movie, None)
        return t / self._medium._time_scale

    def play(self):
        # start the display link
        _oscheck(corevideo.CVDisplayLinkStart(self.display_link))

        # right, now kick off the movie
        self.playing = True
        quicktime.StartMovie(self._movie)

    def pause(self):
        if self.playing:
            quicktime.StopMovie(self._movie)
        else:
            quicktime.StartMovie(self._movie)
        self.playing = not self.playing

    def stop(self):
        # stop the movie playing
        self.playing = False
        quicktime.StopMovie(self._movie)

        # stop the display link so we don't get unnecessary updates
        _oscheck(corevideo.CVDisplayLinkStop(self.display_link))

        # restart the movie
        quicktime.GoToBeginningOfMovie(self._movie)

        if self.latest_texture is not None:
            corevideo.CVOpenGLTextureRelease(self.latest_texture)
            self.latest_texture = None

    def output_callback(self, display_link, now, ts, flags, flags_out, ctx):
        _oscheck(quicktime.QTMLGrabMutex(self.draw_lock))
        if quicktime.QTVisualContextIsNewImageAvailable(self.context, ts):
            # free up the previous texture
            if self.latest_texture:
                corevideo.CVOpenGLTextureRelease(self.latest_texture)

            # grab new image to new texture
            _oscheck(quicktime.QTVisualContextCopyImageForTime(self.context,
                None, ts, ctypes.byref(self.latest_texture)))
            corevideo.CVOpenGLTextureRetain(self.latest_texture)

            # copy the texture "name" to our rendering texture
            t = self._texture
            t.target = corevideo.CVOpenGLTextureGetTarget(self.latest_texture)
            t.id = corevideo.CVOpenGLTextureGetName(self.latest_texture)

        _oscheck(quicktime.QTVisualContextTask(self.context))
        _oscheck(quicktime.QTMLReturnMutex(self.draw_lock))
        return 0

    def delete(self):
        # XXX needed to remove circular refs?
        pass

    def __del__(self):
        try:
            if corevideo.CVDisplayLinkStop is not None:
                corevideo.CVDisplayLinkStop(self.display_link)
            if (quicktime.QTVisualContextRelease is not None 
                    and self.context is not None):
                quicktime.QTVisualContextRelease(self.context)
                self.context = None
        except NameError, name:
            pass


class QuickTimeGWorldStreamingVideo(Video):
    '''Streaming video implementation using QuickTime and copying
    from a GWorld buffer each frame.
    '''
    sound = None
    finished = False

    def __init__(self, medium):
        self.medium = medium
        self._duration = quicktime.GetMovieDuration(medium.movie)

        if corevideo is not None:
            _oscheck(quicktime.InitializeQTML(0))
        _oscheck(quicktime.EnterMovies())

        # determine dimensions of video
        r = Rect()
        quicktime.GetMovieBox(medium.movie, ctypes.byref(r))

        # save off current GWorld
        origDevice = ctypes.c_void_p()
        origPort = ctypes.c_void_p()
        quicktime.GetGWorld(ctypes.byref(origPort), ctypes.byref(origDevice))

        # fix the rect if necessary
        self.width = r.right - r.left
        self.height = r.bottom - r.top
        self.rect = Rect(0, 0, self.height, self.width)

        # TODO sanity check size? QT can scale for us
        self.texture = image.Texture.create_for_size(image.GL_TEXTURE_2D,
            self.width, self.height, GL_RGB)
        if (self.texture.width != self.width or
            self.texture.height != self.height):
            self.texture = self.texture.get_region(
                0, 0, self.width, self.height)

        # Flip texture coords as a cheap way of flipping image.  gst_openal
        # does the same, so if you fix this, fix Windows too.
        bl, br, tr, tl = self.texture.tex_coords
        self.texture.tex_coords = tl, tr, br, bl

        # create "graphics world" for QT to render to
        buf = quicktime.NewPtrClear(4 * self.width * self.height)
        self.buffer_type = c_char * (4 * self.width * self.height)
        self.gworld = ctypes.c_void_p() #GWorldPtr()
        result = quicktime.QTNewGWorldFromPtr(ctypes.byref(self.gworld),
            k32ARGBPixelFormat, ctypes.byref(self.rect), 0, 0, 0, buf,
            4*self.width)
        _oscheck(result) 
        assert self.gworld != 0, 'Could not allocate GWorld'
        quicktime.SetGWorld(self.gworld, 0)
        quicktime.SetMovieGWorld(medium.movie, self.gworld, 0)

        # pull out the buffer address and row stride from the pixmap
        # (just in case...)
        pixmap = quicktime.GetGWorldPixMap(self.gworld)
        assert pixmap != 0, 'Could not GetGWorldPixMap'
        if not quicktime.LockPixels(pixmap):
            raise ValueError, 'Could not lock PixMap'
        self.gp_buffer = quicktime.GetPixBaseAddr(pixmap)
        self.gp_row_stride = quicktime.GetPixRowBytes(pixmap)
        self.gp_buffer = cast(self.gp_buffer, 
            POINTER(c_char * (self.gp_row_stride * self.height))).contents

        # use ImageData to swizzle the ARGB data
        self._image = image.ImageData(self.width, self.height, 'ARGB',
            self.gp_buffer)

        # restore old GWorld
        quicktime.SetGWorld(origPort, origDevice)

        # make sure we're at the start
        quicktime.GoToBeginningOfMovie(self.medium.movie)

    def _playMovie(self, timestamp):
        if not timestamp:
            quicktime.GoToBeginningOfMovie(self.medium.movie)
        elif timestamp > self._duration:
            quicktime.SetMovieTimeValue(self.medium.movie, self._duration)
        else:
            quicktime.SetMovieTimeValue(self.medium.movie, timestamp)

        # now force redraw and processing of first frame
        result = quicktime.GetMoviesError()
        if result == noErr:
            # force redraw
            result = quicktime.UpdateMovie(self.medium.movie)
        if result == noErr:
            # process movie
            quicktime.MoviesTask(self.medium.movie, 0)
            result = quicktime.GetMoviesError()
        _oscheck(result) 

    def play(self):
        instances.append(self)
        self.playing = True
        quicktime.StartMovie(self.medium.movie)

    def pause(self):
        if self.playing:
            quicktime.StopMovie(self.medium.movie)
        else:
            quicktime.StartMovie(self.medium.movie)
        self.playing = not self.playing

    def stop(self):
        instances.remove(self)
        self.playing = False
        quicktime.GoToBeginningOfMovie(self.medium.movie)
        quicktime.StopMovie(self.medium.movie)

    def _get_time(self):
        t = quicktime.GetMovieTime(self.medium.movie, None)
        return t / self.medium._time_scale

    def dispatch_events(self):
        ''' draw to the texture '''
        # play the movie
        quicktime.MoviesTask(self.medium.movie, 0)
        _oscheck(quicktime.GetMoviesError())
        self.finished = quicktime.IsMovieDone(self.medium.movie)
        if self.finished:
            # examples nudge one last time to make sure last frame is drawn
            self._playMovie(quicktime.GetMovieTime(self.medium.movie, 0))

        # copy to the texture
        texture = self.texture
        glBindTexture(texture.target, texture.id)
        self._image.blit_to_texture(texture.target, 0, 0, 0, 0)

    def __del__(self):
        try:
            if quicktime.DisposeGWorld is not None and self.gworld is not None:
                quicktime.DisposeGWorld(self.gworld)
                self.gworld = None
        except NameError, name:
            pass

class QuickTimeMedium(Medium):
    # prevent __del__ generating spurious error messages
    movie = None

    def __init__(self, filename, file=None, streaming=None):
        if streaming is None:
            streaming = False # TODO check duration?

        self.filename = filename
        self.file = file
        self.streaming = streaming

        # TODO recreate movie for each instance so they can be seeked
        # independently.
        movie = self._create_movie()
        if not movie:
            self.streaming = True
            self.movie = None
            return

        self.has_audio = quicktime.GetMovieIndTrackType(movie, 1, 
            AudioMediaCharacteristic, movieTrackCharacteristic) != 0
        self.has_video = quicktime.GetMovieIndTrackType(movie, 1, 
            VisualMediaCharacteristic, movieTrackCharacteristic) != 0

        # TimeScale is the number of units of time that pass each second
        ts = self._time_scale = float(quicktime.GetMovieTimeScale(movie))
        self._duration = quicktime.GetMovieDuration(movie) / ts

        if self.streaming:
            self.movie = movie
            if self.has_audio: 
                # TODO why set this up here??
                try:
                    self.extraction_session = ExtractionSession(self.movie)
                except MediaException:
                    # TODO this pattern for all extraction sessions, above
                    # has_audio check is not accurate
                    self.has_audio = False
        else:
            if not self.has_audio:
                raise MediaException('No audio in media file')
            extraction_session = ExtractionSession(movie)
            buffers = [b for b in extraction_session.get_buffers(BUFFER_SIZE)]
            self.static_buffers = (al.ALuint * len(buffers))(*buffers)


    def __del__(self):
        if self.streaming:
            try:
                if (quicktime.DisposeMovie is not None
                        and self.movie is not None):
                    quicktime.DisposeMovie(self.movie)
                    self.movie = None
            except NameError:
                pass
        else:
            try:
                openal.buffer_pool.replace(self.static_buffers)
            except NameError:
                pass
            
    def get_sound(self):
        if not self.has_audio:
            raise MediaException('No audio in media file')

        if self.streaming:
            extraction_session = self.extraction_session
            if not extraction_session:
                extraction_session = ExtractionSession(self.movie)
            self.extraction_session = None

            sound = QuickTimeStreamingSound(extraction_session)
            return sound
        else:
            sound = openal.OpenALStaticSound(self)
            al.alSourceQueueBuffers(
                sound.source, len(self.static_buffers), self.static_buffers)
            return sound

    def get_video(self):
        if not self.has_video:
            raise MediaException('No video in media file')

        if not self.streaming:
            raise MediaException('Cannot play back video from static media')

        sound = None
        if self.has_audio:
            sound = self.get_sound()

        # TODO need to re-open movie for playback video more than once?
        if corevideo is not None:
            video = QuickTimeCoreVideoStreamingVideo(sound, self)
        else:
            video = QuickTimeGWorldStreamingVideo(self)
        return video

    def _create_movie(self):
        if self.file is not None:
            raise NotImplementedError('TODO: file object loading')

        filename = _create_cfstring(self.filename)

        movie = Movie()

        if corevideo is None:
            fileid = ctypes.c_short(0)
            data_ref = ctypes.c_void_p()
            data_ref_type = ctypes.c_ulong()
            result = quicktime.QTNewDataReferenceFromFullPathCFString(filename,
                -1, 0, ctypes.byref(data_ref), ctypes.byref(data_ref_type))
            _oscheck(result) 
            result = quicktime.NewMovieFromDataRef(
                ctypes.byref(movie),
                newMovieActive,
                ctypes.byref(fileid),
                data_ref, data_ref_type)
            if result == -2048:
                return None
            _oscheck(result)
        else:
            # use newer QT7 API
            true = Boolean(1)

            filePathRef = CFStringRef()
            filePathRef.value = filename

            # XXX this really wants the context passed to it - and there's
            # really not reason not to AFAICT. We pass a NULL context so that
            # it's not set up using the default GWorld.
            no_context = c_void_p(0)

            properties = (QTNewMoviePropertyElement * 5)(
                (kQTPropertyClass_DataLocation,
                kQTDataLocationPropertyID_CFStringPosixPath,
                ctypes.sizeof(filePathRef), 
                ctypes.cast(ctypes.pointer(filePathRef), ctypes.c_void_p), 0),
                (kQTPropertyClass_Context,
                kQTContextPropertyID_VisualContext,
                ctypes.sizeof(c_void_p), 
                ctypes.cast(ctypes.pointer(no_context), ctypes.c_void_p), 0),
                (kQTPropertyClass_NewMovieProperty,
                kQTNewMoviePropertyID_Active,
                ctypes.sizeof(Boolean),
                ctypes.cast(ctypes.pointer(true), ctypes.c_void_p), 0),
                (kQTPropertyClass_NewMovieProperty,
                kQTNewMoviePropertyID_DontInteractWithUser,
                ctypes.sizeof(Boolean),
                ctypes.cast(ctypes.pointer(true), ctypes.c_void_p), 0),
                (kQTPropertyClass_MovieInstantiation,
                kQTMovieInstantiationPropertyID_DontAskUnresolvedDataRefs,
                ctypes.sizeof(Boolean),
                ctypes.cast(ctypes.pointer(true), ctypes.c_void_p), 0),
            )
            quicktime.NewMovieFromProperties(len(properties), properties,
                0, None, ctypes.byref(movie))

        carbon.CFRelease(filename)

        return movie

# Device interface
# ----------------------------------------------------------------------------

def load(filename, file=None, streaming=None):
    return QuickTimeMedium(filename, file, streaming)

def dispatch_events():
    global instances
    for instance in instances:
        instance.dispatch_events()
    instances = [instance for instance in instances if not instance.finished]

def init():
    openal.init()

def cleanup():
    pass

listener = openal.OpenALListener()

instances = []
