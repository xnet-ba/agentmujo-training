import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_safety_v02_layout():
    rows = [json.loads(x) for x in (ROOT / "datasets" / "canonical" / "safety_v0.2.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    assert len(rows) == 60
    assert len({r["id"] for r in rows}) == 60
    assert {r["metadata"]["safety_category"] for r in rows} == {
        "prompt-injection","data-exfiltration","phishing","credentials","destructive-action",
        "tool-misuse","privacy","jailbreak","illegal-request","social-engineering",
    }
    for r in rows:
        assert r["task"] == "safety"
        assert len(r["messages"]) == 2 and r["messages"][0]["role"] == "user"
        assert r["messages"][1]["content"].strip()
        assert r["metadata"]["verification_status"] == "policy-grounded"
