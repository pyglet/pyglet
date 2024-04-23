"""Game Controller support.

This module provides an interface for Game Controller devices, which are a
subset of Joysticks. Game Controllers have consistent button and axis mapping,
which resembles common dual-stick home video game console controllers.
Devices that are of this design can be automatically mapped to the "virtual"
Game Controller layout, providing a consistent abstraction for a large number
of different devices, with no tedious button and axis mapping for each one.
To achieve this, an internal mapping database contains lists of device ids
and their corresponding button and axis mappings. The mapping database is in
the same format as originated by the `SDL` library, which has become a
semi-standard and is in common use. Most popular controllers are included in
the built-in database, and additional mappings can be added at runtime.

Some Joysticks, such as Flight Sticks, etc., do not necessarily fit into the
layout (and limitations) of GameControllers. For those such devices, it is
recommended to use the Joystick interface instead.

To query which GameControllers are available, call :py:func:`get_controllers`.

.. versionadded:: 2.0
"""
from __future__ import annotations

import os as _os
import sys as _sys
import warnings as _warnings

from .base import Sign
from .controller_db import mapping_list

_env_config = _os.environ.get('SDL_GAMECONTROLLERCONFIG')
if _env_config:
    # insert at the front of the list
    mapping_list.insert(0, _env_config)


def _swap_le16(value: int) -> int:
    """Ensure 16bit value is in Big Endian format"""
    if _sys.byteorder == "little":
        return ((value << 8) | (value >> 8)) & 0xFFFF
    return value


def create_guid(bus: int, vendor: int, product: int, version: int, name: str, signature: int, data: int) -> str:
    # byte size      16           16            16            16         str             8          8
    """Create an SDL2 style GUID string from a device's identifiers."""
    bus = _swap_le16(bus)
    vendor = _swap_le16(vendor)
    product = _swap_le16(product)
    version = _swap_le16(version)

    return f"{bus:04x}0000{vendor:04x}0000{product:04x}0000{version:04x}0000"


class Relation:
    __slots__ = 'control_type', 'index', 'sign'

    def __init__(self, control_type: str, index: int, sign: Sign = Sign.DEFAULT):
        self.control_type = control_type
        self.index = index
        self.sign = sign

    def __repr__(self):
        return f"Relation(type={self.control_type}, index={self.index}, sign={self.sign})"


def _parse_mapping(mapping_string: str) -> dict[str, str | Relation] | None:
    """Parse a SDL2 style GameController mapping string.

    Args:
        mapping_string: A string containing an SDL style controller mapping.
    """

    valid_keys = ['guide', 'back', 'start', 'a', 'b', 'x', 'y',
                  'leftshoulder', 'leftstick', 'rightshoulder', 'rightstick',
                  'dpup', 'dpdown', 'dpleft', 'dpright',
                  'lefttrigger', 'righttrigger', 'leftx', 'lefty', 'rightx', 'righty']

    try:
        guid, name, *split_mapping = mapping_string.strip().split(",")
        relations = dict(guid=guid, name=name)
    except ValueError:
        return None

    for item in split_mapping:
        # looking for items like: a:b0, b:b1, etc.
        if ':' not in item:
            continue

        key, relation_string, *etc = item.split(':')

        if key not in valid_keys:
            continue

        # Look for specific flags to signify axis sign:
        if "+" in relation_string:
            relation_string = relation_string.strip('+')
            sign = Sign.POSITIVE
        elif "-" in relation_string:
            relation_string = relation_string.strip('-')
            sign = Sign.NEGATIVE
        elif "~" in relation_string:
            relation_string = relation_string.strip('~')
            sign = Sign.INVERTED
        else:
            sign = Sign.DEFAULT

        # All relations will be one of (Button, Axis, or Hat).
        if relation_string.startswith("b"):  # Button
            relations[key] = Relation("button", int(relation_string[1:]), sign)
        elif relation_string.startswith("a"):  # Axis
            relations[key] = Relation("axis", int(relation_string[1:]), sign)
        elif relation_string.startswith("h0"):  # Hat
            relations[key] = Relation("hat0", int(relation_string.split(".")[1]), sign)

    return relations


def get_mapping(guid: str) -> dict[str, str | Relation] | None:
    """Return a mapping for the passed device GUID.

    Args:
        guid: A device GUID; see :py:meth:`~pyglet.input.Device.get_guid`
    """
    for mapping in mapping_list:
        if not mapping.startswith(guid):
            continue

        try:
            return _parse_mapping(mapping)
        except ValueError:
            _warnings.warn(f"Unable to parse Controller mapping: {mapping}")
            continue


def add_mappings_from_file(filename: str) -> None:
    """Add one or more mappings from a file.

    Given a file path, open and parse the file for mappings.

    Args:
        filename: A file path.
    """
    with open(filename) as f:
        add_mappings_from_string(f.read())


def add_mappings_from_string(string: str) -> None:
    """Add one or more mappings from a string.

        Args:
            string: A string containing one or more mappings,
        """
    for line in string.splitlines():
        line = line.strip()
        if line.startswith('#'):
            continue
        mapping_list.insert(0, line)
