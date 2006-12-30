#!/usr/bin/env python

'''Locator classes for retrieving streams from local or net resources.
Typically take a URI and return a stream.  Can be initialised with some
data such as a base URI.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

class Locator(object):
    '''Interface for locator objects.'''
    def get_stream(self, uri):
        '''Return a file-like object for the given URI, or None if it cannot
        be retrieved.'''
        return None

class LocalFileLocator(object):
    '''Locator for reading local file objects.

    Currently assumes the URI is a file path relative to the working
    directory.  
    
    TODO: allow initialisation for given base directory, accept file:// URIs.
    '''
    def get_stream(self, uri):
        try:
            return open(uri, 'rb')
        except IOError:
            return None

# TODO locators for net and zip resource.


