"""This example demonstrates how to create a compatible font with Pyglets layout system using images."""
from __future__ import annotations

import pyglet
from pyglet.font.user import UserDefinedMappingFont, get_scaled_user_font

# Add our resource path that includes the font atlas.
pyglet.resource.path.append('../../tests/data/fonts')
pyglet.resource.reindex()

# Create Window
window = pyglet.window.Window()

# Create a graphics batch to batch render our objects.
batch = pyglet.graphics.Batch()

atlas_image = pyglet.resource.image("action_man_atlas.png")

# You can use whatever method you want, but you just need to map your ImageData instances to the character
atlas_characters = """ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789,.: '"/?!@#$%^&*()"""
rows = 5
columns = 16

# Ensure the data is image data, as it is needed to blit into a Texture.
image_data = atlas_image.get_image_data()

# Create image grid based on how many glyphs.
grid = pyglet.image.ImageGrid(image_data, rows=rows, columns=columns)

# Map characters to image data. A -> ImageData
# The mapping can be a dictionary lookup, or it can be an object that behaves like a dictionary.
mapping = {}
char = 0
for row in range(rows):
    for column in range(columns):
        y_prime = (rows - 1) - row
        new_index = column + y_prime * columns
        # This chooses values based on the top left. Pyglet uses bottom left indexing.
        glyph = grid[new_index]
        mapping[atlas_characters[char]] = glyph
        char += 1

class ActionManMappedFont(UserDefinedMappingFont):
    glyph_fit = len(atlas_characters)


# Create your font instance.
action_man_font = ActionManMappedFont("custom_action_man1",  # Custom unique name to not clash with others.
                                      default_char=" ",  # Default character to use if a character is not mapped.
                                      size=13,  # The size you want your font to be considered at base size.
                                      mappings=mapping)  # The mapping object containing your character -> glyphs.

# Add the font to usable fonts.
pyglet.font.add_user_font(action_man_font)

# Create a label like normal!
label = pyglet.text.Label("Hello World!",
                          font_size=13,
                          font_name="custom_action_man1",
                          x=window.width // 2,
                          y=window.height // 2,
                          anchor_x="center",
                          anchor_y="center",
                          batch=batch)

# As an optional dependency with Pillow installed, you can scale your bitmap font.
try:
    # Create the size you want it to be scaled to.
    # Only create new font sizes from the original user font object.
    # !! Note that the size will be calculated in relation to your original size.
    action_scaled_32 = get_scaled_user_font(action_man_font, 32)
    pyglet.font.add_user_font(action_scaled_32)

    scaled_label = pyglet.text.Label("Scaled Hello World!",
                              font_size=32,
                              font_name="custom_action_man1",
                              x=window.width // 2,
                              y=window.height // 3,
                              anchor_x="center",
                              anchor_y="center",
                              batch=batch)
except ImportError:
    print("Warning: PIL was not detected, scaled font will not be shown.")


@window.event
def on_draw():
    window.clear()
    batch.draw()


pyglet.app.run()
