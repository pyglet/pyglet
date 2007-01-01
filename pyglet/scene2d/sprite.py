#!/usr/bin/env python

'''
Model code for managing sprites
===============================

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

class Sprite(object):
    '''A sprite with some dimensions, image to draw and optional animation
    to run.

    Attributes:
        x, y, z         -- position (z is optional and defaults to 0)
        width, height   -- sprite dimensions (may differ from image)
        image           -- image for this sprite
        offset          -- offset of image from position (default (0,0))
        animations      -- a queue of SpriteAnimations to run
    '''
    __slots__ = 'x y z image width height offset animations'.split()
    def __init__(self, x, y, width, height, image, offset=(0,0), z=0):
        self.x, self.y, self.z = x, y, z
        self.width, self.height = width, height
        self.image = image
        self.offset = offset
        self.animations = []
 
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
 
class SpriteAnimation:
    def animate(self, sprite, dt):
        ''' run this animation to handle passing of dt time. alters sprite
        position and optionally image'''
        raise NotImplemented()
 
"""
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
