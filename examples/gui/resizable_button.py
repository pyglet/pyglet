"""Use UI element resizing to scale a button with a window.

When overriding the Window.on_resize event handler, it is
easiest to use either ``@window.event`` decoration or
inheritance to make sure you update the GL view projection.
If you do not, the window will cut off drawing at its
original size unless you manually reset the projection.

This demo takes the event decorator approach.
"""
import pyglet

# Add space around the window to make sure button hovering works
PADDING_PX = 30
DOUBLE_PADDING = PADDING_PX * 2


window = pyglet.window.Window(500, 500, caption="Resizable Full-Window Button", resizable=True)
batch = pyglet.graphics.Batch()
pyglet.gl.glClearColor(0.8, 0.8, 0.8, 1.0)
frame = pyglet.gui.Frame(window, order=4)


@window.event
def on_draw():
    window.clear()
    batch.draw()


depressed = pyglet.resource.image('button_up.png')
pressed = pyglet.resource.image('button_down.png')
hover = pyglet.resource.image('button_hover.png')


push_label = pyglet.text.Label("Push Button: False", x=0, y=0, batch=batch, color=(0, 0, 0, 255))
pushbutton = pyglet.gui.PushButton(
    PADDING_PX, PADDING_PX,
    pressed, depressed,
    hover=hover, batch=batch,
    width=window.width - DOUBLE_PADDING, height=window.height - DOUBLE_PADDING
)


# Update the bottom left display label
def update_label_text():
    push_label.text =\
        f"Push Button: pressed={pushbutton.value}, "\
        f"width={pushbutton.width}, height={pushbutton.height}"


# Use a decorator to register the resize handler
@window.event
def on_resize(width, height):
    pushbutton.size = width - DOUBLE_PADDING, height - DOUBLE_PADDING
    update_label_text()


pushbutton.set_handler('on_press', update_label_text)
pushbutton.set_handler('on_release', update_label_text)
frame.add_widget(pushbutton)


pyglet.app.run()