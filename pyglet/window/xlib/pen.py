"""X11 pen discovery and axis states."""
from __future__ import annotations

from ctypes import POINTER, byref, c_int, cast
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from pyglet.libs.linux.x11 import xinput2, xlib

if TYPE_CHECKING:
    from ctypes import _Pointer


@dataclass
class XIPen:
    """Tablet axes by semantic label; sparse valuators retain their previous value."""

    axes: dict[str, tuple[int, float, float]]
    eraser: bool = False
    values: dict[int, float] = field(default_factory=dict)

    def update(self, valuators: xinput2.XIValuatorState) -> None:
        packed = 0
        for number in range(valuators.mask_len * 8):
            if valuators.mask[number >> 3] & (1 << (number & 7)):
                self.values[number] = valuators.values[packed]
                packed += 1

    def axis(self, name: str, low: float, high: float) -> float:
        axis = self.axes.get(name)
        if axis is None:
            return 0.0
        number, minimum, maximum = axis
        if number not in self.values or maximum <= minimum:
            return 0.0
        fraction = max(0.0, min(1.0, (self.values[number] - minimum) / (maximum - minimum)))
        return low + fraction * (high - low)


def query_pen(display: _Pointer[xlib.Display], deviceid: int) -> XIPen | None:
    """Identify pen tools using driver provided valuator labels and tool names."""
    count = c_int()
    devices = xinput2.XIQueryDevice(display, deviceid, byref(count))
    if not devices:
        return None
    try:
        for index in range(count.value):
            device = devices[index]
            # Only physical pointers, not the duplicate.
            if device.use not in (xinput2.XI_SLAVE_POINTER, xinput2.XI_FLOATING_SLAVE):
                continue
            axes: dict[str, tuple[int, float, float]] = {}
            for class_index in range(device.num_classes):
                info = device.classes[class_index]
                if info.contents.type != xinput2.XI_VALUATOR_CLASS:
                    continue
                axis = cast(info, POINTER(xinput2.XIValuatorClassInfo)).contents
                for label in ('Abs Pressure', 'Abs Tilt X', 'Abs Tilt Y'):
                    if axis.label and axis.label == xlib.XInternAtom(display, label.encode(), True):
                        axes[label] = (axis.number, axis.min, axis.max)
            name = (device.name or b'').decode(errors='replace').lower()
            if not any(word in name for word in ('finger', 'touch')) and 'Abs Pressure' in axes and (
                any(tool in name for tool in ('stylus', 'pen', 'eraser', 'tablet'))
                or 'Abs Tilt X' in axes or 'Abs Tilt Y' in axes
            ):
                return XIPen(axes, eraser='eraser' in name)
    finally:
        xinput2.XIFreeDeviceInfo(devices)
    return None


