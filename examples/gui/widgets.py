import pyglet

window = pyglet.window.Window(540, 500, caption="Widget Example", resizable=True)
batch = pyglet.graphics.Batch()
pyglet.gl.glClearColor(0.8, 0.8, 0.8, 1.0)


@window.event
def on_draw():
    window.clear()
    batch.draw()

@window.event
def on_resize(width, height):
    layout.size = (width, height)
    frame.on_widgets_realign()

####################################
# load resources to use for Widgets:
####################################

depressed = pyglet.resource.image('button_up.png')
pressed = pyglet.resource.image('button_down.png')
hover = pyglet.resource.image('button_hover.png')
bar = pyglet.resource.image('bar.png')
knob = pyglet.resource.image('knob.png')
header = pyglet.resource.image('header.png')


######################################
# Create some event handler functions:
######################################

def slider_handler(value):
    slider_label.text = f"Slider Value: {round(value, 1)}"


def toggle_button_handler(value):
    toggle_label.text = f"Toggle Button: {value}"


def push_button_handler():
    push_label.text = f"Push Button: True"


def release_button_handler():
    push_label.text = f"Push Button: False"


def text_entry_handler(text):
    text_entry_label.text = f"Text: {text}"


###############################
# Create some Widget instances:
###############################

# A Frame instance to hold all Widgets:
frame = pyglet.gui.Frame(window, order=4)

# A Layout instance to show widgets on the screen in a table order
layout_style = {
    'padding': 50,
    'row-size': "50px",
    'background': (220, 220, 240, 255),
    'cell-background': (230, 230, 255, 255),
    'cell-margin': 5,
    'cell-padding': 5,
}
layout = pyglet.gui.Layout(0, 0, 
                           width=window.width, height=window.height,
                           rows=5, columns=2,
                           batch=batch, style=layout_style)
layout.set_column_margin(0, 20)
layout.set_column_size(0, "200px")
layout.set_cell_span(0, 0, colspan=2)
layout.set_style('cell-content-alignment', ('center', 'bottom'))

header_label = pyglet.text.Label("Menu", batch=batch, color=(0, 0, 0, 255))
layout.cell(0, 0).content = header_label
header_sprite = pyglet.sprite.Sprite(header, batch=batch, 
                                    image_mesh_generator=pyglet.sprite.NinePatchImageMeshGenerator(11, 11, 11, 11, 2))
layout.cell(0, 0).set_style('background', header_sprite)

togglebutton = pyglet.gui.ToggleButton(0,0, pressed=pressed, depressed=depressed, hover=hover, batch=batch)
togglebutton.set_handler('on_toggle', toggle_button_handler)
toggle_label = pyglet.text.Label("Toggle Button: False", batch=batch, color=(0, 0, 0, 255))
layout.cell(1, 0).content = toggle_label
layout.cell(1, 1).content = togglebutton
frame.add_widget(togglebutton)

pushbutton = pyglet.gui.PushButton(0,0, pressed=pressed, depressed=depressed, hover=hover, batch=batch)
pushbutton.set_handler('on_press', push_button_handler)
pushbutton.set_handler('on_release', release_button_handler)
push_label = pyglet.text.Label("Push Button: False", batch=batch, color=(0, 0, 0, 255))
layout.cell(2, 0).content = push_label
layout.cell(2, 1).content = pushbutton
frame.add_widget(pushbutton)

slider = pyglet.gui.Slider(0,0,0,16, bar, knob, edge=5, batch=batch, value_range=(0, 10), integer=True)
slider._base_spr.set_image_mesh_generator(pyglet.sprite.NinePatchImageMeshGenerator(0, 20, 0, 20))
slider.set_handler('on_change', slider_handler)

slider_label = pyglet.text.Label("Slider Value: 0.0", batch=batch, color=(0, 0, 0, 255))
layout.cell(3, 0).content = slider_label
layout.cell(3, 1).content = slider
layout.cell(3, 1).set_style('stretch-content-x', True)
frame.add_widget(slider)

text_entry = pyglet.gui.TextEntry("Enter Your Name", 0,0, 0, batch=batch)
text_entry.set_handler('on_commit', text_entry_handler)
text_entry_label = pyglet.text.Label("Text: None", batch=batch, color=(0, 0, 0, 255))
layout.cell(4, 0).content = text_entry_label
layout.cell(4, 1).content = text_entry
layout.cell(4, 1).set_style('stretch-content', True)
frame.add_widget(text_entry)

for i in range(5):
    layout.cell(i, 0).set_style({'stretch-content': True, 'padding': 5})
    layout.cell(i, 0).content.content_halign = 'right' if i > 0 else 'center'
    layout.cell(i, 0).content.content_valign = 'center'

frame.on_widgets_realign()

pyglet.app.run()
