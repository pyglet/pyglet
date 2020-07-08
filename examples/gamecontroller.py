import pyglet
from pyglet.gl import *


# pyglet.input.gamecontroller.add_mappings_from_file("gamecontrollerdb.txt")
controllers = pyglet.input.get_game_controllers()

if not controllers:
    print("No Game Controllers were detected.")
    exit()

controller = controllers[0]
controller.open()

window = pyglet.window.Window(720, 480)
batch = pyglet.graphics.Batch()
text = "Detected: {0}\nController GUID: {1}".format(controller.name, controller.guid)
controller_label = pyglet.text.Label(text=text, x=10, y=window.height-20, multiline=True, width=720)


class Point:
    def __init__(self, position, batch, color=(255, 255, 255), visible=True):
        self._position = position
        self._visible = visible
        self.vlist = batch.add(1, GL_POINTS, None, ('vertices2f', position), ('colors3Bn', color))
        self.visible = visible

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._position = value
        self.vlist.vertices[:] = value

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, value):
        self._visible = value
        if value is False:
            self.vlist.vertices[:] = -10, -10
        else:
            self.vlist.vertices[:] = self._position


left_trigger = Point(position=(90, 360 + (controller.lefttrigger * 50)), batch=batch)
right_trigger = Point(position=(630, 360 + (controller.lefttrigger * 50)), batch=batch)
left_stick = Point(position=(180, 240), batch=batch)
right_stick = Point(position=(540, 240), batch=batch)
d_pad = Point(position=(280, 190), batch=batch)

buttons = {'a': Point(position=(440, 170), color=(50, 255, 50), batch=batch, visible=False),
           'b': Point(position=(460, 190), color=(255, 50, 50), batch=batch, visible=False),
           'x': Point(position=(420, 190), color=(50, 50, 255), batch=batch, visible=False),
           'y': Point(position=(440, 210), color=(255, 255, 50), batch=batch, visible=False),
           'leftshoulder': Point(position=(90, 290), batch=batch, visible=False),
           'rightshoulder': Point(position=(630, 290), batch=batch, visible=False),
           'start': Point(position=(390, 240), batch=batch, visible=False),
           'guide': Point(position=(360, 240), color=(255, 255, 100), batch=batch, visible=False),
           'back': Point(position=(330, 240), batch=batch, visible=False)}


@controller.event
def on_button_press(controller, button_name):
    global buttons
    button = buttons.get(button_name, None)
    if button:
        button.visible = True

    controller.rumble_play_weak(1.0, 0.1)


@controller.event
def on_button_release(controller, button_name):
    global buttons
    button = buttons.get(button_name, None)
    if button:
        button.visible = False


@controller.event
def on_dpad_motion(controller, dpleft, dpright, dpup, dpdown):
    global d_pad
    position = [280, 190]
    if dpup:
        position[1] += 25
    if dpdown:
        position[1] -= 25
    if dpleft:
        position[0] -= 25
    if dpright:
        position[0] += 25
    d_pad.position = position


@controller.event
def on_stick_motion(controller, axis, xvalue, yvalue):
    global left_stick, right_stick
    if axis == "leftstick":
        left_stick.position = 180+xvalue*50, 240+yvalue*50
    elif axis == "rightstick":
        right_stick.position = 540+xvalue*50, 240+yvalue*50


@controller.event
def on_trigger_motion(controller, trigger, value):
    global left_trigger, right_trigger
    rumble_strength = (value + 1) / 2
    if trigger == "lefttrigger":
        left_trigger.position = left_trigger.position[0], 360 + (value*50)
        controller.rumble_play_weak(rumble_strength, duration=5)
    elif trigger == "righttrigger":
        right_trigger.position = right_trigger.position[0], 360 + (value*50)
        controller.rumble_play_strong(rumble_strength, duration=5)


@window.event
def on_draw():
    window.clear()
    batch.draw()
    controller_label.draw()


glPointSize(10)
pyglet.app.run()
