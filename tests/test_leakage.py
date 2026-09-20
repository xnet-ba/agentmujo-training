import sys
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from agentmujo_training.benchmark import load_cases  # noqa: E402


def _user_texts(path: Path) -> set[str]:
    out = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        for m in json.loads(line)["messages"]:
            if m.get("role") == "user":
                out.add(m["content"].strip().lower())
    return out


def test_no_literal_bench_overlap():
    """Nijedan bench prompt ne smije doslovno postojati u trening podacima."""
    bench = {c.prompt.strip().lower()
             for c in load_cases(REPO / "benchmark" / "cases_v0.5.jsonl")}
    train = (_user_texts(REPO / "datasets" / "canonical" / "function_calling_v0.1.jsonl")
             | _user_texts(REPO / "datasets" / "canonical" / "agentic_terminal_v0.1.jsonl"))
    assert not (bench & train), f"kontaminacija bencha: {bench & train}"


def test_splits_disjoint():
    for name in ("fc", "ag"):
        ids = []
        for split in ("train.jsonl", "valid.jsonl", "test.jsonl"):
            p = REPO / "datasets" / "splits" / name / split
            rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
            ids.append({r["id"] for r in rows})
        assert not (ids[0] & ids[1]) and not (ids[0] & ids[2]) and not (ids[1] & ids[2])
