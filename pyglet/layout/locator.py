#!/usr/bin/env python

'''Locator classes for retrieving streams from local or net resources.
Typically take a URI and return a stream.  Can be initialised with some
data such as a base URI.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import urlparse
import urllib2
import os.path

def create_locator(address):
    '''Examines address and returns a locator that has address as the base
    URI.'''
    url = urlparse.urlparse(address)
    if not url[0]:
        # No scheme, assume it's a local file
        base = os.path.split(address)[0]
        return LocalFileLocator(base)
    else:
        return URLLocator(address)

class Locator(object):
    '''Interface for locator objects.'''
    def get_stream(self, uri):
        '''Return a file-like object for the given URI, or None if it cannot
        be retrieved.'''
        return None

class LocalFileLocator(Locator):
    '''Locator for reading local file objects.
    '''
    def __init__(self, base=''):
        self.base = base
        
    def get_stream(self, uri):
        if not isabs(uri):
            uri = os.path.join(self.base, uri)
        try:
            return open(uri, 'rb')
        except IOError:
            warnings.warn('Could not open "%s"' % uri)
            return None

class URLLocator(Locator):
    '''Locator for reading network file objects.

    TODO Currently implemented using urllib2, could provide points for
    authentication and proxy.
    '''
    def __init__(self, base=''):
        self.base = base

    def get_stream(self, uri):
        # urljoin takes care of figuring out if it's relative or absolute.
        uri = urlparse.urljoin(self.base, uri)
        try:
            return urllib2.urlopen(uri)
        except IOError:
            warnings.warn('Could not open "%s"' % uri)
            return None

