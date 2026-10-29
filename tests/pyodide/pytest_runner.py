"""Select and run tests supported by the Pyodide browser environment."""
from __future__ import annotations

from pathlib import Path

import pytest


tests_root = Path("/tests")
test_files = sorted(
    str(path)
    for path in (
        *tests_root.joinpath("unit").rglob("test_*.py"),
        *tests_root.joinpath("integration", "graphics").glob("test_*.py"),
        *tests_root.joinpath("integration", "graphics", "webgl").glob("test_*.py"),
        *tests_root.joinpath("integration", "platform", "pyodide").glob("test_*.py"),
    )
)
# Keep the shared text-group coverage in the browser suite as well.
test_files.extend(
    str(tests_root / "integration" / "text" / "test_layout.py") + "::" + name
    for name in (
        "test_label_text_update_reuses_vertex_list_after_shaping",
        "test_label_text_update_rebuilds_for_length_changes_and_empty_text",
        "test_label_reuse_respects_batch_group_and_font_changes",
        "test_label_text_updates_keep_effect_geometry",
        "test_label_text_update_preserves_deferred_updates",
        "test_retained_label_placement_updates_only_affected_attributes",
        "test_label_placement_reuse_checks_shaped_glyph_count",
        "test_retained_scrollable_placement_preserves_view_translation",
        "test_retained_label_reads_uniform_styles_without_run_iterators",
        "test_plain_text_shares_glyph_effect_and_decoration_groups",
        "test_cached_text_groups_keep_depth_configuration_separate",
        "test_cached_text_groups_separate_depth_comparison_values",
        "test_scrollable_groups_and_uniforms_remain_independent",
        "test_scrollable_groups_created_later_use_current_uniforms",
    )
)
if not test_files:
    raise RuntimeError("No supported tests were included in the Pyodide project.")

PYGLET_PYTEST_EXIT_CODE = int(pytest.main([
    *test_files,
    "-v",
    "--tb=short",
    "-p",
    "no:cacheprovider",
]))
