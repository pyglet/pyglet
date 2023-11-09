from typing import List, Optional, Tuple

from pyglet.libs.win32 import com
from pyglet.libs.win32 import _ole32 as ole32
from pyglet.libs.win32.constants import CLSCTX_INPROC_SERVER
from pyglet.libs.win32.types import *
from pyglet.media.devices import base
from pyglet.util import debug_print

_debug = debug_print('debug_input')

EDataFlow = UINT
# Audio rendering stream. Audio data flows from the application to the audio endpoint device, which renders the stream.
eRender = 0

# Audio capture stream. Audio data flows from the audio endpoint device that captures the stream, to the application.
eCapture = 1

# Audio rendering or capture stream. Audio data can flow either from the application to the audio endpoint device,
# or from the audio endpoint device to the application.
eAll = 2

EDataFlow_enum_count = 3

ERole = UINT
eConsole = 0  # Games, system notification sounds, and voice commands.
eMultimedia = 1  # Music, movies, narration, and live music recording.
eCommunications = 2  # Voice communications (talking to another person).
ERole_enum_count = 3

DEVICE_STATE_ACTIVE = 0x00000001
DEVICE_STATE_DISABLED = 0x00000002
DEVICE_STATE_NOTPRESENT = 0x00000004
DEVICE_STATE_UNPLUGGED = 0x00000008
DEVICE_STATEMASK_ALL = 0x0000000F

STGM_READ = 0
STGM_WRITE = 1
STGM_READWRITE = 2

VT_LPWSTR = 0x001F


class PROPERTYKEY(ctypes.Structure):
    _fields_ = [
        ('fmtid', com.GUID),
        ('pid', DWORD),
    ]

    def __repr__(self):
        return "PROPERTYKEY({}, pid={})".format(self.fmtid, self.pid)


REFPROPERTYKEY = POINTER(PROPERTYKEY)

PKEY_Device_FriendlyName = PROPERTYKEY(
    com.GUID(0xa45c254e, 0xdf1c, 0x4efd, 0x80, 0x20, 0x67, 0xd1, 0x46, 0xa8, 0x50, 0xe0), 14)
PKEY_Device_DeviceDesc = PROPERTYKEY(
    com.GUID(0xa45c254e, 0xdf1c, 0x4efd, 0x80, 0x20, 0x67, 0xd1, 0x46, 0xa8, 0x50, 0xe0), 2)
PKEY_DeviceInterface_FriendlyName = PROPERTYKEY(
    com.GUID(0x026e516e, 0xb814, 0x414b, 0x83, 0xcd, 0x85, 0x6d, 0x6f, 0xef, 0x48, 0x22), 2)


class IPropertyStore(com.pIUnknown):
    _methods_ = [
        ('GetCount',
         com.STDMETHOD(POINTER(DWORD))),
        ('GetAt',
         com.STDMETHOD(DWORD, POINTER(PROPERTYKEY))),
        ('GetValue',
         com.STDMETHOD(REFPROPERTYKEY, POINTER(PROPVARIANT))),
        ('SetValue',
         com.STDMETHOD()),
        ('Commit',
         com.STDMETHOD()),
    ]


CLSID_MMDeviceEnumerator = com.GUID(0xbcde0395, 0xe52f, 0x467c, 0x8e, 0x3d, 0xc4, 0x57, 0x92, 0x91, 0x69, 0x2e)
IID_IMMDeviceEnumerator = com.GUID(0xa95664d2, 0x9614, 0x4f35, 0xa7, 0x46, 0xde, 0x8d, 0xb6, 0x36, 0x17, 0xe6)


class IMMNotificationClient(com.IUnknown):
    _methods_ = [
        ('OnDeviceStateChanged',
         com.STDMETHOD(LPCWSTR, DWORD)),
        ('OnDeviceAdded',
         com.STDMETHOD(LPCWSTR)),
        ('OnDeviceRemoved',
         com.STDMETHOD(LPCWSTR)),
        ('OnDefaultDeviceChanged',
         com.STDMETHOD(EDataFlow, ERole, LPCWSTR)),
        ('OnPropertyValueChanged',
         com.STDMETHOD(LPCWSTR, PROPERTYKEY)),
    ]


IID_IMMEndpoint = com.GUID(0x1BE09788, 0x6894, 0x4089, 0x85, 0x86, 0x9A, 0x2A, 0x6C, 0x26, 0x5A, 0xC5)


class IMMEndpoint(com.pIUnknown):
    _methods_ = [
        ('GetDataFlow',
         com.STDMETHOD(POINTER(EDataFlow))),
    ]


class AudioNotificationCB(com.COMObject):
    _interfaces_ = [IMMNotificationClient]

    def __init__(self, audio_devices: 'Win32AudioDeviceManager'):
        super().__init__()
        self.audio_devices = audio_devices
        self._lost = False

    def OnDeviceStateChanged(self, pwstrDeviceId, dwNewState):
        device = self.audio_devices.get_cached_device(pwstrDeviceId)

        old_state = device.state

        pyglet_old_state = Win32AudioDevice.platform_state[old_state]
        pyglet_new_state = Win32AudioDevice.platform_state[dwNewState]
        assert _debug(
            f"Audio device '{device.name}' changed state. From: {pyglet_old_state} to: {pyglet_new_state}")

        device.state = dwNewState
        self.audio_devices.dispatch_event('on_device_state_changed', device, pyglet_old_state, pyglet_new_state)

    def OnDeviceAdded(self, pwstrDeviceId):
        dev = self.audio_devices.add_device(pwstrDeviceId)
        assert _debug(f"Audio device was added {pwstrDeviceId}: {dev}")
        self.audio_devices.dispatch_event('on_device_added', dev)

    def OnDeviceRemoved(self, pwstrDeviceId):
        dev = self.audio_devices.remove_device(pwstrDeviceId)
        assert _debug(f"Audio device was removed {pwstrDeviceId} : {dev}")
        self.audio_devices.dispatch_event('on_device_removed', dev)

    def OnDefaultDeviceChanged(self, flow, role, pwstrDeviceId):
        # Only support eConsole role right now
        if role == 0:
            if pwstrDeviceId is None:
                device = None
            else:
                device = self.audio_devices.get_cached_device(pwstrDeviceId)

            pyglet_flow = Win32AudioDevice.platform_flow[flow]
            assert _debug(f"Default device was changed to: {device} ({pyglet_flow})")

            self.audio_devices.dispatch_event('on_default_changed', device, pyglet_flow)

    def OnPropertyValueChanged(self, pwstrDeviceId, key):
        pass


class IMMDevice(com.pIUnknown):
    _methods_ = [
        ('Activate',
         com.STDMETHOD(com.REFIID, DWORD, POINTER(PROPVARIANT))),
        ('OpenPropertyStore',
         com.STDMETHOD(UINT, POINTER(IPropertyStore))),
        ('GetId',
         com.STDMETHOD(POINTER(LPWSTR))),
        ('GetState',
         com.STDMETHOD(POINTER(DWORD))),
    ]


class IMMDeviceCollection(com.pIUnknown):
    _methods_ = [
        ('GetCount',
         com.STDMETHOD(POINTER(UINT))),
        ('Item',
         com.STDMETHOD(UINT, POINTER(IMMDevice))),
    ]


class IMMDeviceEnumerator(com.pIUnknown):
    _methods_ = [
        ('EnumAudioEndpoints',
         com.STDMETHOD(EDataFlow, DWORD, c_void_p)),
        ('GetDefaultAudioEndpoint',
         com.STDMETHOD(EDataFlow, ERole, ctypes.POINTER(IMMDevice))),
        ('GetDevice',
         com.STDMETHOD(LPCWSTR, POINTER(IMMDevice))),
        ('RegisterEndpointNotificationCallback',
         com.STDMETHOD(POINTER(IMMNotificationClient))),
        ('UnregisterEndpointNotificationCallback',
         com.STDMETHOD()),
    ]


class Win32AudioDevice(base.AudioDevice):
    platform_state = {
        DEVICE_STATE_ACTIVE: base.DeviceState.ACTIVE,
        DEVICE_STATE_DISABLED: base.DeviceState.DISABLED,
        DEVICE_STATE_NOTPRESENT: base.DeviceState.MISSING,
        DEVICE_STATE_UNPLUGGED: base.DeviceState.UNPLUGGED
    }

    platform_flow = {
        eRender: base.DeviceFlow.OUTPUT,
        eCapture: base.DeviceFlow.INPUT,
        eAll: base.DeviceFlow.INPUT_OUTPUT
    }


class Win32AudioDeviceManager(base.AbstractAudioDeviceManager):
    def __init__(self):
        self._device_enum = IMMDeviceEnumerator()
        ole32.CoCreateInstance(CLSID_MMDeviceEnumerator, None, CLSCTX_INPROC_SERVER, IID_IMMDeviceEnumerator,
                               byref(self._device_enum))

        # Keep all devices cached, and the callback can keep them updated.
        self.devices: List[Win32AudioDevice] = self._query_all_devices()

        super().__init__()

        self._callback = AudioNotificationCB(self)
        self._device_enum.RegisterEndpointNotificationCallback(self._callback)

    def add_device(self, pwstrDeviceId: str) -> Win32AudioDevice:
        dev = self.get_device(pwstrDeviceId)
        self.devices.append(dev)
        return dev

    def remove_device(self, pwstrDeviceId: str) -> Win32AudioDevice:
        dev = self.audio_devices.get_cached_device(pwstrDeviceId)
        self.audio_devices.devices.remove(dev)
        return dev

    def get_device(self, pwstrDeviceId: str) -> Win32AudioDevice:
        device = IMMDevice()

        self._device_enum.GetDevice(pwstrDeviceId, byref(device))
        dev_id, name, desc, dev_state = self.get_device_info(device)

        ep = IMMEndpoint()
        device.QueryInterface(IID_IMMEndpoint, byref(ep))

        dataflow = EDataFlow()
        ep.GetDataFlow(byref(dataflow))
        flow = dataflow.value

        windevice = Win32AudioDevice(dev_id, name, desc, flow, dev_state)
        ep.Release()
        device.Release()
        return windevice

    def get_default_output(self) -> Optional[Win32AudioDevice]:
        """Attempts to retrieve a default audio output for the system. Returns None if no available devices found."""
        try:
            device = IMMDevice()
            self._device_enum.GetDefaultAudioEndpoint(eRender, eConsole, byref(device))
            dev_id, name, desc, dev_state = self.get_device_info(device)
            device.Release()

            cached_dev = self.get_cached_device(dev_id)
            cached_dev.state = dev_state
            return cached_dev
        except OSError as err:
            assert _debug(f"No default audio output was found. {err}")
            return None

    def get_default_input(self) -> Optional[Win32AudioDevice]:
        """Attempts to retrieve a default audio input for the system. Returns None if no available devices found."""
        try:
            device = IMMDevice()
            self._device_enum.GetDefaultAudioEndpoint(eCapture, eConsole, byref(device))
            dev_id, name, desc, dev_state = self.get_device_info(device)
            device.Release()

            cached_dev = self.get_cached_device(dev_id)
            cached_dev.state = dev_state
            return cached_dev
        except OSError as err:
            assert _debug(f"No default input output was found. {err}")
            return None

    def get_cached_device(self, dev_id) -> Win32AudioDevice:
        """Gets the cached devices, so we can reduce calls to COM and tell current state vs new states."""
        for device in self.devices:
            if device.id == dev_id:
                return device

        raise Exception("Attempted to get a device that does not exist.", dev_id)

    def get_output_devices(self, state=DEVICE_STATE_ACTIVE) -> List[Win32AudioDevice]:
        return [device for device in self.devices if device.state == state and device.flow == eRender]

    def get_input_devices(self, state=DEVICE_STATE_ACTIVE) -> List[Win32AudioDevice]:
        return [device for device in self.devices if device.state == state and device.flow == eCapture]

    def get_all_devices(self) -> List[Win32AudioDevice]:
        return self.devices

    def _query_all_devices(self) -> List[Win32AudioDevice]:
        return self.get_devices(flow=eRender, state=DEVICE_STATEMASK_ALL) + self.get_devices(flow=eCapture,
                                                                                             state=DEVICE_STATEMASK_ALL)

    def get_device_info(self, device: IMMDevice) -> Tuple[str, str, str, int]:
        """Return the ID, Name, and Description of the Audio Device."""
        store = IPropertyStore()
        device.OpenPropertyStore(STGM_READ, byref(store))

        dev_id = LPWSTR()
        device.GetId(byref(dev_id))

        name = self.get_pkey_value(store, PKEY_Device_FriendlyName)
        description = self.get_pkey_value(store, PKEY_Device_DeviceDesc)

        state = DWORD()
        device.GetState(byref(state))

        store.Release()

        return dev_id.value, name, description, state.value

    def get_devices(self, flow=eRender, state=DEVICE_STATE_ACTIVE):
        """Get's all of the specified devices (by default, all output and active)."""
        collection = IMMDeviceCollection()
        self._device_enum.EnumAudioEndpoints(flow, state, byref(collection))

        count = UINT()
        collection.GetCount(byref(count))

        devices = []
        for i in range(count.value):
            dev_itf = IMMDevice()
            collection.Item(i, byref(dev_itf))

            dev_id, name, desc, dev_state = self.get_device_info(dev_itf)
            device = Win32AudioDevice(dev_id, name, desc, flow, dev_state)
            dev_itf.Release()
            devices.append(device)

        collection.Release()

        return devices

    @staticmethod
    def get_pkey_value(store: IPropertyStore, pkey: PROPERTYKEY):
        try:
            propvar = PROPVARIANT()
            store.GetValue(pkey, byref(propvar))
            value = propvar.pwszVal
            ole32.PropVariantClear(byref(propvar))
        except Exception:
            value = "Unknown"

        return value
