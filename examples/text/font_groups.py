"""Demonstrate automatic and range-based font group fallback."""

import pyglet
from pyglet.font.group import FontGroup, FontRangeGroup


window = pyglet.window.Window(800, 250, caption="Font Group Fallback")

# FontGroup selects the first family that contains each character. This is the
# most common use case.
automatic_group = FontGroup("AutomaticGUIFontGroup")

# FontRangeGroup assigns a family from explicit Unicode ranges. Use this when
# the application needs predictable routing rather than coverage-based choice.
range_group = FontRangeGroup("RangeGUIFontGroup")

if pyglet.compat_platform == "win32":
    families = ("Arial", "MS Gothic", "Segoe UI Emoji")
elif pyglet.compat_platform == "darwin":
    families = ("Helvetica Neue", "Hiragino Sans", "Apple Color Emoji")
elif pyglet.compat_platform == "linux":
    families = ("DejaVu Sans", "Noto Sans CJK JP", "Noto Color Emoji")
else:
    families = ("sans-serif", "sans-serif", "sans-serif")

latin_family, cjk_family, emoji_family = families

automatic_group.add(latin_family)
automatic_group.add(cjk_family)
automatic_group.add(emoji_family)

range_group.add(latin_family, 0x0000, 0x024F)
range_group.add(cjk_family, 0x4E00, 0x9FFF)
range_group.add(emoji_family, 0x1F600, 0x1F64F)

pyglet.font.add_group(automatic_group)
pyglet.font.add_group(range_group)

text = "Hello 世界 😀"

automatic_label = pyglet.text.Label(
    f"Automatic fallback: {text}",
    font_name=automatic_group.name,
    font_size=24,
    x=window.width // 2,
    y=window.height * 2 // 3,
    anchor_x="center",
    anchor_y="center",
)

range_label = pyglet.text.Label(
    f"Range fallback: {text}",
    font_name=range_group.name,
    font_size=24,
    x=window.width // 2,
    y=window.height // 3,
    anchor_x="center",
    anchor_y="center",
)


@window.event
def on_draw():
    window.clear()
    automatic_label.draw()
    range_label.draw()


pyglet.app.run()
