#!/usr/bin/python
# $Id$

import ctypes
import time

from pyglet.media import Medium, MediaException
from pyglet.media import gstreamer
from pyglet.media import lib_openal as al
from pyglet.media import openal
from pyglet.media.gstreamer import gst, gstaudio, gobject

DecodebinNewDecodedPad = ctypes.CFUNCTYPE(None,
    ctypes.POINTER(gstreamer.GstElement), ctypes.POINTER(gstreamer.GstPad),
    ctypes.c_int, ctypes.c_void_p)
DecodebinNoMorePads = ctypes.CFUNCTYPE(None,
    ctypes.POINTER(gstreamer.GstElement), ctypes.c_void_p)

GstBusFunc = ctypes.CFUNCTYPE(ctypes.c_int,
    ctypes.c_void_p, ctypes.POINTER(gstreamer.GstMessage), ctypes.c_void_p)

class GstreamerDecoder(object):
    def _create_decoder_pipeline(self, filename, file):
        # Create filesrc to read file (TODO: file-like objects)
        src = gst.gst_element_factory_make('filesrc', 'src')
        gobject.g_object_set(src, 'location', filename, None)

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

    def _new_audio_pad(self, channels, depth, sample_rate):
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
        albuffer = openal.buffer_pool.get()
        size = buffer.contents.size
        al.alBufferData(albuffer, self.format, 
                        buffer.contents.data, size,
                        self.rate)
        #gst.gst_object_unref(buffer)

        self.element._add_buffer(albuffer, size / self.bytes_per_second)
        return gstreamer.GST_FLOW_OK

    def event(self, this, event):
        if event.contents.type == gstreamer.GST_EVENT_EOS:
            self.element._finished_buffering()
            return True
        return False

# OpenAL streaming
# -----------------------------------------------------------------------------

class OpenALStreamingSinkElement(gstreamer.Element):
    name = 'openalstreamingsink'
    klass = 'audio/openal-streaming-sink'
    description = 'Sink to streaming OpenAL buffers'
    author = 'pyglet.org'

    pad_templates = (OpenALSinkPad,)
    pad_instances = [
        ('sink', OpenALSinkPad),
    ]

    def init(self, sound):
        self.sound = sound

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
        pysink.sound = self

    def _on_eos(self):
        pass

class GstreamerOpenALStreamingMedium(Medium):
    def __init__(self, filename, file):
        self.filename = filename
        self.file = file

    def get_sound(self):
        sound = GstreamerOpenALStreamingSound(self.filename, self.file)
        sounds.append(sound)
        return sound


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

    def init(self):
        self.buffers = []
        self.sounds = []
        self.buffering = True

    def _add_buffer(self, buffer, buffer_time):
        self.buffers.append(buffer)
        for sound in self.sounds:
            al.alSourceQueueBuffers(sound.source, 1, buffer)
            if sound.play_when_buffered:
                sound.play()

    def _finished_buffering(self):
        self.buffering = False
        self.sounds = []

    def get_sound(self):
        sound = openal.OpenALSound()
        sounds.append(sound)
        for buffer in self.buffers:
            # TODO all at once
            al.alSourceQueueBuffers(sound.source, 1, buffer)
        if self.buffering:
            self.sounds.append(sound)
        return sound

class OpenALPlugin(gstreamer.Plugin):
    name = 'openal-plugin'
    description = 'OpenAL plugin'
    version = '1.0'
    license = 'LGPL'
    package = 'pyglet'
    origin = 'http://www.pyglet.org'

    elements = (OpenALStreamingSinkElement, OpenALStaticSinkElement)

# Front-end Medium
# --------------------------------------------------------------------------

class GstreamerBlockingDelegate(Medium):
    def __init__(self, medium):
        self.medium = medium

    def get_sound(self):
        while self.medium.delegate is self:
            time.sleep(0.1)
        return self.medium.delegate.get_sound()

class GstreamerErrorDelegate(Medium):
    def __init__(self, message):
        self.message = message

    def get_sound(self):
        raise MediaException(self.message)

class GstreamerMedium(Medium, GstreamerDecoder):
    # All media
    duration = 0        # Not filled in
    delegate = None

    def __init__(self, filename, file=None, streaming=None):
        self.delegate = GstreamerBlockingDelegate(self)

        if file is not None:
            raise NotImplementedError('TODO: file object loading')

        if streaming is None:
            # It would be nice if we could choose to stream media < 5 secs,
            # for example, but unfortunately Gstreamer duration messages
            # don't ever work.
            streaming = False

        self.filename = filename
        self.file = file
        self.streaming = streaming

        # TODO cleanup into device.load()
        if self.streaming:
            self.delegate = GstreamerOpenALStreamingMedium(self.filename, self.file)
        else:
            self.pipeline = self._create_decoder_pipeline(filename, file)

            # All elements that _might_ be attached to the decodebin must
            # be in the pipeline before it goes to PAUSED, otherwise they never
            # receive buffers.  Why??
            self.sink = gst.gst_element_factory_make('openalstaticsink', 'sink')
            gst.gst_bin_add(self.pipeline, self.sink)
            gst.gst_element_link(self.convert, self.sink)

            # Set to pause state so that pads are detected (in another thread)
            # as soon as possible.
            gst.gst_element_set_state(self.pipeline, gstreamer.GST_STATE_PAUSED)
 
    def _new_audio_pad(self, pad, channels, depth, sample_rate):
        '''Create and connect an OpenALStaticSink for the given source pad.'''
        convertpad = gst.gst_element_get_pad(self.convert, 'sink')
        gst.gst_pad_link(pad, convertpad)
        gst.gst_object_unref(convertpad)

        sink = self.sink
        pysink = OpenALStaticSinkElement.get_instance(self.sink)
        pysink.init()
        pysink.media = self

        # Set state to playing to push all the content into the sink straight
        # away (where it is held in OpenAL buffers).
        gst.gst_element_set_state(self.pipeline, gstreamer.GST_STATE_PLAYING)

        self.delegate = pysink        
        self.channels = channels

    def _no_more_pads(self, decodebin, data):
        if isinstance(self.delegate, GstreamerBlockingDelegate):
            self.delegate = GstreamerErrorDelegate('No useable streams')

    def get_sound(self):
        return self.delegate.get_sound()

# Device interface
# --------------------------------------------------------------------------

def load(filename, file=None, streaming=None):
    return GstreamerMedium(filename, file, streaming)

def dispatch_events():
    global sounds

    gstreamer.heartbeat()
    for sound in sounds:
        sound.dispatch_events()
    sounds = [sound for sound in sounds if not sound.finished]

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
    while sounds:
        sounds.pop()
    import gc
    gc.collect()

# Active sounds
sounds = []


