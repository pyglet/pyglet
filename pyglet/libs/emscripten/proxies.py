"""Lifecycle management for Python callbacks exposed to JavaScript."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyodide.ffi import create_proxy

if TYPE_CHECKING:
    from collections.abc import Callable


class ProxyRegistry:
    """Own JavaScript callback proxies and release them together.

    A proxy must remain alive for as long as JavaScript can invoke it, then be
    explicitly destroyed. Event listeners are unregistered before their
    proxies are released.
    """

    def __init__(self) -> None:
        self._proxies: list[Any] = []
        self._event_listeners: list[tuple[Any, str, Any]] = []

    def create(self, callback: Callable[..., Any]) -> Any:
        """Create and retain a JavaScript proxy for ``callback``."""
        proxy = create_proxy(callback)
        self._proxies.append(proxy)
        return proxy

    def add_event_listener(
        self,
        target: Any,
        event_type: str,
        callback: Callable[..., Any],
        *,
        passive: bool | None = None,
    ) -> Any:
        """Register ``callback`` and retain its proxy until :meth:`destroy`."""
        proxy = self.create(callback)
        if passive is None:
            target.addEventListener(event_type, proxy)
        else:
            target.addEventListener(event_type, proxy, passive=passive)
        self._event_listeners.append((target, event_type, proxy))
        return proxy

    def destroy(self) -> None:
        """Unregister all listeners and destroy every managed proxy."""
        for target, event_type, proxy in reversed(self._event_listeners):
            target.removeEventListener(event_type, proxy)
        self._event_listeners.clear()

        for proxy in reversed(self._proxies):
            proxy.destroy()
        self._proxies.clear()
