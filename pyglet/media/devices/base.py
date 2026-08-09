"""Base types and interfaces for audio-device management."""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from enum import Enum, auto
from typing import ClassVar

from pyglet import event


class DeviceState(Enum):
    """States reported by a platform audio device."""

    ACTIVE = auto()
    DISABLED = auto()
    MISSING = auto()
    UNPLUGGED = auto()


class DeviceFlow(Enum):
    """Directions supported by a platform audio device."""

    OUTPUT = auto()
    INPUT = auto()
    INPUT_OUTPUT = auto()


class AudioDevice:
    """Base class for a platform independent audio device.

    ``platform_state`` and ``platform_flow`` map platform values to enums.
    """

    platform_state: ClassVar[dict[int, DeviceState]] = {}
    platform_flow: ClassVar[dict[int, DeviceFlow]] = {}

    def __init__(self, dev_id: str, name: str, description: str, flow: int, state: int) -> None:
        """Create an audio device from platform-specific identifiers."""
        self.id = dev_id
        self.flow = flow  # platform value
        self.state = state  # platform value
        self.name = name
        self.description = description

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(name='{self.name}', "
            f"state={self.platform_state[self.state].name}, "
            f"flow={self.platform_flow[self.flow].name})"
        )


class AbstractAudioDeviceManager(event.EventDispatcher, metaclass=ABCMeta):
    """Base interface for platform audio-device managers."""

    def __del__(self) -> None:
        """Required to remove handlers before exit, as it can cause problems with the event system's weakrefs."""
        self.remove_handlers(self)

    @abstractmethod
    def get_default_output(self) -> AudioDevice | None:
        """Returns a default active output device or None if none available."""

    @abstractmethod
    def get_default_input(self) -> AudioDevice | None:
        """Returns a default active input device or None if none available."""

    @abstractmethod
    def get_output_devices(self) -> list[AudioDevice]:
        """Returns a list of all active output devices."""

    @abstractmethod
    def get_input_devices(self) -> list[AudioDevice]:
        """Returns a list of all active input devices."""

    @abstractmethod
    def get_all_devices(self) -> list[AudioDevice]:
        """Returns a list of all audio devices, no matter what state they are in."""

    def on_device_state_changed(self, device: AudioDevice, old_state: DeviceState, new_state: DeviceState) -> None:
        """Event, occurs when the state of a device changes, provides the old state and new state."""

    def on_device_added(self, device: AudioDevice) -> None:
        """Event, occurs when a new device is added to the system."""

    def on_device_removed(self, device: AudioDevice) -> None:
        """Event, occurs when an existing device is removed from the system."""

    def on_default_changed(self, device: AudioDevice | None, flow: DeviceFlow) -> None:
        """Event, occurs when the default audio device changes.

        If there is no eligible device on the system, ``device`` is ``None``.
        ``flow`` identifies whether an input or output device became its default.
        """


AbstractAudioDeviceManager.register_event_type('on_device_state_changed')
AbstractAudioDeviceManager.register_event_type('on_device_added')
AbstractAudioDeviceManager.register_event_type('on_device_removed')
AbstractAudioDeviceManager.register_event_type('on_default_changed')
