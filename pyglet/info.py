#!/usr/bin/env python

'''Get environment information useful for debugging.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

_first_heading = True
def _heading(heading):
    global _first_heading
    if not _first_heading:
        print
    else:
        _first_heading = False
    print heading
    print '-' * 78

def dump_python():
    '''Dump Python version and environment to stdout.'''
    import os
    import sys
    print 'sys.version:', sys.version
    print 'sys.platform:', sys.platform
    print 'os.getcwd():', os.getcwd()
    for key, value in os.environ.items():
        if key.startswith('PYGLET_'):
            print "os.environ['%s']: %s" % (key, value)

def dump_pyglet():
    '''Dump pyglet version and options.'''
    import pyglet
    print 'pyglet.version:', pyglet.version
    print 'pyglet.__file__:', pyglet.__file__
    for key, value in pyglet.options.items():
        print "pyglet.options['%s'] = %r" % (key, value)

def dump_window():
    '''Dump display, windowm, screen and default config info.'''
    import pyglet.window
    platform = pyglet.window.get_platform()
    print 'platform:', repr(platform)
    display = platform.get_default_display()
    print 'display:', repr(display)
    screens = display.get_screens()
    for i, screen in enumerate(screens):
        print 'screens[%d]: %r' % (i, screen)
    window = pyglet.window.Window()
    for key, value in window.config.get_gl_attributes():
        print "config['%s'] = %r" % (key, value)
    print 'context:', repr(window.context)
    window.close()

def dump_gl():
    '''Dump GL info.'''
    from pyglet.gl import gl_info
    print 'gl_info.get_version():',  gl_info.get_version()
    print 'gl_info.get_vendor():',  gl_info.get_vendor()
    print 'gl_info.get_renderer():',  gl_info.get_renderer()
    print 'gl_info.get_extensions():'
    extensions = list(gl_info.get_extensions())
    extensions.sort()
    for name in extensions:
        print '  ', name

def dump_glu():
    '''Dump GLU info.'''
    from pyglet.gl import glu_info
    print 'glu_info.get_version():',  glu_info.get_version()
    print 'glu_info.get_extensions():'
    extensions = list(glu_info.get_extensions())
    extensions.sort()
    for name in extensions:
        print '  ', name

def dump_media():
    '''Dump pyglet.media info.'''
    import pyglet.media
    print 'driver:', pyglet.media.driver.__name__

def dump_avbin():
    '''Dump AVbin info.'''
    try:
        import pyglet.media.avbin
        print 'Library:', pyglet.media.avbin.av
        print 'AVbin version:', pyglet.media.avbin.av.avbin_get_version()
        print 'FFmpeg revision:', \
            pyglet.media.avbin.av.avbin_get_ffmpeg_revision()
    except:
        print 'AVbin not available.'

def _try_dump(heading, func):
    _heading(heading)
    try:
        func()
    except:
        import traceback
        traceback.print_exc()

def dump():
    '''Dump all information to stdout.'''
    _try_dump('Python', dump_python)
    _try_dump('pyglet', dump_pyglet)
    _try_dump('pyglet.window', dump_window)
    _try_dump('pyglet.gl.gl_info', dump_gl)
    _try_dump('pyglet.gl.glu_info', dump_glu)
    _try_dump('pyglet.media', dump_media)
    _try_dump('pyglet.media.avbin', dump_avbin)

if __name__ == '__main__':
    dump()
