import warnings

import pyglet

from .evdev import get_devices
from .evdev import get_joysticks
from .evdev import get_controllers
from .evdev import EvdevControllerManager as ControllerManager

if not (pyglet.options.headless or pyglet.options.wayland):
    from .x11_xinput_tablet import get_tablets

else:
    def get_tablets():
        warnings.warn('Tablets are currently only supported under Xlib.')
        return []
