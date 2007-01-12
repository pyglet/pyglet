#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from pyglet.window import *
from pyglet.window.event import *

class MyWindow(Window):
    def run(self):
        while not self.has_exit:
            self.dispatch_events()

if __name__ == '__main__':
    MyWindow().run()
