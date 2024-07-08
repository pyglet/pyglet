"""Example of advanced font rendering features."""
# ruff: noqa: E501
import pyglet
import os

if os.name == "nt":
    # On Windows, it's possible to change the font anti-aliasing mode.
    # Uncomment the below lines to set the options:
    #
    from pyglet.font.directwrite import DirectWriteGlyphRenderer
    D2D1_TEXT_ANTIALIAS_MODE_DEFAULT = 0
    D2D1_TEXT_ANTIALIAS_MODE_CLEARTYPE = 1 # not working?
    D2D1_TEXT_ANTIALIAS_MODE_GRAYSCALE = 2 # same as default
    D2D1_TEXT_ANTIALIAS_MODE_ALIASED = 3 # looks worse than grayscale
    DirectWriteGlyphRenderer.antialias_mode = D2D1_TEXT_ANTIALIAS_MODE_DEFAULT

window = pyglet.window.Window()
batch = pyglet.graphics.Batch()

float_font_size = pyglet.text.Label("Hello World on size 15.1", font_name="Arial", font_size=15.1, x=30, y=500, batch=batch)
float_font_size_1 = pyglet.text.Label("Hello World on size 15", font_name="Arial", font_size=15, x=270, y=500, batch=batch)

arial_bold = pyglet.text.Label("Hello World 👽", font_name="Arial", bold=True, font_size=25, x=50, y=400, batch=batch)
arial_black = pyglet.text.Label("Hello World 👾", font_name="Arial", bold="black", font_size=25, x=50, y=350, batch=batch)
arial_narrow = pyglet.text.Label("Hello World 🤖", font_name="Arial", bold=False, stretch="condensed", font_size=25, x=50, y=300, batch=batch)
arial = pyglet.text.Label("Hello World 👀", font_name="Arial", font_size=25, x=50, y=250, batch=batch)

segoe_ui_black = pyglet.text.Label("Hello World ☂️", font_name="Segoe UI", bold="black", font_size=25, x=50, y=200, batch=batch)
segoe_ui_semilbold = pyglet.text.Label("Hello World ⚽️", font_name="Segoe UI", bold="semibold", font_size=25, x=50, y=150, batch=batch)
segoe_ui_semilight = pyglet.text.Label("Hello World 🎱", font_name="Segoe UI", bold="semilight", font_size=25, x=50, y=100, batch=batch)
segoe_ui_light = pyglet.text.Label("Hello World 🥳👍", font_name="Segoe UI", bold="light", font_size=25, x=50, y=50, batch=batch)
segoe_ui = pyglet.text.Label("Hello World 😀✌", font_name="Segoe UI", font_size=25, x=50, y=10, batch=batch)

if os.name == "nt":
    # On Windows DirectWrite can render directly to an image for special cases!
    # Note: Labels are recommended unless you know what you are doing, or if you use these in a limited fashion.
    font = pyglet.font.load("Segoe UI")
    image = font.render_to_image("I am rendered as a texture! 🌎", 100, 300) # pyright: ignore reportAttributeAccessIssue
    sprite = pyglet.sprite.Sprite(image, x=400, y=400, batch=batch)
    sprite.rotation = 45


@window.event
def on_draw() -> None:  # noqa: D103
    window.clear()
    batch.draw()


pyglet.app.run()
