import pyglet
from pyglet.font.group import FontGroup

window = pyglet.window.Window(caption="Font Group Test")

font_group = FontGroup("GUIFontGroup")
if pyglet.compat_platform == "win32":
    font_group.add("Arial", 0x0000, 0x024F)
    font_group.add("MS Gothic", 0x4E00, 0x9FFF)
    font_group.add("Segoe UI Emoji", 0x1F600, 0x1F64F)
elif pyglet.compat_platform == "darwin":
    font_group.add("Helvetica Neue", 0x0000, 0x024F)
    font_group.add("Hiragino Sans", 0x4E00, 0x9FFF)
    font_group.add("Apple Color Emoji", 0x1F600, 0x1F64F)
elif pyglet.compat_platform == "linux":
    font_group.add("DejaVu Sans", 0x0000, 0x024F)
    font_group.add("Noto Sans CJK JP", 0x4E00, 0x9FFF)
    font_group.add("Noto Color Emoji", 0x1F600, 0x1F64F)

pyglet.font.add_group(font_group)

text = "Hello 世界 😀"

label = pyglet.text.Label(text,
                          font_name='GUIFontGroup',
                          font_size=36,
                          x=window.width // 2,
                          y=window.height // 2,
                          anchor_x='center',
                          anchor_y='center')


@window.event
def on_draw():
    window.clear()
    label.draw()


pyglet.app.run()
