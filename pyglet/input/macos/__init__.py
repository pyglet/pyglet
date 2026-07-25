from .darwin_hid import get_devices
from .darwin_hid import get_joysticks
from .darwin_hid import get_apple_remote
#from .darwin_hid import DarwinControllerManager as ControllerManager
from .darwin_gc import AppleControllerManager as ControllerManager

def get_controllers(display=None):
    from .darwin_gc import get_controllers as get_apple_controllers
    from .darwin_hid import get_controllers as get_darwin_controllers

    return [*get_apple_controllers(), *get_darwin_controllers()]

def get_tablets(display=None):
    import warnings
    warnings.warn("Tablets not yet supported on macOS.")
    return []
