#!/usr/bin/python
# $Id:$

'''Software decoder for S3TC compressed texture (i.e., DDS).

http://oss.sgi.com/projects/ogl-sample/registry/EXT/texture_compression_s3tc.txt
'''

import ctypes
import re

split_8byte = re.compile('........', flags=re.DOTALL)

def decode_dxt1_packed(data, width, height):
    # Decode to 16-bit RGB UNSIGNED_SHORT_5_6_5
    image = (ctypes.c_uint16 * (width * height))()

    # Read 8 bytes at a time
    image_offset = 0
    col = 0
    for c0_lo, c0_hi, c1_lo, c1_hi, b0, b1, b2, b3 in split_8byte.findall(data):
        color0 = ord(c0_lo) | ord(c0_hi) << 8
        color1 = ord(c1_lo) | ord(c1_hi) << 8
        bits = ord(b0) | ord(b1) << 8 | ord(b2) << 16 | ord(b3) << 24

        # i is the dest ptr for this block
        i = image_offset
        for y in range(4):
            for x in range(4):
                code = bits & 0x3

                if code == 0:
                    image[i] = color0
                elif code == 1:
                    image[i] = color1
                elif code == 3 and color0 <= color1:
                    image[i] = 0
                else:
                    r0 = color0 & 0x1f
                    g0 = (color0 & 0x7e0) >> 5
                    b0 = (color0 & 0xf800) >> 11
                    r1 = color1 & 0x1f
                    g1 = (color1 & 0x7e0) >> 5
                    b1 = (color1 & 0xf800) >> 11
                    r = g = b = 0
                    if code == 2 and color0 > color1:
                        r = (2 * r0 + r1) / 3
                        g = (2 * g0 + g1) / 3
                        b = (2 * b0 + b1) / 3
                    elif code == 3 and color0 > color1:
                        r = (r0 + 2 * r1) / 3
                        g = (g0 + 2 * g1) / 3
                        b = (b0 + 2 * b1) / 3
                    else:
                        assert code == 2 and color0 <= color1
                        r = (r0 + r1) / 2
                        g = (g0 + g1) / 2
                        b = (b0 + b1) / 2
                    image[i] = r | g << 5 | b << 11

                bits >>= 2
                i += 1
            i += width - 4

        # Move dest ptr to next 4x4 block
        advance_row = (image_offset + 4) % width == 0
        image_offset += width * 3 * advance_row + 4

    return image
