import pyglet

window = pyglet.window.Window(resizable=True)

# create a frame
reposition_frame = pyglet.gui.control.RePositionFrame(window)

# create labels
label = pyglet.text.Label("Hello World", x=0, y=0)
b_label = pyglet.text.Label("Hello World with call back", x=0, y=0)

# create a callback function
def callback(obj, width, height, window):
   obj.x = width/3
   obj.y = height/3
   obj.text = f"Hello World with call back, width: {width}, height: {height}"

# add the callback function to the frame
reposition_frame.add_callback_func(b_label, callback)

# add the calculate function to the frame
# NOTICE: label need x, y, z, so the function must return a tuple with 3 elements
reposition_frame.add_calculate_func(label, lambda obj, width, height, window: (width/2, height/2, 0))

# draw the labels
@window.event
def on_draw():
    window.clear()
    label.draw()
    b_label.draw()

# run the app
pyglet.app.run()
