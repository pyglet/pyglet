from .darwin_hid import get_devices
from .darwin_hid import get_joysticks
from .darwin_hid import get_apple_remote
from .darwin_hid import get_controllers
from .darwin_hid import DarwinControllerManager as ControllerManager


def get_tablets(display=None):
    import warnings
    warnings.warn("Tablets not yet supported on macOS.")
    return []
