from pathlib import Path

from agentmujo_training.datasets.sources import load_sources, validate_sources

REPO = Path(__file__).resolve().parents[1]


def test_sources_registry_valid():
    sources = load_sources(REPO)
    assert len(sources) >= 8
    ids = [s["id"] for s in sources]
    assert len(ids) == len(set(ids))
    assert validate_sources(REPO) == []


def test_sources_validation_catches_bad(tmp_path):
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "sources.yaml").write_text(
        "sources:\n  - id: x\n    name: X\n    type: t\n    url: https://x\n"
        "    access: public\n    status: pending\n    categories: [a]\n",
        encoding="utf-8",
    )
    issues = validate_sources(tmp_path)
    assert any("license" in i for i in issues)
