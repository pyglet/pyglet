import threading

from Cocoa import NSAutoreleasePool
from Cocoa import NSThread

__all__ = ["enter_autorelease_pool",
           "exit_autorelease_pool",
           "clean_autorelease_pools",
           "autorelease"]

autorelease_pool_lock = threading.Lock()
autorelease_pools = {}

def create_pool():
    return NSAutoreleasePool.alloc().init()

def enter_autorelease_pool():
    autorelease_pool_lock.acquire()
    thread = NSThread.currentThread()
    if thread not in autorelease_pools:
        autorelease_pools[thread] = []
    pool_stack = autorelease_pools[thread]
    pool_stack.append(create_pool())
    autorelease_pool_lock.release()

def exit_autorelease_pool():
    autorelease_pool_lock.acquire()
    thread = NSThread.currentThread()
    pool_stack = autorelease_pools[thread]
    pool = pool_stack.pop()
    pool.release()
    autorelease_pool_lock.release()

def clean_autorelease_pools():
    autorelease_pool_lock.acquire()
    for thread in list(autorelease_pools):
        pool_stack = autorelease_pools[thread]
        if thread.isFinished():
            for pool in pool_stack:
                pool.release()
            del autorelease_pools[thread]
        else:
            for idx, pool in enumerate(pool_stack):
                pool_stack[idx] = create_pool()
                pool.release()
    autorelease_pool_lock.release()

class AutoreleasePoolContextManager(object):
    def __enter__(self):
        enter_autorelease_pool()
    def __exit__(self, type, value, traceback):
        exit_autorelease_pool()

autorelease = AutoreleasePoolContextManager()
