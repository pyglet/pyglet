# Test the Objective-C integration.
import unittest
import weakref
import gc
from ctypes import c_int

import pyglet
from tests.annotations import require_platform, Platform

pytestmark = require_platform(Platform.OSX)

if pyglet.compat_platform in ("darwin",):
    from pyglet.libs.darwin import (AutoReleasePool, ObjCSubclass, ObjCClass, objc_classmethod, objc_ivar,
                                    objc_method, objc_rawmethod)
    from pyglet.libs.darwin.cocoapy.runtime import (
        _cache_observer_internal_name,
        _is_objc_tagged_pointer,
        get_cached_instances,
        get_instance_variable,
        objc,
        send_super,
        set_instance_variable,
    )

    NSObject = ObjCClass('NSObject')
    NSNumber = ObjCClass('NSNumber')
    NSDate = ObjCClass('NSDate')


class ObjCIntegrationTest(unittest.TestCase):
    def test_declarative_objc_subclass(self):
        class DeclarativeObjCSubclassTest(NSObject):
            stored_value = objc_ivar(c_int)

            @objc_classmethod('B')
            def isDeclarativeClass(self):
                return True

            @objc_method('B')
            def isDeclarativeSubclass(self):
                return True

            @objc_rawmethod('i')
            def storedValue(self, cmd):
                return get_instance_variable(self, 'stored_value', c_int)

        gc.collect()
        test_object = DeclarativeObjCSubclassTest.alloc().init()
        try:
            self.assertTrue(DeclarativeObjCSubclassTest.isDeclarativeClass())
            self.assertTrue(test_object.isDeclarativeSubclass())
            set_instance_variable(test_object, 'stored_value', 42, c_int)
            self.assertEqual(test_object.storedValue(), 42)
            self.assertEqual(test_object.objc_class.name, b'DeclarativeObjCSubclassTest')
            self.assertNotIn('stored_value', DeclarativeObjCSubclassTest.__dict__)
            self.assertNotIn('storedValue', DeclarativeObjCSubclassTest.__dict__)
        finally:
            test_object.release()

    def test_declarative_objc_subclass_dealloc(self):
        deallocated = False

        class DeclarativeObjCSubclassDeallocTest(NSObject):
            @objc_method('v')
            def dealloc(self):
                nonlocal deallocated
                deallocated = True
                send_super(self, 'dealloc')

        gc.collect()
        test_object = DeclarativeObjCSubclassDeallocTest.alloc().init()
        test_object.release()
        self.assertTrue(deallocated)

    @staticmethod
    def _has_cached_pointer(ptr):
        return any(obj.ptr.value == ptr for _, _, _, obj in get_cached_instances())

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

    def test_objc_cache_invalidates_on_manual_release_with_live_wrapper(self):
        """A native release must evict the wrapper cache even if Python still holds the wrapper."""
        start_count = len(get_cached_instances())

        test_object = NSObject.alloc().init()
        ptr = test_object.ptr.value

        self.assertTrue(self._has_cached_pointer(ptr))

        test_object.release()

        self.assertFalse(self._has_cached_pointer(ptr))

        reused_pointer = False
        for _ in range(1000):
            candidate = NSObject.alloc().init()

            try:
                if candidate.ptr.value == ptr:
                    reused_pointer = True
                    self.assertIsNot(candidate, test_object)
                    break
            finally:
                candidate.release()

        if not reused_pointer:
            self.skipTest("Objective-C runtime did not reuse the released pointer.")

        del test_object
        gc.collect()

        self.assertEqual(len(get_cached_instances()), start_count)

    def test_objc_matches_native_class_debug_helper(self):
        """The opt-in debug helper should report the current native class for a live wrapper."""
        start_count = len(get_cached_instances())

        test_object = NSObject.alloc().init()

        self.assertTrue(test_object.matches_native_class())

        test_object.release()
        del test_object
        gc.collect()

        self.assertEqual(len(get_cached_instances()), start_count)

    def test_objc_deallocated_wrapper_is_invalid(self):
        """A released native object should mark the existing Python wrapper invalid."""
        start_count = len(get_cached_instances())

        test_object = NSObject.alloc().init()
        self.assertTrue(test_object.is_valid)

        test_object.release()

        self.assertFalse(test_object.is_valid)

        with self.assertRaises(ReferenceError):
            test_object.description()

        del test_object
        gc.collect()

        self.assertEqual(len(get_cached_instances()), start_count)

    def test_objc_cache_invalidates_on_autorelease_with_live_wrapper(self):
        """Autorelease pool pop must evict wrappers while Python references are still alive."""
        start_count = len(get_cached_instances())

        with AutoReleasePool():
            test_object = NSObject.alloc().init().autorelease()
            ptr = test_object.ptr.value

            self.assertTrue(self._has_cached_pointer(ptr))

        self.assertFalse(self._has_cached_pointer(ptr))

        del test_object
        gc.collect()

        self.assertEqual(len(get_cached_instances()), start_count)

    def test_objc_heap_autorelease_churn_does_not_grow_cache(self):
        """Repeated heap autorelease objects should leave no wrapper cache entries after pool drain."""
        start_count = len(get_cached_instances())

        for _ in range(1000):
            with AutoReleasePool():
                NSObject.alloc().init().autorelease()

        gc.collect()

        self.assertEqual(len(get_cached_instances()), start_count)

    def test_objc_cache_does_not_observe_tagged_pointers(self):
        """Tagged pointers are value encoded and should not receive retained dealloc observers."""
        tagged_number = NSNumber.numberWithInt_(1)
        ptr = tagged_number.ptr.value

        if not _is_objc_tagged_pointer(tagged_number.ptr):
            self.skipTest("Objective-C runtime did not use a tagged pointer for this NSNumber.")

        observer = objc.objc_getAssociatedObject(tagged_number, _cache_observer_internal_name())
        self.assertFalse(observer)

        del tagged_number
        gc.collect()

        self.assertFalse(self._has_cached_pointer(ptr))

    def test_objc_tagged_pointer_churn_does_not_grow_cache(self):
        """Repeated tagged values should not accumulate cached wrappers like the old pool tracking did."""
        start_count = len(get_cached_instances())
        saw_tagged_date = False

        for _ in range(1000):
            with AutoReleasePool():
                date = NSDate.dateWithTimeIntervalSinceNow_(0.001)
                saw_tagged_date = saw_tagged_date or _is_objc_tagged_pointer(date.ptr)

            del date

        gc.collect()

        if not saw_tagged_date:
            self.skipTest("Objective-C runtime did not use tagged pointers for generated NSDate values.")

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
        """Pytest doesn't like reusing an ObjCClass in the setUpClass. Just make a new one for testing."""
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
            self.assertTrue(self._has_cached_pointer(test_object.ptr.value))

            del test_object
            gc.collect()

        self.assertIsNone(data_ref())
