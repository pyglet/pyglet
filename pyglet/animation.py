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

"""This module lets you create animation easily.

.. versionadded:: 1.5.22
"""

import math

from pyglet.clock import schedule_once

def out_of_animation_range(num, from_, to):
    if from_ >= to:
        if num <= to:
            return True
    else:
        if num >= to:
            return True
    return False


class AnimationClip:
    """A single animation clip."""

    def __init__(self, obj, attr, to, duration): 
        self._obj = obj
        self._attr = attr
        self._now = self._from_values = getattr(self._obj, self._attr)
        self._to_values = to

        # Special animation type
        # 0 - normal(int, float)
        # 1 - color(tuple)
        # 2 - text(str)
        self._special_animation = None

        self._check_attr()
        self._duration = duration
        self._finished = False

    def _check_attr(self):
        if isinstance(self._from_values, (int, float)):
            self._special_animation = 0
        elif isinstance(self._from_values, tuple):
            if len(self._from_values) == len(self._to_values):
                self._special_animation = 1
            else:
                raise ValueError("length of from_(%d) and to(%d) isn't equal" % (len(self._from_values), len(self._to_values)))
        elif isinstance(self._from_values, str):
            if self._to_values.startswith(self._from_values) or self._from_values.startswith(self._to_values):
                self._special_animation = 2
            else:
                raise ValueError()

    def set_attr(self, t):
        if self._finished:
            return True
        if self._special_animation == 0:
            self._now += ((self._to_values - self._from_values) / self._duration) * t
            if out_of_animation_range(self._now, self._from_values, self._to_values):
                self._now = self._to_values
                self._finished = True
                setattr(self._obj, self._attr, self._now)
                return True
            setattr(self._obj, self._attr, self._now)
        else:
            raise NotImplementedError()
        return False


class Animation:
    
    def __init__(self):
        self._clips = []
        self._started = False
        self._point = 0
        self._count = 0

    def add(self, *clips, callback=None):
        """Add some animation clips."""
        if self._started:
            raise RuntimeError("can't add animation clips after animation start")
        self._clips.append({"clips": clips, "func": callback})
        return self

    def start(self, count=60):
        """Start animation.
            
        :Parameters:
            `count` : int
                Update objects ``count`` times in 1s.
        """
        self._started = True
        self._count = count
        schedule_once(self._start, 1 / self._count)

    def _start(self, t):
        if self._point >= len(self._clips):
            self._started = False
            return
        if all([result for result in [clip.set_attr(t) for clip in self._clips[self._point]["clips"]]]):
            if self._clips[self._point]["func"] is not None:
                self._clips[self._point]["func"]()
                self._point += 1
        schedule_once(self._start, 1 / self._count)
