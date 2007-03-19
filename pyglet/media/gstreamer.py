#!/usr/bin/python
# $Id:$

import ctypes
from ctypes import util
import time
import sys

def get_library(name):
    path = util.find_library(name)
    if not path:
        raise ImportError('Could not find library "%s"' % name)
    return ctypes.cdll.LoadLibrary(path)

gst = get_library('gstreamer-0.10')
gstaudio = get_library('gstaudio.0.10')
glib = get_library('glib-2.0')
gobject = get_library('gobject-2.0')

GST_VERSION_MAJOR = 0
GST_VERSION_MINOR = 10
GST_VERSION_BUILD = 11

GST_STATE_PLAYING = 4

mainloop = None
mainloop_context = None

def init():
    global mainloop, mainloop_context
    glib.g_main_loop_new.restype = ctypes.c_void_p
    mainloop = glib.g_main_loop_new(None, True)
    glib.g_main_loop_get_context.restype = ctypes.c_void_p
    mainloop_context = glib.g_main_loop_get_context(mainloop)

    argc = ctypes.c_int(0)
    argv = ctypes.c_void_p()
    gst.gst_init(ctypes.byref(argc), ctypes.byref(argv))

def play(uri):
    playbin = gst.gst_element_factory_make('playbin', 'play')
    gobject.g_object_set(playbin, 'uri', uri, None)

    gst.gst_element_set_state(playbin, GST_STATE_PLAYING)

def heartbeat():
    glib.g_main_context_iteration(mainloop_context, False)

if __name__ == '__main__':
    init()
    play('file://%s' % sys.argv[1])
    while True:
        heartbeat()
        time.sleep(0.1)
