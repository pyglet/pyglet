#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import pyglet

import xinput
window = pyglet.window.Window()

class XInputEventLogger(object):
    def __init__(self, device):
        self.device = device

    def on_button_press(self, button):
        print self.device.name, 'on_button_press(%d)' % button

    def on_button_release(self, button):
        print self.device.name, 'on_button_release(%d)' % button

    def on_motion(self, axis_data, x, y):
        print self.device.name, 'on_motion(%r, %r, %r)' % (axis_data, x, y)

    def on_proximity_in(self):
        print self.device.name, 'on_proximity_in()'

    def on_proximity_out(self):
        print self.device.name, 'on_proximity_out()'

for device in xinput.get_devices(window.display):
    try:
        device.open()
        instance = device.attach(window)
        instance.push_handlers(XInputEventLogger(device))
        print "Opened device %s" % device.name
    except:
        print "Couldn't open device %s" % device.name

pyglet.app.run()
