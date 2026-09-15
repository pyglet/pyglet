from __future__ import annotations

import pytest

import pyglet
from tests.annotations import Platform, require_platform

pytestmark = require_platform(Platform.LINUX)

if pyglet.compat_platform in Platform.LINUX:
    from pyglet.display import xlib
    from pyglet.libs.x11 import xf86vmode, xrandr


def _xrandr_mode(dot_clock=712_000_000, h_total=5_312, v_total=2_237):
    mode = xrandr.XRRModeInfo()
    mode.dotClock = dot_clock
    mode.hTotal = h_total
    mode.vTotal = v_total
    return mode


def _xf86_mode(dot_clock=712_000, h_total=5_312, v_total=2_237):
    mode = xf86vmode.XF86VidModeModeInfo()
    mode.dotclock = dot_clock
    mode.htotal = h_total
    mode.vtotal = v_total
    return mode


def test_xrandr_rate_keeps_the_fraction():
    rate = xlib.XlibScreenModeXrandr._calculate_refresh_rate(_xrandr_mode())
    assert rate == pytest.approx(59.91781, abs=1e-5)
    assert rate != 60


def test_xf86_rate_keeps_the_fraction():
    rate = xlib.XlibScreenModeXF86._calculate_refresh_rate(_xf86_mode())
    assert rate == pytest.approx(59.91781, abs=1e-5)
    assert rate != 60


def test_both_backends_agree_on_the_same_modeline():
    # XF86VidMode reports the pixel clock in kHz, XRandR in Hz.
    assert xlib.XlibScreenModeXF86._calculate_refresh_rate(
        _xf86_mode()
    ) == pytest.approx(
        xlib.XlibScreenModeXrandr._calculate_refresh_rate(_xrandr_mode())
    )


@pytest.mark.parametrize('rate', [59.94, 143.998848, 239.76])
def test_common_non_integer_rates_survive(rate):
    # A 1000-line modeline makes the arithmetic exact for the assertion.
    v_total = 1_000
    h_total = 1_000
    dot_clock = round(rate * h_total * v_total)
    assert xlib.XlibScreenModeXrandr._calculate_refresh_rate(
        _xrandr_mode(dot_clock, h_total, v_total)
    ) == pytest.approx(rate, abs=1e-6)


@pytest.mark.parametrize('h_total,v_total', [(0, 2_237), (5_312, 0), (0, 0)])
def test_a_modeline_without_totals_is_zero_rather_than_an_error(h_total, v_total):
    assert xlib.XlibScreenModeXrandr._calculate_refresh_rate(
        _xrandr_mode(h_total=h_total, v_total=v_total)
    ) == 0
    assert xlib.XlibScreenModeXF86._calculate_refresh_rate(
        _xf86_mode(h_total=h_total, v_total=v_total)
    ) == 0


def test_an_integer_rate_stays_comparable_to_an_integer():
    # `Screen.get_closest_mode` scores modes with `mode.rate == current.rate`,
    # so an exact 60Hz modeline must still equal 60 after the change.
    rate = xlib.XlibScreenModeXrandr._calculate_refresh_rate(
        _xrandr_mode(dot_clock=60_000_000, h_total=1_000, v_total=1_000)
    )
    assert rate == 60
