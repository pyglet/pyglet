#!/usr/bin/python
# $Id$

import ctypes

from pyglet.media import gstreamer
from pyglet.media.gstreamer import gst, gstaudio, gobject
from pyglet.media import gst_plugin
from pyglet.media import lib_openal as al
from pyglet.media import openal

class OpenALStaticSinkPad(gst_plugin.Pad):
    name = 'sink'
    direction = gst_plugin.GST_PAD_SINK
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
        self.element.sound.add_buffer(albuffer)
        return gst_plugin.GST_FLOW_OK

    def event(self, this, event):
        if event.contents.type == gst_plugin.GST_EVENT_EOS:
            self.element.sound.finished_buffering()
            return True
        return False

class OpenALStaticSinkElement(gst_plugin.Element):
    name = 'openalstaticsink'
    klass = 'audio/openal-static-sink'
    description = 'Sink to static OpenAL buffers'
    author = 'pyglet.org'

    pad_templates = (OpenALStaticSinkPad,)
    pad_instances = [
        ('sink', OpenALStaticSinkPad),
    ]

    # Filled in by GstreamerStaticSound when it has instance
    sound = None

class GstreamerStaticSound(openal.Sound):
    def __init__(self, uri):
        self.buffers = []
        self.sources = []
        self.buffering = True

        sink = gst.gst_element_factory_make('openalstaticsink', 'alsink')
        element = OpenALStaticSinkElement.get_instance(sink)
        element.sound = self
        playbin = gst.gst_element_factory_make('playbin', 'play')
        gobject.g_object_set(playbin, 'audio-sink', sink, None)
        gobject.g_object_set(playbin, 'uri', uri, None)

        gst.gst_element_set_state(playbin, gstreamer.GST_STATE_PLAYING)

    def add_buffer(self, buffer):
        self.buffers.append(buffer)
        if self.buffering:
            for source in self.sources:
                al.alSourceQueueBuffers(source.source, 1, buffer)
                if source.play_when_buffered:
                    source.play()

    def get_source(self):
        source = openal.Source()
        sources.append(source)
        for buffer in self.buffers:
            al.alSourceQueueBuffers(source.source, 1, buffer)
        if self.buffering:
            self.sources.append(source)
        return source

    def finished_buffering(self):
        self.buffering = False
        self.sources = None

class OpenALStreamingSinkElement(gst_plugin.Element):
    name = 'openalstreamingsink'
    klass = 'audio/openal-streaming-sink'
    description = 'Sink to streaming OpenAL buffers'
    author = 'pyglet.org'

    instance_struct = gst_plugin.GstAudioSink
    class_struct = gst_plugin.GstAudioSinkClass
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

class OpenALPlugin(gst_plugin.Plugin):
    name = 'openal-plugin'
    description = 'OpenAL plugin'
    version = '0.1'
    license = 'LGPL'
    package = 'pyglet'
    origin = 'http://www.pyglet.org'

    elements = (OpenALStreamingSinkElement, OpenALStaticSinkElement)


openal.init()
gstreamer.init()
openal_plugin = OpenALPlugin()
openal_plugin.register()

# Active sources
sources = []

# Device interface
# --------------------------------------------------------------------------

def load(filename, file=None, streaming=None):
    if streaming is None:
        streaming = False

    uri = 'file://%s' % filename

    if not streaming:
        return GstreamerStaticSound(uri)

    raise NotImplementedError('streaming')
    # TODO streaming, file objects 

def dispatch_events():
    global sources
    for source in sources:
        source.pump()
    sources = [source for source in sources if not source.finished]
