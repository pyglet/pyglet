# Utilies to patch Pyglet to provide more precise event timing on Windows.
# HighTimerResolution is generally the most important of the bunch,
# since most 60+fps games in Windows will not work right without
# changing the timer resolution for the app

import pyglet
import ctypes

try:
    winmm = ctypes.windll.winmm
    k32 = ctypes.windll.kernel32
except AttributeError:
    raise NotImplementedError("This is not a Win32 compatible platform.")


class HighTimerResolution:
    """
    A context manager to adjust the main Win32 platform event loop.    
    
    Events inside the context manager will use the specified resolution of the
    multimedia timer to provide proper timings for 60fps+ framerates.    
    On exiting the context manager, the default resolution timer is restored.

    Most 60fps games can use a resolution of 4, but you may need to go as low
    as 1 to get the most consistent results.

    Example:

    with HighTimerResolution():
        pyglet.app.run()

    """

    def __init__(self, resolution=1):
        self.resolution = resolution

    def __enter__(self):
        winmm.timeBeginPeriod(self.resolution)

    def __exit__(self, *a):
        winmm.timeEndPeriod()


def pin_thread(pin_thread_mask=0x01):
    """
    Pin the main Pyglet app thread to one or more cores by way of a thread affinity mask.
    The default thread mask is 1.
    """
    k32.SetThreadAffinityMask(
        pyglet.app.platform_event_loop._event_thread, pin_thread_mask
    )


def pin_process():
    """
    Pins the entire Python interpreter process to the first CPU core.
    This may slightly improve performance due to affinity.
    """
    k32.SetProcessAffinityMask(k32.GetCurrentProcess(), 1)


def raise_priority(
    priority_class=0x080,
):
    """
    Raises the process priority to High. Other priorities can be provided.
    """
    k32.SetPriorityClass(-1, priority_class)
