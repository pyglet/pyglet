from abc import ABCMeta, abstractmethod
from enum import Enum, auto
from typing import Dict, Optional

from pyglet import event


class DeviceState(Enum):
    ACTIVE = auto()
    DISABLED = auto()
    MISSING = auto()
    UNPLUGGED = auto()


class DeviceFlow(Enum):
    OUTPUT = auto()
    INPUT = auto()
    INPUT_OUTPUT = auto()


class AudioDevice:
    """Base class for a platform independent audio device.
       _platform_state and _platform_flow is used to make device state numbers."""
    platform_state: Dict[int, DeviceState] = {}  # Must be defined by the parent.
    platform_flow: Dict[int, DeviceFlow] = {}  # Must be defined by the parent.

    def __init__(self, dev_id: str, name: str, description: str, flow: int, state: int):
        self.id = dev_id
        self.flow = flow  # platform value
        self.state = state  # platform value
        self.name = name
        self.description = description

    def __repr__(self):
        return "{}(name='{}', state={}, flow={})".format(
            self.__class__.__name__, self.name, self.platform_state[self.state].name, self.platform_flow[self.flow].name)


class AbstractAudioDeviceManager(event.EventDispatcher, metaclass=ABCMeta):

    def __del__(self):
        """Required to remove handlers before exit, as it can cause problems with the event system's weakrefs."""
        self.remove_handlers(self)

    @abstractmethod
    def get_default_output(self):
        """Returns a default active output device or None if none available."""
        pass

    @abstractmethod
    def get_default_input(self):
        """Returns a default active input device or None if none available."""
        pass

    @abstractmethod
    def get_output_devices(self):
        """Returns a list of all active output devices."""
        pass

    @abstractmethod
    def get_input_devices(self):
        """Returns a list of all active input devices."""
        pass

    @abstractmethod
    def get_all_devices(self):
        """Returns a list of all audio devices, no matter what state they are in."""
        pass

    def on_device_state_changed(self, device: AudioDevice, old_state: DeviceState, new_state: DeviceState):
        """Event, occurs when the state of a device changes, provides the old state and new state."""
        pass

    def on_device_added(self, device: AudioDevice):
        """Event, occurs when a new device is added to the system."""
        pass

    def on_device_removed(self, device: AudioDevice):
        """Event, occurs when an existing device is removed from the system."""
        pass

    def on_default_changed(self, device: Optional[AudioDevice], flow: DeviceFlow):
        """Event, occurs when the default audio device changes.
           If there is no device that can be the default on the system, can be None.
           The flow determines whether an input or output device became it's respective default.
        """
        pass


AbstractAudioDeviceManager.register_event_type('on_device_state_changed')
AbstractAudioDeviceManager.register_event_type('on_device_added')
AbstractAudioDeviceManager.register_event_type('on_device_removed')
AbstractAudioDeviceManager.register_event_type('on_default_changed')
