"""Tests for pixpop.config."""

from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import patch

from pixpop.config import AppConfig, _parse_toml, load_config


class TestParseToml:
    """Unit tests for _parse_toml coercion logic."""

    def test_empty_dict_returns_defaults(self) -> None:
        assert _parse_toml({}) == AppConfig()

    def test_valid_overrides(self) -> None:
        cfg = _parse_toml({"max_layers": 5, "theme_name": "dracula"})
        assert cfg.max_layers == 5
        assert cfg.theme_name == "dracula"

    def test_invalid_int_falls_back(self) -> None:
        cfg = _parse_toml({"max_layers": -3})
        assert cfg.max_layers == AppConfig().max_layers

    def test_non_int_falls_back(self) -> None:
        cfg = _parse_toml({"max_layers": "many"})
        assert cfg.max_layers == AppConfig().max_layers

    def test_valid_hex_color(self) -> None:
        cfg = _parse_toml({"background_color": "#ff0000"})
        assert cfg.background_color == "#ff0000"

    def test_short_hex_color(self) -> None:
        cfg = _parse_toml({"background_color": "#f00"})
        assert cfg.background_color == "#f00"

    def test_invalid_color_falls_back(self) -> None:
        cfg = _parse_toml({"background_color": "red"})
        assert cfg.background_color == AppConfig().background_color

    def test_background_mode_solid(self) -> None:
        cfg = _parse_toml({"background_mode": "solid"})
        assert cfg.background_mode == "solid"

    def test_background_mode_invalid_falls_back(self) -> None:
        cfg = _parse_toml({"background_mode": "plaid"})
        assert cfg.background_mode == AppConfig().background_mode

    def test_background_mode_case_insensitive(self) -> None:
        cfg = _parse_toml({"background_mode": "Solid"})
        assert cfg.background_mode == "solid"


class TestLoadConfig:
    """Integration tests for load_config file discovery."""

    def test_no_files_returns_defaults(self, tmp_path: Path) -> None:
        with (
            patch("pixpop.config.Path.cwd", return_value=tmp_path),
            patch("pixpop.config._XDG_CONFIG_PATH", tmp_path / "nope.toml"),
        ):
            assert load_config() == AppConfig()

    def test_cwd_config_loaded(self, tmp_path: Path) -> None:
        config_file = tmp_path / "pixpop-config.toml"
        config_file.write_text('theme_name = "dracula"\nmax_layers = 3\n')
        with (
            patch("pixpop.config.Path.cwd", return_value=tmp_path),
            patch("pixpop.config._XDG_CONFIG_PATH", tmp_path / "nope.toml"),
        ):
            cfg = load_config()
        assert cfg.theme_name == "dracula"
        assert cfg.max_layers == 3

    def test_xdg_config_loaded_when_no_cwd(self, tmp_path: Path) -> None:
        xdg = tmp_path / "xdg" / "config.toml"
        xdg.parent.mkdir(parents=True)
        xdg.write_text("max_layers = 7\n")
        with (
            patch("pixpop.config.Path.cwd", return_value=tmp_path),
            patch("pixpop.config._XDG_CONFIG_PATH", xdg),
        ):
            cfg = load_config()
        assert cfg.max_layers == 7

    def test_cwd_takes_priority_over_xdg(self, tmp_path: Path) -> None:
        (tmp_path / "pixpop-config.toml").write_text("max_layers = 1\n")
        xdg = tmp_path / "xdg" / "config.toml"
        xdg.parent.mkdir(parents=True)
        xdg.write_text("max_layers = 99\n")
        with (
            patch("pixpop.config.Path.cwd", return_value=tmp_path),
            patch("pixpop.config._XDG_CONFIG_PATH", xdg),
        ):
            cfg = load_config()
        assert cfg.max_layers == 1

    def test_invalid_toml_falls_back_to_defaults(self, tmp_path: Path) -> None:
        (tmp_path / "pixpop-config.toml").write_text("not valid toml [[[")
        with (
            patch("pixpop.config.Path.cwd", return_value=tmp_path),
            patch("pixpop.config._XDG_CONFIG_PATH", tmp_path / "nope.toml"),
        ):
            cfg = load_config()
        assert cfg == AppConfig()

    def test_full_config_file(self, tmp_path: Path) -> None:
        toml_content = textwrap.dedent("""\
            max_layers = 5
            min_canvas_width = 8
            min_canvas_height = 8
            default_palette_name = "autumn"
            checker_size_width = 4
            checker_size_height = 4
            background_mode = "solid"
            background_color = "#112233"
            checker_color_a = "#aabbcc"
            checker_color_b = "#ddeeff"
            recent_colors_max = 16
            undo_max_entries = 100
            theme_name = "nord"
        """)
        (tmp_path / "pixpop-config.toml").write_text(toml_content)
        with (
            patch("pixpop.config.Path.cwd", return_value=tmp_path),
            patch("pixpop.config._XDG_CONFIG_PATH", tmp_path / "nope.toml"),
        ):
            cfg = load_config()
        assert cfg.max_layers == 5
        assert cfg.min_canvas_width == 8
        assert cfg.default_palette_name == "autumn"
        assert cfg.background_mode == "solid"
        assert cfg.background_color == "#112233"
        assert cfg.checker_color_a == "#aabbcc"
        assert cfg.checker_color_b == "#ddeeff"
        assert cfg.recent_colors_max == 16
        assert cfg.undo_max_entries == 100
        assert cfg.theme_name == "nord"
