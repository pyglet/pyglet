import pytest
from unittest.mock import Mock

# Skip this entire test module if on a non-win32 platform.
# Although it's ugly, it's easier than refactoring platform restriction
# code to allow exceptions to enable mock-backed testing.
try:
    from pyglet.libs.win32 import context_managers
    from ctypes.wintypes import HANDLE
except ImportError:
    context_managers = HANDLE = None

pytestmark = pytest.mark.skipif(
    context_managers is None,
    reason='Win32 context managers only available on Windows...')


# = Fixtures & Constants = #

GET_DC_SUCCESS = 1
GET_DC_FAILURE = None
RELEASE_DC_SUCCESS = 1
RELEASE_DC_FAILURE = 0
USER32_MODPATH = 'pyglet.libs.win32.context_managers.user32'


# === Fixtures === #

# Indirectly parametrize via pytest.mark.parametrize
# https://docs.pytest.org/en/stable/example/parametrize.html#indirect-parametrization
@pytest.fixture
def dc_handle(request) -> "HANDLE":
    return HANDLE(request.param)


@pytest.fixture
def release_result(request) -> int:
    return request.param


@pytest.fixture
def patched_get_dc(monkeypatch, dc_handle):
    mock = Mock(return_value=dc_handle)
    monkeypatch.setattr(context_managers.user32, 'GetDC', mock)
    return mock


@pytest.fixture
def patched_release_dc(monkeypatch, release_result):
    mock = Mock(return_value=release_result)
    monkeypatch.setattr(context_managers.user32, 'ReleaseDC', mock)
    return mock


# Kludge to avoid IDE typing issues or ugly cast / type: ignore
@pytest.fixture
def patched_win_error_type(monkeypatch):
    monkeypatch.setattr(context_managers, 'WinError', OSError)
    return OSError


# = Tests = #


@pytest.mark.parametrize('dc_handle', [GET_DC_SUCCESS], indirect=True)
@pytest.mark.parametrize('release_result', [RELEASE_DC_SUCCESS], indirect=True)
def test_device_context_yields_correct_value_when_get_dc_succeeds(
        patched_get_dc, patched_release_dc, dc_handle
):
    with context_managers.device_context() as dc:
        assert dc is dc_handle


# TODO: Review the following tests to see why they are failing.

# @pytest.mark.parametrize('dc_handle', [GET_DC_FAILURE], indirect=True)
# @pytest.mark.parametrize('release_result', [RELEASE_DC_SUCCESS], indirect=True)
# def test_device_context_raises_winerror_when_get_dc_fails(
#         patched_win_error_type, patched_get_dc, patched_release_dc
# ):
#     with pytest.raises(patched_win_error_type):
#         with context_managers.device_context() as dc:
#             pass
#
#
# @pytest.mark.parametrize('dc_handle', [GET_DC_SUCCESS], indirect=True)
# @pytest.mark.parametrize('release_result', [RELEASE_DC_FAILURE], indirect=True)
# def test_device_context_raises_winerror_when_cleanup_fails(
#         patched_win_error_type,
#         patched_get_dc, patched_release_dc
# ):
#     with pytest.raises(patched_win_error_type):
#         with context_managers.device_context() as dc:
#             pass
#
#
# # Nasty whitebox tests
# @pytest.mark.parametrize('dc_handle', [GET_DC_SUCCESS, GET_DC_FAILURE], indirect=True)
# @pytest.mark.parametrize('release_result', [RELEASE_DC_SUCCESS], indirect=True)
# def test_device_context_calls_get_dc(
#         patched_get_dc,
#         dc_handle,
#         patched_release_dc
# ):
#     try:
#         with context_managers.device_context() as dc:
#             pass
#     finally:
#         patched_get_dc.assert_called_with(dc_handle.value)
#
#
# @pytest.mark.parametrize('dc_handle', [GET_DC_SUCCESS], indirect=True)
# @pytest.mark.parametrize('release_result',
#                          [RELEASE_DC_FAILURE, RELEASE_DC_SUCCESS], indirect=True)
# def test_device_context_calls_release_dc(
#         patched_get_dc,
#         dc_handle,
#         patched_release_dc
# ):
#     try:
#         with context_managers.device_context() as dc:
#             pass
#     finally:
#         patched_release_dc.assert_called_with(dc_handle)
