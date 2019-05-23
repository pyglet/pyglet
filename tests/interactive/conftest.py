"""
py.test hooks for interactive test cases.
"""
from __future__ import absolute_import
import inspect
import pytest


def pytest_collection_modifyitems(items, config):
    """Determine whether test should be skipped based on command-line options."""
    sanity = config.getoption('--sanity', False)
    non_interactive = config.getoption('--non-interactive', False)

    remaining = []
    deselected = []
    for item in items:
        if _skip_item(item, sanity, non_interactive):
            deselected.append(item)
        else:
            remaining.append(item)
    if deselected:
        items[:] = remaining
        config.hook.pytest_deselected(items=deselected)


def _skip_item(item, sanity, non_interactive):
    requires_user_action = item.get_closest_marker('requires_user_action')
    requires_user_validation = item.get_closest_marker('requires_user_validation')
    only_interactive = item.get_closest_marker('only_interactive')

    if ((requires_user_action is not None or only_interactive is not None) 
            and (sanity or non_interactive)):
        return True

    if ((requires_user_validation is not None) 
            and (non_interactive)):
        return True

    return False

def pytest_runtest_setup(item):
    # TODO: Remove after migrating tests
    sanity = item.config.getoption('--sanity', False)
    non_interactive = item.config.getoption('--non-interactive', False)
    interactive = not sanity and not non_interactive

    if interactive:
        _show_test_header(item)
    _try_set_class_attribute(item, 'interactive', interactive)
    _try_set_class_attribute(item, 'allow_missing_screenshots', sanity)

def _show_test_header(item):
    print()
    print('='*80)
    print(item.name)
    print(_get_doc(item))
    print('-'*80)

def _try_set_class_attribute(item, name, value):
    if hasattr(item.obj, 'im_class'):
        if hasattr(item.obj.im_class, name):
            setattr(item.obj.im_class, name, value)

def _get_doc(item):
    i = item
    while i is not None:
        if hasattr(i, 'obj') and hasattr(i.obj, '__doc__') and i.obj.__doc__ is not None:
            return inspect.cleandoc(i.obj.__doc__)
        i = i.parent

def pytest_runtest_makereport(item, call):
    if call.when == 'call' and call.excinfo is None:
        _legacy_check_screenshots(item)
        _commit_screenshots(item)

def _legacy_check_screenshots(item):
    # TODO: Remove after migrating all tests
    if hasattr(item, 'obj') and hasattr(item.obj, '__self__'):
        if hasattr(item.obj.__self__, 'check_screenshots'):
            item.obj.__self__.check_screenshots()

def _commit_screenshots(item):
    if hasattr(item.session, 'pending_screenshots'):
        for fixture in item.session.pending_screenshots:
            fixture.commit_screenshots()

