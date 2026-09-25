"""Helpers for generating adjective-noun names."""

from __future__ import annotations

import random
from functools import lru_cache
from pathlib import Path


def _assets_dir() -> Path:
    """Locate the assets directory in both source and installed layouts.

    Source tree:  <repo>/src/assets  (sibling of the pixpop package).
    Wheel layout: <site-packages>/pixpop/assets  (force-included).
    """
    here = Path(__file__).resolve()
    package_relative = here.parent / "assets"  # installed: pixpop/assets
    if package_relative.is_dir():
        return package_relative
    return here.parents[1] / "assets"  # source: src/assets


_ASSETS_DIR = _assets_dir()
_ADJECTIVES_FILE = _ASSETS_DIR / "adjectives.txt"
_NOUNS_FILE = _ASSETS_DIR / "nouns.txt"

# Fallbacks keep the app working if the asset files are missing (e.g. a
# wheel that doesn't bundle src/assets).
_FALLBACK_ADJECTIVES = ("brave", "calm", "clever", "eager", "gentle", "swift")
_FALLBACK_NOUNS = ("canvas", "falcon", "harbor", "meadow", "pixel", "willow")


def _load_word_list(path: Path) -> tuple[str, ...]:
    """Load a list of words from a newline-delimited text file."""
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    return tuple(line for line in lines if line and not line.startswith("#"))


@lru_cache(maxsize=1)
def _adjectives() -> tuple[str, ...]:
    try:
        words = _load_word_list(_ADJECTIVES_FILE)
    except OSError:
        return _FALLBACK_ADJECTIVES
    return words or _FALLBACK_ADJECTIVES


@lru_cache(maxsize=1)
def _nouns() -> tuple[str, ...]:
    try:
        words = _load_word_list(_NOUNS_FILE)
    except OSError:
        return _FALLBACK_NOUNS
    return words or _FALLBACK_NOUNS


def get_adjective_noun_name(rng: random.Random | None = None) -> str:
    """Return a hyphenated adjective-noun name.

    Args:
        rng: Optional random generator for deterministic selection.

    Returns:
        A name in the format "adjective-noun".
    """
    source = rng if rng is not None else random
    return f"{source.choice(_adjectives())}-{source.choice(_nouns())}"
