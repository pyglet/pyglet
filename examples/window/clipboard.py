import pyglet

"""Simple example demonstrating how to get the text in the clipboard as well as putting text in the clipboard."""

window = pyglet.window.Window()
print("Existing Clipboard Text:", window.get_clipboard_text())


@window.event
def on_key_press(symbol, modifiers):
    print("Clipboard changed to: Hello World!")

    window.set_clipboard_text("Hello World!")

    print("Clipboard Text:", window.get_clipboard_text())


@window.event
def on_draw():
    window.clear()


pyglet.app.run()
