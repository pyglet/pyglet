#!/usr/bin/python
# $Id$

import ctypes
import time

from pyglet.media import Sound, Medium
from pyglet.media import gstreamer
from pyglet.media.gstreamer import gst, gstaudio, gobject
from pyglet.media import lib_openal as al
from pyglet.media import openal

DecodebinNewDecodedPad = ctypes.CFUNCTYPE(None,
    ctypes.POINTER(gstreamer.GstElement), ctypes.POINTER(gstreamer.GstPad),
    ctypes.c_int, ctypes.c_void_p)
DecodebinNoMorePads = ctypes.CFUNCTYPE(None,
    ctypes.POINTER(gstreamer.GstElement), ctypes.c_void_p)

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

        return pipeline

    def _new_decoded_pad(self, decodebin, pad, last, data):
        pass

    def _no_more_pads(self, decodebin, data):
        pass


# OpenAL streaming
# -----------------------------------------------------------------------------

'''
class OpenALStreamingSinkElement(gstreamer.Element):
    name = 'openalstreamingsink'
    klass = 'audio/openal-streaming-sink'
    description = 'Sink to streaming OpenAL buffers'
    author = 'pyglet.org'

    instance_struct = gstreamer.GstAudioSink
    class_struct = gstreamer.GstAudioSinkClass
    parent_type = gstaudio.gst_audio_sink_get_type

    pad_templates = (OpenALStaticSinkPad,)

    vmethods = (
        'open', 
        'prepare', 
        'write', 
        'unprepare', 
        'close', 
        'delay',
        'reset')

    def open(self):
        print 'open!'
        return True

    def prepare(self, spec):
        print 'prepare!', self, spec
        print spec.contents.sign, spec.contents.bigend, spec.contents.depth
        print spec.contents.rate, spec.contents.channels
        return True

    def write(self, data, length):
        print 'write', length
        return 0

    def delay(self):
        print 'delay'
        return 0

    def unprepare(self):
        print 'unprepare!'

    def close(self):
        print 'close!'

    def reset(self):
        print 'reset'
'''

# OpenAL static
# -----------------------------------------------------------------------------

class OpenALStaticSinkPad(gstreamer.Pad):
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

        self.format = {
            (1,  8): al.AL_FORMAT_MONO8,
            (1, 16): al.AL_FORMAT_MONO16,
            (2,  8): al.AL_FORMAT_STEREO8,
            (2, 16): al.AL_FORMAT_STEREO16,
        }[(channels.value, depth.value)]

        self.element.channels = channels.value
        self.element.rate = rate.value

        return True

    def chain(self, this, buffer):
        albuffer = openal.buffer_pool.get()
        al.alBufferData(albuffer, self.format, 
                        buffer.contents.data, buffer.contents.size,
                        self.rate)

        self.element._add_buffer(albuffer)
        return gstreamer.GST_FLOW_OK

    def event(self, this, event):
        if event.contents.type == gstreamer.GST_EVENT_EOS:
            self.element._finished_buffering()
            return True
        return False

class OpenALStaticSinkElement(gstreamer.Element, Medium):
    name = 'openalstaticsink'
    klass = 'audio/openal-static-sink'
    description = 'Sink to static OpenAL buffers'
    author = 'pyglet.org'

    pad_templates = (OpenALStaticSinkPad,)
    pad_instances = [
        ('sink', OpenALStaticSinkPad),
    ]

    def init(self):
        self.buffers = []
        self.sounds = []
        self.buffering = True

    def _add_buffer(self, buffer):
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
    version = '0.1'
    license = 'LGPL'
    package = 'pyglet'
    origin = 'http://www.pyglet.org'

    #elements = (OpenALStreamingSinkElement, OpenALStaticSinkElement)
    elements = (OpenALStaticSinkElement,)

# ALSA streaming
# -----------------------------------------------------------------------------

class ALSAStreamingMedium(Medium):
    def __init__(self, filename, file):
        self.filename = filename
        self.file = file

    def get_sound(self):
        return ALSAStreamingSound(self.filename, self.file)

class ALSAStreamingSound(Sound, GstreamerDecoder):
    def __init__(self, filename, file):
        self.pipeline = self._create_decoder_pipeline(filename, file)

        convert = gst.gst_element_factory_make('audioconvert', 'aconv')
        sink = gst.gst_element_factory_make('alsasink', 'sink')
        gst.gst_bin_add_many(self.pipeline, convert, sink, None)
        gst.gst_element_link(convert, sink)
        self.audio_element = convert

        gst.gst_element_set_state(self.pipeline, gstreamer.GST_STATE_PAUSED)

    def _new_decoded_pad(self, decodebin, pad, last, data):
        '''Called by decodebin when a source pad is created'''
        gst.gst_element_link(decodebin, self.audio_element)

    def play(self):
        gst.gst_element_set_state(self.pipeline, gstreamer.GST_STATE_PLAYING)

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
        raise Exception(self.message)

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

        self.pipeline = self._create_decoder_pipeline(filename, file)

        # All elements that _might_ be attached to the decodebin must
        # be in the pipeline before it goes to PAUSED, otherwise they never
        # receive buffers.  Why??
        self.openalstaticsink = \
            gst.gst_element_factory_make('openalstaticsink', 'sink')
        gst.gst_bin_add(self.pipeline, self.openalstaticsink)

        # Set to pause state so that pads are detected (in another thread) as
        # soon as possible.
        gst.gst_element_set_state(self.pipeline, gstreamer.GST_STATE_PAUSED)
 
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
            self.channels = channels.value
            
            if self.channels == 1 and not self.streaming:
                self._sink_static_openal(pad)
            else:
                self.streaming = True
                self._sink_streaming_alsa(pad)
        elif name.startswith('video/x-raw'):
            pass

    def _no_more_pads(self, decodebin, data):
        if isinstance(self.delegate, GstreamerBlockingDelegate):
            self.delegate = GstreamerErrorDelegate('No useable streams')

    def _sink_static_openal(self, pad):
        '''Create and connect an OpenALStaticSink for the given source pad.'''
        sink = self.openalstaticsink
        sinkpad = gst.gst_element_get_pad(sink, 'sink')
        pysink = OpenALStaticSinkElement.get_instance(sink)
        pysink.init()
        pysink.media = self
        gst.gst_pad_link(pad, sinkpad)
        gst.gst_object_unref(sinkpad)

        # Set state to playing to push all the content into the sink straight
        # away (where it is held in OpenAL buffers).
        gst.gst_element_set_state(self.pipeline, gstreamer.GST_STATE_PLAYING)

        self.delegate = pysink

    def _sink_streaming_alsa(self, pad):
        self.delegate = ALSAStreamingMedium(self.filename, self.file)
        # TODO cleanup self.pipeline

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
    openal.init()
    gstreamer.init()
    openal_plugin = OpenALPlugin()
    openal_plugin.register()

def cleanup():
    pass

# Active sounds
sounds = []


