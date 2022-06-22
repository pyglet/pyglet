Working with other input devices
================================

pyglet's :py:mod:`~pyglet.input` module allows you to accept input
from any USB human interface device (HID). High-level abstractions are
provided for working with game controllers, joysticks, and the Apple
Remote. The game controller abstraction is suited for modern gamepads,
such as are found on home video game consoles. These types of controllers
have a strictly defined set of inputs. The joystick abstraction is more
generalized, and works with devices with an arbitrary number of buttons,
axis, and hats. This includes devices like steering wheels, joysticks
used for flight simulators, and just about anything else. For most types
of games, the Controller abstraction is usually the better choice.
For advanced use cases, it's also possible to access the low-level
devices directly.

The :py:mod:`~pyglet.input` module provides several methods for querying
devices, and a ControllerManager class for hot-plugging of Controllers::

    # get a list of all low-level devices:
    devices = pyglet.input.get_devices()

    # get a list of all controllers:
    controllers = pyglet.input.get_controllers()

    # get a list of all joysticks:
    joysticks = pyglet.input.get_controllers()

    # get a list of tablets:
    tablets = pyglet.input.get_tablets()

    # get an Apple Remote, if available:
    remote = pyglet.input.get_apple_remote()

    # create a ControllerManager instance:
    controller_manager = pyglet.input.ControllerManager()


Using Controllers
-----------------

Controllers have a strictly defined set of inputs that mimic the
layout of popular video game console Controllers. This includes two
analog sticks, a directional pad (dpad), face and shoulder buttons,
as well as start/back/guide and stick press buttons. Many controllers
also include the ability to play rumble effects (vibration).
The following platform interfaces are used for Controller support:

    .. list-table::
        :header-rows: 1

        * - platform
          - interface
          - notes

        * - Linux
          - evdev
          -

        * - Windows
          - DirectInput & Xinput
          - rumble not implemented on DirectInput

        * - MacOSX
          - IOKit
          - rumble not yet implemented

Before using a controller, you must find it and open it. A ControllerManager
class is provided to allow hot-plugging of Controllers, but they can also
be opened manually. To manually get a list of all controllers currently
connected to your computer, call pyglet.input.get_controllers()::

    controllers = pyglet.input.get_controllers()

Then choose a controller from the list and call `Controller.open()` to open it::

    if controllers:
        controller = controllers[0]

    controller.open()

Once opened, you you can start receiving data from the the inputs.
A variety of analog and digital :py:class:`~pyglet.input.Control` types
are defined, which are automatically normalized to consistent ranges. The
following analog controls are available:

    .. list-table::
        :header-rows: 1

        * - name
          - type
          - range

        * - leftx
          - float
          - -1,1

        * - lefty
          - float
          - -1,1

        * - rightx
          - float
          - -1,1

        * - righty
          - float
          - -1,1

        * - lefttrigger
          - float
          - 0,1

        * - lefttrigger
          - float
          - 0,1

The following digital controls are available:

    .. list-table::
        :header-rows: 1

        * - Name
          - notes
        * - a
          - the "south" face button
        * - b
          - the "east" face button
        * - x
          - the "west" face button
        * - y
          - the "north" face button
        * - leftshoulder
          -
        * - rightshoulder
          -
        * - start
          - called "options" on some controllers
        * - back
          - called "select" or "share" on some controllers
        * - guide
          - usually in the center, with a company logo
        * - leftstick
          - pressing in the left analog stick
        * - rightstick
          - pressing in the right analog stick
        * - dpleft
          -
        * - dpright
          -
        * - dpup
          -
        * - dpdown
          -

These values can be read in two ways. All controls listed above are properties
on the controller instance, so they can be manually queried in your game loop::

    controller_instance.a       # boolean
    controller_instance.leftx   # float


Alternatively, since controllers are a subclass of :py:class:`~pyglet.event.EventDispatcher`,
events will be dispatched when any of the values change. This is generally the
recommended way to handle input, since it reduces the chance of "missed" button
presses due to slow polling. The different controls are grouped into the following
event types:

    .. list-table::
        :header-rows: 1

        * - Event
          - Arguments
          - types

        * - on_button_press
          - controller, button_name
          - :py:class:`~pyglet.input.Controller`, `str`

        * - on_button_release
          - controller, button_name
          - :py:class:`~pyglet.input.Controller`, `str`

        * - on_stick_motion
          - controller, stick_name, x_value, y_value
          - :py:class:`~pyglet.input.Controller`, `str`, `float`, `float`

        * - on_dpad_motion
          - controller, left, right, up, down
          - :py:class:`~pyglet.input.Controller`, `bool`, `bool`, `bool`, `bool`

        * - on_trigger_motion
          - controller, trigger_name, value
          - :py:class:`~pyglet.input.Controller`, `str`, `float`


Here is how you would handle the analog events::

    @controller.event
    def on_stick_motion(controller, name, x_value, y_value):
        # Optionally enforce a "deadzone"

        if name == "leftstick":
            # Do something with the x/y_values
        elif name == "rightstick":
            # Do something with the x/y_values

    @controller.event
    def on_trigger_motion(controller, name, value):

        if name == "lefttrigger":
            # Do something with the value
        elif name == "righttrigger":
            # Do something with the value

Here is how you would handle the digital events::

    @controller.event
    def on_button_press(controller, button_name):
        if button_name == 'a':
            # start firing
        elif button_name == 'b':
            # do something else


    @controller.event
    def on_button_release(controller, button_name):
        if button_name == 'a':
            # stop firing
        elif button_name == 'b':
            # do something else

Finally, the directional pad event can be handled like this::

    @controller.event
    def on_dpad_motion(controller, dpleft, dpright, dpup, dpdown):
        if dpup:
            # move up
        if dpdown:
            # move down
        if dpleft:
            # move left
        if dpright:
            # move right

Rumble
^^^^^^

Many controllers also support playing rumble (vibration) effects. There
are both strong and weak effects, which can be played independently::

    controller.rumble_play_weak(strength, duration=0.5)
    controller.rumble_play_strong(strength, duration=0.5)

The `strength` parameter should be on a scale of 0-1. Values outside of
this range will be clamped. The optional `duration` parameter is in seconds.
The maximum duration can vary from platform to platform, but is usually
at least 5 seconds. If you call play again while an existing effect is
still playing, it will replace the current one. You can also stop
playback of a rumble effect at any time::

    controller.rumble_stop_weak()
    controller.rumble_stop_strong()


ControllerManager
^^^^^^^^^^^^^^^^^

To simplify hot-plugging of Controllers, the :py:class:`~pyglet.input.ControllerManager`
class is available. This class has a `get_controllers()` method
which will return a list of all currently connected Controllers.
There are also `on_connect` and `on_disconnect` events, which will
dispatch a Controller instance whenever one is connected or disconnected.
If case a previously connected Controller is re-connected, the same
instance will be returned when possible.

To use a ControllerManager, first create an instance::

    manager = pyglet.input.ControllerManager()

You can then query the currently connected controllers, similar to
doing it directly::

    controllers = manager.get_controllers()

As usual, choose a controller from the list and call `Controller.open()` to open it::

    if controllers:
        controller = controllers[0]

    controller.open()

To handle controller connections, attach handlers to the following methods::

    @manager.event
    def on_connect(controller):
        print(f"Connected:  {controller}")

    @manager.event
    def on_disconnect(controller):
        print(f"Disconnected:  {controller}")


Using Joysticks
---------------

Before using a joystick, you must find it and open it.  To get a list
of all joystick devices currently connected to your computer, call
:py:func:`pyglet.input.get_joysticks`::

    joysticks = pyglet.input.get_joysticks()

Then choose a joystick from the list and call `Joystick.open` to open
the device::

    if joysticks:
        joystick = joysticks[0]
    joystick.open()

The current position of the joystick is recorded in its 'x' and 'y'
attributes, both of which are normalized to values within the range
of -1 to 1.  For the x-axis, `x` = -1 means the joystick is pushed
all the way to the left and `x` = 1 means the joystick is pushed to the right.
For the y-axis, a value of `y` = -1 means that the joystick is pushed up
and a value of `y` = 1 means that the joystick is pushed down.

If your joystick has two analog controllers, the position of the
second controller is typically given by `z` and `rz`, where `z` is the
horizontal axis position and `rz` is the vertical axis position.

The state of the joystick buttons is contained in the `buttons`
attribute as a list of boolean values.  A True value indicates that
the corresponding button is being pressed.  While buttons may be
labeled A, B, X, or Y on the physical joystick, they are simply
referred to by their index when accessing the `buttons` list. There
is no easy way to know which button index corresponds to which
physical button on the device without testing the particular joystick,
so it is a good idea to let users change button assignments.

Each open joystick dispatches events when the joystick changes state.
For buttons, there is the :py:meth:`~pyglet.input.Joystick.on_joybutton_press`
event which is sent whenever any of the joystick's buttons are pressed::

    def on_joybutton_press(joystick, button):
        pass

and the :py:meth:`~pyglet.input.Joystick.on_joybutton_release` event which is
sent whenever any of the joystick's buttons are released::

    def on_joybutton_release(joystick, button):
        pass

The :py:class:`~pyglet.input.Joystick` parameter is the
:py:class:`~pyglet.input.Joystick` instance whose buttons changed state
(useful if you have multiple joysticks connected).
The `button` parameter signifies which button changed and is simply an
integer value, the index of the corresponding button in the `buttons`
list.

For most games, it is probably best to examine the current position of
the joystick directly by using the `x` and `y` attributes.  However if
you want to receive notifications whenever these values change you
should handle the :py:meth:`~pyglet.input.Joystick.on_joyaxis_motion` event::

    def on_joyaxis_motion(joystick, axis, value):
        pass

The :py:class:`~pyglet.input.Joystick` parameter again tells you which
joystick device changed.  The `axis` parameter is string such as
"x", "y", or "rx" telling you which axis changed value.  And `value`
gives the current normalized value of the axis, ranging between -1 and 1.

If the joystick has a hat switch, you may examine its current value by
looking at the `hat_x` and `hat_y` attributes.  For both, the values
are either -1, 0, or 1.  Note that `hat_y` will output 1 in the up
position and -1 in the down position, which is the opposite of the
y-axis control.

To be notified when the hat switch changes value, handle the
:py:meth:`~pyglet.input.Joystick.on_joyhat_motion` event::

    def on_joyhat_motion(joystick, hat_x, hat_y):
        pass

The `hat_x` and `hat_y` parameters give the same values as the
joystick's `hat_x` and `hat_y` attributes.

A good way to use the joystick event handlers might be to define them
within a controller class and then call::

    joystick.push_handlers(my_controller)

Please note that you need a running application event loop for the joystick
button an axis values to be properly updated. See the
:ref:`programming-guide-eventloop` section for more details on how to start
an event loop.


Using the Apple Remote
----------------------

The Apple Remote is a small infrared remote originally distributed
with the iMac.  The remote has six buttons, which are accessed with
the names `left`, `right`, `up`, `down`, `menu`, and `select`.
Additionally when certain buttons are held down, they act as virtual
buttons.  These are named `left_hold`, `right_hold`, `menu_hold`, and
`select_hold`.

To use the remote, first call :py:func:`~pyglet.input.get_apple_remote`::

    remote = pyglet.input.get_apple_remote()

Then open it::

    if remote:
        remote.open(window, exclusive=True)

The remote is opened in exclusive mode so that while we are using the
remote in our program, pressing the buttons does not activate Front
Row, or change the volume, etc. on the computer.

The following event handlers tell you when a button on the remote has
been either pressed or released::

    def on_button_press(button):
        pass

    def on_button_release(button):
        pass

The `button` parameter indicates which button changed and is a string
equal to one of the ten button names defined above: "up", "down",
"left", "left_hold", "right",  "right_hold", "select", "select_hold",
"menu", or "menu_hold".

To use the remote, you may define code for the event handlers in
some controller class and then call::

    remote.push_handlers(my_controller)


Low-level Devices
-----------------

It's usually easier to use the high-level interfaces but, for specialized
hardware, the low-level device can be accessed directly. You can query the
list of all devices, and check the `name` attribute to find the correct
device::

    for device in pyglet.input.get_devices():
        print(device.name)

After identifying the Device you wish to use, you must first open it::

    device.open()

Devices contain a list of :py:class:`~pyglet.input.Control` objects.
There are three types of controls: :py:class:`~pyglet.input.Button`,
:py:class:`~pyglet.input.AbsoluteAxis`, and :py:class:`~pyglet.input.RelativeAxis`.
For helping identify individual controls, each control has at least a
`name`, and optionally a `raw_name` attribute. Control values can by
queried at any time by checking the `Control.value` property. In addition,
every control is also a subclass of :py:class:`~pyglet.event.EventDispatcher`,
so you can add handlers to receive changes as well. All Controls dispatch the
`on_change` event. Buttons also dispatch `on_press` and `on_release` events.::

    # All controls:

    @control.event
    def on_change(value):
        print("value:", value)

    # Buttons:

    @control.event
    def on_press():
        print("button pressed")

    @control.event
    def on_release():
        print("button release")
