#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import pyglet
import input

devices = input.get_devices()
show_all = True

window = pyglet.window.Window(1024, 768)
batch = pyglet.graphics.Batch()

class TrackedElement(object):
    def __init__(self, element):
        self.element = element
        self.label = pyglet.text.Label(element.name, 
            font_size=8,
            x=x, y=y, anchor_y='top', batch=batch)

    def update(self):
        self.label.text = '%s: %s' % (self.element.name, 
                                      self.element.get_value())

x = 0
tracked_elements = []
for device in devices:
    y = window.height
    label = pyglet.text.Label(device.name or '', x=x, y=y, anchor_y='top', batch=batch)
    y -= label.content_height

    try:
        device.open()
        for element in device.elements:
            if not show_all and not element.known:
                continue

            tracked_element = TrackedElement(element)
            tracked_elements.append(tracked_element)
            y -= tracked_element.label.content_height
            if y < 0:
                break
    except input.InputDeviceExclusiveException:
        msg = '(Device is exclusive)'
        label = pyglet.text.Label(msg, x=x, y=y, anchor_y='top', batch=batch)
        y -= label.content_height

    x += window.width / len(devices)

@window.event
def on_draw():
    window.clear()
    batch.draw()

def update(dt):
    for tracked_element in tracked_elements:
        tracked_element.update()
pyglet.clock.schedule(update)

pyglet.app.run()

for device in devices:
    device.close()
