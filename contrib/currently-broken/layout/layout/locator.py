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
import warnings

def create_locator(address):
    '''Examines address and returns a locator that has address as the base
    URI.'''
    url = urlparse.urlparse(address)
    if not url[0]:
        return LocalFileLocator(address)
    else:
        return URLLocator(address)

class Locator(object):
    '''Interface for locator objects.'''
    def get_stream(self, uri):
        '''Return a file-like object for the given URI, or None if it cannot
        be retrieved.'''
        return None

    def get_default_stream(self):
        '''Return a file-like object for the URI that was used to construct
        the locator.
        '''
        return None

class LocalFileLocator(Locator):
    '''Locator for reading local file objects.
    '''
    def __init__(self, uri=''):
        self.uri = uri
        self.base = os.path.split(uri)[0]
        
    def get_stream(self, uri):
        if not os.path.isabs(uri):
            uri = os.path.join(self.base, uri)
        try:
            return open(uri, 'rb')
        except IOError:
            warnings.warn('Could not open "%s"' % uri)
            return None

    def get_default_stream(self):
        try:
            return open(self.uri, 'rb')
        except IOError:
            warnings.warn('Could not open "%s"' % self.uri)
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

    def get_default_stream(self):
        return self.get_stream(self.base)
