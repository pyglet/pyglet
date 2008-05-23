#!/usr/bin/python
# $Id:$

import ctypes
import math
import optparse
import pyglet

root2 = math.sqrt(2)

def gen_dist_field(img, width, height, spread):
    sample_width = img.width // width
    sample_height = img.height // height
    dist_scale = 127. / (spread * root2)

    # Grab image data as list of int.
    data = img.get_data('L', img.width)
    if isinstance(data, str):
        data = map(ord, data)

    # Pad input image by `spread` on each side to avoid having to check bounds
    # Add left and right sides
    data_tmp = []
    padx = [0] * spread
    pitch = img.width
    in_i = 0
    for row_i in range(img.height):
        data_tmp.extend(padx)
        data_tmp.extend(data[in_i:in_i + pitch])
        data_tmp.extend(padx)
        in_i += pitch
    pitch += spread * 2
    # Add top and bottom
    pady = [0] * (pitch * spread)
    data = pady + data_tmp + pady

    field = []
    for y in range(height):
        in_i = (spread + int((y + 0.5) * sample_height)) * pitch + \
            spread + sample_width // 2
        for x in range(width):
            colour = data[in_i]
            for s in range(1, spread + 1):
                if data[in_i - s] != colour:
                    dist = s
                    break
                if data[in_i + s] != colour:
                    dist = s
                    break
                if data[in_i - s * pitch] != colour:
                    dist = s
                    break
                if data[in_i + s * pitch] != colour:
                    dist = s
                    break
                if data[in_i - s * pitch - s] != colour:
                    dist = s * root2
                    break
                if data[in_i - s * pitch + s] != colour:
                    dist = s * root2
                    break
                if data[in_i + s * pitch - s] != colour:
                    dist = s * root2
                    break
                if data[in_i + s * pitch + s] != colour:
                    dist = s * root2
                    break
            else:
                dist = spread 
            if not colour:
                dist = -dist
            dist = int(dist * dist_scale) + 127
            field.append(255)
            field.append(dist)
            in_i += sample_width

    field = (ctypes.c_byte * len(field))(*field)

    out_img = pyglet.image.create(width, height)
    out_img.set_data('LA', width * 2, field)
    return out_img

if __name__ == '__main__':
    import os
    
    parser = optparse.OptionParser()
    parser.add_option('-s', '--size', type=int, default=32)
    parser.add_option('-p', '--spread', type=int, default=128)
    parser.add_option('-o', '--output', default=None)
    (options, args) = parser.parse_args()

    filename = args[0]
    img = pyglet.image.load(filename)
    img2 = gen_dist_field(img, options.sample_size, options.sample_size, 
                          options.spread)
    if not options.output:
        base, _ = os.path.splitext(filename)
        options.output = '%s.df.png' % base
    img2.save(options.output)

