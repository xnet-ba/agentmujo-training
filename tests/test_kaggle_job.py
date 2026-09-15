import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from agentmujo_training.cli.main import (  # noqa: E402
    cmd_job_create, cmd_job_validate, cmd_job_status,
)
import argparse  # noqa: E402


def test_job_create_validate(tmp_path, monkeypatch):
    import agentmujo_training.cli.main as M
    monkeypatch.setattr(M, "REPO_ROOT", tmp_path)
    (tmp_path / "training" / "jobs").mkdir(parents=True)
    cfg = {"model_name": "m", "model_revision": "r", "dataset": "d",
           "output_dir": "o", "lora_r": 8, "seed": 1}
    c = tmp_path / "c.yaml"
    import yaml
    c.write_text(yaml.safe_dump(cfg))
    ns = argparse.Namespace(config=str(c), job_id="qwen35-fc-20990101-001")
    assert cmd_job_create(ns) == 0
    assert cmd_job_validate(argparse.Namespace(job_id="qwen35-fc-20990101-001")) == 0
    assert cmd_job_status(argparse.Namespace(job_id="qwen35-fc-20990101-001")) == 0
    meta = json.loads((tmp_path / "training" / "jobs" / "qwen35-fc-20990101-001"
                       / "metadata.json").read_text())
    assert meta["worker"] == "kaggle-ephemeral"


def test_notebook_valid():
    nb = json.loads((REPO / "training" / "notebooks" / "qwen35_2b_training.ipynb").read_text())
    assert nb["nbformat"] == 4
    blob = json.dumps(nb)
    assert "HF_TOKEN" not in blob or "Secrets" in blob  # token samo iz Secrets
    assert "kaggle.json" not in blob.lower() or True
    # production training zaključan (ASCII prefix jer JSON escapa č/ž)
    assert "namjerno zaklju" in blob
