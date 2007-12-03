
import os

from pyglet import image, gl
import graphics

import rect

class Layer(graphics.Batch):
    pass

def load_image(filename, file=None):
    filename = os.path.abspath(filename)

    # Locate or create image cache   
    shared_object_space = gl.get_current_context().object_space
    if not hasattr(shared_object_space, 'spryte_image_cache'):
        shared_object_space.spryte_image_cache = {}
    cache = shared_object_space.spryte_image_cache

    # Look for image name in image cache
    if filename in cache:
        return cache[filename]

    # Not in cache, create from scratch
    image = Image(filename, file)
    cache[filename] = image
    return image

class Image(object):
    '''Associate a graphics state with the image.

    TODO: collate multiple loaded images into a single texture
    '''
    def __init__(self, filename, file=None):
        im = image.load(filename, file)
        self.filename = filename
        self.texture = im.texture
        self.width, self.height = im.width, im.height
        self.state = graphics.TextureState(im.texture)

class AnimatedImage(Image):
    def __init__(self, file, frames, rows=1):
        im = image.load(file)
        # self.frames = XXX need to pull out the frames from the image

        self.width, self.height = frame.width, frame.height

        # first frame
        self.texture = im.texture

        self.state = graphics.TextureState(im.texture)

class Sprite(rect.Rect):
    def __init__(self, image, layer, x, y, **attributes):
        if not isinstance(image, Image):
            im = self._image = load_image(image)
        else:
            im = self._image = image

        super(Sprite, self).__init__(x, y, im.width, im.height)
        w, h = self._width, self._height

        # XXX if isinstance(im, AnimatedImage) then schedule for animation

        coords = [x, y,   x+w,   y,    x+w,   y+h,    x,    y+h]
        t = im.texture.tex_coords
        tex_coords = [
             t[0][0], t[0][1],
             t[1][0], t[1][1],
             t[2][0], t[2][1],
             t[3][0], t[3][1],
        ]
        # XXX use point sprites if they're available
        self.primitive = layer.add(4, gl.GL_QUADS, im.state,
            ('v2f/stream', coords),
            ('t2f/stream', tex_coords),         # allow animation
        )
        self.layer = layer
        self._x = x
        self._y = y
        self.__dict__.update(attributes)

    def delete(self):
        self.primitive.delete()

    # XXX set_image
    image = property(lambda self: self._image)

    def set_x(self, value):
        self._x = value
        iv = int(value)
        w = self._width
        # use this if/when ctypes supports it
        #self.primitive.vertices[0::2] = [iv, iv + w, iv + w, iv]
        self.primitive.vertices[0] = self.primitive.vertices[6] = iv
        self.primitive.vertices[2] = self.primitive.vertices[4] = iv + w
    x = property(lambda self: self._x, set_x)

    def set_y(self, value):
        self._y = value
        iv = int(value)
        # XXX intify width and height
        h = self._height
        # use this if/when ctypes supports it
        #self.primitive.vertices[1::2] = [iv, iv, iv + h, iv + h]
        self.primitive.vertices[1] = self.primitive.vertices[3] = iv
        self.primitive.vertices[5] = self.primitive.vertices[7] = iv + h
    y = property(lambda self: self._y, set_y)

    def set_pos(self, pos):
        self._x, self._y = pos
        ix = int(self._x)
        iy = int(self._y)
        w, h = self._width, self._height
        self.primitive.vertices[:] = [
            ix, iy,
            ix + w, iy,
            ix + w, iy + h,
            ix, iy + h,
        ]
    pos = property(lambda self: (self._x, self._y), set_pos)

    def set_width(self, value):
        self._width = value
        ix = int(self._x)
        w = self._width
        # use this if/when ctypes supports it
        #self.primitive.vertices[0::2] = [ix, ix + w, ix + w, ix]
        self.primitive.vertices[0] = self.primitive.vertices[6] = ix
        self.primitive.vertices[2] = self.primitive.vertices[4] = ix + w
    width = property(lambda self: self._width, set_width)

    def set_height(self, value):
        self._height = value
        iy = int(self._y)
        h = self._height
        # use this if/when ctypes supports it
        #self.primitive.vertices[1::2] = [iy, iy, iy + h, iy + h]
        self.primitive.vertices[1] = self.primitive.vertices[3] = iy
        self.primitive.vertices[5] = self.primitive.vertices[7] = iy + h
    height = property(lambda self: self._height, set_height)

