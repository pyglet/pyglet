"""An example of using `pyglet.font.add_user_font` to draw custom fonts.

In this example, two fonts called `ascii` and `sga` are added. They are both
generated from bitmap files rather than read from font files.
"""

import string
from io import BytesIO

from PIL import Image
from PIL.Image import Resampling

from pyglet import app, clock, image, resource
from pyglet.font import add_user_font
from pyglet.font.user.mapping import UserDefinedMappingFont
from pyglet.font.user.search_texture import UserDefinedSearchTextureFont
from pyglet.text import Label
from pyglet.window import Window

font_ascii = resource.image("ascii.png")
font_sga = resource.image("sga.png")
image_cache = {}
special_width_ascii = {
    " ": 0.375,
    ",": 0.5,
    "!": 0.5,
    "F": 0.625,
    "I": 0.5,
    "f": 0.625,
    "i": 0.25,
    "l": 0.375,
    "t": 0.5,
    '"': 0.5,
    "'": 0.25,
    ".": 0.375,
    ":": 0.375,
    ";": 0.375,
    "[": 0.5,
    "]": 0.5,
    "{": 0.5,
    "|": 0.5,
    "}": 0.5,
}
special_width_sga = {
    "C": 0.5,
    "G": 0.625,
    "I": 0.25,
    "J": 0.25,
    "L": 0.625,
    "P": 0.625,
    "S": 0.5,
    "Y": 0.625,
}
lorem_ipsum = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
    "Donec a diam lectus. Sed sit amet ipsum mauris. Maecenas congue ligula "
    "ac quam viverra nec consectetur ante hendrerit. Donec et mollis dolor. "
    "Praesent et diam eget libero egestas mattis sit amet vitae augue."
)


def get_ascii_texture(char, size=8, **kwargs):
    """Return glyph of ASCII character in different size.

    It gets glyph info, which arranged by ascii code, from an image file.
    """
    if char not in " " + string.ascii_letters + string.digits + string.punctuation:
        return None
    if ("ascii", size) not in image_cache:
        # The following code scale an image to a certain size by using PIL.
        # It converts images from pyglet to PIL and back again.
        cache = BytesIO()
        font_ascii.save("cache.png", file=cache)
        image_original = Image.open(cache)
        # scaling...
        image_resized = image_original.resize((16 * size,) * 2, Resampling.NEAREST)
        cache = BytesIO()
        image_resized.save(cache, format="png")
        cache.seek(0)
        image_cache[("ascii", size)] = image.load("cache.png", file=cache)
    font_image = image_cache[("ascii", size)]
    # Get the position of the glyph in the image.
    x, y = ord(char) % 16 * size, size * 16 - (ord(char) // 16 + 1) * size
    # Get the width of the glyph.
    w = (special_width_ascii[char] if char in special_width_ascii else 0.75) * size
    return font_image.get_region(x, y, int(w), size).get_image_data()


def get_sga_mappings():
    """Return a mapping of SGA characters from an image."""
    # Scale the image.
    cache = BytesIO()
    font_sga.save("cache.png", file=cache)
    image_original = Image.open(cache)
    image_resized = image_original.resize((16 * 24,) * 2, Resampling.NEAREST)
    cache = BytesIO()
    image_resized.save(cache, format="png")
    cache.seek(0)
    font_image = image.load("cache.png", file=cache)
    mappings = {}
    for char in " " + string.ascii_letters:
        # Get the position of the glyph in the image.
        x, y = ord(char) % 16 * 24, 24 * 16 - (ord(char) // 16 + 1) * 24
        cap = char.capitalize()
        # Get the width of the glyph.
        w = (special_width_sga[cap] if cap in special_width_sga else 0.75) * 24
        mappings[char] = font_image.get_region(x, y, int(w), 24).get_image_data()
    return mappings


class AddUserFontWindow(Window):
    def __init__(self):
        super().__init__(640, 480, "add_user_font")
        self.label_title = Label(
            "pyglet",
            font_name="ascii",
            font_size=32,
            x=320,
            y=400,
            anchor_x="center",
        )
        self.lable_subtitle = Label(
            "a cross-platform windowing and multimedia library for Python",
            font_name="ascii",
            font_size=16,
            x=320,
            y=380,
            anchor_x="center",
        )
        self.label_lipsum = Label(
            lorem_ipsum,
            font_name="ascii",
            font_size=24,
            x=320,
            y=240,
            multiline=True,
            width=600,
            anchor_x="center",
            anchor_y="center",
        )
        self.label_sga = Label(
            "Standard Galactic Alphabet",
            font_name="sga",
            font_size=24,
            x=320,
            y=80,
            anchor_x="center",
        )

    def on_draw(self):
        self.clear()
        self.label_title.draw()
        self.lable_subtitle.draw()
        self.label_lipsum.draw()
        self.label_sga.draw()


if __name__ == "__main__":
    fonts = []
    # Use `add_user_font` to add custom fonts.
    for size in [16, 24, 32]:
        ascii_font = UserDefinedSearchTextureFont(
            "ascii",
            default_char=" ",
            size=size,
            search_texture=get_ascii_texture,
        )
        fonts.append(ascii_font)
        add_user_font(ascii_font)

    sga_font = UserDefinedMappingFont(
        "sga", default_char=" ", size=24, mappings=get_sga_mappings()
    )
    add_user_font(sga_font)
    window = AddUserFontWindow()
    clock.schedule_interval(window.draw, 1 / 60)
    app.run()
