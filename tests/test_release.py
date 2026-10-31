import json
from pathlib import Path

from agentmujo_training.datasets.release import build_release


def _sample(i=1):
    return {"id": f"amj-fc-{i:04d}", "version": "0.1.0", "language": "bs-ijekavica",
            "task": "function-calling", "difficulty": "easy",
            "messages": [{"role": "user", "content": f"test {i}"},
                         {"role": "assistant", "content": "ok"}],
            "metadata": {"quality_tier": "GOLD"}}


def test_release_build(tmp_path):
    canon = tmp_path / "datasets" / "canonical"
    canon.mkdir(parents=True)
    (canon / "bosnian_core_v0.1.jsonl").write_text(json.dumps(_sample(1)) + "\n")
    (canon / "dpo_v0.5.jsonl").write_text(json.dumps({"id": "d1", "prompt": "p", "chosen": "a", "rejected": "b"}) + "\n")
    r = build_release(tmp_path, "0.1.0", tmp_path / "rel")
    assert r["ok"] and r["total_rows"] == 2
    assert "bosnian-language" in r["covered_categories"]
    assert "knowledge" in r["gaps"] and "coding" in r["gaps"]
    assert (tmp_path / "rel" / "RELEASE.json").exists()
    assert (tmp_path / "rel" / "DATASET_CARD.md").exists()
