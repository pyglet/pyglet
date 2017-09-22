#!/usr/bin/env python
# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
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
"""
Usage

    media_player.py [options] <filename> [<filename> ...]

Plays the audio / video files listed as arguments, optionally
collecting debug info

Options
    --debug : saves sequence of internal state as a binary *.dbg
    --outfile : filename to store the debug info, defaults to filename.dbg

The raw data captured in the .dbg can be rendered as human readable
using the script report.py
"""

from __future__ import print_function

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import os
import sys
import weakref

from pyglet.gl import *
import pyglet
from pyglet.window import key

pyglet.options['debug_media'] = False
from pyglet.media import buffered_logger as bl
# pyglet.options['audio'] = ('openal', 'pulse', 'silent')


def draw_rect(x, y, width, height):
    glBegin(GL_LINE_LOOP)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()


class Control(pyglet.event.EventDispatcher):
    x = y = 0
    width = height = 10

    def __init__(self, parent):
        super(Control, self).__init__()
        self.parent = weakref.proxy(parent)

    def hit_test(self, x, y):
        return (self.x < x < self.x + self.width and
                self.y < y < self.y + self.height)

    def capture_events(self):
        self.parent.push_handlers(self)

    def release_events(self):
        self.parent.remove_handlers(self)


class Button(Control):
    charged = False

    def draw(self):
        if self.charged:
            glColor3f(1, 0, 0)
        draw_rect(self.x, self.y, self.width, self.height)
        glColor3f(1, 1, 1)
        self.draw_label()

    def on_mouse_press(self, x, y, button, modifiers):
        self.capture_events()
        self.charged = True

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.charged = self.hit_test(x, y)

    def on_mouse_release(self, x, y, button, modifiers):
        self.release_events()
        if self.hit_test(x, y):
            self.dispatch_event('on_press')
        self.charged = False

Button.register_event_type('on_press')


class TextButton(Button):
    def __init__(self, *args, **kwargs):
        super(TextButton, self).__init__(*args, **kwargs)
        self._text = pyglet.text.Label('', anchor_x='center', anchor_y='center')

    def draw_label(self):
        self._text.x = self.x + self.width / 2
        self._text.y = self.y + self.height / 2
        self._text.draw()

    def set_text(self, text):
        self._text.text = text

    text = property(lambda self: self._text.text,
                    set_text)


class Slider(Control):
    THUMB_WIDTH = 6
    THUMB_HEIGHT = 10
    GROOVE_HEIGHT = 2

    def draw(self):
        center_y = self.y + self.height / 2
        draw_rect(self.x, center_y - self.GROOVE_HEIGHT / 2,
                  self.width, self.GROOVE_HEIGHT)
        pos = self.x + self.value * self.width / (self.max - self.min)
        draw_rect(pos - self.THUMB_WIDTH / 2, center_y - self.THUMB_HEIGHT / 2,
                  self.THUMB_WIDTH, self.THUMB_HEIGHT)

    def coordinate_to_value(self, x):
        value = float(x - self.x) / self.width * (self.max - self.min) + self.min
        # value = max(self.min, min(value, self.max))
        # print('coordinate_to_value', value)
        return value

    def on_mouse_press(self, x, y, button, modifiers):
        value = self.coordinate_to_value(x)
        self.capture_events()
        self.dispatch_event('on_begin_scroll')
        self.dispatch_event('on_change', value)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        value = min(max(self.coordinate_to_value(x), self.min), self.max)
        self.dispatch_event('on_change', value)

    def on_mouse_release(self, x, y, button, modifiers):
        self.release_events()
        self.dispatch_event('on_end_scroll')

Slider.register_event_type('on_begin_scroll')
Slider.register_event_type('on_end_scroll')
Slider.register_event_type('on_change')


class PlayerWindow(pyglet.window.Window):
    GUI_WIDTH = 400
    GUI_HEIGHT = 40
    GUI_PADDING = 4
    GUI_BUTTON_HEIGHT = 16

    def __init__(self, player):
        super(PlayerWindow, self).__init__(caption='Media Player',
                                           visible=False,
                                           resizable=True)
        # We only keep a weakref to player as we are about to push ourself
        # as a handler which would then create a circular reference between
        # player and window.
        self.player = weakref.proxy(player)
        self._player_playing = False
        self.player.push_handlers(self)

        self.slider = Slider(self)
        self.slider.push_handlers(self)
        self.slider.x = self.GUI_PADDING
        self.slider.y = self.GUI_PADDING * 2 + self.GUI_BUTTON_HEIGHT

        self.play_pause_button = TextButton(self)
        self.play_pause_button.x = self.GUI_PADDING
        self.play_pause_button.y = self.GUI_PADDING
        self.play_pause_button.height = self.GUI_BUTTON_HEIGHT
        self.play_pause_button.width = 45
        self.play_pause_button.on_press = self.on_play_pause

        self.window_button = TextButton(self)
        self.window_button.x = self.play_pause_button.x + \
                               self.play_pause_button.width + self.GUI_PADDING
        self.window_button.y = self.GUI_PADDING
        self.window_button.height = self.GUI_BUTTON_HEIGHT
        self.window_button.width = 90
        self.window_button.text = 'Windowed'
        self.window_button.on_press = lambda: self.set_fullscreen(False)

        self.controls = [
            self.slider,
            self.play_pause_button,
            self.window_button,
        ]

        x = self.window_button.x + self.window_button.width + self.GUI_PADDING
        i = 0
        for screen in self.display.get_screens():
            screen_button = TextButton(self)
            screen_button.x = x
            screen_button.y = self.GUI_PADDING
            screen_button.height = self.GUI_BUTTON_HEIGHT
            screen_button.width = 80
            screen_button.text = 'Screen %d' % (i + 1)
            screen_button.on_press = \
                lambda screen=screen: self.set_fullscreen(True, screen)
            self.controls.append(screen_button)
            i += 1
            x += screen_button.width + self.GUI_PADDING

    def on_player_next_source(self):
        self.gui_update_state()
        self.gui_update_source()
        self.set_default_video_size()
        return True

    def on_player_eos(self):
        self.gui_update_state()
        pyglet.clock.schedule_once(self.auto_close, 0.1)
        return True

    def gui_update_source(self):
        if self.player.source:
            source = self.player.source
            self.slider.min = 0.
            self.slider.max = source.duration
        self.gui_update_state()

    def gui_update_state(self):
        if self.player.playing:
            self.play_pause_button.text = 'Pause'
        else:
            self.play_pause_button.text = 'Play'

    def get_video_size(self):
        if not self.player.source or not self.player.source.video_format:
            return 0, 0
        video_format = self.player.source.video_format
        width = video_format.width
        height = video_format.height
        if video_format.sample_aspect > 1:
            width *= video_format.sample_aspect
        elif video_format.sample_aspect < 1:
            height /= video_format.sample_aspect
        return width, height

    def set_default_video_size(self):
        '''Make the window size just big enough to show the current
        video and the GUI.'''
        width = self.GUI_WIDTH
        height = self.GUI_HEIGHT
        video_width, video_height = self.get_video_size()
        width = max(width, video_width)
        height += video_height
        self.set_size(int(width), int(height))

    def on_resize(self, width, height):
        '''Position and size video image.'''
        super(PlayerWindow, self).on_resize(width, height)
        self.slider.width = width - self.GUI_PADDING * 2

        height -= self.GUI_HEIGHT
        if height <= 0:
            return

        video_width, video_height = self.get_video_size()
        if video_width == 0 or video_height == 0:
            return
        display_aspect = width / float(height)
        video_aspect = video_width / float(video_height)
        if video_aspect > display_aspect:
            self.video_width = width
            self.video_height = width / video_aspect
        else:
            self.video_height = height
            self.video_width = height * video_aspect
        self.video_x = (width - self.video_width) / 2
        self.video_y = (height - self.video_height) / 2 + \
                        self.GUI_HEIGHT

    def on_mouse_press(self, x, y, button, modifiers):
        for control in self.controls:
            if control.hit_test(x, y):
                control.on_mouse_press(x, y, button, modifiers)

    def on_key_press(self, symbol, modifiers):
        if symbol == key.SPACE:
            self.on_play_pause()
        elif symbol == key.ESCAPE:
            self.dispatch_event('on_close')
        elif symbol == key.LEFT:
            self.player.seek(0)
        elif symbol == key.RIGHT:
            self.player.next_source()

    def on_close(self):
        self.player.pause()
        self.close()

    def auto_close(self, dt):
        self.close()

    def on_play_pause(self):
        if self.player.playing:
            self.player.pause()
        else:
            if self.player.time >= self.player.source.duration:
                self.player.seek(0)
            self.player.play()
        self.gui_update_state()

    def on_draw(self):
        self.clear()

        # Video
        if self.player.source and self.player.source.video_format:
            video_texture = self.player.get_texture()
            video_texture.blit(self.video_x,
                               self.video_y,
                               width=self.video_width,
                               height=self.video_height)

        # GUI
        self.slider.value = self.player.time
        for control in self.controls:
            control.draw()

    def on_begin_scroll(self):
        self._player_playing = self.player.playing
        self.player.pause()

    def on_change(self, value):
        self.player.seek(value)

    def on_end_scroll(self):
        if self._player_playing:
            self.player.play()

def main(target, dbg_file, debug):
    set_logging_parameters(target, dbg_file, debug)

    player = pyglet.media.Player()
    window = PlayerWindow(player)
    
    for filename in sys.argv[1:]:
        source = pyglet.media.load(filename)
        player.queue(source)

    window.gui_update_source()
    window.set_visible(True)
    window.set_default_video_size()

    # this is an async call
    player.play()
    window.gui_update_state()

    pyglet.app.run()

def set_logging_parameters(target_file, dbg_file, debug):
    if not debug:
        bl.logger = None
        return
    if dbg_file is None:
        dbg_file = target_file + ".dbg"
    else:
        dbg_dir = os.path.dirname(dbg_file)
        if dbg_dir and not os.path.isdir(dbg_dir):
            os.mkdir(dbg_dir)
    bl.logger = bl.BufferedLogger(dbg_file)
    from pyglet.media.instrumentation import mp_events
    # allow to detect crashes by prewriting a crash file, if no crash
    # it will be overwrited by the captured data
    sample = os.path.basename(target_file)
    bl.logger.log("version", mp_events["version"])
    bl.logger.log("crash", sample)
    bl.logger.save_log_entries_as_pickle()    
    bl.logger.clear()
    # start the real capture data
    bl.logger.log("version", mp_events["version"])
    bl.logger.log("mp.im", sample)

def usage():
    print(__doc__)
    sys.exit(1)

def sysargs_to_mainargs():
    """builds main args from sys.argv"""
    if len(sys.argv) < 2:
        usage()
    debug = False
    dbg_file = None
    for i in range(2):
        if sys.argv[1].startswith("--"):
            a = sys.argv.pop(1)
            if a.startswith("--debug"):
                debug = True
            elif a.startswith("--outfile="):
                dbg_file = a[len("--outfile="):]
            else:
                print("Error unknown option:", a)
                usage()
    target_file = sys.argv[1]
    return target_file, dbg_file, debug

if __name__ == '__main__':
    target_file, dbg_file, debug = sysargs_to_mainargs() 
    main(target_file, dbg_file, debug)
