#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import pyglet

import xinput
window = xinput.XlibWithXinputWindow()

@window.event
def on_xinput_button_press(device, button):
    print 'button press', device, button

@window.event
def on_xinput_button_release(device, button):
    print 'button release', device, button

@window.event
def on_xinput_motion(device, axis_data, x, y):
    print 'motion', device, axis_data, x, y

@window.event
def on_xinput_proximity_in(device):
    print 'proximity in', device

@window.event
def on_xinput_proximity_out(device):
    print 'proximity out', device

for device in xinput.get_devices(window.display):
    try:
        device.open(window)
        print "Opened device %s" % device.name
    except:
        print "Couldn't open device %s" % device.name

pyglet.app.run()
