import pyglet

pyglet.options["advanced_font_features"] = True

window = pyglet.window.Window()

batch = pyglet.graphics.Batch()


arial_bold = pyglet.text.Label("Hello World 👽", font_name="Arial", bold=True, font_size=25, x=50, y=400, batch=batch)
arial_black = pyglet.text.Label("Hello World 👾", font_name="Arial", bold="black", font_size=25, x=50, y=350, batch=batch)
arial_narrow = pyglet.text.Label("Hello World 🤖", font_name="Arial", bold=False, stretch="condensed", font_size=25, x=50, y=300, batch=batch)
arial = pyglet.text.Label("Hello World 👀", font_name="Arial", font_size=25, x=50, y=250, batch=batch)

segoe_ui_black = pyglet.text.Label("Hello World ☂️", font_name="Segoe UI", bold="black", font_size=25, x=50, y=200, batch=batch)
segoe_ui_semilbold = pyglet.text.Label("Hello World ⚽️", font_name="Segoe UI", bold="semibold", font_size=25, x=50, y=150, batch=batch)
segoe_ui_semilight = pyglet.text.Label("Hello World 🎱", font_name="Segoe UI", bold="semilight", font_size=25, x=50, y=100, batch=batch)
segoe_ui_light = pyglet.text.Label("Hello World 🥳👍", font_name="Segoe UI", bold="light", font_size=25, x=50, y=50, batch=batch)
segoe_ui = pyglet.text.Label("Hello World 😀✌", font_name="Segoe UI", font_size=25, x=50, y=10, batch=batch)

@window.event
def on_draw():
    window.clear()

    batch.draw()

pyglet.app.run()

