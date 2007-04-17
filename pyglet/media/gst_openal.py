#!/usr/bin/python
# $Id$

import ctypes
import time

from pyglet.media import Sound, Medium, MediaException
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

# OpenAL streaming
# -----------------------------------------------------------------------------

class OpenALStreamingSinkPad(gstreamer.Pad):
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

class OpenALStreamingSinkElement(gstreamer.Element):
    name = 'openalstreamingsink'
    klass = 'audio/openal-streaming-sink'
    description = 'Sink to streaming OpenAL buffers'
    author = 'pyglet.org'

    instance_struct = gstreamer.GstAudioSink
    class_struct = gstreamer.GstAudioSinkClass
    parent_type = gstaudio.gst_audio_sink_get_type

    pad_templates = (OpenALStreamingSinkPad,)
    pad_instances = [] # GstAudioSink takes care of creating the pad

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
        self.bytes_per_sample = spec.contents.bytes_per_sample

        print spec.contents.buffer_time
        print spec.contents.latency_time
        #spec.contents.segsize = 100
        #spec.contents.segtotal = 8

        self.format = openal.get_format(spec.contents.channels, 
                                        spec.contents.depth)
        self.rate = spec.contents.rate
        return True

    count = 0
    def write(self, data, length):
        self.count += 1
        #print 'write', data, length, self.count

        albuffer = openal.buffer_pool.get()
        al.alBufferData(albuffer, self.format, 
                        data, length,
                        self.rate)

        self.sound._add_buffer(albuffer)
        return length

    def delay(self):
        print 'delay'
        return 0

    def unprepare(self):
        print 'unprepare!'
        return 1

    def close(self):
        print 'close!'
        return 1

    def reset(self):
        print 'reset'

class OpenALStreamingSound(openal.OpenALSound, 
                           GstreamerDecoder):
    def __init__(self, filename, file):
        super(OpenALStreamingSound, self).__init__()
        self.pipeline = self._create_decoder_pipeline(filename, file)
        self.bus = gst.gst_pipeline_get_bus(self.pipeline)

        self.sink = gst.gst_element_factory_make('openalstreamingsink', 'sink')
        self.pysink = OpenALStreamingSinkElement.get_instance(self.sink)
        self.pysink.sound = self
        gst.gst_bin_add(self.pipeline, self.sink)

        gst.gst_element_set_state(self.pipeline, gstreamer.GST_STATE_PAUSED)

    def _new_audio_pad(self, pad, channels, depth, sample_rate):
        sinkpad = gst.gst_element_get_pad(self.sink, 'sink')
        gst.gst_pad_link(pad, sinkpad)
        gst.gst_object_unref(sinkpad)

    def _add_buffer(self, buffer):
        al.alSourceQueueBuffers(self.source, 1, buffer)
        if self.play_when_buffered:
            al.alSourcePlay(self.source) # TODO merge into openal.py

    def play(self):
        self.play_when_buffered = True
        gst.gst_element_set_state(self.pipeline, gstreamer.GST_STATE_PLAYING)

    def cleanup(self):
        '''Dispose of GST elements to prevent stale callbacks.'''
        del self.pysink
        gst.gst_object_unref(self.sink)
        del self.sink

        gst.gst_object_unref(self.bus)
        del self.bus

        gst.gst_object_unref(self.pipeline)
        del self.pipeline

        self.dispatch_events = lambda self: None

    def dispatch_events(self):
        super(OpenALStreamingSound, self).dispatch_events()
        print 'pp', self._processed_buffers, self._queued_buffers

        msg = gst.gst_bus_poll(self.bus, gstreamer.GST_MESSAGE_ANY, 0)
        if msg:
            print 'msg', msg.contents.type
        if msg.contents.type == gstreamer.GST_MESSAGE_STATE_CHANGED:
            state = gstreamer.GstState()
            pending = gstreamer.GstState()
            gst.gst_element_get_state(self.pipeline,
                                      ctypes.byref(state),
                                      ctypes.byref(pending),
                                      0)
            print 'state change', state, pending
            if pending.value == gstreamer.GST_STATE_VOID_PENDING:
                gst.gst_element_set_state(self.pipeline, 
                                          gstreamer.GST_STATE_NULL)
                #self.finished = True

        # This never happens; instead we get the VOID_PENDING state, above.
        if msg.contents.type == gstreamer.GST_MESSAGE_EOS:
            self.finished = True
            print 'done'

class OpenALStreamingMedium(Medium):
    def __init__(self, filename, file):
        self.filename = filename
        self.file = file

    def get_sound(self):
        sound = OpenALStreamingSound(self.filename, self.file)
        sounds.append(sound)
        import gc
        print gc.get_referrers(sound)
        return sound

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

        self.format = openal.get_format(channels.value, depth.value)
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
            self.delegate = OpenALStreamingMedium(self.filename, self.file)
        else:
            self.pipeline = self._create_decoder_pipeline(filename, file)

            # All elements that _might_ be attached to the decodebin must
            # be in the pipeline before it goes to PAUSED, otherwise they never
            # receive buffers.  Why??
            self.sink = gst.gst_element_factory_make('openalstaticsink', 'sink')
            gst.gst_bin_add(self.pipeline, self.sink)

            # Set to pause state so that pads are detected (in another thread)
            # as soon as possible.
            gst.gst_element_set_state(self.pipeline, gstreamer.GST_STATE_PAUSED)
 
    def _new_audio_pad(self, pad, channels, depth, sample_rate):
        '''Create and connect an OpenALStaticSink for the given source pad.'''
        sink = self.sink
        sinkpad = gst.gst_element_get_pad(self.sink, 'sink')
        pysink = OpenALStaticSinkElement.get_instance(self.sink)
        pysink.init()
        pysink.media = self
        gst.gst_pad_link(pad, sinkpad)
        gst.gst_object_unref(sinkpad)

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


