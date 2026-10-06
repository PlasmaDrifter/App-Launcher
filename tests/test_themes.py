"""Unit tests for AutoLaunch Modern Minimalist theme integration."""

import shutil
import tempfile
import unittest
from pathlib import Path

from config import ConfigManager
from ui.themes import (
    DEFAULT_THEME,
    THEMES,
    Theme,
    get_theme,
    get_theme_choices,
    build_card_stylesheet,
    build_header_btn_stylesheet,
    build_default_btn_active_stylesheet,
    build_delete_btn_stylesheet,
    build_micro_btn_stylesheet,
    build_micro_delete_btn_stylesheet,
    build_primary_btn_stylesheet,
)


class TestThemes(unittest.TestCase):
    """Verifies Modern Minimalist theme registry, palette validation, and stylesheet generation."""

    def test_themes_registry_completeness(self):
        expected_keys = {
            "modern_minimalist",
        }
        self.assertEqual(set(THEMES.keys()), expected_keys)
        self.assertEqual(DEFAULT_THEME, "modern_minimalist")

    def test_theme_attributes_integrity(self):
        theme = THEMES["modern_minimalist"]
        self.assertEqual(theme.key, "modern_minimalist")
        self.assertEqual(theme.name, "Modern Minimalist")
        self.assertTrue(theme.description)
        # Ensure hex colors start with # or rgba
        for field_name in (
            "bg_base", "bg_surface", "bg_card", "bg_header",
            "card_hover", "border_subtle", "border_focus",
            "text_primary", "text_secondary", "text_muted",
            "accent_primary", "accent_hover", "accent_active",
            "danger", "danger_hover", "success", "success_hover"
        ):
            val = getattr(theme, field_name)
            self.assertTrue(val.startswith("#") or val.startswith("rgba"), f"{field_name} is {val}")

    def test_get_theme_valid(self):
        theme = get_theme("modern_minimalist")
        self.assertEqual(theme.key, "modern_minimalist")
        self.assertEqual(theme.name, "Modern Minimalist")

    def test_get_theme_fallback(self):
        fallback = get_theme("non_existent_theme_key")
        self.assertEqual(fallback.key, "modern_minimalist")

    def test_get_theme_choices(self):
        choices = get_theme_choices()
        self.assertEqual(len(choices), 1)
        self.assertEqual(choices[0][0], "modern_minimalist")

    def test_stylesheet_builders(self):
        theme = get_theme("modern_minimalist")
        qss = theme.build_stylesheet()
        self.assertIn(theme.bg_base, qss)
        self.assertIn(theme.accent_primary, qss)

        card_qss = build_card_stylesheet(theme)
        self.assertIn(theme.bg_card, card_qss)

        header_btn_qss = build_header_btn_stylesheet(theme)
        self.assertIn("QPushButton", header_btn_qss)

        active_default_qss = build_default_btn_active_stylesheet(theme)
        self.assertIn(theme.accent_hover, active_default_qss)

        delete_btn_qss = build_delete_btn_stylesheet(theme)
        self.assertIn(theme.danger, delete_btn_qss)

        micro_btn_qss = build_micro_btn_stylesheet(theme)
        self.assertIn(theme.accent_primary, micro_btn_qss)

        micro_del_qss = build_micro_delete_btn_stylesheet(theme)
        self.assertIn(theme.danger, micro_del_qss)

        primary_btn_qss = build_primary_btn_stylesheet(theme)
        self.assertIn(theme.accent_primary, primary_btn_qss)

    def test_config_manager_theme_persistence(self):
        test_dir = tempfile.mkdtemp()
        try:
            config_dir = Path(test_dir) / "autolaunch"
            mgr = ConfigManager(config_dir)
            self.assertEqual(mgr.theme, "modern_minimalist")

            mgr.theme = "modern_minimalist"
            mgr.save()

            mgr2 = ConfigManager(config_dir)
            self.assertEqual(mgr2.theme, "modern_minimalist")
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
