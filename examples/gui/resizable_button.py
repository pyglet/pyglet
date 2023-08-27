"""A button which resizes along with the window it fills.

This example is written in object-oriented style rather than
functions and decorators because overriding the default
Window event handler stops automatic gl viewport resizing.

See the Setting Event handlers section of the Programming Guide
for more information:
https://pyglet.readthedocs.io/en/latest/programming_guide/events.html#setting-event-handlers
"""
import pyglet

# How much space to leave around the inside of the window
PADDING_PX = 30


class ResizableButtonWindow(pyglet.window.Window):

    def __init__(self, width: int = 500, height: int = 500):
        super().__init__(
            width, height,
            caption="Resizable Button", resizable= True)

        # Load button textures
        self.depressed=pyglet.resource.image('button_up.png')
        self.pressed = pyglet.resource.image('button_down.png')
        self.hover=pyglet.resource.image('button_hover.png')

        self.batch = pyglet.graphics.Batch()
        self.frame = pyglet.gui.Frame(self, order=4)

        self.push_label = pyglet.text.Label(
            "Push Button: ", x=0, y=0, batch=self.batch, color=(0, 0, 0, 255))
        self.pushbutton = pyglet.gui.PushButton(
            PADDING_PX, PADDING_PX,
            self.pressed,
            self.depressed,
            hover=self.hover,
            width=self.width - 2 * PADDING_PX,
            height=self.height - 2 * PADDING_PX,
            batch=self.batch
        )

        self.pushbutton.set_handler('on_press', self.push_button_handler)
        self.pushbutton.set_handler('on_release', self.release_button_handler)
        self.frame.add_widget(self.pushbutton)
        self.update_label()

    def on_draw(self):
        self.clear()
        self.batch.draw()

    def update_label(self):
        """Update the label contents with current data"""
        button = self.pushbutton
        self.push_label.text =\
            f"Push Button: pressed={button.value}, "\
            f"width={button.width}, height={button.height}"

    def push_button_handler(self):
        self.update_label()

    def release_button_handler(self):
        self.update_label()

    def on_resize(self, width, height):
        # Crucial: update the GL viewport so we don't cut things off!
        super().on_resize(width, height)
        # Avoid division by zero
        self.pushbutton.size = (
            max(1, width - 2 * PADDING_PX),
            max(1, height - 2 * PADDING_PX)
        )
        self.update_label()


if __name__ == "__main__":
    _ = ResizableButtonWindow()
    pyglet.gl.glClearColor(0.8, 0.8, 0.8, 1.0)
    pyglet.app.run()
