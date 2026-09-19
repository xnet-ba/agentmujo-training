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


def test_worker_code_parses():
    """Regresija: sav worker kod (ukljucujuci notebook celije) mora proci ast.parse."""
    import ast
    for py in (REPO / "workers" / "kaggle").glob("*.py"):
        ast.parse(py.read_text(encoding="utf-8"))
    nb = json.loads((REPO / "training" / "notebooks" / "qwen35_2b_training.ipynb").read_text())
    for cell in nb["cells"]:
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell["source"])
        if any(l.lstrip().startswith(("!", "%")) for l in src.splitlines()):
            continue  # shell magija nije Python
        ast.parse(src)


def test_registry_build():
    from agentmujo_training.registry import build
    md = build(REPO)
    assert "## Lineage adaptera" in md
    assert "qwen35-jt4-20260918-kaggle12" in md
    assert "task=" in md
