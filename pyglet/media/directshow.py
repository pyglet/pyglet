#!/usr/bin/python
# $Id:$

import ctypes
from comtypes import client

from pyglet.media import Sound, Medium

_qedit = client.GetModule('qedit.dll')
_quartz = client.GetModule('quartz.dll')

CLSID_FilterGraph = '{e436ebb3-524f-11ce-9f53-0020af0ba770}'


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
        

# Device interface
# -----------------------------------------------------------------------------

def load(filename, file=None, streaming=None):
    if streaming is None:
        streaming = True

    if streaming:
        return DirectShowStreamingMedium(filename, file)
    else:
        raise NotImplementedError('TODO: non-streaming')

def dispatch_events():
    global sounds
    for sound in sounds:
        sound.dispatch_events()
    sounds = [sound for sound in sounds if not sound.finished]

sounds = []
