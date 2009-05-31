# Copyright 2009 Joe Wreschnig and others.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The names of the authors and contributors may be used to endorse or
#    promote products derived from this software without specific prior
#    written permission.
#
# All warranties and liabilities, express or implied, are hereby
# disclaimed.

"""Draw a NinePatch image.

NinePatch is a format for storing how to cut up a 9-part resizable
rectangular image within the image pixel data directly.

For more information on the NinePatch format, see
http://developer.android.com/guide/topics/graphics/2d-graphics.html#nine-patch.

"""

__all__ = ["NinePatch"]

from pyglet.gl import *

class PixelData(object):
    def __init__(self, image):
        image_data = image.get_image_data()
        self.has_alpha = 'A' in image_data.format
        self.data = image_data.get_data("RGBA", image.width * 4)
        self.width = image.width
        self.height = image.height

    def is_black(self, x, y):
        p = (y * self.width + x) * 4
        if self.has_alpha:
            if self.data[p+3] == '\x00':
                return False # Fully transparent

        return self.data[p:p+3] == '\x00\x00\x00'

class NinePatch(object):
    """A scalable 9-patch image.
    """

    # Content area of the image, in pixels from the edge.
    padding_top = None
    padding_bottom = None
    padding_right = None
    padding_left = None

    # Resizable area of the image, in pixels from the closest edge
    stretch_top = None
    stretch_left = None
    stretch_right = None
    stretch_bottom = None

    def __init__(self, image):
        """Create NinePatch cuts of an image

        Arguments:
            image - an ImageData (Texture, TextureRegion, etc)
            texture - force cut ImageDatas to be Textures (or Regions)
        """

        data = PixelData(image)
        width = data.width
        height = data.height

        # Texture dimensions after removing the 9patch outline.
        self.width = width - 2
        self.height = height - 2

        # Only need to retain the texture for drawing
        self.texture = image.get_texture()

        # Find stretch area markers
        for x in range(1, width - 1):
            if data.is_black(x, height - 1):
                self.stretch_left = x
                break
        else:
            self.stretch_left = 1

        for x in range(width - 2, 0, -1):
            if data.is_black(x, height - 1):
                self.stretch_right = width - x
                break
        else:
            self.stretch_right = 1

        for y in range(1, height - 1):
            if data.is_black(0, y):
                self.stretch_bottom = y
                break
        else:
            self.stretch_bottom = 1

        for y in range(height - 2, 0, -1):
            if data.is_black(0, y):
                self.stretch_top = height - y
                break
        else:
            self.stretch_top = 1

        # Find content area markers, if any
        for x in range(1, width - 1):
            if data.is_black(x, 0):
                self.padding_left = x - 1
                break

        for x in range(width - 2, 0, -1):
            if data.is_black(x, 0):
                self.padding_right = self.width - x
                break

        for y in range(1, height - 1):
            if data.is_black(width - 1, y):
                self.padding_bottom = y - 1
                break

        for y in range(height - 2, 0, -1):
            if data.is_black(width - 1, y):
                self.padding_top = self.height - y
                break

        # Texture coordinates, in pixels
        u1 = 1
        v1 = 1
        u2 = self.stretch_left + 1
        v2 = self.stretch_bottom + 1
        u3 = width - self.stretch_right - 1
        v3 = height - self.stretch_top - 1
        u4 = width - 1
        v4 = height - 1

        # Texture coordinates as ratio of image size (0 to 1)
        u1, u2, u3, u4 = [s / float(width) for s in (u1, u2, u3, u4)]
        v1, v2, v3, v4 = [s / float(height) for s in (v1, v2, v3, v4)]

        # Scale texture coordinates to match the tex_coords pyglet gives us
        # (these aren't necessarily 0-1 as the texture may have been packed)
        (tu1, tv1, _, 
         _, _, _, 
         tu2, tv2, _, 
         _, _, _) = self.texture.tex_coords
        u_scale = tu2 - tu1
        u_bias = tu1
        v_scale = tv2 - tv1
        v_bias = tv1
        u1, u2, u3, u4 = [u_bias + u_scale * s for s in (u1, u2, u3, u4)]
        v1, v2, v3, v4 = [v_bias + v_scale * s for s in (v1, v2, v3, v4)]

        # 2D texture coordinates, bottom-left to top-right
        self.tex_coords = (
            u1, v1,
            u2, v1,
            u3, v1,
            u4, v1,
            u1, v2,
            u2, v2,
            u3, v2,
            u4, v2,
            u1, v3,
            u2, v3,
            u3, v3,
            u4, v3,
            u1, v4,
            u2, v4,
            u3, v4,
            u4, v4,
        )

        # Quad indices
        self.indices = []
        for y in range(3):
            for x in range(3):
                self.indices.extend([
                    x + y * 4,
                    (x + 1) + y * 4,
                    (x + 1) + (y + 1) * 4,
                    x + (y + 1) * 4,
                ])

    def get_vertices(self, x, y, width, height):
        """Get 16 2D vertices for the given image region"""
        x1 = x
        y1 = y
        x2 = x + self.stretch_left
        y2 = y + self.stretch_bottom
        x3 = x + width - self.stretch_right
        y3 = y + height - self.stretch_top
        x4 = x + width
        y4 = y + height

        # To match tex coords, vertices are bottom-left to top-right
        return (
            x1, y1,
            x2, y1,
            x3, y1,
            x4, y1,
            x1, y2,
            x2, y2,
            x3, y2,
            x4, y2,
            x1, y3,
            x2, y3,
            x3, y3,
            x4, y3,
            x1, y4,
            x2, y4,
            x3, y4,
            x4, y4,
        )

    def draw(self, x, y, width, height):
        """Draw the nine-patch at the given image dimensions."""
        width = max(width, self.width + 2)
        height = max(height, self.height + 2)
        vertices = self.get_vertices(x, y, width, height)

        glPushAttrib(GL_ENABLE_BIT)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(self.texture.target)
        glBindTexture(self.texture.target, self.texture.id)
        pyglet.graphics.draw_indexed(
            16, GL_QUADS, self.indices,
            ('v2i', vertices),
            ('t2f', self.tex_coords))
        glPopAttrib()

    def draw_around(self, x, y, width, height):
        """Draw the nine-patch around the given content area"""
        self.draw(x - self.padding_left,
                  y - self.padding_bottom,
                  width + self.padding_left + self.padding_right,
                  height + self.padding_bottom + self.padding_top)

if __name__ == '__main__':
    import sys
    image = pyglet.image.load(sys.argv[1])
    ninepatch = NinePatch(image)

    window = pyglet.window.Window(resizable=True)
    label = pyglet.text.Label('Hello, NinePatch', 
                              font_size=16,
                              anchor_y='bottom',
                              color=(0,0,0,255))

    @window.event
    def on_draw():
        glClearColor(.7, .7, .7, 1.)
        window.clear()
        width = label.content_width
        height = label.content_height
        label.x = window.width / 2 - width / 2
        label.y = window.height / 2 - height / 2
        ninepatch.draw_around(label.x, label.y, width, height)
        label.draw()
        
    pyglet.app.run()
