from pyglet.gl import *
 
class DrawEnv(object):
    '''Sets up drawing environment.

    My have either or both of a "before" and "after" method.
    '''
    pass
 
class DrawBlended(DrawEnv):
    '''Sets up texture env for an alpha-blended draw.
    '''
    def before(self):
        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT)
        # XXX this belongs in a "DrawTextureBlended" or something
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def after(self):
        glPopAttrib()
DRAW_BLENDED = DrawBlended()
 
class Drawable(object):
    def __init__(self):
        self.effects = []
        self._style = None

    def add_effect(self, effect):
        self.effects.append(effect)
        self._style = None
    def remove_effect(self, effect):
        self.effects.remove(effect)
        self._style = None
 
    def get_drawstyle(self):
        raise NotImplemented('implement on subclass')
 
    def get_style(self):
        '''Return the DrawStyle for this Drawable.

        This method should return None if nothing should be drawn.
        '''
        if self._style is None:
            self._style = self.get_drawstyle()
            for effect in self.effects:
                self._style = effect.apply(self._style)
        return self._style

    def draw(self):
        '''Convenience method.

        Don't use this if you have a lot of drawables and care about
        performance. Collect up your drawables in a list and pass that to
        draw_many().
        '''
        style = self.get_style()
        if style is not None: style.draw()


class Effect(object):
    def apply(self, style):
        '''Modify some aspect of the style. If style.is_copy is False then
        .copy() it. We don't do that automatically because there's a chance
        this method is a NOOP.
        '''
        raise NotImplemented()
 
class TintEffect(Effect):
    '''Apply a tint to the Drawable:

    For each component RGBA:

        resultant color = drawable.color * tint.color
    '''
    def __init__(self, tint):
        self.tint = tint
    def apply(self, style):
        style = style.copy()
        style.color = tuple([style.color[i] * self.tint[i] for i in range(4)])
        return style
 
class ScaleEffect(Effect):
    '''Apply a scale to the Drawable.
    '''
    def __init__(self, sx, sy):
        self.sx, self.sy = sx, sy
    def apply(self, style):
        style = style.copy()
        style.sx = self.sx
        style.sy = self.sy
        return style

class RotateEffect(Effect):
    '''Apply a rotation (about the Z axis) to the Drawable.
    '''
    def __init__(self, angle):
        self.angle = angle
    def apply(self, style):
        style = style.copy()
        style.angle = self.angle
        return style

class DrawStyle(object):
    '''

    Notes:

        draw_func(<DrawStyle instance>)
    '''
    def __init__(self, color=None, texture=None, x=0, y=0, sx=1, sy=1,
            angle=0, width=None, height=None, uvs=None, draw_list=None,
            draw_env=None, draw_func=None):
        self.color = color
        self.x, self.y = x, y
        self.sx, self.sy = sx, sy
        self.angle = angle
        self.width, self.height = width, height

        self.texture = texture
        if texture is not None and uvs is None:
            raise ValueError('texture and uvs must both be supplied')
        self.uvs = uvs
        if uvs is not None and texture is None:
            raise ValueError('texture and uvs must both be supplied')

        self.draw_list = draw_list
        self.draw_env = draw_env
        self.draw_func = draw_func
        self.is_copy = False
 
    def copy(self):
        s = DrawStyle(color=self.color, texture=self.texture, x=self.x,
            y=self.y, width=self.width, height=self.height,
            uvs=self.uvs, draw_list=self.draw_list, draw_env=self.draw_env,
            draw_func=self.draw_func)
        s.is_copy = True
        return s
 
    def draw(self):
        if self.color is not None:
            glColor4f(*self.color)
        
        if self.texture is not None:
            glBindTexture(GL_TEXTURE_2D, self.texture.id)

        if hasattr(self.draw_env, 'before'):
            self.draw_env.before()

        transform = self.x or self.y or self.sx != self.sy != 1 or self.angle
        if transform:
            glPushMatrix()

        if self.x or self.y:
            glTranslatef(self.x, self.y, 0)

        if self.sx or self.sy:
            glScalef(self.sx, self.sy, 1)

        if self.angle:
            cx, cy = self.width/2, self.height/2
            glTranslatef(cx, cy, 0)
            glRotatef(self.angle, 0, 0, 1)
            glTranslatef(-cx, -cy, 0)

        if self.draw_func is not None:
            self.draw_func(self)

        if self.draw_list is not None:
            glCallList(self.draw_list)

        if hasattr(self.draw_env, 'after'):
            self.draw_env.after()

        if transform:
            glPopMatrix()

    def __cmp__(self, other):
        return (
            cmp(self.color, other.color) or
            cmp(self.texture.id, other.texture.id) or
            cmp(self.draw_env, other.draw_env) or
            cmp(self.draw_func, other.draw_func) or
            cmp(self.draw_list, other.draw_list)
        )


def draw_many(drawables):
    styles = filter(None, [d.get_style() for d in drawables])
    drawables.sort()
    old_color = None
    old_texture = None
    old_env = None
    for d in styles:
        if d.color != old_color:
            glColor4f(*d.color)
            old_color = d.color
        if d.texture != old_texture:
            if d.texture is not None:
                glBindTexture(GL_TEXTURE_2D, d.texture.id)
            old_texture = d.texture.id
        if d.draw_env != old_env:
            if old_env is not None and hasattr(old_env, 'after'):
                old_env.after()
            if hasattr(d.draw_env, 'before'):
                d.draw_env.before()
            old_env = d.draw_env
        transform = d.x or d.y or d.sx != d.sy != 1 or d.angle
        if transform:
            glPushMatrix()
        if d.x or d.y:
            glTranslatef(d.x, d.y, 0)
        if d.sx != 1 or d.sy != 1:
            glScalef(d.sx, d.sy, 1)
        if d.angle:
            cx, cy = d.width/2, d.height/2
            glTranslatef(cx, cy, 0)
            glRotatef(d.angle, 0, 0, 1)
            glTranslatef(-cx, -cy, 0)
        if d.draw_list is not None:
            glCallList(d.draw_list)
        if d.draw_func is not None:
            d.draw_func(d)
        if transform:
            glPopMatrix()

    if old_env is not None and hasattr(old_env, 'after'):
        old_env.after()

