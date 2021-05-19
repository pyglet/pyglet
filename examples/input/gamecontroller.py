import pyglet

from pyglet.shapes import Circle, Rectangle, Arc

# pyglet.input.gamecontroller.add_mappings_from_file("gamecontrollerdb.txt")
controllers = pyglet.input.get_game_controllers()

if not controllers:
    print("No Game Controllers were detected.")
    exit()

controller = controllers[0]
controller.open()

window = pyglet.window.Window(720, 480)
batch = pyglet.graphics.Batch()

text = f"Detected: {controller.name}\nController GUID: {controller.guid}"
controller_label = pyglet.text.Label(text=text, x=10, y=window.height-20, multiline=True, width=720, batch=batch)


left_trigger = Rectangle(70, 360 + (controller.lefttrigger * 50), 40, 10, batch=batch)
right_trigger = Rectangle(610, 360 + (controller.lefttrigger * 50), 40, 10, batch=batch)
d_pad = Rectangle(280, 190, 10, 10, batch=batch)
left_stick = Arc(180, 240, 20, batch=batch)
right_stick = Arc(540, 240, 20, batch=batch)

buttons = {'a': Circle(440, 170, 9, color=(50, 255, 50), batch=batch),
           'b': Circle(460, 190, 9, color=(255, 50, 50), batch=batch),
           'x': Circle(420, 190, 9, color=(50, 50, 255), batch=batch),
           'y': Circle(440, 210, 9, color=(255, 255, 50), batch=batch),
           'leftshoulder': Rectangle(70, 290, 40, 10, batch=batch),
           'rightshoulder': Rectangle(610, 290, 40, 10, batch=batch),
           'start': Circle(390, 240, 9, batch=batch),
           'guide': Circle(360, 240, 9, color=(255, 255, 100), batch=batch),
           'back': Circle(330, 240, 9, batch=batch),
           'leftstick': Circle(180, 240, 9, batch=batch),
           'rightstick': Circle(540, 240, 9, batch=batch)}

for button in buttons.values():
    button.visible = False


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


pyglet.app.run()
