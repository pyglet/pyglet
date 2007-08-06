#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: //depot/task/DEV-99/client/tests.py#13 $'

import sys
sys.path.append('../../')
sys.path.append('../layout/')

from pyglet.window import *
from pyglet import clock
from pyglet.gl import *
from pyglet import media

import layout

from wydget import GUI
from wydget import event, dialogs, dragndrop, anim, layouts, widgets

if len(sys.argv) > 1:
    if '--help' in sys.argv:
        print '%s [test_file.xml] [--dump] [--once]'%sys.argv[0]
        print ' test_file.xml  -- a single XML file to display (see tests/)'
        print ' --dump         -- text dump of constructed GUI objects'
        print ' --once         -- render the GUI exactly once and exit'
        sys.exit(0)
    print '-'*75
    print 'To exit the test, hit <escape> or close the window'
    print '-'*75
else:
    print '-'*75
    print 'To move on to the next test, hit <escape>.'
    print 'Close the window to exit the tests.'
    print '-'*75

window = Window(width=800, height=600, vsync=False)

fps = clock.ClockDisplay(color=(1, .5, .5, 1))
window.push_handlers(fps)

class MyEscape(object):
    has_exit = False
    def on_key_press(self, symbol, modifiers):
        if symbol == key.ESCAPE:
            self.has_exit = True
        return event.EVENT_HANDLED
my_escape = MyEscape()
window.push_handlers(my_escape)

def run(xml_file):
    gui = GUI.fromXML(window, xml_file)
    window.push_handlers(gui)
    if '--dump' in sys.argv:
        print '-'*75
        gui.dump()
        print '-'*75

    gui.push_handlers(dragndrop.DragHandler('.draggable'))

    @gui.select('#press-me')
    def on_click(widget, *args):
        print 'on_click', widget
        return event.EVENT_HANDLED

    if 0:
        @gui.select('button,text-button')
        def on_click(widget, *args):
            print 'DEBUG', widget, 'PRESSED'
            return event.EVENT_HANDLED
        @gui.select('*')
        def on_change(widget, text):
            print 'DEBUG', widget, 'VALUE CHANGED', `text`
            return event.EVENT_HANDLED

    @gui.select('frame#menu-test', 'on_click')
    def on_menu(w, x, y, button, modifiers, click_count):
        if not button & mouse.RIGHT:
            return event.EVENT_UNHANDLED
        gui.getByID('test-menu').expose((x, y))
        return event.EVENT_HANDLED

    @gui.select('.hover')
    def on_element_enter(widget, *args):
        print 'ENTER ELEMENT', widget.id
        return event.EVENT_HANDLED
    @gui.select('.hover')
    def on_element_leave(widget, *args):
        print 'LEAVE ELEMENT', widget.id
        return event.EVENT_HANDLED

    @gui.select('.drawer-control')
    def on_click(widget, *args):
        id = widget.id.replace('drawer-control', 'test-drawer')
        gui.getByID(id).toggle_state()
        return event.EVENT_HANDLED

    @gui.select('#music-test')
    def on_click(widget, x, y, button, modifiers, click_count):
        if not button & mouse.RIGHT:
            return event.EVENT_UNHANDLED

        def load_music(file=None):
            if not file: return
            gui.getByID('music-test').delete()
            m = widgets.Music(gui, file, id='music-test', playing=True)
            m.gainFocus()

        dialogs.FileOpenDialog(gui, callback=load_music)
        return event.EVENT_HANDLED

    @gui.select('#movie-test')
    def on_click(widget, x, y, button, modifiers, click_count):
        if not button & mouse.RIGHT:
            return event.EVENT_UNHANDLED

        def load_movie(file=None):
            if not file: return
            gui.getByID('movie-test').delete()
            m = widgets.Movie(gui, file, id='movie-test', playing=True)
            # XXX handle scaling!
            m.gainFocus()

        dialogs.FileOpenDialog(gui, callback=load_movie)
        return event.EVENT_HANDLED

    @gui.select('#movie-test')
    def on_text(widget, text):
        if text == 'f':
            gui.getByID('movie-test').video.pause()
            anim.Delayed(gui.getByID('movie-test').video.play, duration=10)
            window.set_fullscreen()
        return event.EVENT_HANDLED

    @gui.select('.droppable')
    def on_drop(widget, x, y, button, modifiers, element):
        element.reparent(widget)
        widget.bgcolor = (1, 1, 1, 1)
        return event.EVENT_HANDLED

    @gui.select('.droppable')
    def on_drag_enter(widget, x, y, element):
        widget.bgcolor = (.8, 1, .8, 1)
        return event.EVENT_HANDLED

    @gui.select('.droppable')
    def on_drag_leave(widget, x, y, element):
        widget.bgcolor = (1, 1, 1, 1)
        return event.EVENT_HANDLED

    try:
        sample = gui.getByID('xhtml-sample')
    except KeyError:
        sample = None
    if sample:
        @layout.select('#click-me')
        def on_mouse_press(element, x, y, button, modifiers):
            print 'CLICK ON', element
            return event.EVENT_HANDLED
        sample.layout.push_handlers(on_mouse_press)

    my_escape.has_exit = False
    while not (window.has_exit or my_escape.has_exit):
        clock.tick()
        window.dispatch_events()
        media.dispatch_events()

        glClearColor(.2, .2, .2, 1)
        glClear(GL_COLOR_BUFFER_BIT)
        gui.draw()
        fps.draw()
        window.flip()
        if '--once' in sys.argv:
            window.close()
            sys.exit()

    window.pop_handlers()
    media.cleanup()
    gui.delete()

    return window.has_exit

if len(sys.argv) > 1:
    run(sys.argv[1])
else:
    import os
    for file in os.listdir('tests'):
        if not os.path.isfile(os.path.join('tests', file)): continue
        print 'Running', file
        if run(os.path.join('tests', file)): break

window.close()

