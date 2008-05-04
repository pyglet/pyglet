#!/usr/bin/python
# $Id:$

import pyglet

import wintab

window = pyglet.window.Window()

class WintabLogger(object):
    def on_cursor_enter(self, cursor):
        print 'on_cursor_enter(%r)' % cursor

    def on_cursor_leave(self, cursor):
        print 'on_cursor_leave(%r)' % cursor

    def on_motion(self, cursor, x, y, pressure):
        print 'on_motion(%r, %r, %r, %r)' % (cursor, x, y, pressure)

wintab.check_version()
for device in wintab.get_devices():
    print 'Opened device', device
    instance = device.open(window)
    instance.push_handlers(WintabLogger())

pyglet.app.run()
