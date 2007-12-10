#!/usr/bin/python
# $Id:$

# Play an audio file with DirectShow.  Tested ok with MP3, WMA, MID, WAV, AU.
# Caveats:
# - Requires a filename (not from memory or stream yet).  Looks like we need
#   to manually implement a filter which provides an output IPin.  Lot of
#   work.
# - Theoretically can traverse the graph to get the output filter, which by
#   default is supposed to implement IDirectSound3DBuffer, for positioned
#   sounds.  Untested.
# - Requires comtypes.  Can work around this in future by implementing the
#   small subset of comtypes ourselves (or including a snapshot of comtypes in
#   pyglet).

import ctypes
from comtypes import client
import sys
import time

filename = sys.argv[1]

qedit = client.GetModule('qedit.dll') # DexterLib
quartz = client.GetModule('quartz.dll') # 

CLSID_FilterGraph = '{e436ebb3-524f-11ce-9f53-0020af0ba770}'

filter_graph = client.CreateObject(CLSID_FilterGraph,
                                   interface=qedit.IFilterGraph)
filter_builder = filter_graph.QueryInterface(qedit.IGraphBuilder)
filter_builder.RenderFile(filename, None)

enum = filter_graph.EnumFilters()
filter, count = enum.Next(1)
while filter:
    filter_name = u''.join(
        [unichr(c) for c in filter.QueryFilterInfo().achName]).strip(u'\0')
    if 'DirectSound' in filter_name:
        output_filter = filter
    else:
        del filter
    filter, count = enum.Next(1)
del enum

media_control = filter_graph.QueryInterface(quartz.IMediaControl)
media_control.Run()

try:
    # Look at IMediaEvent interface for EOS notification
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass

# Need these because finalisers don't have enough context to clean up after
# themselves when script exits.
del media_control
del filter_builder
del filter_graph
