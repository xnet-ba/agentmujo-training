import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _rows():
    return [json.loads(x) for x in (ROOT / "benchmarks" / "agentic_eval_v0.1.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]


def test_agentic_eval_benchmark_file():
    rows = _rows()
    assert len(rows) == 50
    assert len({r["id"] for r in rows}) == 50
    assert {r["category"] for r in rows} == {"sql","files","web","office","security","multi-step","bosnian","data","tool-selection","verification"}
    for r in rows:
        assert r["task"] == "agentic-evaluation"
        assert r["goal"] and r["success_criteria"] and r["verification"]
        assert isinstance(r["allowed_tools"], list) and isinstance(r["expected_tools"], list)
        assert r["metadata"]["held_out"] is True
        assert r["metadata"]["license"] == "Apache-2.0"


def test_agentic_eval_security_requires_no_silent_tool():
    sec = [r for r in _rows() if r["category"] == "security"]
    assert len(sec) == 5
    for r in sec:
        assert r["allowed_tools"] == [] and r["expected_tools"] == []
