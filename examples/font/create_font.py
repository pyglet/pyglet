import string
from io import BytesIO

from PIL import Image
from PIL.Image import Resampling

from pyglet import app, clock, image, resource
from pyglet.font import create_font
from pyglet.font.user.search_texture import UserDefinedSearchTextureFont
from pyglet.text import Label
from pyglet.window import Window

font_ascii = resource.image("ascii.png")
font_sga = resource.image("sga.png")
special_width = {
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
image_cache = {}
lorem_ipsum = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
    "Donec a diam lectus. Sed sit amet ipsum mauris. Maecenas congue ligula "
    "ac quam viverra nec consectetur ante hendrerit. Donec et mollis dolor. "
    "Praesent et diam eget libero egestas mattis sit amet vitae augue."
)


def get_texture_ascii(char, size=8, **kwargs):
    if char not in " " + string.ascii_letters + string.digits + string.punctuation:
        return None
    if ("ascii", size) not in image_cache:
        cache = BytesIO()
        font_ascii.save("cache.png", file=cache)
        image_original = Image.open(cache)
        image_resized = image_original.resize((16 * size,) * 2, Resampling.NEAREST)
        cache = BytesIO()
        image_resized.save(cache, format="png")
        cache.seek(0)
        image_cache.setdefault(("ascii", size), image.load("cache.png", file=cache))
    font_image = image_cache[("ascii", size)]
    x, y = ord(char) % 16 * size, size * 16 - (ord(char) // 16 + 1) * size
    w = (special_width[char] if char in special_width else 0.75) * size
    return font_image.get_region(x, y, int(w), size).get_image_data()


def create_font_sga():
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
        x, y = ord(char) % 16 * 24, 24 * 16 - (ord(char) // 16 + 1) * 24
        mappings[char] = font_image.get_region(x, y, 18, 24).get_image_data()
    return create_font("sga", default_char=" ", ascent=24, size=24, mappings=mappings)


class CreateFontWindow(Window):
    def __init__(self):
        super().__init__(640, 480, "create_font")
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
    for size in [16, 24, 32]:
        fonts.append(
            create_font(
                "ascii",
                default_char=" ",
                ascent=size,
                size=size,
                font_class=UserDefinedSearchTextureFont,
                search_texture=get_texture_ascii
            )
        )
    fonts.append(create_font_sga())
    window = CreateFontWindow()
    clock.schedule_interval(window.draw, 1 / 60)
    app.run()
