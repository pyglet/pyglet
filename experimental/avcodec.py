#!/usr/bin/env python

'''
Ref: http://www.inb.uni-luebeck.de/~boehme/using_libavcodec.html

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import ctypes
from ctypes import util
import os

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
openal = get_library('openal')

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

if __name__ == '__main__':
    import sys

    init()
    container = open(sys.argv[1])
    stream = get_audio_stream(container)
    codec = get_codec(container, stream)
    
    sample_rate = codec.contents.sample_rate
    channels = codec.contents.channels
    print 'Found %d channels at %d Hz' % (channels, sample_rate)


    samples = (ctypes.c_int16 * (avcodec.AVCODEC_MAX_AUDIO_FRAME_SIZE/2))()
    frame_size = ctypes.c_int(len(samples)*2)

    packet = avformat.AVPacket()

    while True:
        avformat.av_read_packet(container, packet)

        size = packet.size
        if size == 0:
            # EOS
            break

        inbuf = packet.data

        while size > 0:
            len = avcodec.avcodec_decode_audio(codec, samples, 
                                               ctypes.byref(frame_size),
                                               inbuf, size)
            # len: number of bytes from packet that were used
            # frame_size: number of bytes filled into 'samples'

            if len < 0:
                raise Exception('Decode error')

            if frame_size.value > 0:
                # yield these samples
                print 'Yield %d samples' % frame_size.value
                pass

            # ptr add
            inbuf = ctypes.c_uint8.from_address(
                        ctypes.addressof(inbuf) + len)
            size -= len

