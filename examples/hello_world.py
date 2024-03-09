import pyglet

window = pyglet.window.Window()
label = pyglet.text.Label('Hello, world!',
                          font_size=36,
                          x=window.width // 2,
                          y=window.height // 2,
                          anchor_x='center',
                          anchor_y='center')


@window.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.SPACE:
        label.text = "This is just a test to see how it works again?"

    elif symbol == pyglet.window.key.A:
        label.position = (100, 100, 0)

    elif symbol == pyglet.window.key.B:
        label.document.set_style(0, 2, dict(color=(255, 0, 0, 255)))

@window.event
def on_draw():
    window.clear()
    label.draw()


pyglet.app.run()
