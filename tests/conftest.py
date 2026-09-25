"""Pytest configuration for snapshot tests."""

from pathlib import Path

import pytest
import pytest_textual_snapshot as pts

from pixpop import workspace


def pytest_configure() -> None:
    """Patch snapshot report path generation for Windows path types."""

    def _node_to_report_path(node) -> Path:
        tempdir = pts.get_tempdir()
        path, _, name = node.reportinfo()
        path = Path(path)
        temp = Path(path.parent)
        base: list[str] = []
        while temp != temp.parent and temp.name != "tests":
            base.append(temp.name)
            temp = temp.parent
        parts: list[str] = []
        if base:
            parts.append("_".join(reversed(base)))
        parts.append(path.name.replace(".", "_"))
        parts.append(name.replace("[", "_").replace("]", "_"))
        return Path(tempdir.name) / "_".join(parts)

    pts.node_to_report_path = _node_to_report_path


@pytest.fixture(autouse=True)
def _stable_canvas_names(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force deterministic canvas names for snapshot tests."""
    monkeypatch.setattr(
        workspace, "get_adjective_noun_name", lambda rng=None: "test-canvas"
    )
