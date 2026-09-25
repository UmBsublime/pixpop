"""Application configuration loaded from pixpop-config.toml."""

from __future__ import annotations

import sys
import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path

_CONFIG_FILENAME = "pixpop-config.toml"
_XDG_CONFIG_PATH = Path.home() / ".config" / "pixpop" / "config.toml"

_VALID_BACKGROUND_MODES = frozenset({"solid", "checker"})


@dataclass(frozen=True)
class AppConfig:
    """Application-wide configuration with sensible defaults."""

    max_layers: int = 10
    min_canvas_width: int = 4
    min_canvas_height: int = 4
    default_canvas_width: int = 128
    default_canvas_height: int = 128
    max_canvas_width: int = 1024
    max_canvas_height: int = 1024
    default_palette_name: str = "default"
    checker_size_width: int = 16
    checker_size_height: int = 16
    background_mode: str = "checker"
    background_color: str = "#2b2b2b"
    checker_color_a: str = "#2b2b2b"
    checker_color_b: str = "#313131"
    recent_colors_max: int = 8
    undo_max_entries: int = 50
    theme_name: str = "twilight-bog"


def _coerce_int(value: object, fallback: int) -> int:
    """Coerce *value* to a positive int, falling back on failure."""
    try:
        result = int(value)  # type: ignore[arg-type]
        return result if result > 0 else fallback
    except TypeError, ValueError:
        return fallback


def _coerce_color(value: object, fallback: str) -> str:
    """Return *value* if it looks like a hex color, else *fallback*."""
    if isinstance(value, str) and value.startswith("#") and len(value) in (4, 7):
        try:
            int(value[1:], 16)
            return value
        except ValueError:
            pass
    return fallback


def _coerce_str(value: object, fallback: str) -> str:
    return value if isinstance(value, str) and value else fallback


def _parse_toml(data: dict[str, object]) -> AppConfig:
    """Build an :class:`AppConfig` from raw TOML data, coercing types."""
    defaults = AppConfig()
    kwargs: dict[str, object] = {}

    int_fields = {
        f.name
        for f in fields(AppConfig)
        if f.type == "int"
        or f.default is not field(default=0)
        and isinstance(f.default, int)
    }
    color_fields = {"background_color", "checker_color_a", "checker_color_b"}

    for f in fields(AppConfig):
        raw = data.get(f.name)
        if raw is None:
            continue
        fallback = getattr(defaults, f.name)
        if f.name in color_fields:
            kwargs[f.name] = _coerce_color(raw, fallback)
        elif f.name in int_fields:
            kwargs[f.name] = _coerce_int(raw, fallback)
        elif f.name == "background_mode":
            candidate = str(raw).lower() if isinstance(raw, str) else fallback
            kwargs[f.name] = (
                candidate if candidate in _VALID_BACKGROUND_MODES else fallback
            )
        else:
            kwargs[f.name] = _coerce_str(raw, fallback)

    return AppConfig(**kwargs)  # type: ignore[arg-type]


def load_config() -> AppConfig:
    """Load configuration from the first TOML file found.

    Search order:
        1. ``./pixpop-config.toml`` (current working directory)
        2. ``~/.config/pixpop/config.toml``
        3. Built-in defaults

    Returns:
        A fully-populated :class:`AppConfig`.
    """
    candidates = [Path.cwd() / _CONFIG_FILENAME, _XDG_CONFIG_PATH]
    for path in candidates:
        if path.is_file():
            try:
                data = tomllib.loads(path.read_text(encoding="utf-8"))
                return _parse_toml(data)
            except Exception as exc:  # noqa: BLE001
                print(
                    f"pixpop: warning: ignoring {path}: {exc}",
                    file=sys.stderr,
                )
    return AppConfig()
