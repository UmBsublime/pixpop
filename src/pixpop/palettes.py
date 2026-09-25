"""Palette loader utilities."""

from __future__ import annotations

from pathlib import Path

from textual.color import Color as TextualColor

DEFAULT_COLORS: list[str] = [
    "#a0ddd3",
    "#6fb0b7",
    "#577f9d",
    "#4a5786",
    "#3e3b66",
    "#392945",
    "#2d1e2f",
    "#452e3f",
    "#5d4550",
    "#7b6268",
    "#9c807e",
    "#c3a79c",
    "#dbc9b4",
    "#fcecd1",
    "#aad795",
    "#64b082",
    "#488885",
    "#3f5b74",
    "#ebc8a7",
    "#d3a084",
    "#b87e6c",
    "#8f5252",
    "#6a3948",
    "#c57f79",
    "#ab597d",
    "#7c3d64",
    "#4e2b45",
    "#7a3b4f",
    "#a94b54",
    "#d8725e",
    "#f09f71",
    "#f7cf91",
]


def _palettes_dir() -> Path:
    """Locate the palettes directory in both source and installed layouts."""
    here = Path(__file__).resolve()
    package_relative = here.parent / "assets" / "palettes"  # installed wheel
    if package_relative.is_dir():
        return package_relative
    return here.parents[1] / "assets" / "palettes"  # source tree


def load_palettes() -> tuple[dict[str, list[str]], dict[str, str]]:
    """Load palettes from disk with default fallback."""
    palettes: dict[str, list[str]] = {"default": list(DEFAULT_COLORS)}
    labels: dict[str, str] = {"default": "Default"}

    palettes_dir = _palettes_dir()
    if not palettes_dir.exists():
        return palettes, labels

    for palette_file in sorted(palettes_dir.glob("*.hex")):
        try:
            colors = _parse_palette_hex(palette_file.read_text(encoding="utf-8"))
        except OSError, UnicodeDecodeError:
            # A single unreadable palette file must not kill the others.
            continue
        valid_colors: list[str] = []
        for value in colors:
            candidate = value if value.startswith("#") else f"#{value}"
            try:
                TextualColor.parse(candidate)
            except ValueError:
                continue
            valid_colors.append(candidate)
        if not valid_colors:
            continue
        key = palette_file.stem
        palettes[key] = valid_colors
        labels[key] = key

    return palettes, labels


def _parse_palette_hex(text: str) -> list[str]:
    colors: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            line = line[1:]
        if line:
            colors.append(line)
    return colors
