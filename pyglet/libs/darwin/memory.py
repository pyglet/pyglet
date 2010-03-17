import threading
import time

from Cocoa import NSAutoreleasePool
from Cocoa import NSThread

__all__ = ["enter_autorelease_pool",
           "exit_autorelease_pool",
           "autorelease"]


## Pool directory & lock.

_autorelease_pool_lock = threading.Lock()
_autorelease_pools = {}


## Utility.

def _create_pool():
    return NSAutoreleasePool.alloc().init()


## Non-context manager API.

def enter_autorelease_pool():
    _autorelease_pool_lock.acquire()
    thread = NSThread.currentThread()
    if thread not in _autorelease_pools:
        _autorelease_pools[thread] = []
    pool_stack = _autorelease_pools[thread]
    pool_stack.append(_create_pool())
    _autorelease_pool_lock.release()

def exit_autorelease_pool():
    _autorelease_pool_lock.acquire()
    thread = NSThread.currentThread()
    pool_stack = _autorelease_pools[thread]
    pool = pool_stack.pop()
    pool.release()
    _autorelease_pool_lock.release()


## Context manager API.

class _AutoreleasePoolContextManager(object):
    def __enter__(self):
        enter_autorelease_pool()
    def __exit__(self, type, value, traceback):
        exit_autorelease_pool()

autorelease = _AutoreleasePoolContextManager()


## Cleaning thread.

def _clean_autorelease_pools():
    _autorelease_pool_lock.acquire()
    for thread in list(_autorelease_pools):
        pool_stack = _autorelease_pools[thread]
        if thread.isFinished():
            for pool in pool_stack:
                pool.release()
            del _autorelease_pools[thread]
        else:
            for idx, pool in enumerate(pool_stack):
                pool_stack[idx] = create_pool()
                pool.release()
    _autorelease_pool_lock.release()

def _cleaner():
    while True:
        _clean_autorelease_pools()
        time.sleep(1.0)
_cleaner = threading.Thread(target=_cleaner)
_cleaner.daemon = True
_cleaner.start()
