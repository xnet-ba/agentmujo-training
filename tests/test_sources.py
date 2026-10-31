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


def test_scan_own_file(tmp_path):
    from agentmujo_training.datasets.sources import scan_sources
    (tmp_path / "configs").mkdir()
    (tmp_path / "datasets" / "canonical").mkdir(parents=True)
    (tmp_path / "configs" / "sources.yaml").write_text(
        "sources:\n  - id: own\n    name: Own\n    type: internal\n    url: file://datasets/canonical\n"
        "    license: internal\n    access: internal\n    status: approved\n    categories: [bosnian-language]\n",
        encoding="utf-8",
    )
    r = scan_sources(tmp_path, only=["own"])
    assert len(r) == 1 and r[0]["reachable"] is True
