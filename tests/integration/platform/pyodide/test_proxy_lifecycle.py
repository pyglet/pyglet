from __future__ import annotations

import sys

import pytest

if sys.platform != "emscripten":
    pytest.skip("requires the Emscripten/Pyodide runtime", allow_module_level=True)

from js import Event, document

from pyglet.libs.emscripten.proxies import ProxyRegistry


def test_proxy_registry_unregisters_listeners_and_releases_proxies():
    element = document.createElement("button")
    received = []
    proxies = ProxyRegistry()

    proxies.add_event_listener(element, "click", received.append)
    element.dispatchEvent(Event.new("click"))
    assert len(received) == 1

    proxies.destroy()
    proxies.destroy()
    element.dispatchEvent(Event.new("click"))
    assert len(received) == 1
