#!/usr/bin/env python

'''
Ref: http://www.inb.uni-luebeck.de/~boehme/using_libavcodec.html

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import ctypes
from ctypes import util
import os
import time

def get_library(name):
    path = util.find_library(name)
    if not path:
        # HACK libavformat/libavcodec do not have SONAME filled in, so
        # find_library doesn't find them!
        if os.path.exists('/usr/lib/lib%s.so' % name):
            path = '/usr/lib/lib%s.so' % name
        else:
            raise ImportError('%s not found' % name)
    return ctypes.cdll.LoadLibrary(path)

import lib_avformat as avformat
import lib_avcodec as avcodec
import lib_openal as al
import lib_alc as alc

def init():
    avformat.av_register_all()

def open(filename):
    context = ctypes.POINTER(avformat.AVFormatContext)()
    result = avformat.av_open_input_file(
        ctypes.byref(context), filename, None, 0, None)
    if result != 0:
        raise Exception('Cannot open file')

    result = avformat.av_find_stream_info(context)
    if result < 0:
        raise Exception('Cannot find streams in file')

    # Pretty
    avformat.dump_format(context, 0, filename, False)
    
    return context

CODEC_TYPE_UNKNOWN = -1
CODEC_TYPE_VIDEO = 0
CODEC_TYPE_AUDIO = 1
CODEC_TYPE_DATA = 2

def get_audio_stream(container):
    for i in range(container.contents.nb_streams):
        if (container.contents.streams[i].contents.codec.codec_type ==
            CODEC_TYPE_AUDIO):
            return i
    raise Exception('No audio stream in container')

def get_codec(container, stream):
    context = container.contents.streams[stream].contents.codec
    codec = avcodec.avcodec_find_decoder(context.codec_id)
    if not codec:
        raise Exception('No codec found for stream ')

    # XXX need to set truncated flag?

    # TODO link lib_avcodec and lib_avformat
    context = ctypes.cast(ctypes.pointer(context),
                          ctypes.POINTER(avcodec.AVCodecContext))
    result = avcodec.avcodec_open(context, codec)
    if result < 0:
        raise Exception('Cannot open codec for stream')

    return context

class BufferPool(list):
    def get_buffer(self):
        if not self:
            buffer = al.ALuint()
            al.alGenBuffers(1, buffer)
        else:
            buffer = self.pop(0)
        return buffer

    def replace_buffer(self, buffer):
        self.insert(0, buffer)

class AVCodecDecoder(object):
    def __init__(self, container, stream):
        self.codec = get_codec(container, stream)
        if self.codec.contents.channels == 1:
            self.buffer_format = al.AL_FORMAT_MONO16
        elif self.codec.contents.channels == 2:
            self.buffer_format = al.AL_FORMAT_STEREO16
        else:
            raise Exception('Invalid number of channels')
        self.sample_rate = self.codec.contents.sample_rate

        self.container = container
        self.stream = stream
        self.packet = avformat.AVPacket()
        self.sample_buffer = \
            (ctypes.c_int16 * (avcodec.AVCODEC_MAX_AUDIO_FRAME_SIZE/2))() 

        self.read_packet()

    def read_packet(self):
        while True:
            if self.packet.data:
                self.packet.data = None
                self.packet.size = 0

            if avformat.av_read_packet(self.container, self.packet) < 0:
                break

            if self.packet.stream_index == self.stream:
                break

        self.packet_data = self.packet.data
        self.packet_size = self.packet.size

    def fill_buffer(self, buffer):
        if self.packet_size <= 0:
            self.read_packet()
        
        if self.packet_size == 0: # EOS
            return False

        sample_buffer_size = ctypes.c_int()
        len = avcodec.avcodec_decode_audio(self.codec, 
                                           self.sample_buffer,
                                           sample_buffer_size,
                                           self.packet_data,
                                           self.packet_size)
        if len < 0:
            # Error, skip frame
            raise Exception('frame error TODO')

        if sample_buffer_size.value > 0:
            al.alBufferData(buffer, self.buffer_format, 
                            self.sample_buffer, sample_buffer_size.value,
                            self.sample_rate)

        # Advance buffer pointer
        self.packet_data = ctypes.c_uint8.from_address(
                                ctypes.addressof(self.packet_data) + len)
        self.packet_size -= len

        return True
        
if __name__ == '__main__':
    import sys

    # openal
    device = alc.alcOpenDevice(None)
    if not device:
        raise Exception('No OpenAL device.')

    alcontext = alc.alcCreateContext(device, None)
    alc.alcMakeContextCurrent(alcontext)

    source = al.ALuint()
    al.alGenSources(1, source)

    pool = BufferPool()

    # avcodec
    init()
    container = open(sys.argv[1])
    stream = get_audio_stream(container)
    
    decoder = AVCodecDecoder(container, stream)
    
    while True:
        buffer = pool.get_buffer()
        if not decoder.fill_buffer(buffer):
            break
        al.alSourceQueueBuffers(source, 1, buffer)

    al.alSourcePlay(source)

    while True:
        value = al.ALint()
        al.alGetSourcei(source, al.AL_SOURCE_STATE, value)
        if value.value == al.AL_STOPPED:
            break

        time.sleep(1)
