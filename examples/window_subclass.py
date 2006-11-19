#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from pyglet.window import *
from pyglet.window.event import *

class MyWindow(Window):
    def __init__(self):
        super(MyWindow, self).__init__()
        self.exit_handler = ExitHandler()
        self.push_handlers(self.exit_handler)

    def run(self):
        while not self.exit_handler.exit:
            self.dispatch_events()

if __name__ == '__main__':
    MyWindow().run()
