#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import weakref

class WeakSet(object):
    '''Set of objects, referenced weakly.

    Adding an object to this set does not prevent it from being garbage
    collected.  Upon being garbage collected, the object is automatically
    removed from the set.
    '''
    def __init__(self):
        self._dict = weakref.WeakKeyDictionary()

    def add(self, value):
        self._dict[value] = True

    def remove(self, value):
        del self._dict[value]

    def __iter__(self):
        for key in self._dict.keys():
            yield key

#: Set of all open displays.  Instances of `Display` are automatically added
#: to this set upon construction.  The set uses weak references, so displays
#: are removed from the set when they are no longer referenced.
displays = WeakSet()

#: Set of all open windows (including invisible windows).  Instances of
#: `Window` are automatically added to this set upon construction.  The set
#: uses weak references, so windows are removed from the set when they are no
#: longer referenced or are closed explicitly.
windows = WeakSet()
