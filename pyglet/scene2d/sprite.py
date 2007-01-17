#!/usr/bin/env python

'''
Model code for managing sprites
===============================

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'


from pyglet.GL.VERSION_1_1 import *
from pyglet.scene2d.drawable import *

class Sprite(Drawable):
    '''A sprite with some dimensions, image to draw and optional animation
    to run.

    Attributes:
        x, y, z         -- position (z is optional and defaults to 0)
        width, height   -- sprite dimensions (may differ from image)
        image           -- image for this sprite
        offset          -- offset of image from position (default (0,0))
        animations      -- a queue of SpriteAnimations to run
        properties      -- arbitrary data in a dict
    '''
    __slots__ = '_x _y z image width height offset properties animations _style'.split()
    def __init__(self, x, y, width, height, image, offset=(0,0), z=0,
            properties=None):
        super(Sprite, self).__init__()
        self._x, self._y, self.z = x, y, z
        self.width, self.height = width, height
        self.image = image
        self.offset = offset
        self.animations = []
        if properties is None:
            self.properties = {}
        else:
            self.properties = properties

        self._style = DrawStyle(color=(1, 1, 1, 1), texture=image.texture,
            x=x, y=y, z=z, width=width, height=height, uvs=image.uvs,
            draw_env=DRAW_BLENDED, draw_list=image.quad_list)

    @classmethod
    def from_image(cls, x, y, image, offset=(0,0), z=0, properties=None):
        '''Set up the sprite from the image - sprite dimensions are the
        same as the image.'''
        return cls(x, y, image.width, image.height, image, offset, z,
            properties)

    def get_drawstyle(self):
        return self._style
 
    def push_animation(self, animation):
        "Push a SpriteAnimation onto this sprite's animation queue."
        raise NotImplemented()
 
    def cancel_animation(self):
        'Cancel the current animation being run.'
        raise NotImplemented()
 
    def clear_animation(self):
        'Clear the animation queue.'
        raise NotImplemented()
 
    def animate(self, dt):
        '''Animate this sprite to handle passing of dt time.
        If self.image has a .animate method it will be called.
        '''
        raise NotImplemented()

    def contains(self, x, y):
        '''Return True if the point is inside the sprite.'''
        if x < self.x: return False
        if y < self.y: return False
        if x >= self.x + self.width: return False
        if y >= self.y + self.height: return False
        return True

    def overlaps(self, rect):
        '''Return True if this sprite overlaps the other rect.

        A rect is an object that has an origin .x, .y and size .width,
        .height.
        '''
        # we avoid using .right and .top properties here to speed things up
        if self.x > (rect.x + rect.width): return False
        if (self.x + self.width) < rect.x: return False
        if self.y > (rect.y + rect.height): return False
        if (self.y + self.height) < rect.y: return False
        return True

    def get_x(self):
        # XXX this calls another getter
        return self._x
    def set_x(self, x):
        self._x = x
        self._style.x = x
    x = property(get_x, set_x)
    def get_y(self):
        # XXX this calls another getter
        return self._y
    def set_y(self, y):
        self._y = y
        self._style.y = y
    y = property(get_y, set_y)
 
    # r/w, in pixels, y extent
    def get_top(self): return self.y + self.height
    def set_top(self, y): self.y = y - self.height
    top = property(get_top, set_top)

    # r/w, in pixels, y extent
    def get_bottom(self): return self.y
    def set_bottom(self, y): self.y = y
    bottom = property(get_bottom, set_bottom)

    # r/w, in pixels, x extent
    def get_left(self): return self.x
    def set_left(self, x): self.x = x
    left = property(get_left, set_left)

    # r/w, in pixels, x extent
    def get_right(self): return self.x + self.width
    def set_right(self, x): self.x = x - self.width
    right = property(get_right, set_right)

    # r/w, in pixels, (x, y)
    def get_center(self):
        return (self.x + self.width/2, self.y + self.height/2)
    def set_center(self, center):
        x, y = center
        self.x = x - self.width/2
        self.y = y - self.height/2
    center = property(get_center, set_center)

    # r/w, in pixels, (x, y)
    def get_midtop(self):
        return (self.x + self.width/2, self.y + self.height)
    def set_midtop(self, midtop):
        x, y = midtop
        self.x = x - self.width/2
        self.y = y - self.height
    midtop = property(get_midtop, set_midtop)

    # r/w, in pixels, (x, y)
    def get_midbottom(self):
        return (self.x + self.width/2, self.y)
    def set_midbottom(self, midbottom):
        x, y = midbottom
        self.x = x - self.width/2
        self.y = y
    midbottom = property(get_midbottom, set_midbottom)

    # r/w, in pixels, (x, y)
    def get_midleft(self):
        return (self.x, self.y + self.height/2)
    def set_midleft(self, midleft):
        x, y = midleft
        self.x = x
        self.y = y - self.height/2
    midleft = property(get_midleft, set_midleft)

    # r/w, in pixels, (x, y)
    def get_midright(self):
        return (self.x + self.width, self.y + self.height/2)
    def set_midright(self, midright):
        x, y = midright
        self.x = x - self.width
        self.y = y - self.height/2
    midright = property(get_midright, set_midright)
 

class RotatableSprite(Sprite):
    '''A sprite that may be rotated.

    Additional attributes:
        angle           -- angle of rotation in degrees
        cog             -- center of gravity for rotation (x, y)
                           (defaults to middle of sprite)
    '''
    __slots__ = Sprite.__slots__ + '_angle cog'.split()
    def __init__(self, x, y, width, height, image, angle=0, cog=None,
            offset=(0,0), z=0, properties=None):
        super(RotatableSprite, self).__init__(x, y, width, height, image,
            offset, z, properties)
        self._angle = 0
        if cog is None:
            cog = (width/2, height/2)
        self.cog = cog

    def get_angle(self):
        return self._angle
    def set_angle(self, angle):
        self._angle = angle
        s = self._style
        if angle:
            s.draw_func = self.draw_rotated
            s.draw_list = None
        else:
            s.draw_func = None
            s.draw_list = self.image.quad_list
    angle = property(get_angle, set_angle)

    @classmethod
    def from_image(cls, x, y, image, angle=0, cog=None, offset=(0,0), z=0,
            properties=None):
        '''Set up the sprite from the image - sprite dimensions are the
        same as the image.'''
        return cls(x, y, image.width, image.height, image, angle, cog,
            offset, z, properties)

    def draw_rotated(self):
        cog = self.cog
        glPushMatrix()
        glTranslatef(cog[0], cog[1], 0)
        glRotatef(self._angle, 0, 0, 1)
        glTranslatef(-cog[0], -cog[1], 0)
        glCallList(self.image.quad_list)
        glPopMatrix()

    def get_drawstyle(self):
        return self._style


"""
class SpriteAnimation:
    def animate(self, sprite, dt):
        ''' run this animation to handle passing of dt time. alters sprite
        position and optionally image'''
        raise NotImplemented()
 
class JumpAnimation(SpriteAnimation):
    velocity = (vx, vy)         # in pixels / second?
    gravity =                   # in pixels / second?
    ground =                    # height of ground
    map =                       # tilemap with the ground / walls in it
    image =                     # optional ImageAnimation to run
 
class PathAnimation(SpriteAnimation):
    ''' Will animate smoothly from one position to another, optionallyo to
    another, optionally accelerating, etc. '''
    points = [(x, y, z)]        # points to move to in order
    speed =                     # initial speed in direction of first point
    velocity =                  # initial velocity if not in ^^^
    turn_speed =                # optional speed to slow to for turning
    acceleration =              # needed if turn_speed != None
    max_speed =                 # needed if acceleration != None
"""
