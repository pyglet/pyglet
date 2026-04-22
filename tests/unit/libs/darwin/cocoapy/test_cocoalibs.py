import logging
from unittest.mock import Mock, patch

from pytest import LogCaptureFixture

import pyglet
from tests.annotations import Platform, require_platform

pytestmark = require_platform(Platform.OSX)

if pyglet.compat_platform in Platform.OSX:
    from pyglet.libs.darwin.cocoapy import (
        TimeConstraintThreadPolicy,
        get_realtime_thread_policy,
        set_realtime_thread_policy,
    )


def test_get_realtime_thread_policy__call_success__timeConstraintThreadPolicy_returned_and_no_error_logged():
    cocoa_mock = Mock()
    cocoa_mock.thread_policy_get.return_value = 0
    expected_return_type = type(TimeConstraintThreadPolicy())

    with patch("pyglet.libs.darwin.cocoapy.cocoalibs.cocoa", cocoa_mock):
        actual_return_type = type(get_realtime_thread_policy())

    cocoa_mock.thread_policy_get.assert_called_once()
    assert actual_return_type == expected_return_type


def test_get_realtime_thread_policy__call_failure__None_returned_and_error_logged(
    caplog: LogCaptureFixture,
):
    caplog.set_level(logging.ERROR)
    cocoa_mock = Mock()
    cocoa_mock.thread_policy_get.return_value = -1
    expected_return = None

    with patch("pyglet.libs.darwin.cocoapy.cocoalibs.cocoa", cocoa_mock):
        actual_return = get_realtime_thread_policy()

    cocoa_mock.thread_policy_get.assert_called_once()
    assert actual_return == expected_return
    assert any(
        record.levelname == "ERROR" for record in caplog.records
    ), "No error logged"


def test_set_realtime_thread_policy__call_success__no_error_logged(
    caplog: LogCaptureFixture,
):
    caplog.set_level(logging.ERROR)
    cocoa_mock = Mock()
    cocoa_mock.thread_policy_set.return_value = 0
    get_realtime_thread_policy_mock = Mock()
    get_realtime_thread_policy_mock.return_value = TimeConstraintThreadPolicy()

    with (
        patch("pyglet.libs.darwin.cocoapy.cocoalibs.cocoa", cocoa_mock),
        patch(
            "pyglet.libs.darwin.cocoapy.cocoalibs.get_realtime_thread_policy",
            get_realtime_thread_policy_mock,
        ),
    ):
        set_realtime_thread_policy()

    cocoa_mock.thread_policy_set.assert_called_once()
    get_realtime_thread_policy_mock.assert_called_once()
    assert not any(
        record.levelname == "ERROR" for record in caplog.records
    ), "Error was logged"


def test_set_realtime_thread_policy__call_failure__error_logged(
    caplog: LogCaptureFixture,
):
    caplog.set_level(logging.ERROR)
    cocoa_mock = Mock()
    get_realtime_thread_policy_mock = Mock()
    get_realtime_thread_policy_mock.return_value = None

    with (
        patch("pyglet.libs.darwin.cocoapy.cocoalibs.cocoa", cocoa_mock),
        patch(
            "pyglet.libs.darwin.cocoapy.cocoalibs.get_realtime_thread_policy",
            get_realtime_thread_policy_mock,
        ),
    ):
        set_realtime_thread_policy()

    cocoa_mock.thread_policy_set.assert_not_called()
    get_realtime_thread_policy_mock.assert_called_once()
    assert any(
        record.levelname == "ERROR" for record in caplog.records
    ), "No error logged"
