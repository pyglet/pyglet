import math

from pyglet import clock

linear = lambda t: t
cosine90 = lambda t: 1-math.cos(t * math.pi/2)
cosine180 = lambda t: 1-abs(math.cos(t * math.pi))
exponential = lambda t: (math.exp(t)-1) / (math.exp(1)-1)
half_parabola = lambda t: (1000*t)**2 / 1000**2
inverted_half_parabola = lambda t: 1-((1000*t)**2 / 1000**2)
parabola = lambda t: (2000*(t-.5))**2 / 1000**2
inverted_parabola = lambda t: 1-((2000*(t-.5))**2 / 1000**2)

def tween(v1, v2, t, function=cosine90):
    '''Tween the values v1 and v2 by the factor 0 < t < 1 using the supplied
    function.
    '''
    return type(v1)(v1 + (v2-v1)*function(t))


def tween_triple(p1, p2, t, function=cosine90):
    '''Tween the triples p1 and p2 by the factor 0 < t < 1 using the supplied
    function.
    '''
    r = function(t)
    x1, y1, z1 = p1
    x2, y2, z2 = p2
    x = type(x1)(x1 + (x2-x1)*r)
    y = type(x1)(y1 + (y2-y1)*r)
    z = type(x1)(z1 + (z2-z1)*r)
    return x, y, z


class Animation(object):
    def __init__(self):
        self.anim_time = 0
        self.is_running = True
        clock.schedule(self.animate)

    def cancel(self):
        if self.is_running:
            self.is_running = False
            clock.unschedule(self.animate)


class Delayed(Animation):
    def __init__(self, *args, **kw):
        self.callable = args[0]
        self.args = args[1:]
        self.duration = kw.pop('delay', 1.)
        self.kw = kw
        super(Delayed, self).__init__()

    def animate(self, dt):
        self.anim_time += dt
        if self.anim_time > self.duration:
            self.cancel()
            self.callable(*self.args, **self.kw)


class Called(Animation):
    def __init__(self, *args, **kw):
        self.callable = args[0]
        self.args = args[1:]
        self.duration = kw.pop('duration', 1.)
        self.kw = kw
        super(Called, self).__init__()

    def animate(self, dt):
        self.anim_time += dt
        self.callable(*self.args, **self.kw)
        if self.anim_time > self.duration:
            self.cancel()


class Translate(Animation):
    '''Translate some object that has a .position (x, y, z) property to the
    specified x, y, z position.

    Duration is the number of seconds to animate over.

    Function is the translation function, by default using a cosine curve
    between 0 and 90 degrees.

    Callback is called once the translation is complete.
    '''
    def __init__(self, object, x, y, z, duration=1, function=cosine90,
            callback=None):
        self.object = object
        self.source = object.position
        self.destination = (x, y, z)
        self.duration = duration
        self.function = function
        self.callback = callback
        super(Translate, self).__init__()

    def animate(self, dt):
        self.anim_time += dt
        if self.anim_time > self.duration:
            self.cancel()
            self_anim_time = self.duration
            if self.function in (cosine180, inverted_parabola):
                self.object.position = self.source
            else:
                self.object.position = self.destination
            if self.callback: self.callback()
        else:
            self.object.position = tween_triple(self.source,
                self.destination, self.anim_time / self.duration,
                self.function)


class Rotate(Animation):
    '''Rotate some object that has a .angle (rx, ry, rz) property to the
    specified rx, ry, rz angles.

    Duration is the number of seconds to animate over.

    Function is the translation function, by default using a cosine curve
    between 0 and 90 degrees.
    '''
    def __init__(self, object, rx, ry, rz, duration=1, function=cosine90):
        self.object = object
        self.source = object.angle
        self.destination = (rx, ry, rz)
        self.duration = duration
        self.function = function
        super(Rotate, self).__init__()

    def animate(self, dt):
        self.anim_time += dt
        if self.anim_time >= self.duration:
            self.cancel()
            self_anim_time = self.duration
            if self.function in (cosine180, inverted_parabola):
                self.object.angle = self.source
            else:
                self.object.angle = self.destination
        else:
            self.object.angle = tween_triple(self.source,
                self.destination, self.anim_time / self.duration,
                self.function)


class TranslateProperty(Animation):
    '''Translate some property on an object.

    Duration is the number of seconds to animate over.

    Function is the translation function, by default using a cosine curve
    between 0 and 90 degrees.

    Callback is called once the translation is complete.
    '''
    def __init__(self, object, property, value, duration=1, function=cosine90,
            callback=None):
        self.object = object
        self.property = property
        self.source = getattr(object, property)
        self.destination = value
        self.duration = duration
        self.function = function
        self.callback = callback
        super(TranslateProperty, self).__init__()

    def animate(self, dt):
        self.anim_time += dt
        if self.anim_time >= self.duration:
            self.cancel()
            self_anim_time = self.duration
            if self.function in (cosine180, inverted_parabola):
                setattr(self.object, self.property, self.source)
            else:
                setattr(self.object, self.property, self.destination)
            if self.callback: self.callback()
        else:
            value = tween(self.source, self.destination,
                self.anim_time / self.duration, self.function)
            setattr(self.object, self.property, value)

