#!/usr/bin/python
# $Id$

'''Media playback interface.

'''

import sys

if sys.platform == 'linux2':
    from pyglet.media import gst_openal
    device = gst_openal
else:
    raise ImportError('pyglet.media not yet supported on %s' % sys.platform)

load = device.load
dispatch_events = device.dispatch_events
