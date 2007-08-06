from wydget import anim
from wydget.widgets.frame import Frame

class Drawer(Frame):
    '''A *transparent container* that may hide and expose its contents.
    '''
    name='drawer'

    HIDDEN='hidden'
    EXPOSED='exposed'
    LEFT='left'
    RIGHT='right'
    TOP='top'
    BOTTOM='bottom'

    def __init__(self, parent, state=HIDDEN, side=LEFT,
            is_transparent=True, **kw):
        super(Drawer, self).__init__(parent, is_transparent=is_transparent,
            **kw)
        self.state = state
        self.side = side
        if state == self.HIDDEN:
            self.setVisible(False)

    def toggle_state(self):
        if self.state == self.EXPOSED: self.hide()
        else: self.expose()

    _anim = None
    def expose(self):
        if self.state == self.EXPOSED: return
        if self._anim is not None and self._anim.is_running:
            self._anim.cancel()
        self._anim = ExposeAnimation(self)
        self.setVisible(True)
        self.state = self.EXPOSED

    def hide(self):
        if self.state == self.HIDDEN: return
        if self._anim is not None and self._anim.is_running:
            self._anim.cancel()
        self._anim = HideAnimation(self)
        self.state = self.HIDDEN

class HideAnimation(anim.Animation):
    def __init__(self, drawer, duration=.25, function=anim.cosine90):
        self.drawer = drawer
        self.duration = duration
        self.function = function
        if drawer.side == Drawer.LEFT:
            self.sx = int(drawer.x)
            self.ex = int(drawer.x - drawer.width)
            self.sw = int(drawer.width)
            self.ew = 0
        elif drawer.side == Drawer.RIGHT:
            self.sx = int(drawer.x)
            self.ex = int(drawer.x + drawer.width)
            self.sw = int(drawer.width)
            self.ew = 0
        elif drawer.side == Drawer.TOP:
            self.sy = int(drawer.y)
            self.ey = int(drawer.y - drawer.height)
            self.sh = int(drawer.height)
            self.eh = 0
        elif drawer.side == Drawer.BOTTOM:
            self.sy = int(drawer.y)
            self.ey = int(drawer.y + drawer.height)
            self.sh = int(drawer.height)
            self.eh = 0
        super(HideAnimation, self).__init__()

    def cancel(self):
        self.drawer.setVisible(False)
        if self.drawer.side in (Drawer.LEFT, Drawer.RIGHT):
            self.drawer.setViewClip((self.sx, 0, self.ew,
                self.drawer.height))
            self.drawer.x = self.ex
        else:
            self.drawer.setViewClip((0, self.sy, self.drawer.width,
                self.eh))
            self.drawer.y = self.ey
        super(HideAnimation, self).cancel()

    def animate(self, dt):
        self.anim_time += dt
        if self.anim_time >= self.duration:
            self.cancel()
        else:
            t = self.anim_time / self.duration
            if self.drawer.side in (Drawer.LEFT, Drawer.RIGHT):
                x = anim.tween(self.sx, self.ex, t, self.function)
                w = anim.tween(self.sw, self.ew, t, self.function)
                if self.drawer.side == Drawer.LEFT:
                    vcx = self.sw - w
                elif self.drawer.side == Drawer.RIGHT:
                    vcx = 0
                self.drawer.setViewClip((vcx, 0, w, self.drawer.height))
                self.drawer.x = x
            else:
                y = anim.tween(self.sy, self.ey, t, self.function)
                h = anim.tween(self.sh, self.eh, t, self.function)
                if self.drawer.side == Drawer.TOP:
                    vcy = self.sh - h
                elif self.drawer.side == Drawer.BOTTOM:
                    vcy = 0
                self.drawer.setViewClip((0, vcy, self.drawer.width, h))
                self.drawer.y = y

class ExposeAnimation(anim.Animation):
    def __init__(self, drawer, duration=.25, function=anim.cosine90):
        self.drawer = drawer
        self.duration = duration
        self.function = function
        if drawer.side == Drawer.LEFT:
            self.sx = int(drawer.x)
            self.ex = int(drawer.x + drawer.width)
            self.sw = 0
            self.ew = int(drawer.width)
        elif drawer.side == Drawer.RIGHT:
            self.sx = int(drawer.x)
            self.ex = int(drawer.x - drawer.width)
            self.sw = 0
            self.ew = int(drawer.width)
        elif drawer.side == Drawer.TOP:
            self.sy = int(drawer.y)
            self.ey = int(drawer.y + drawer.height)
            self.sh = 0
            self.eh = int(drawer.height)
        elif drawer.side == Drawer.BOTTOM:
            self.sy = int(drawer.y)
            self.ey = int(drawer.y - drawer.height)
            self.sh = 0
            self.eh = int(drawer.height)
        super(ExposeAnimation, self).__init__()

    def cancel(self):
        if self.drawer.side in (Drawer.LEFT, Drawer.RIGHT):
            self.drawer.setViewClip((0, 0, self.ew, self.drawer.height))
            self.drawer.x = self.ex
        else:
            self.drawer.setViewClip((0, 0, self.drawer.width, self.eh))
            self.drawer.y = self.ey
        super(ExposeAnimation, self).cancel()

    def animate(self, dt):
        self.anim_time += dt
        if self.anim_time >= self.duration:
            self.cancel()
        else:
            t = self.anim_time / self.duration
            if self.drawer.side in (Drawer.LEFT, Drawer.RIGHT):
                x = anim.tween(self.sx, self.ex, t, self.function)
                w = anim.tween(self.sw, self.ew, t, self.function)
                if self.drawer.side == Drawer.LEFT:
                    vcx = self.ew - w
                elif self.drawer.side == Drawer.RIGHT:
                    vcx = 0
                self.drawer.setViewClip((vcx, 0, w, self.drawer.height))
                self.drawer.x = x
            else:
                y = anim.tween(self.sy, self.ey, t, self.function)
                h = anim.tween(self.sh, self.eh, t, self.function)
                if self.drawer.side == Drawer.TOP:
                    vcy = self.eh - h
                elif self.drawer.side == Drawer.BOTTOM:
                    vcy = 0
                self.drawer.setViewClip((0, vcy, self.drawer.width, h))
                self.drawer.y = y

