import pyglet

from pyglet.shapes import Circle, Rectangle, Arc


window = pyglet.window.Window(720, 480)
batch = pyglet.graphics.Batch()


@window.event
def on_draw():
    window.clear()
    batch.draw()


class ControllerDisplay:
    """A class to visualize all the Controller inputs."""

    label = pyglet.text.Label("No Controller connected.", x=10, y=window.height - 20,
                              multiline=True, width=720, batch=batch)

    left_trigger = Rectangle(70, 310, 40, 10, batch=batch)
    right_trigger = Rectangle(610, 310, 40, 10, batch=batch)
    d_pad = Rectangle(280, 185, 10, 10, batch=batch)
    left_stick = Arc(180, 240, 20, batch=batch)
    right_stick = Arc(540, 240, 20, batch=batch)

    l_outline1 = Arc(180, 240, 75, color=(44, 44, 44), batch=batch)
    l_outline2 = Arc(285, 190, 35, color=(44, 44, 44), batch=batch)
    r_outline1 = Arc(540, 240, 75, color=(44, 44, 44), batch=batch)
    r_outline2 = Arc(435, 190, 35, color=(44, 44, 44), batch=batch)

    buttons = {'a': Circle(435, 170, 9, color=(124, 178, 232), batch=batch),
               'b': Circle(455, 190, 9, color=(255, 102, 102), batch=batch),
               'x': Circle(415, 190, 9, color=(255, 105, 248), batch=batch),
               'y': Circle(435, 210, 9, color=(64, 226, 160), batch=batch),
               'leftshoulder': Rectangle(70, 290, 40, 10, batch=batch),
               'rightshoulder': Rectangle(610, 290, 40, 10, batch=batch),
               'start': Circle(390, 240, 9, batch=batch),
               'guide': Circle(360, 240, 9, color=(255, 255, 100), batch=batch),
               'back': Circle(330, 240, 9, batch=batch),
               'leftstick': Circle(180, 240, 9, batch=batch),
               'rightstick': Circle(540, 240, 9, batch=batch)}

    for button in buttons.values():
        button.visible = False

    def on_button_press(self, controller, button_name):
        button = self.buttons.get(button_name, None)
        if button:
            button.visible = True

        controller.rumble_play_weak(1.0, 0.1)

    def on_button_release(self, controller, button_name):
        button = self.buttons.get(button_name, None)
        if button:
            button.visible = False

    def on_dpad_motion(self, controller, dpleft, dpright, dpup, dpdown):
        position = [280, 185]
        if dpup:
            position[1] += 25
        if dpdown:
            position[1] -= 25
        if dpleft:
            position[0] -= 25
        if dpright:
            position[0] += 25
        self.d_pad.position = position

    def on_stick_motion(self, controller, stick, xvalue, yvalue):
        if stick == "leftstick":
            self.left_stick.position = 180+xvalue*50, 240+yvalue*50
        elif stick == "rightstick":
            self.right_stick.position = 540+xvalue*50, 240+yvalue*50

    def on_trigger_motion(self, controller, trigger, value):
        if trigger == "lefttrigger":
            self.left_trigger.y = 310 + (value*50)
            controller.rumble_play_weak(value, duration=5)
        elif trigger == "righttrigger":
            self.right_trigger.y = 310 + (value*50)
            controller.rumble_play_strong(value, duration=5)


controller_display = ControllerDisplay()


def on_connect(controller):
    controller.open()
    controller_display.label.text = f"Detected: {controller.name}\nController GUID: {controller.guid}"
    controller.push_handlers(controller_display)


def on_disconnect(controller):
    controller_display.label.text = "No Controller connected."
    controller.remove_handlers(controller_display)


# ControllerManager instance to handle hot-plugging:
controller_manager = pyglet.input.ControllerManager()
controller_manager.on_connect = on_connect
controller_manager.on_disconnect = on_disconnect

# Handle already connected controller:
if controllers := controller_manager.get_controllers():
    on_connect(controllers[0])

pyglet.app.run()
