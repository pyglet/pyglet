#!/usr/bin/python
# $Id:$

import ctypes
import comtypes
from comtypes import client, GUID

from pyglet.media import Sound, Medium

_qedit = client.GetModule('qedit.dll')
_quartz = client.GetModule('quartz.dll')
_dsound = client.GetModule('dx8vb.dll')

_qedit_c = ctypes.windll.LoadLibrary('qedit.dll')
_dsound_c = ctypes.windll.LoadLibrary('dsound.dll')

CLSID_FilterGraph =   '{e436ebb3-524f-11ce-9f53-0020af0ba770}'
CLSID_SampleGrabber = '{c1f400a0-3f08-11d3-9f0b-006008039e37}'
CLSID_NullRenderer =  '{c1f400a4-3f08-11d3-9f0b-006008039e37}'

MEDIATYPE_Audio =  '{73647561-0000-0010-8000-00AA00389B71}'
MEDIASUBTYPE_PCM = '{00000001-0000-0010-8000-00AA00389B71}'

INFINITE = 0xFFFFFFFF

AM_MEDIA_TYPE = _qedit._AMMediaType

PINDIR_INPUT = 0
PINDIR_OUTPUT = 1

class DirectShowStreamingSound(Sound):
    def __init__(self, filename):
        filter_graph = client.CreateObject(
            CLSID_FilterGraph, interface=_qedit.IFilterGraph)
        
        filter_builder = filter_graph.QueryInterface(_qedit.IGraphBuilder)
        filter_builder.RenderFile(filename, None)
        del filter_builder

        self._position = filter_graph.QueryInterface(_quartz.IMediaPosition)
        self._control = filter_graph.QueryInterface(_quartz.IMediaControl)
        del filter_graph

        self._control.Pause()

        self._stop_time = self._position.StopTime

    def play(self):
        self._control.Run()

    def dispatch_events(self):
        position = self._position.CurrentPosition
          
        if position >= self._stop_time:
            self.finished = True


class DirectShowStreamingMedium(Medium):
    def __init__(self, filename, file=None):
        if file is not None:
            raise NotImplementedError('TODO file objects')

        self.filename = filename

    def get_sound(self):
        sound = DirectShowStreamingSound(self.filename)
        sounds.append(sound)
        return sound
        
class DirectShow_BufferGrabber(comtypes.COMObject):
    _com_interfaces_ = [_qedit.ISampleGrabberCB]

    def __init__(self, buffers):
        self.buffers = buffers

    def ISampleGrabberCB_BufferCB(self, this, sample_time, buffer, len):
        dest = (ctypes.c_byte * len)()
        ctypes.memmove(dest, buffer, len)
        self.buffers.append(dest)
        return 0

    def ISampleGrabberCB_SampleCB(self, this, sample_time, sample):
        raise NotImplementedError('Use BufferCB instead')
        return 0

class DirectShowStaticMedium(Medium):
    def __init__(self, filename, file=None):
        filter_graph = client.CreateObject(
            CLSID_FilterGraph, interface=_qedit.IFilterGraph)

        graph_builder = filter_graph.QueryInterface(_qedit.IGraphBuilder)
        source_filter = graph_builder.AddSourceFilter(filename, filename)

        sample_grabber = client.CreateObject(
            CLSID_SampleGrabber, interface=_qedit.ISampleGrabber)
        filter_graph.AddFilter(sample_grabber, None)

        media_type = AM_MEDIA_TYPE()
        media_type.majortype = GUID(MEDIATYPE_Audio)
        media_type.subtype = GUID(MEDIASUBTYPE_PCM)
        sample_grabber.SetMediaType(media_type)
        sample_grabber.SetBufferSamples(True)

        self.buffers = []
        buffer_grabber = DirectShow_BufferGrabber(self.buffers)
        sample_grabber.SetCallback(buffer_grabber, 1)

        self._connect_filters(filter_graph, source_filter, sample_grabber)

        null_renderer = client.CreateObject(
            CLSID_NullRenderer, interface=_qedit.IBaseFilter)
        filter_graph.AddFilter(null_renderer, None)
        self._connect_filters(filter_graph, sample_grabber, null_renderer)
        
        media_filter = filter_graph.QueryInterface(_qedit.IMediaFilter)
        media_filter.SetSyncSource(None)

        control = filter_graph.QueryInterface(_quartz.IMediaControl)
        control.Run()

        media_event = filter_graph.QueryInterface(_quartz.IMediaEvent)
        media_event.WaitForCompletion(INFINITE)

        sample_grabber.GetConnectedMediaType(media_type)
        self.format = ctypes.cast(media_type.pbFormat,
                                  ctypes.POINTER(_dsound.WAVEFORMATEX)).contents

        self.sample_rate = self.format.lSamplesPerSec
        self.channels = self.format.nChannels

        print 'done'

        self.buffer = []
        for buffer in self.buffers:
            self.buffer += buffer[:]
        self.buffer = (ctypes.c_byte * len(self.buffer))(*self.buffer)

    def get_sound(self):
        return DirectShowStaticSound(self.format, self.buffer)

    def _connect_filters(self, graph, source, sink):
        source = source.QueryInterface(_qedit.IBaseFilter)
        sink = sink.QueryInterface(_qedit.IBaseFilter)
        source_pin = self._get_filter_pin(source, PINDIR_OUTPUT)
        sink_pin = self._get_filter_pin(sink, PINDIR_INPUT)

        graph_builder = graph.QueryInterface(_qedit.IGraphBuilder)
        graph_builder.Connect(source_pin, sink_pin)
        
    def _get_filter_pin(self, filter, direction):
        enum = filter.EnumPins()
        pin, count = enum.Next(1)
        while pin:
            if pin.QueryDirection() == direction:
                return pin
            pin, count = enum.Next(1)

class DirectShowStaticSound(Sound):
    def __init__(self, format, buffer):
        desc = _dsound.DSBUFFERDESC()
        desc.lFlags = _dsound.DSBCAPS_CTRL3D
        desc.lBufferBytes = len(buffer)
        desc.fxFormat = format
        desc.guid3DAlgorithm = _dsound.GUID_DS3DALG_NO_VIRTUALIZATION
        
        self.sound_buffer = directsound.CreateSoundBuffer(desc)
        self.sound_buffer.WriteBuffer(0, 0, buffer,
                                      _dsound.DSBLOCK_ENTIREBUFFER)

    def play(self):
        self.sound_buffer.Play(_dsound.DSBPLAY_DEFAULT)

# Device interface
# -----------------------------------------------------------------------------

def load(filename, file=None, streaming=None):
    if streaming is None:
        streaming = True

    if streaming:
        return DirectShowStreamingMedium(filename, file)
    else:
        return DirectShowStaticMedium(filename, file)

def dispatch_events():
    global sounds
    for sound in sounds:
        sound.dispatch_events()
    sounds = [sound for sound in sounds if not sound.finished]

directx = None
directsound = None

# TODO TODO TODO TODO 
# grab any available window and SetCooperativeLevel when possible.
from pyglet.window import Window
w = Window(visible=False)
# TODO TODO TODO TODO

def init():
    global directx
    global directsound
    directx = client.CreateObject(_dsound.DirectX8._reg_clsid_,
                                  interface=_dsound.IDirectX8)
    directsound = directx.DirectSoundCreate(None)
    directsound.SetCooperativeLevel(w._hwnd, _dsound.DSSCL_PRIORITY)

def cleanup():
    while sounds:
        sounds.pop()
    
    global directx
    global directsound
    del directsound
    del directx

sounds = []

'''
Grabbing real-time samples (e.g., for video):

size = ctypes.c_long(0)
# Need to use raw_func here because func has argtypes mangled too
# much.
GetCurrentBuffer = \
    sample_grabber._ISampleGrabber__com_GetCurrentBuffer
GetCurrentBuffer(size, None)
buffer = (ctypes.c_byte * size.value)()
GetCurrentBuffer(size, 
                 ctypes.cast(buffer, ctypes.POINTER(ctypes.c_long)))
print size, buffer[:]
'''

'''
Valid fields in format

desc.fxFormat.nSize = ctypes.sizeof(desc.fxFormat)
desc.fxFormat.nFormatTag = _dsound.WAVE_FORMAT_PCM
desc.fxFormat.nChannels = 2
desc.fxFormat.lSamplesPerSec = 22050
desc.fxFormat.nBitsPerSample = 16
desc.fxFormat.nBlockAlign = \
    (desc.fxFormat.nChannels * desc.fxFormat.nBitsPerSample) / 8
desc.fxFormat.nAvgBytesPerSec =  \
    (desc.fxFormat.lSamplesPerSec * desc.fxFormat.nBlockAlign)
'''
