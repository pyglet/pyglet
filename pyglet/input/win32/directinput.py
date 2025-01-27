import ctypes
import warnings

from typing import List, Dict, Optional

from pyglet.libs.win32.constants import WM_DEVICECHANGE, DBT_DEVICEARRIVAL, DBT_DEVICEREMOVECOMPLETE, \
    DBT_DEVTYP_DEVICEINTERFACE, DEVICE_NOTIFY_WINDOW_HANDLE

from pyglet.event import EventDispatcher

import pyglet
from pyglet.input import base
from pyglet.libs import win32
from pyglet.libs.win32 import dinput, _user32, DEV_BROADCAST_DEVICEINTERFACE, com, DEV_BROADCAST_HDR
from pyglet.libs.win32 import _kernel32
from pyglet.input.controller import get_mapping
from pyglet.input.base import ControllerManager

# These instance names are not defined anywhere, obtained by experiment.  The
# GUID names (which seem to be ideally what are needed) are wrong/missing for
# most of my devices.

_abs_instance_names = {
    0: 'x',
    1: 'y',
    2: 'z',
    3: 'rx',
    4: 'ry',
    5: 'rz',
}

_rel_instance_names = {
    0: 'x',
    1: 'y',
    2: 'wheel',
}

_btn_instance_names = {}


def _create_control(object_instance):
    raw_name = object_instance.tszName
    ctrl_type = object_instance.dwType
    instance = dinput.DIDFT_GETINSTANCE(ctrl_type)

    if ctrl_type & dinput.DIDFT_ABSAXIS:
        name = _abs_instance_names.get(instance)
        control = base.AbsoluteAxis(name, 0, 0xffff, raw_name)
    elif ctrl_type & dinput.DIDFT_RELAXIS:
        name = _rel_instance_names.get(instance)
        control = base.RelativeAxis(name, raw_name)
    elif ctrl_type & dinput.DIDFT_BUTTON:
        name = _btn_instance_names.get(instance)
        control = base.Button(name, raw_name)
    elif ctrl_type & dinput.DIDFT_POV:
        control = base.AbsoluteAxis(base.AbsoluteAxis.HAT, 0, 0xffffffff, raw_name)
    else:
        return

    control._type = object_instance.dwType
    return control


class DirectInputDevice(base.Device):
    def __init__(self, display, device, device_instance):
        name = device_instance.tszInstanceName
        super(DirectInputDevice, self).__init__(display, name)

        self._type = device_instance.dwDevType & 0xff
        self._subtype = device_instance.dwDevType & 0xff00
        self._device = device
        self._init_controls()
        self._set_format()

        self.id_name = device_instance.tszProductName
        self.id_product_guid = format(device_instance.guidProduct.Data1, "08x")
        self.device_instance = device_instance

    def __del__(self):
        self._device.Release()

    def get_guid(self):
        """Generate an SDL2 style GUID from the product guid."""
        first = self.id_product_guid[6:8] + self.id_product_guid[4:6]
        second = self.id_product_guid[2:4] + self.id_product_guid[0:2]
        return f"03000000{first}0000{second}000000000000"

    def _init_controls(self):
        self.controls = []
        self._device.EnumObjects(dinput.LPDIENUMDEVICEOBJECTSCALLBACK(self._object_enum), None, dinput.DIDFT_ALL)
        self.controls.sort(key=lambda c: c._type)

    def _object_enum(self, object_instance, arg):
        control = _create_control(object_instance.contents)
        if control:
            self.controls.append(control)
        return dinput.DIENUM_CONTINUE

    def _set_format(self):
        if not self.controls:
            return

        object_formats = (dinput.DIOBJECTDATAFORMAT * len(self.controls))()
        offset = 0
        for object_format, control in zip(object_formats, self.controls):
            object_format.dwOfs = offset
            object_format.dwType = control._type
            offset += 4

        fmt = dinput.DIDATAFORMAT()
        fmt.dwSize = ctypes.sizeof(fmt)
        fmt.dwObjSize = ctypes.sizeof(dinput.DIOBJECTDATAFORMAT)
        fmt.dwFlags = 0
        fmt.dwDataSize = offset
        fmt.dwNumObjs = len(object_formats)
        fmt.rgodf = ctypes.cast(ctypes.pointer(object_formats), dinput.LPDIOBJECTDATAFORMAT)
        self._device.SetDataFormat(fmt)

        prop = dinput.DIPROPDWORD()
        prop.diph.dwSize = ctypes.sizeof(prop)
        prop.diph.dwHeaderSize = ctypes.sizeof(prop.diph)
        prop.diph.dwObj = 0
        prop.diph.dwHow = dinput.DIPH_DEVICE
        prop.dwData = 64 * ctypes.sizeof(dinput.DIDATAFORMAT)
        self._device.SetProperty(dinput.DIPROP_BUFFERSIZE, ctypes.byref(prop.diph))

    def open(self, window=None, exclusive=False):
        if not self.controls:
            return

        if window is None:
            # Pick any open window, or the shadow window if no windows
            # have been created yet.
            window = pyglet.gl._shadow_window
            for window in pyglet.app.windows:
                break

        flags = dinput.DISCL_BACKGROUND
        if exclusive:
            flags |= dinput.DISCL_EXCLUSIVE
        else:
            flags |= dinput.DISCL_NONEXCLUSIVE

        self._wait_object = _kernel32.CreateEventW(None, False, False, None)
        self._device.SetEventNotification(self._wait_object)
        pyglet.app.platform_event_loop.add_wait_object(self._wait_object, self._dispatch_events)

        self._device.SetCooperativeLevel(window._hwnd, flags)
        self._device.Acquire()

    def close(self):
        if not self.controls:
            return

        pyglet.app.platform_event_loop.remove_wait_object(self._wait_object)

        self._device.Unacquire()
        self._device.SetEventNotification(None)

        _kernel32.CloseHandle(self._wait_object)

    def get_controls(self):
        return self.controls

    def _dispatch_events(self):
        if not self.controls:
            return

        events = (dinput.DIDEVICEOBJECTDATA * 64)()
        n_events = win32.DWORD(len(events))
        try:
            self._device.GetDeviceData(ctypes.sizeof(dinput.DIDEVICEOBJECTDATA),
                                       ctypes.cast(ctypes.pointer(events),
                                                   dinput.LPDIDEVICEOBJECTDATA),
                                       ctypes.byref(n_events),
                                       0)
        except OSError:
            return

        for event in events[:n_events.value]:
            index = event.dwOfs // 4
            self.controls[index].value = event.dwData

    def matches(self, guid_id, device_instance):
        guid_id = format(device_instance.contents.guidProduct.Data1, "08x")

        if (self.id_product_guid == guid_id and
                self.id_name == device_instance.contents.tszProductName and
                self._type == device_instance.contents.dwDevType & 0xff and
                self._subtype == device_instance.contents.dwDevType & 0xff00):
            return True

        return False


def _init_directinput():
    _i_dinput = dinput.IDirectInput8()
    module_handle = _kernel32.GetModuleHandleW(None)
    dinput.DirectInput8Create(module_handle,
                              dinput.DIRECTINPUT_VERSION,
                              dinput.IID_IDirectInput8W,
                              ctypes.byref(_i_dinput),
                              None)

    return _i_dinput


_i_dinput = _init_directinput()

GUID_DEVINTERFACE_HID = com.GUID(0x4D1E55B2, 0xF16F, 0x11CF, 0x88, 0xCB, 0x00, 0x11, 0x11, 0x00, 0x00, 0x30)


class DIDeviceManager(EventDispatcher):
    def __init__(self):
        self.registered = False
        self.window = None
        self._devnotify = None
        self.devices: List[DirectInputDevice] = []

        if self.register_device_events(skip_warning=True):
            self.set_current_devices()

    def set_current_devices(self):
        """Sets all currently discovered devices in the devices list.
        Be careful when using this, as this creates new device objects. Should only be called on initialization of
        the manager and if for some reason the window connection event isn't registered.
        """
        new_devices, _ = self._get_devices()
        self.devices = new_devices

    def register_device_events(self, skip_warning=False, window=None):
        """Register the first OS Window to receive events of disconnect and connection of devices.
        Returns True if events were successfully registered.
        """
        if not self.registered:
            # If a specific window is not specified, find one.
            if not window:
                # Pick any open window, or the shadow window if no windows have been created yet.
                window = pyglet.gl._shadow_window
                if not window:
                    for window in pyglet.app.windows:
                        break

            self.window = window
            if self.window is not None:
                dbi = DEV_BROADCAST_DEVICEINTERFACE()
                dbi.dbcc_size = ctypes.sizeof(dbi)
                dbi.dbcc_devicetype = DBT_DEVTYP_DEVICEINTERFACE
                dbi.dbcc_classguid = GUID_DEVINTERFACE_HID

                # Register we look for HID device unplug/plug.
                self._devnotify = _user32.RegisterDeviceNotificationW(self.window._hwnd, ctypes.byref(dbi), DEVICE_NOTIFY_WINDOW_HANDLE)

                self.window._event_handlers[WM_DEVICECHANGE] = self._event_devicechange
                self.registered = True
                self.window.push_handlers(self)
                return True
            else:
                if not skip_warning:
                    warnings.warn("DirectInput Device Manager requires a window to receive device connection events.")

        return False

    def _unregister_device_events(self):
        del self.window._event_handlers[WM_DEVICECHANGE]
        _user32.UnregisterDeviceNotification(self._devnotify)
        self.registered = False
        self._devnotify = None

    def on_close(self):
        if self.registered:
            self._unregister_device_events()

        import pyglet.app
        if len(pyglet.app.windows) != 0:
            # At this point the closed windows aren't removed from the app.windows list. Check for non-current window.
            for existing_window in pyglet.app.windows:
                if existing_window != self.window:
                    self.register_device_events(skip_warning=True, window=existing_window)
                    return

        self.window = None

    def __del__(self):
        if self.registered:
            self._unregister_device_events()

    def _get_devices(self, display=None):
        """Enumerate all the devices on the system.
        Returns two values: new devices, missing devices"""
        _missing_devices = list(self.devices)
        _new_devices = []
        _xinput_devices = []

        if not pyglet.options["win32_disable_xinput"]:
            try:
                from pyglet.input.win32.xinput import get_xinput_guids
                _xinput_devices = get_xinput_guids()
            except ImportError:
                pass

        def _device_enum(device_instance, arg):  # DIDEVICEINSTANCE
            guid_id = format(device_instance.contents.guidProduct.Data1, "08x")
            # Only XInput should handle XInput compatible devices if enabled. Filter them out.
            if guid_id in _xinput_devices:
                return dinput.DIENUM_CONTINUE

            # Check if device already exists.
            for dev in list(_missing_devices):
                if dev.matches(guid_id, device_instance):
                    _missing_devices.remove(dev)
                    return dinput.DIENUM_CONTINUE

            device = dinput.IDirectInputDevice8()
            _i_dinput.CreateDevice(device_instance.contents.guidInstance, ctypes.byref(device), None)
            di_dev = DirectInputDevice(display, device, device_instance.contents)

            _new_devices.append(di_dev)
            return dinput.DIENUM_CONTINUE

        _i_dinput.EnumDevices(dinput.DI8DEVCLASS_ALL,
                              dinput.LPDIENUMDEVICESCALLBACK(_device_enum),
                              None,
                              dinput.DIEDFL_ATTACHEDONLY)
        return _new_devices, _missing_devices

    def _recheck_devices(self):
        new_devices, missing_devices = self._get_devices()
        if new_devices:
            self.devices.extend(new_devices)
            for device in new_devices:
                self.dispatch_event('on_connect', device)

        if missing_devices:
            for device in missing_devices:
                self.devices.remove(device)
                self.dispatch_event('on_disconnect', device)

    def _event_devicechange(self, msg, wParam, lParam):
        if lParam == 0:
            return

        if wParam == DBT_DEVICEARRIVAL or wParam == DBT_DEVICEREMOVECOMPLETE:
            hdr_ptr = ctypes.cast(lParam, ctypes.POINTER(DEV_BROADCAST_HDR))
            if hdr_ptr.contents.dbch_devicetype == DBT_DEVTYP_DEVICEINTERFACE:
                # Need to call this outside the generate OS event to prevent COM deadlock.
                pyglet.app.platform_event_loop.post_event(self, '_recheck_devices')


DIDeviceManager.register_event_type('on_connect')
DIDeviceManager.register_event_type('on_disconnect')
DIDeviceManager.register_event_type('_recheck_devices')  # Not to be used by subclasses!

_di_manager = DIDeviceManager()


class DIControllerManager(ControllerManager):

    def __init__(self, display=None):
        self._display = display
        self._controllers: Dict[DirectInputDevice, base.Controller] = {}

        for device in _di_manager.devices:
            self._add_controller(device)

        @_di_manager.event
        def on_connect(di_device):
            if di_device not in self._controllers:
                if self._add_controller(di_device):
                    pyglet.app.platform_event_loop.post_event(self, 'on_connect', self._controllers[di_device])

        @_di_manager.event
        def on_disconnect(di_device):
            if di_device in self._controllers:
                _controller = self._controllers[di_device]
                del self._controllers[di_device]
                pyglet.app.platform_event_loop.post_event(self, 'on_disconnect', _controller)

    def _add_controller(self, device: DirectInputDevice) -> Optional[base.Controller]:
        controller = _create_controller(device)
        if controller:
            self._controllers[device] = controller
            return controller

        return None

    def get_controllers(self):
        if not _di_manager.registered:
            _di_manager.register_device_events()
            _di_manager.set_current_devices()

        return list(self._controllers.values())


def get_devices(display=None):
    _init_directinput()
    _devices = []
    _xinput_devices = []

    if not pyglet.options["win32_disable_xinput"]:
        try:
            from pyglet.input.win32.xinput import get_xinput_guids
            _xinput_devices = get_xinput_guids()
        except ImportError:
            pass

    def _device_enum(device_instance, arg):
        guid_id = format(device_instance.contents.guidProduct.Data1, "08x")
        # Only XInput should handle DirectInput devices if enabled. Filter them out.
        if guid_id in _xinput_devices:
            # Log somewhere?
            return dinput.DIENUM_CONTINUE

        device = dinput.IDirectInputDevice8()
        _i_dinput.CreateDevice(device_instance.contents.guidInstance, ctypes.byref(device), None)
        _devices.append(DirectInputDevice(display, device, device_instance.contents))
        return dinput.DIENUM_CONTINUE

    _i_dinput.EnumDevices(dinput.DI8DEVCLASS_ALL,
                          dinput.LPDIENUMDEVICESCALLBACK(_device_enum),
                          None,
                          dinput.DIEDFL_ATTACHEDONLY)
    return _devices


def _create_controller(device):
    mapping = get_mapping(device.get_guid())
    if device._type in (dinput.DI8DEVTYPE_JOYSTICK, dinput.DI8DEVTYPE_1STPERSON, dinput.DI8DEVTYPE_GAMEPAD):
        if mapping is not None:
            return base.Controller(device, mapping)
        else:
            warnings.warn(f"Warning: {device} (GUID: {device.get_guid()}) "
                          f"has no controller mappings. Update the mappings in the Controller DB.")


def _create_joystick(device):
    if device._type in (dinput.DI8DEVTYPE_JOYSTICK,
                        dinput.DI8DEVTYPE_1STPERSON,
                        dinput.DI8DEVTYPE_GAMEPAD,
                        dinput.DI8DEVTYPE_SUPPLEMENTAL):
        return base.Joystick(device)


def get_joysticks(display=None):
    if not _di_manager.registered:
        _di_manager.register_device_events()
        _di_manager.set_current_devices()

    return [joystick for joystick in
            [_create_joystick(device) for device in _di_manager.devices]
            if joystick is not None]


def get_controllers(display=None):
    if not _di_manager.registered:
        _di_manager.register_device_events()
        _di_manager.set_current_devices()

    return [controller for controller in
            [_create_controller(device) for device in _di_manager.devices]
            if controller is not None]
