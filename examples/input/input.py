#!/usr/bin/env python

"""Print the details of all available input devices to stdout.
"""


__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import pyglet

window = pyglet.window.Window()
devices = pyglet.input.get_devices()


def watch_control(device, control):
    @control.event
    def on_change(value):
        print(f'{device!r}: {control!r}.on_change({value!r})')

    if isinstance(control, pyglet.input.base.Button):
        @control.event
        def on_press():
            print(f"{device!r}: {control!r}.on_press()")

        @control.event
        def on_release():
            print(f'{device!r}: {control!r}.on_release()')


print('Devices:')
for device in devices:
    print('  ', device.name, end=' ')
    try:
        device.open(window=window)
        print('OK')

        for control in device.get_controls():
            print('    ', control.name)
            watch_control(device, control)

    except pyglet.input.DeviceException:
        print('Fail')

pyglet.app.run()
