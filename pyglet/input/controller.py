# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# Copyright (c) 2008-2022 pyglet contributors
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
import os as _os
import warnings as _warnings

from .controller_db import mapping_list


_env_config = _os.environ.get('SDL_GAMECONTROLLERCONFIG')
if _env_config:
    # insert at the front of the list
    mapping_list.insert(0, _env_config)


class Relation:
    __slots__ = 'control_type', 'index', 'inverted'

    def __init__(self, control_type, index, inverted=False):
        self.control_type = control_type
        self.index = index
        self.inverted = inverted

    def __repr__(self):
        return f"Relation(type={self.control_type}, index={self.index}, inverted={self.inverted})"


def _parse_mapping(mapping_string):
    """Parse a SDL2 style GameController mapping string.

    :Parameters:
        `mapping_string` : str
            A raw string containing an SDL style controller mapping.

    :rtype: A dict containing axis/button mapping relations.
    """

    valid_keys = ['guide', 'back', 'start', 'a', 'b', 'x', 'y',
                  'leftshoulder', 'leftstick', 'rightshoulder', 'rightstick',
                  'dpup', 'dpdown', 'dpleft', 'dpright',
                  'lefttrigger', 'righttrigger', 'leftx', 'lefty', 'rightx', 'righty']

    split_mapping = mapping_string.strip().split(",")
    relations = dict(guid=split_mapping[0], name=split_mapping[1])

    for item in split_mapping[2:]:
        # looking for items like: a:b0, b:b1, etc.
        if ':' not in item:
            continue

        key, relation_string, *etc = item.split(':')

        if key not in valid_keys:
            continue

        # Look for specific flags to signify inverted axis:
        if "+" in relation_string:
            relation_string = relation_string.strip('+')
            inverted = False
        elif "-" in relation_string:
            relation_string = relation_string.strip('-')
            inverted = True
        elif "~" in relation_string:
            relation_string = relation_string.strip('~')
            inverted = True
        else:
            inverted = False

        # All relations will be one of (Button, Axis, or Hat).
        if relation_string.startswith("b"):  # Button
            relations[key] = Relation("button", int(relation_string[1:]), inverted)
        elif relation_string.startswith("a"):  # Axis
            relations[key] = Relation("axis", int(relation_string[1:]), inverted)
        elif relation_string.startswith("h0"):  # Hat
            relations[key] = Relation("hat0", int(relation_string.split(".")[1]), inverted)

    return relations


def get_mapping(guid):
    """Return a mapping for the passed device GUID.

    :Parameters:
        `guid` : str
            A pyglet input device GUID

    :rtype: dict of axis/button mapping relations, or None
            if no mapping is available for this Controller.
    """
    for mapping in mapping_list:
        if mapping.startswith(guid):
            try:
                return _parse_mapping(mapping)
            except ValueError:
                _warnings.warn(f"Unable to parse Controller mapping: {mapping}")
                continue


def add_mappings_from_file(filename) -> None:
    """Add mappings from a file.

    Given a file path, open and parse the file for mappings.

    :Parameters:
        `filename` : str
            A file path.
    """
    with open(filename) as f:
        add_mappings_from_string(f.read())


def add_mappings_from_string(string) -> None:
    """Add one or more mappings from a raw string.

        :Parameters:
            `string` : str
                A string containing one or more mappings,
        """
    for line in string.splitlines():
        if line.startswith('#'):
            continue
        line = line.strip()
        mapping_list.append(line)
