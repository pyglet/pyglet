# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# Copyright (c) 2008-2023 pyglet contributors
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------
from abc import ABCMeta, abstractmethod

from pyglet import event
from pyglet.util import with_metaclass


class DeviceState:
    ACTIVE = "active"
    DISABLED = "disabled"
    MISSING = "missing"
    UNPLUGGED = "unplugged"


class DeviceFlow:
    OUTPUT = "output"
    INPUT = "input"
    INPUT_OUTPUT = "input/output"


class AudioDevice:
    """Base class for a platform independent audio device.
       _platform_state and _platform_flow is used to make device state numbers."""
    _platform_state = {}  # Must be defined by the parent.
    _platform_flow = {}  # Must be defined by the parent.

    def __init__(self, dev_id, name, description, flow, state):
        self.id = dev_id
        self.flow = flow
        self.state = state
        self.name = name
        self.description = description

    def __repr__(self):
        return "{}(name={}, state={}, flow={})".format(
            self.__class__.__name__, self.name, self._platform_state[self.state], self._platform_flow[self.flow])


class AbstractAudioDeviceManager(with_metaclass(ABCMeta, event.EventDispatcher, object)):

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

    def on_device_state_changed(self, device, old_state, new_state):
        """Event, occurs when the state of a device changes, provides old state and new state."""
        pass

    def on_device_added(self, device):
        """Event, occurs when a new device is added to the system."""
        pass

    def on_device_removed(self, device):
        """Event, occurs when an existing device is removed from the system."""
        pass

    def on_default_changed(self, device):
        """Event, occurs when the default audio device changes."""
        pass


AbstractAudioDeviceManager.register_event_type('on_device_state_changed')
AbstractAudioDeviceManager.register_event_type('on_device_added')
AbstractAudioDeviceManager.register_event_type('on_device_removed')
AbstractAudioDeviceManager.register_event_type('on_default_changed')
