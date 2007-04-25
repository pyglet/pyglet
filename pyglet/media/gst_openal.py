#!/usr/bin/python
# $Id$

'''Provide a media device that decodes with Gstreamer and plays back with
OpenAL.
'''

import ctypes
import time

from pyglet.gl import *
from pyglet import image
from pyglet.media import Medium, MediaException, Video
from pyglet.media import gstreamer
from pyglet.media import lib_openal as al
from pyglet.media import openal
from pyglet.media.gstreamer import gst, gstbase, gobject

DecodebinNewDecodedPad = ctypes.CFUNCTYPE(None,
    ctypes.POINTER(gstreamer.GstElement), ctypes.POINTER(gstreamer.GstPad),
    ctypes.c_int, ctypes.c_void_p)
DecodebinNoMorePads = ctypes.CFUNCTYPE(None,
    ctypes.POINTER(gstreamer.GstElement), ctypes.c_void_p)

GstBusFunc = ctypes.CFUNCTYPE(ctypes.c_int,
    ctypes.c_void_p, ctypes.POINTER(gstreamer.GstMessage), ctypes.c_void_p)

class PythonFileObjectSrcPad(gstreamer.Pad):
    name = 'src'
    direction = gstreamer.GST_PAD_SRC
    caps = 'ANY'

class PythonFileObjectSrc(gstreamer.Element):
    name = 'pyfileobjectsrc'
    klass = 'Source/PythonFileObject'
    description = 'Read from a Python file object'
    author = 'pyglet.org'

    class_struct = gstreamer.GstBaseSrcClass
    instance_struct = gstreamer.GstBaseSrc
    parent_type = gstbase.gst_base_src_get_type

    vmethods = ('create', 'start', 'stop', 'is_seekable', 'do_seek')

    pad_templates = (PythonFileObjectSrcPad,)
    pad_instances = [
        # Instance is created from template by superclass (GstBaseSrcClass)
    ]

    def init(self, file):
        # Not a vmethod; this is the Python interface
        self.file = file
        self.offset =  0

    def start(self):
        return True

    def stop(self):
        return True

    def is_seekable(self):
        return False
        # TODO return hasattr(self.file, 'seek')

    def do_seek(self, segment):
        # TODO
        return True

    def create(self, offset, size, bufp):
        if offset != self.offset:
            self.file.seek(offset)
            self.offset = offset

        try:
            data = self.file.read(size)
            if not data and size > 0:
                # EOF
                return gstreamer.GST_FLOW_UNEXPECTED
        except IOError:
            return gstreamer.GST_FLOW_ERROR

        gst.gst_buffer_new_and_alloc.restype = \
            ctypes.POINTER(gstreamer.GstBuffer)
        buffer = gst.gst_buffer_new_and_alloc(size)

        size = len(data)
        ctypes.memmove(buffer.contents.data, data, size)

        buffer.contents.size = size
        buffer.contents.offset = offset
        buffer.contents.offset_end = offset + size
        buffer.contents.timestamp = gstreamer.GST_CLOCK_TIME_NONE

        self.offset += size

        bufp.contents.contents = buffer.contents

        return gstreamer.GST_FLOW_OK


class GstreamerDecoder(object):
    def _create_decoder_pipeline(self, filename, file):
        if file is None:
            # Hooray, can just use filename
            src = gst.gst_element_factory_make('filesrc', 'src')
            gobject.g_object_set(src, 'location', filename, None)
        else:
            # Boo, use PythonFileObjectSrc
            src = gst.gst_element_factory_make('pyfileobjectsrc', 'src')
            pysrc = PythonFileObjectSrc.get_instance(src)
            pysrc.init(file)
            
            # Don't GC the source
            self._file_source = pysrc

        # Create pipeline to manage pause/play state.
        pipeline = gst.gst_pipeline_new('pipeline')

        # Create decodebin to find audio and video streams in file
        decoder = gst.gst_element_factory_make('decodebin', 'decoder')
        self._new_decoded_pad_func = DecodebinNewDecodedPad(
            self._new_decoded_pad)
        self._no_more_pads_func = DecodebinNoMorePads(self._no_more_pads)
        gobject.g_signal_connect_data(decoder, 'new-decoded-pad', 
            self._new_decoded_pad_func, None, None, 0)
        gobject.g_signal_connect_data(decoder, 'no-more-pads',
            self._no_more_pads_func, None, None, 0)
        gst.gst_bin_add_many(pipeline, src, decoder, None)
        gst.gst_element_link(src, decoder)

        # Create audioconvert
        self.convert = gst.gst_element_factory_make('audioconvert', 'convert')
        gst.gst_bin_add(pipeline, self.convert)

        return pipeline

    def _new_decoded_pad(self, decodebin, pad, last, data):
        '''Called by decodebin element when a source pad is created.'''
        caps = gst.gst_pad_get_caps(pad)
        struct = gst.gst_caps_get_structure(caps, 0)
        gst.gst_structure_get_name.restype = ctypes.c_char_p
        name = gst.gst_structure_get_name(struct)

        if name.startswith('audio/x-raw'):
            channels = ctypes.c_int()
            gst.gst_structure_get_int(
                struct, 'channels', ctypes.byref(channels))
            depth = sample_rate = 0 # TODO
            self._new_audio_pad(pad, channels.value, depth, sample_rate)
        elif name.startswith('video/x-raw'):
            self._new_video_pad(pad)

    def _new_audio_pad(self, pad, channels, depth, sample_rate):
        pass

    def _new_video_pad(self, pad):
        pass

    def _no_more_pads(self, decodebin, data):
        pass

class OpenALSinkPad(gstreamer.Pad):
    name = 'sink'
    direction = gstreamer.GST_PAD_SINK
    caps = '''audio/x-raw-int,
                width = (int) 16,
                depth = (int) 16,
                signed = (boolean) TRUE,
                endianness = (int) BYTE_ORDER,
                channels = (int) { 1, 2 },
                rate = (int) [ 1, MAX ];
              audio/x-raw-int,
                width = (int) 8,
                depth = (int) 8,
                signed = (boolean) FALSE,
                channels = (int) { 1, 2 },
                rate = (int) [ 1, MAX ]
        '''

    def setcaps(self, this, caps):
        gst.gst_caps_get_structure.restype = ctypes.c_void_p
        structure = gst.gst_caps_get_structure(caps, 0)

        rate = ctypes.c_int()
        gst.gst_structure_get_int(structure, 'rate', ctypes.byref(rate))
        self.rate = rate.value

        channels = ctypes.c_int()
        gst.gst_structure_get_int(structure, 'channels', ctypes.byref(channels))

        depth = ctypes.c_int()
        gst.gst_structure_get_int(structure, 'depth', ctypes.byref(depth))

        self.format = openal.get_format(channels.value, depth.value)
        self.element.channels = channels.value
        self.element.rate = rate.value

        self.bytes_per_second = \
            float(channels.value * depth.value / 8 * rate.value)

        return True

    def chain(self, this, buffer):
        timestamp = buffer.contents.timestamp * 0.000000001
        albuffer = openal.buffer_pool.get(timestamp)
        size = buffer.contents.size
        al.alBufferData(albuffer, self.format, 
                        buffer.contents.data, size,
                        self.rate)
        gst.gst_mini_object_unref(buffer)

        self.element._add_buffer(albuffer, size / self.bytes_per_second)
        return gstreamer.GST_FLOW_OK

    def event(self, this, event):
        if event.contents.type == gstreamer.GST_EVENT_EOS:
            self.element._finished_buffering()
            return True
        return False

class TextureSinkPad(gstreamer.Pad):
    name = 'texturesink'
    direction = gstreamer.GST_PAD_SINK
    caps = '''video/x-raw-rgb,
                bpp = (int) 32,
                depth = (int) 24,
                endianness = (int) BIG_ENDIAN,
                red_mask = (int) 0xFF000000,
                green_mask = (int) 0x00FF0000,
                blue_mask = (int) 0x0000FF00
        '''

    def setcaps(self, this, caps):
        gst.gst_caps_get_structure.restype = ctypes.c_void_p
        structure = gst.gst_caps_get_structure(caps, 0)

        width = ctypes.c_int()
        gst.gst_structure_get_int(structure, 'width', ctypes.byref(width))

        height = ctypes.c_int()
        gst.gst_structure_get_int(structure, 'height', ctypes.byref(height))

        return True

    def chain(self, this, buffer):
        self.element._add_frame(buffer.contents.data, 
                                buffer.contents.size,
                                buffer.contents.timestamp * 0.000000001)
        gst.gst_mini_object_unref(buffer)
        return gstreamer.GST_FLOW_OK

    def event(self, this, event):
        return False

# OpenAL streaming
# -----------------------------------------------------------------------------

class OpenALStreamingSinkElement(gstreamer.Element):
    name = 'openalstreamingsink'
    klass = 'audio/openal-streaming-sink'
    description = 'Sink to streaming OpenAL buffers'
    author = 'pyglet.org'

    pad_templates = (OpenALSinkPad,TextureSinkPad)
    pad_instances = [
        ('sink', OpenALSinkPad),
        ('texturesink', TextureSinkPad),
    ]

    def init(self, sound, video=None):
        self.sound = sound
        self.video = video

    def _add_buffer(self, buffer, buffer_time):
        al.alSourceQueueBuffers(self.sound.source, 1, buffer)
        if self.sound._buffers_ahead is None:
            # Now we know how many buffers are needed
            self.sound._buffers_ahead = self.sound._buffer_time / buffer_time
        
        # Assume GIL will lock for us
        self.sound._queued_buffers += 1

        extra_buffers = self.sound._queued_buffers - self.sound._buffers_ahead
        if extra_buffers > 0:
            # We've buffered more than necessary, take a break (this is
            # running in a separate thread, so sleeping is cool).
            time.sleep(buffer_time * extra_buffers)

    def _set_frame_format(self, width, height):
        self.video._set_frame_format(width, height)

    def _add_frame(self, data, length, timestamp):
        self.video._add_frame(data, length, timestamp)

    def _finished_buffering(self):
        self.sound._on_eos()

class GstreamerOpenALStreamingSound(openal.OpenALStreamingSound, 
                                    GstreamerDecoder):
    _buffer_time = .5  # seconds ahead to buffer
    _buffers_ahead = None # Number of buffers ahead to buffer (calculated later)

    def __init__(self, filename, file):
        super(GstreamerOpenALStreamingSound, self).__init__()
        self.pipeline = self._create_decoder_pipeline(filename, file)

        self.sink = gst.gst_element_factory_make('openalstreamingsink', 'sink')
        gst.gst_bin_add(self.pipeline, self.sink)
        gst.gst_element_link(self.convert, self.sink)

        gst.gst_element_set_state(self.pipeline, gstreamer.GST_STATE_PAUSED)

    def play(self):
        super(GstreamerOpenALStreamingSound, self).play()
        gst.gst_element_set_state(self.pipeline, gstreamer.GST_STATE_PLAYING)

    def _new_audio_pad(self, pad, channels, depth, sample_rate):
        '''Create and connect the sink for the given source pad.'''
        convertpad = gst.gst_element_get_pad(self.convert, 'sink')
        gst.gst_pad_link(pad, convertpad)
        gst.gst_object_unref(convertpad)

        sink = self.sink
        pysink = OpenALStreamingSinkElement.get_instance(self.sink)
        pysink.init(self)

    def _on_eos(self):
        pass

class GstreamerOpenALStreamingVideo(Video,
                                    GstreamerDecoder):
    _buffer_time = .5  # seconds ahead to buffer
    _buffers_ahead = None # Number of buffers ahead to buffer (calculated later)

    finished = False

    def __init__(self, filename, file):
        super(GstreamerOpenALStreamingVideo, self).__init__()
        self.pipeline = self._create_decoder_pipeline(filename, file)

        self.sink = gst.gst_element_factory_make('openalstreamingsink', 'sink')
        gst.gst_bin_add(self.pipeline, self.sink)
        gst.gst_element_link(self.convert, self.sink)

        self.videoconvert = \
            gst.gst_element_factory_make('ffmpegcolorspace', 'videoconvert')
        gst.gst_bin_add(self.pipeline, self.videoconvert)
        gst.gst_element_link(self.videoconvert, self.sink)

        gst.gst_element_set_state(self.pipeline, gstreamer.GST_STATE_PAUSED)

        self._frames = [] # queued upcoming video frames
        self._last_frame_timestamp = 0.


    def play(self):
        gst.gst_element_set_state(self.pipeline, gstreamer.GST_STATE_PLAYING)
        self.sound.play()

    def pause(self):
        gst.gst_element_set_state(self.pipeline, gstreamer.GST_STATE_PAUSED)
        self.sound.pause()

    def _get_time(self):
        return self.sound.time

    def _new_audio_pad(self, pad, channels, depth, sample_rate):
        '''Create and connect the sink for the given source pad.'''
        convertpad = gst.gst_element_get_pad(self.convert, 'sink')
        gst.gst_pad_link(pad, convertpad)
        gst.gst_object_unref(convertpad)

        self.sound = openal.OpenALStreamingSound()
        self.sound._buffers_ahead = self._buffers_ahead # XXX
        self.sound._buffer_time = self._buffer_time

    def _new_video_pad(self, pad):
        sinkpad = gst.gst_element_get_pad(self.videoconvert, 'sink')
        gst.gst_pad_link(pad, sinkpad)
        gst.gst_object_unref(sinkpad)

    def _set_frame_format(self, width, height):
        self.width = width
        self.height = height
    
    def _add_frame(self, buffer, length, timestamp):
        # Make a copy of the frame and queue it up with its timestamp
        frame_buffer = (ctypes.c_byte * length)()
        ctypes.memmove(frame_buffer, buffer, length)
        self._frames.append((frame_buffer, timestamp))

        # If we've queued enough, sleep (otherwise chain will just run hot
        # and exhaust cpu and memory).
        if timestamp > self._frames[0][1] + self._buffer_time:
            time.sleep(self._buffer_time / 2)

        '''
        # Deal with frames != packets
        offset = 0
        while length:
            if self._frame_buffer is None:
                self._frame_buffer = \
                    (ctypes.c_byte * (self.width * self.height * 4))()
                self._frame_buffer_len = 0
            copylen = min(length, 
                          len(self._frame_buffer) - self._frame_buffer_len)
            ctypes.memmove(
                ctypes.addressof(self._frame_buffer) + self._frame_buffer_len, 
                buffer + offset, 
                copylen)
            length -= copylen
            offset += copylen
            self._frame_buffer_len += copylen
            if self._frame_buffer_len == len(self._frame_buffer):
                self._frames.append((self._frame_buffer, timestamp))
                self._frame_buffer = None
        '''

    def _no_more_pads(self, decodebin, data):
        sink = self.sink
        pysink = OpenALStreamingSinkElement.get_instance(self.sink)
        pysink.init(self.sound, self)

    def _on_eos(self):
        pass

    def dispatch_events(self):
        self.sound.dispatch_events()

        if not self.texture:
            glEnable(GL_TEXTURE_2D)
            texture = image.Texture.create_for_size(GL_TEXTURE_2D,
                self.width, self.height, GL_RGB)
            if texture.width != self.width or texture.height != self.height:
                self.texture = texture.get_region(0, 0, self.width, self.height)
            else:
                self.texture = texture

            # Flip texture coords (good enough for simple apps).
            bl, br, tr, tl = self.texture.tex_coords
            self.texture.tex_coords = tl, tr, br, bl

        time = self.sound.time
        frame = None
        timestamp = self._last_frame_timestamp
        while self._frames and time >= timestamp:
            frame, timestamp = self._frames.pop(0)
        self._last_frame_timestamp = timestamp

        if frame:
            glBindTexture(self.texture.target, self.texture.id)
            glTexSubImage2D(self.texture.target,
                            self.texture.level,
                            0, 0,
                            self.width, self.height,
                            GL_RGBA, # TODO
                            GL_UNSIGNED_BYTE,
                            frame)

class GstreamerOpenALStreamingMedium(Medium):
    def __init__(self, filename, file):
        self.filename = filename
        self.file = file

    def get_sound(self):
        sound = GstreamerOpenALStreamingSound(self.filename, self.file)
        instances.append(sound)
        return sound

    def get_video(self):
        video = GstreamerOpenALStreamingVideo(self.filename, self.file)
        instances.append(video)
        return video

# OpenAL static
# -----------------------------------------------------------------------------

class OpenALStaticSinkElement(gstreamer.Element, Medium):
    name = 'openalstaticsink'
    klass = 'audio/openal-static-sink'
    description = 'Sink to static OpenAL buffers'
    author = 'pyglet.org'

    pad_templates = (OpenALSinkPad,)
    pad_instances = [
        ('sink', OpenALSinkPad),
    ]

    def init(self, medium):
        self.medium = medium

    def _add_buffer(self, buffer, buffer_time):
        self.medium.buffers.append(buffer)

        # Any sounds that are already created, queue the new buffer as well
        for sound in self.medium.sounds:
            al.alSourceQueueBuffers(sound.source, 1, buffer)

    def _finished_buffering(self):
        # Convert list of buffers to an array of buffers for fast queueing
        # in the future.
        del self.medium.sounds
        self.medium.buffering = False
        self.medium.buffers = \
            (al.ALuint * len(self.medium.buffers))(*self.medium.buffers)
       
class GstreamerOpenALStaticMedium(Medium, GstreamerDecoder):
    '''A Medium which decodes all data into a list of OpenAL buffers which
    are shared by many OpenALSound instances.

    The pipeline created during decoding is::

        filesrc ! decodebin ! audioconvert ! openalstaticsink

    OpenALStaticSinkElement implements ``openalstaticsink`` and contains
    a reference to this instance.
    '''
    def __init__(self, filename, file=None):
        self._pipeline = self._create_decoder_pipeline(filename, file)
        self._sink = gst.gst_element_factory_make('openalstaticsink', 'sink')
        gst.gst_bin_add(self._pipeline, self._sink)
        gst.gst_element_link(self.convert, self._sink)

        self._element = OpenALStaticSinkElement.get_instance(self._sink)
        self._element.init(self)

        self.has_audio = False

        # The list of OpenAL buffers.  When self.buffering is True, newly
        # decoded buffers must also be queued on all sounds in self.sounds.
        # When self.buffering is False (the entire sound is decoded),
        # self.sounds is no longer maintained.
        self.buffering = True
        self.buffers = []
        self.sounds = []

        gst.gst_element_set_state(self._pipeline, gstreamer.GST_STATE_PLAYING)

    def _new_audio_pad(self, pad, channels, depth, sample_rate):
        # Connect the decoded audio pad to the audioconvert
        convertpad = gst.gst_element_get_pad(self.convert, 'sink')
        gst.gst_pad_link(pad, convertpad)
        gst.gst_object_unref(convertpad)

        self.has_audio = True

    def _no_more_pads(self, decodebin, data):
        # XXX This will pop out of another thread, which is not ideal.
        if not self.has_audio:
            raise MediaException('No useable audio stream')

    def get_sound(self):
        sound = openal.OpenALSound()
        instances.append(sound)

        if self.buffering:
            # Queue buffers already decoded
            for buffer in self.buffers:
                al.alSourceQueueBuffers(sound.source, 1, buffer)

            # Keep track of this sound so we can queue additional buffers
            # as they are decoded
            self.sounds.append(sound)
        else:
            # Queue all buffers in one go
            al.alSourceQueueBuffers(sound.source, 
                len(self.buffers), self.buffers)

        return sound

 
class OpenALPlugin(gstreamer.Plugin):
    '''A static plugin to hold the ``openalstreamingsink`` and
    ``openalstaticsink`` elements.
    
    This is equivalent to the GST_PLUGIN_DEFINE macro.
    '''

    name = 'openal-plugin'
    description = 'OpenAL plugin'
    version = '1.0'
    license = 'LGPL'
    package = 'pyglet'
    origin = 'http://www.pyglet.org'

    elements = (
        PythonFileObjectSrc,
        OpenALStreamingSinkElement, 
        OpenALStaticSinkElement)


# Device interface
# --------------------------------------------------------------------------

def load(filename, file=None, streaming=None):
    if streaming is None:
        # Gstreamer can't tell us the duration of a file, so don't stream
        # unless asked to.  This gives best runtime performance at the
        # expense of higher CPU and memory usage for long music clips.
        streaming = False
    if streaming:
        return GstreamerOpenALStreamingMedium(filename, file)
    else:
        return GstreamerOpenALStaticMedium(filename, file)

def dispatch_events():
    global instances

    gstreamer.heartbeat()
    for instance in instances:
        instance.dispatch_events()
    instances = [instance for instance in instances if not instance.finished]

def init():
    gthread = gstreamer.get_library('gthread-2.0')
    thread_supported = ctypes.cast(gthread.g_threads_got_initialized,
                                   ctypes.POINTER(ctypes.c_int)).contents.value
    if not thread_supported:
        gthread.g_thread_init(None)

    openal.init()
    gstreamer.init()
    openal_plugin = OpenALPlugin()
    openal_plugin.register()

def cleanup():
    while instances:
        instances.pop()
    import gc
    gc.collect()

listener = openal.OpenALListener()

# Active instances
instances = []


