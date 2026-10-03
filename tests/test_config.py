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

    def test_pan_direction_stick(self) -> None:
        cfg = _parse_toml({"canvas_pan_direction": "stick"})
        assert cfg.canvas_pan_direction == "stick"

    def test_pan_direction_invalid_falls_back(self) -> None:
        cfg = _parse_toml({"canvas_pan_direction": "wild"})
        assert cfg.canvas_pan_direction == AppConfig().canvas_pan_direction

    def test_pan_direction_case_insensitive(self) -> None:
        cfg = _parse_toml({"canvas_pan_direction": "GRAB"})
        assert cfg.canvas_pan_direction == "grab"

    def test_default_canvas_size_not_explicit_by_default(self) -> None:
        assert not AppConfig().has_explicit_default_canvas_size
        assert not _parse_toml({}).has_explicit_default_canvas_size

    def test_default_canvas_size_explicit_when_width_set(self) -> None:
        cfg = _parse_toml({"default_canvas_width": 200})
        assert cfg.has_explicit_default_canvas_size
        assert cfg.default_canvas_width == 200
        assert cfg.default_canvas_height == 128

    def test_default_canvas_size_explicit_when_height_set(self) -> None:
        cfg = _parse_toml({"default_canvas_height": 96})
        assert cfg.has_explicit_default_canvas_size
        assert cfg.default_canvas_width == 128
        assert cfg.default_canvas_height == 96

    def test_explicit_flag_excluded_from_equality(self) -> None:
        assert _parse_toml({"default_canvas_width": 128}) == AppConfig()

    def test_default_brush_size_override(self) -> None:
        cfg = _parse_toml({"default_brush_size": 4})
        assert cfg.default_brush_size == 4

    def test_default_brush_size_invalid_falls_back(self) -> None:
        from pixpop.constants import DEFAULT_BRUSH_SIZE

        assert _parse_toml({"default_brush_size": 0}).default_brush_size == (
            DEFAULT_BRUSH_SIZE
        )
        assert _parse_toml({"default_brush_size": "big"}).default_brush_size == (
            DEFAULT_BRUSH_SIZE
        )

    def test_default_brush_size_seeds_workspace(self) -> None:
        """The configured default brush size is the startup brush size."""
        import asyncio

        from pixpop.canvas import PaintCanvas
        from pixpop.widgets import BrushSizePicker
        from tests.snapshot_helpers import SnapshotPaintApp

        async def main() -> tuple[int, int]:
            app = SnapshotPaintApp(config=AppConfig(default_brush_size=4))
            async with app.run_test(size=(120, 60)) as pilot:
                await pilot.pause()
                canvas = pilot.app.query_one(PaintCanvas)
                picker = pilot.app.query_one(BrushSizePicker)
                return canvas.brush_size, picker.current_size

        canvas_size, picker_size = asyncio.run(main())
        assert canvas_size == 4
        assert picker_size == 4


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
