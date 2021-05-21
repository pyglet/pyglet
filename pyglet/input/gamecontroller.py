# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# Copyright (c) 2008-2021 pyglet contributors
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

To query which GameControllers are available, call :py:func:`get_game_controllers`.

.. versionadded:: 2.0
"""
import os

from .gamecontrollerdb import mapping_list


env_config = os.environ.get('SDL_GAMECONTROLLERCONFIG')
if env_config:
    mapping_list.append(env_config)


class _Relation:
    __slots__ = 'control_type', 'index', 'inverted'

    def __init__(self, control_type, index, inverted=False):
        self.control_type = control_type
        self.index = index
        self.inverted = inverted

    def __repr__(self):
        return f"Relation(type={self.control_type}, index={self.index}, inverted={self.inverted})"


def _map_pair(raw_relation):
    inverted = False
    relation_string = raw_relation.split(":")[1]
    if relation_string.startswith("+"):
        relation_string = relation_string[1:]
        inverted = False
    elif relation_string.startswith("-"):
        relation_string = relation_string[1:]
        inverted = True
    if "~" in relation_string:
        # TODO: handle this
        return None
    if relation_string.startswith("b"):     # Button
        return _Relation("button", int(relation_string[1:]), inverted)
    elif relation_string.startswith("a"):   # Axis
        return _Relation("axis", int(relation_string[1:]), inverted)
    elif relation_string.startswith("h0"):  # Hat
        return _Relation("hat0", int(relation_string.split(".")[1]), inverted)


def _parse_mapping(mapping_string):
    """Parse a SDL2 style GameController mapping string.

    :Parameters:
        `mapping_string` : str
            A raw string containing an SDL style controller mapping.

    :rtype: A dict containing axis/button mapping relations.
    """
    relations = dict(guid=None, name=None, guide=None, a=None, b=None,
                     x=None, y=None, leftshoulder=None, leftstick=None,
                     rightshoulder=None, rightstick=None, back=None,
                     start=None, dpup=None, dpdown=None, dpleft=None,
                     dpright=None, lefttrigger=None, righttrigger=None,
                     leftx=None, lefty=None, rightx=None, righty=None)

    split_mapping = mapping_string.strip().split(",")

    relations["guid"] = split_mapping[0]
    relations["name"] = split_mapping[1]
    for item in split_mapping:
        if item.startswith("guide:"):
            relations["guide"] = _map_pair(item)
        elif item.startswith("a:"):
            relations["a"] = _map_pair(item)
        elif item.startswith("b:"):
            relations["b"] = _map_pair(item)
        elif item.startswith("x:"):
            relations["x"] = _map_pair(item)
        elif item.startswith("y:"):
            relations["y"] = _map_pair(item)
        elif item.startswith("leftshoulder:"):
            relations["leftshoulder"] = _map_pair(item)
        elif item.startswith("leftstick:"):
            relations["leftstick"] = _map_pair(item)
        elif item.startswith("rightshoulder:"):
            relations["rightshoulder"] = _map_pair(item)
        elif item.startswith("rightstick:"):
            relations["rightstick"] = _map_pair(item)
        elif item.startswith("back:"):
            relations["back"] = _map_pair(item)
        elif item.startswith("start:"):
            relations["start"] = _map_pair(item)
        elif item.startswith("lefttrigger:"):
            relations["lefttrigger"] = _map_pair(item)
        elif item.startswith("righttrigger:"):
            relations["righttrigger"] = _map_pair(item)
        elif item.startswith("dpup"):
            relations["dpup"] = _map_pair(item)
        elif item.startswith("dpdown"):
            relations["dpdown"] = _map_pair(item)
        elif item.startswith("dpleft"):
            relations["dpleft"] = _map_pair(item)
        elif item.startswith("dpright"):
            relations["dpright"] = _map_pair(item)
        elif item.startswith("leftx"):
            relations["leftx"] = _map_pair(item)
        elif item.startswith("lefty"):
            relations["lefty"] = _map_pair(item)
        elif item.startswith("rightx"):
            relations["rightx"] = _map_pair(item)
        elif item.startswith("righty"):
            relations["righty"] = _map_pair(item)

    return relations


def is_game_controller(device):
    """Check if the passed device is a GameController.

    :Parameters:
        `device` : `~pyglet.input.Device`
            A pyglet input device

    :rtype True if this device is a GameController.
    """
    guid = device.get_guid()
    return any(m.startswith(guid) for m in mapping_list)


def get_mapping(guid):
    """Return a mapping for the passed device GUID.

    :Parameters:
        `guid` : str
            A pyglet input device GUID

    :rtype: dict of the Game Controller axis/button mapping relations.
    """
    for mapping in mapping_list:
        if mapping.startswith(guid):
            return _parse_mapping(mapping)


def add_mappings_from_file(filename) -> None:
    """Add mappings from a file.

    Given a file path, open and parse the file for mappings.

    :Parameters:
        `filename` : str
            A file path.
    """
    assert os.path.exists(filename), f"Invalid path: {filename}"
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
