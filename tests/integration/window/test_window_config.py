import pyglet


def _backend_config(config: pyglet.config.Config):
    return getattr(config, pyglet.options.backend)


def test_window_accepts_single_config():
    user_config = pyglet.config.Config()
    expected = _backend_config(user_config)

    window = pyglet.window.Window(visible=False, config=user_config)
    try:
        assert window.config.config is expected
    finally:
        window.close()


def test_window_accepts_multiple_configs():
    preferred = pyglet.config.Config()
    fallback = pyglet.config.Config()
    expected = _backend_config(preferred)

    window = pyglet.window.Window(visible=False, config=(preferred, fallback))
    try:
        assert window.config.config is expected
    finally:
        window.close()


def test_window_tries_next_config_when_first_match_fails(monkeypatch):
    preferred = pyglet.config.Config()
    fallback = pyglet.config.Config()
    preferred_backend_config = _backend_config(preferred)
    fallback_backend_config = _backend_config(fallback)
    match_calls = []
    original_match_surface_config = pyglet.config.match_surface_config

    def fail_first_then_match(config, surface):
        match_calls.append(config)
        if config is preferred_backend_config:
            return None
        return original_match_surface_config(config, surface)

    monkeypatch.setattr(pyglet.config, "match_surface_config", fail_first_then_match)

    window = pyglet.window.Window(visible=False, config=(preferred, fallback))
    try:
        assert match_calls[:2] == [preferred_backend_config, fallback_backend_config]
        assert window.config.config is fallback_backend_config
    finally:
        window.close()
