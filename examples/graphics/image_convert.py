#!/usr/bin/env python
"""Convert an image to another file format supported by pyglet.

Usage::
    python image_convert.py <src-file> <dest-file>

"""


import sys

import pyglet


def convert(src, dest):
    if '.dds' in src.lower():
        # Compressed textures need to be uploaded to the video card before
        # they can be saved.
        texture = pyglet.image.load(src).get_texture()
        texture.save(dest)
    else:
        # Otherwise just save the loaded image in the new format.
        image = pyglet.image.load(src)
        image.save(dest)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    src = sys.argv[1]
    dest = sys.argv[2]
    convert(src, dest)
