#!/usr/bin/python

import pyglet
pyglet.options["debug_input"] = True

window = pyglet.window.Window()
tablets = pyglet.input.get_tablets()
canvases = []

if tablets:
    print('Tablets:')
    for i, tablet in enumerate(tablets):
        print('  (%d) %s' % (i + 1, tablet.name))
    print('Press number key to open corresponding tablet device.')
else:
    print('No tablets found.')


@window.event
def on_text(text):
    try:
        index = int(text) - 1
    except ValueError:
        return

    if not (0 <= index < len(tablets)):
        return

    name = tablets[index].name

    try:
        canvas = tablets[index].open(window)
    except pyglet.input.DeviceException:
        print('Failed to open tablet %d on window' % index)
        return

    print('Opened %s' % name)

    @canvas.event
    def on_enter(cursor):
        print('%s: on_enter(%r)' % (name, cursor))

    @canvas.event
    def on_leave(cursor):
        print('%s: on_leave(%r)' % (name, cursor))

    @canvas.event
    def on_motion(cursor, x, y, pressure, tilt_x, tilt_y, buttons):
        print('%s: on_motion(%r, %r, %r, %r, %r, %r, %r)' % (name, cursor, x, y, pressure, tilt_x, tilt_y, buttons))

    # If ExpressKey is supported for the OS, the events will be supported.
    if 'on_express_key_press' in canvas.event_types:
        @canvas.event
        def on_express_key_press(control_id, location_id):
            print(f'on_express_key_press(control_id={control_id}, location_id={location_id}')

        @canvas.event
        def on_express_key_release(control_id, location_id):
            print(f'on_express_key_release(control_id={control_id}, location_id={location_id}')

@window.event
def on_mouse_press(x, y, button, modifiers):
    print('on_mouse_press(%r, %r, %r, %r' % (x, y, button, modifiers))


@window.event
def on_mouse_release(x, y, button, modifiers):
    print('on_mouse_release(%r, %r, %r, %r' % (x, y, button, modifiers))


pyglet.app.run()
