# Test the Objective-C integration.
import unittest
import weakref
import gc

import pyglet
from tests.annotations import require_platform, Platform

pytestmark = require_platform(Platform.OSX)

if pyglet.compat_platform in ("darwin",):
    from pyglet.libs.darwin import AutoReleasePool, ObjCSubclass, ObjCClass
    from pyglet.libs.darwin.cocoapy.runtime import get_cached_instances, send_super

    NSObject = ObjCClass('NSObject')


class ObjCIntegrationTest(unittest.TestCase):
    def test_objc_leak_gc(self):
        """Test deleting """
        start_count = len(get_cached_instances())
        test_object = NSObject.alloc().init()
        del test_object

        gc.collect()

        self.assertEqual(len(get_cached_instances()), start_count)

    def test_objc_leak_cache_release_manual_delete(self):
        start_count = len(get_cached_instances())
        test_object = NSObject.alloc().init()

        self.assertIs(test_object._retained, True)

        test_object.release()

        self.assertIs(test_object._retained, False)

        del test_object

        self.assertEqual(len(get_cached_instances()), start_count)

    def test_objc_subclass_dealloc_release(self):
        start_count = len(get_cached_instances())

        allocated = True

        class MyCustomObjectTestRelease_Implementation:
            MyCustomObjectTestRelease = ObjCSubclass("NSObject", "MyCustomObjectTestRelease")

            @MyCustomObjectTestRelease.method('v')
            def dealloc(self) -> None:
                nonlocal allocated
                allocated = False
                send_super(self, 'dealloc')

        MyCustomObjectTestRelease = ObjCClass('MyCustomObjectTestRelease')

        instance = MyCustomObjectTestRelease.alloc().init()
        instance.release()

        self.assertEqual(allocated, False)

        del instance

        self.assertEqual(len(get_cached_instances()), start_count)

    def test_objc_subclass_dealloc_autorelease(self):
        """Pytest doesn't like re-using an ObjCClass in the setUpClass. Just make a new one for testing."""
        start_count = len(get_cached_instances())

        allocated = True

        class MyCustomObjectTestAutorelease_Implementation:
            MyCustomObjectTestAutorelease = ObjCSubclass("NSObject", "MyCustomObjectTestAutorelease")

            @MyCustomObjectTestAutorelease.method('v')
            def dealloc(self) -> None:
                nonlocal allocated
                allocated = False
                send_super(self, 'dealloc')

        MyCustomObjectTestAutorelease = ObjCClass('MyCustomObjectTestAutorelease')

        with AutoReleasePool():
            MyCustomObjectTestAutorelease.alloc().init().autorelease()

        self.assertEqual(allocated, False)
        self.assertEqual(len(get_cached_instances()), start_count)

    def test_objc_association(self):
        """Make sure associated Python objects don't get GC'd until the ObjC instance does."""
        with AutoReleasePool():
            test_object = NSObject.alloc().init()

            class Data:
                pass

            data = Data()

            data_ref = weakref.ref(data)

            test_object.associate("data", data)

            del data

            gc.collect()

            self.assertIs(test_object.data, data_ref())

            del test_object
            gc.collect()

        self.assertIsNone(data_ref())
