import pyglet

joysticks = pyglet.input.get_joysticks()
assert joysticks, 'No joystick device is connected'
joystick = joysticks[0]
joystick.open()

window = pyglet.window.Window(width=800, height=800)
batch = pyglet.graphics.Batch()

# Labels
pyglet.text.Label("Buttons:", x=15, y=window.height - 25, font_size=14, batch=batch)
pyglet.text.Label("D Pad:", x=window.width - 125, y=window.height - 25, font_size=14, batch=batch)


button_labels = []
button_shapes = []

for i in range(len(joystick.buttons)):
    rows = len(joystick.buttons) // 2
    y = window.height - 50 - 25 * (i % rows)
    x = 35 + 60 * (i // rows)
    label = pyglet.text.Label(f"{i}:", x=x, y=y, font_size=14, anchor_x='right', batch=batch)
    button_labels.append(label)
    shape = pyglet.shapes.Rectangle(x + 10, y + 1, 10, 10, color=(255, 0, 0), batch=batch)
    button_shapes.append(shape)


joystick_rect = pyglet.shapes.Rectangle(window.width // 2, window.height // 2, 10, 10, color=(255, 0, 255), batch=batch)
joystick_rect.anchor_position = joystick_rect.width // 2, joystick_rect.height // 2
d_pad_rect = pyglet.shapes.Rectangle(window.width - 75, window.height - 100, 10, 10, color=(0, 0, 255), batch=batch)


@window.event
def on_draw():
    window.clear()
    batch.draw()
    x = round((.5 * joystick.x + 1), 2) * window.width / 2
    y = round((-.5 * joystick.y + 1), 2) * window.height / 2
    rx = (.5 * joystick.rx + 1) * 60
    ry = (-.5 * joystick.ry + 1) * 60
    z = joystick.z * 50

    # Axes
    joystick_rect.position = x, y
    joystick_rect.anchor_position = joystick_rect.width // 2, joystick_rect.height // 2
    joystick_rect.width = 10 + rx + z
    joystick_rect.height = 10 + ry + z

    # Buttons
    for i in range(len(joystick.buttons)):
        rect = button_shapes[i]
        rect.color = (0, 255, 0) if joystick.buttons[i] else (255, 0, 0)

    # Hat
    d_pad_x = window.width - 100 + joystick.hat_x * 50
    d_pad_y = window.height - 100 + joystick.hat_y * 50
    d_pad_rect.position = d_pad_x, d_pad_y


pyglet.app.run()
