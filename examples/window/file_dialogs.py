import pyglet

if __name__ == '__main__':
    from pyglet.window.dialog import FileOpenDialog, FileSaveDialog

    window = pyglet.window.Window(400, 100, caption="File Dialog Example")
    batch = pyglet.graphics.Batch()


    @window.event
    def on_draw():
        window.clear()
        batch.draw()


    # Create the save dialog object and the restrictions for saving.
    save_dialog = FileSaveDialog(title="Save Image", initial_file="myimage", filetypes=[("PNG", ".png"), ("24-bit Bitmap", ".bmp")])

    # Assign the event to handle the file path returned.
    @save_dialog.event
    def on_dialog_save(filename: str):
        if not filename:
            print("No filename received or user cancelled!")
        else:
            print("Filename received for save dialog:", filename)

    # Create the open dialog object and the restrictions for files to open.
    open_dialog = FileOpenDialog(title="Open files", filetypes=[("Images", "*.png *.bmp"), ("JSON", "*.json")], multiple=True)

    # Assign the event to handle the file paths returned.
    @open_dialog.event
    def on_dialog_open(filenames: list[str]):
       print("Filenames received for open dialog:", filenames)


    # Setup simple UI buttons to demonstrate the behavior.
    frame = pyglet.gui.Frame(window, order=4)

    def _open_button_release(widget):
        open_dialog.open()

    def _save_button_release(widget):
        save_dialog.open()

    open_button = pyglet.gui.TextButton(50, 50, text="Open File Dialog", batch=batch)
    open_button.set_handler('on_release', _open_button_release)
    frame.add_widget(open_button)

    save_button = pyglet.gui.TextButton(230, 50, text="Save File Dialog", batch=batch)
    save_button.set_handler('on_release', _save_button_release)
    frame.add_widget(save_button)


    pyglet.app.run()
