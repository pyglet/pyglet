import pyglet

window = pyglet.window.Window()
label = pyglet.text.Label('',
                          font_size=36,
                          x=window.width // 2,
                          y=window.height // 2,
                          #anchor_x='center',
                          #anchor_y='center'
                          )

label.position = (100, 100, 0)

@window.event
def on_draw():
    window.clear()
    label.draw()


pyglet.app.run()
