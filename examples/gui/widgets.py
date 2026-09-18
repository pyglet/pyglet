import pyglet

window = pyglet.window.Window(540, 600, caption="Widget Example")
batch = pyglet.graphics.Batch()
window.context.set_clear_color(0.8, 0.8, 0.8, 1.0)


@window.event
def on_draw():
    window.clear()
    batch.draw()


####################################
# load resources to use for Widgets:
####################################

unpressed = pyglet.resource.texture('button_unpressed.png')
pressed = pyglet.resource.texture('button_pressed.png')
hover = pyglet.resource.texture('button_hover.png')
bar = pyglet.resource.texture('bar.png')
knob = pyglet.resource.texture('knob.png')


######################################
# Create some event handler functions:
######################################

def slider_handler(widget, value):
    slider_label.text = f"Slider Value: {round(value, 1)}"


def toggle_button_handler(widget, value):
    toggle_label.text = f"Toggle Button: {value}"


def push_button_handler(widget):
    push_label.text = "Push Button: True"


def release_button_handler(widget):
    push_label.text = "Push Button: False"


def text_button_handler(widget):
    text_label.text = "Text Button: True"


def text_release_button_handler(widget):
    text_label.text = "Text Button: False"

def text_entry_handler(widget, text):
    text_entry_label.text = f"Text: {text}"


###############################
# Create some Widget instances:
###############################

# One UIManager owns window input, focus, and hashing for all widgets.
ui = pyglet.gui.UIManager(window, order=4)


text_button = pyglet.gui.TextButton(ui, 100, 500, text="Click me!", unpressed_color=(0, 0, 0, 255), batch=batch)
text_button.set_handler('on_press', text_button_handler)
text_button.set_handler('on_release', text_release_button_handler)
text_label = pyglet.text.Label("Text Button: False", x=300, y=500, batch=batch, color=(0, 0, 0, 255))


togglebutton = pyglet.gui.ToggleButton(ui, 100, 400, pressed=pressed, unpressed=unpressed, hover=hover, batch=batch)
togglebutton.set_handler('on_toggle', toggle_button_handler)
toggle_label = pyglet.text.Label("Toggle Button: False", x=300, y=400, batch=batch, color=(0, 0, 0, 255))


pushbutton = pyglet.gui.PushButton(ui, 100, 300, pressed=pressed, unpressed=unpressed, hover=hover, batch=batch)
pushbutton.set_handler('on_press', push_button_handler)
pushbutton.set_handler('on_release', release_button_handler)
push_label = pyglet.text.Label("Push Button: False", x=300, y=300, batch=batch, color=(0, 0, 0, 255))


slider = pyglet.gui.Slider(ui, 100, 200, bar, knob, edge=5, batch=batch)
slider.set_handler('on_change', slider_handler)
slider_label = pyglet.text.Label("Slider Value: 0.0", x=300, y=200, batch=batch, color=(0, 0, 0, 255))


text_entry = pyglet.gui.TextEntry(ui, "Enter Your Name", 100, 100, 150, batch=batch)
text_entry.set_handler('on_commit', text_entry_handler)
text_entry_label = pyglet.text.Label("Text: None", x=300, y=100, batch=batch, color=(0, 0, 0, 255))


pyglet.app.run()
