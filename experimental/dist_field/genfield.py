#!/usr/bin/python
# $Id:$

import ctypes
import math
import optparse
import pyglet

root2 = math.sqrt(2)

def gen_dist_field(img, width, height, spread, bidirectional=True):
    sample_width = img.width // width
    sample_height = img.height // height
    max_dist = spread * root2
    dist_scale = 127. / max_dist

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
            dist1_sq = dist2_sq = dist_sq = (max_dist + 1) ** 2
            for sy in range(-spread, spread + 1):
                row_i = in_i + sy * pitch
                for sx in range(-spread, spread + 1):
                    if data[row_i + sx] != colour:
                        dist_sq = min(dist_sq, sy * sy + sx * sx)
                        if sx * sy > 0:
                            dist1_sq = min(dist1_sq, sy * sy + sx * sx)
                        else:
                            dist2_sq = min(dist2_sq, sy * sy + sx * sx)
            dist = math.sqrt(dist_sq)
            dist1 = math.sqrt(dist1_sq)
            dist2 = math.sqrt(dist2_sq)

            if not colour:
                dist = -dist
                dist1 = -dist1
                dist2 = -dist2
            dist = int(dist * dist_scale) + 128
            dist1 = int(dist1 * dist_scale) + 128
            dist2 = int(dist2 * dist_scale) + 128
            if bidirectional:
                field.append(dist1)
                field.append(dist2)
                field.append(dist)
            else:
                field.append(255)
            field.append(dist)
            in_i += sample_width

    field = (ctypes.c_byte * len(field))(*field)

    out_img = pyglet.image.create(width, height)
    if bidirectional:
        out_img.set_data('RGBA', width * 4, field)
    else:
        out_img.set_data('LA', width * 2, field)
    return out_img

if __name__ == '__main__':
    import os
    
    parser = optparse.OptionParser()
    parser.add_option('-s', '--size', type=int, default=32)
    parser.add_option('-p', '--spread', type=int, default=128)
    parser.add_option('-o', '--output', default=None)
    parser.add_option('-b', '--bidirectional', action='store_true', 
                      default=False)
    (options, args) = parser.parse_args()

    filename = args[0]
    img = pyglet.image.load(filename)
    img2 = gen_dist_field(img, options.size, options.size, 
                          options.spread, options.bidirectional)
    if not options.output:
        base, _ = os.path.splitext(filename)
        options.output = f'{base}.df.png'
    img2.save(options.output)

