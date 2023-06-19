from .evdev import get_devices as evdev_get_devices
from .evdev import get_joysticks
from .evdev import get_controllers
from .evdev import EvdevControllerManager as ControllerManager
from .x11_xinput_tablet import get_tablets
from .x11_xinput import get_devices as x11xinput_get_devices


def get_devices(display=None):
    return evdev_get_devices(display) + x11xinput_get_devices(display)
