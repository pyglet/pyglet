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

# A Frame instance to hold all widgets, and provide special
# hashing to avoid sending all the Window events to every widget:
frame = pyglet.gui.Frame(window, order=4)


text_button = pyglet.gui.TextButton(100, 500, text="Click me!", batch=batch)
text_button.set_handler('on_press', text_button_handler)
text_button.set_handler('on_release', text_release_button_handler)
frame.add_widget(text_button)
text_label = pyglet.text.Label("Text Button: False", x=300, y=500, batch=batch, color=(0, 0, 0, 255))


togglebutton = pyglet.gui.ToggleButton(100, 400, pressed=pressed, unpressed=unpressed, hover=hover, batch=batch)
togglebutton.set_handler('on_toggle', toggle_button_handler)
frame.add_widget(togglebutton)
toggle_label = pyglet.text.Label("Toggle Button: False", x=300, y=400, batch=batch, color=(0, 0, 0, 255))


pushbutton = pyglet.gui.PushButton(100, 300, pressed=pressed, unpressed=unpressed, hover=hover, batch=batch)
pushbutton.set_handler('on_press', push_button_handler)
pushbutton.set_handler('on_release', release_button_handler)
frame.add_widget(pushbutton)
push_label = pyglet.text.Label("Push Button: False", x=300, y=300, batch=batch, color=(0, 0, 0, 255))


slider = pyglet.gui.Slider(100, 200, bar, knob, edge=5, batch=batch)
slider.set_handler('on_change', slider_handler)
frame.add_widget(slider)
slider_label = pyglet.text.Label("Slider Value: 0.0", x=300, y=200, batch=batch, color=(0, 0, 0, 255))


# This Widget is not added to the Frame. Because it is sensitive
# to drag-and-select events falling outside the Frame's spatial hash,
# it's best to let it handle Window events directly.
text_entry = pyglet.gui.TextEntry("Enter Your Name", 100, 100, 150, batch=batch)
window.push_handlers(text_entry)
text_entry.set_handler('on_commit', text_entry_handler)
text_entry_label = pyglet.text.Label("Text: None", x=300, y=100, batch=batch, color=(0, 0, 0, 255))


pyglet.app.run()
