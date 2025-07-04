from .gamepad_js import get_controllers
from .gamepad_js import JavascriptGamepadManager as ControllerManager


def get_tablets(display=None):
    import warnings
    warnings.warn("Tablets not yet supported on JavaScript.")
    return []

def get_joysticks(display=None):
    import warnings
    warnings.warn("Joysticks not yet supported on JavaScript.")
    return []

def get_devices(display=None):
    import warnings
    warnings.warn("Devices not yet supported on JavaScript.")
    return []
