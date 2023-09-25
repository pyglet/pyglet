import pyglet
import timeit


window = pyglet.window.Window(600, 600, caption="Selection Example", resizable=True)
pyglet.gl.glClearColor(0.8, 0.8, 0.8, 1.0)

region = pyglet.gui.ScrollableRegion(100, 100, 400, 400, window, 
                                     slider_base=(200, 230, 255, 255), slider_knob=(100, 150, 200, 255), horizontal=False)

vbox = pyglet.gui.VBox(0,0,0,0)

region.content = vbox
region.set_style({
    'stretch-content': (True, False),
    'background': (150, 150, 150, 255)
})
vbox.set_style({
    'cell-stretch-content': True,
    'row-size': '30px',
    'column-size': '99%'
})

import pyglet.text.formats.html
options = list(pyglet.text.formats.html._color_names.keys())

selected_value_label = pyglet.text.Label('Select color', x=100, y=520, width=300, height=50, anchor_y='bottom', color=(0,0,0,255), font_size=20)

def create_button(text):
    pushbutton = pyglet.gui.TextPushButton(0,0, text=text)
    def f():
        selected_value_label.text = "Selected color: " + text
    pushbutton.set_handler('on_press', f)
    region.frame.add_widget(pushbutton)
    vbox.add(pushbutton)

for color_name in options:
    create_button(color_name)

vbox.fit_to_content()
region.on_content_bounds_updated()

@window.event
def on_draw():
    window.clear()
    region.draw()
    selected_value_label.draw()

@window.event
def on_resize(width, height):
    region.size = (width - 200, height - 200)
    selected_value_label.y = height - 80

pyglet.app.run()