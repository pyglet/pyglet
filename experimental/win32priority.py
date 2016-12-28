"""
win32priority.py
A set of utilies to patch Pyglet to provide more precise event timing on Windows.

The following options are provided:

    pin_thread: Pin the main Pyglet app thread to one or more cores by way of a thread affinity mask.
        Default is True.

    pin_thread_mask: The affinity mask for pin_thread. Default is 1.

    set_switch_interval: For Python 3.x only. Sets the sys.setswitchinterval interpreter option
        to a value that ensures all threads run to completion before being switched away.
        I have not objectively confirmed this helps performance, but I've provided it anyway.
        It might be useful on slower machines.

    switch_interval_value: The timeslice value provided to set_switch_interval.
        Default is 1/65, or just under the amount of time neede to render 60 fps.

    raise_priority: Raises the process priority to High.

    patch_timer: Adjusts the main Win32 platform event loop so that it uses the
        high-resolution multimedia timer to provide proper timings for 60fps+ framerates.

    pin_process: Pins the entire Python interpreter process to the first CPU core.
        You usually don't need to do this, but I'm providing it anyway.

    patch_event_loop: Replaces the default event loop with one that is more amenable
        to an application where you're firing the main event loop by way of the
        scheduler. If you use this, you'll need to manually call window.flip() in your
        draw routine.

"""


def priority_patch(
        pin_thread=True,
        pin_thread_mask=0x01,
        set_switch_interval=True,
        switch_interval_value=1. / 65.,
        raise_priority=True,
        priority_class=0x080,
        patch_timer=True,
        pin_process=False,
        patch_event_loop=False,
):
    import ctypes
    try:
        _winmm = ctypes.windll.winmm
    except AttributeError:
        raise NotImplementedError("This is not a Win32 compatible platform.")

    if set_switch_interval:
        import sys
        sys.setswitchinterval(switch_interval_value)

    time_start = _winmm.timeBeginPeriod
    time_stop = _winmm.timeEndPeriod
    _1 = ctypes.c_uint(1)

    k32 = ctypes.windll.kernel32

    if raise_priority:
        k32.SetPriorityClass(-1, priority_class)

    import pyglet

    if pin_thread:
        k32.SetThreadAffinityMask(pyglet.app.platform_event_loop._event_thread, pin_thread_mask)

    if pin_process:
        k32.SetProcessAffinityMask(k32.GetCurrentProcess(), 1)

    if patch_event_loop:
        class Loop(pyglet.app.EventLoop):
            def idle(self):
                self.clock.call_scheduled_functions(self.clock.update_time())
                return self.clock.get_sleep_time(True)

        loop = Loop()
        pyglet.app.event_loop = loop

    if patch_timer:
        old_step = pyglet.app.base.EventLoop._run_estimated

        def new_step(*a, **ka):
            time_start(_1)
            old_step(*a, **ka)
            time_stop(_1)

        pyglet.app.base.EventLoop._run_estimated = new_step