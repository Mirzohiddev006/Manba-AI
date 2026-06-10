"""pytest konfiguratsiya: --accuracy-threshold darvozasi (CI da 0.97)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--accuracy-threshold",
        action="store",
        type=float,
        default=0.97,
        help="Etalon to'plamda minimal aniqlik (CI darvozasi)",
    )


@pytest.fixture(scope="session")
def accuracy_threshold(request: pytest.FixtureRequest) -> float:
    return float(request.config.getoption("--accuracy-threshold"))


@pytest.fixture(scope="session")
def etalon_pairs() -> list[dict]:
    """Barcha fixture fayllardagi (input, expected, type) juftliklar."""
    pairs: list[dict] = []
    for path in sorted(FIXTURES_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for stype, items in data.items():
            if stype.startswith("_"):
                continue
            for item in items:
                pairs.append({**item, "type": stype, "file": path.name})
    return pairs
