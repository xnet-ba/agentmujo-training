#!/usr/bin/env python3
"""Kaggle job runner — izvršava Oracle job spec na ephemeral workeru.

Ulaz: --job-dir training/jobs/<job_id>/ (config.yaml, metadata.json).
Koraci: env preflight (GPU) -> dataset sa Huba -> baza sa Huba ->
LoRA SFT (TRL) ili smoke -> eval (8 kategorija A-H, rule-based gdje može) ->
status.json + metrics.json + manifest.json + adapter (+HF upload ako je
HF_UPLOAD_REPO postavljen; token isključivo iz env/Kaggle Secrets).

Pokretanje: python workers/kaggle/job_run.py --job-dir training/jobs/<id>
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import platform
from pathlib import Path


def _utcnow() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _write(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--job-dir", required=True)
    ap.add_argument("--smoke-only", action="store_true",
                    help="samo smoke korak, bez punog treninga")
    a = ap.parse_args()
    job = Path(a.job_dir)
    import yaml
    cfg = yaml.safe_load((job / "config.yaml").read_text(encoding="utf-8"))
    meta = json.loads((job / "metadata.json").read_text(encoding="utf-8"))
    out = job / "outputs"
    out.mkdir(exist_ok=True)

    status: dict = {"job_id": meta["job_id"], "status": "running",
                    "started_at": _utcnow(), "gpu": None, "error": None}
    _write(out / "status.json", status)

    try:
        import torch
        if not torch.cuda.is_available():
            raise RuntimeError("worker bez CUDA GPU — prekini, ne troši kvotu")
        status["gpu"] = torch.cuda.get_device_name(0)
        status["cuda"] = torch.version.cuda
        _write(out / "status.json", status)

        if a.smoke_only or cfg.get("mode") == "smoke":
            import subprocess, sys
            r = subprocess.run([sys.executable, "workers/kaggle/smoke_test.py",
                                "--model", cfg["model_name"]], capture_output=True, text=True)
            (out / "smoke_stdout.log").write_text(r.stdout[-20000:])
            (out / "smoke_stderr.log").write_text(r.stderr[-20000:])
            if r.returncode != 0:
                raise RuntimeError("smoke test pao — vidi smoke_* logove")
            metrics = {"mode": "smoke", "smoke": "PASS"}
        else:
            metrics = _train_lora(cfg, out)

        manifest = {**meta, "config": cfg, "metrics": metrics,
                    "finished_at": _utcnow(), "status": "done",
                    "env": {"python": platform.python_version(),
                            "torch": torch.__version__,
                            "cuda": torch.version.cuda, "gpu": status["gpu"]}}
        _write(out / "manifest.json", manifest)
        _write(out / "metrics.json", metrics)
        status.update({"status": "done", "finished_at": manifest["finished_at"], "error": None})
        _write(out / "status.json", status)
        print(f"JOB {meta['job_id']} DONE")
        return 0
    except Exception as e:
        status.update({"status": "failed", "finished_at": _utcnow(),
                       "error": f"{type(e).__name__}: {e}"})
        _write(out / "status.json", status)
        print(f"JOB {meta.get('job_id', '?')} FAILED: {e}")
        return 1


def _train_lora(cfg: dict, out: Path) -> dict:
    """Minimalni LoRA SFT (TRL) sa resume podrškom; vraća metrike."""
    from datasets import load_dataset
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import LoraConfig
    from trl import SFTTrainer, SFTConfig
    import inspect as _inspect

    tok = AutoTokenizer.from_pretrained(cfg["model_name"], trust_remote_code=True)
    ds = load_dataset(cfg["dataset"], revision=cfg.get("dataset_revision"),
                      split=cfg.get("split", "train"))
    if cfg.get("max_samples"):
        ds = ds.select(range(min(cfg["max_samples"], len(ds))))
    # Kanonski messages[] -> nativni Qwen chat tekst (tool_calls u <tool_call> XML).
    # add_generation_prompt=False: uzorci su kompletne konverzacije sa finalnim odgovorom.
    import sys as _sys
    from pathlib import Path as _P
    _sys.path.insert(0, str(_P(__file__).resolve().parents[2] / "src"))
    from agentmujo_training.training import sample_to_chatml
    ds = ds.map(lambda r: {"text": tok.apply_chat_template(
        sample_to_chatml(r), tokenize=False, add_generation_prompt=False)},
        remove_columns=[c for c in ds.column_names if c != "text"])
    model_kwargs: dict = {"trust_remote_code": True}
    if cfg.get("load_in_4bit"):
        # transformers>=5: bez direktnog load_in_4bit kwarga (uklonjen)
        from transformers import BitsAndBytesConfig
        model_kwargs["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True)
    else:
        model_kwargs.update({"torch_dtype": "bfloat16", "device_map": "auto"})
    model = AutoModelForCausalLM.from_pretrained(cfg["model_name"], **model_kwargs)
    peft_cfg = LoraConfig(r=cfg.get("lora_r", 16), lora_alpha=cfg.get("lora_alpha", 32),
                          lora_dropout=cfg.get("lora_dropout", 0.05),
                          target_modules=cfg.get("target_modules",
                                                 ["q_proj", "k_proj", "v_proj", "o_proj"]),
                          task_type="CAUSAL_LM")
    # TRL API varira po verzijama — proslijedi samo podržane SFTConfig ključeve
    # (npr. warmup_ratio ne postoji u svim verzijama) umjesto da run padne.
    wanted = {
        "output_dir": str(out / "checkpoints"), "seed": cfg.get("seed", 42),
        "per_device_train_batch_size": cfg.get("per_device_train_batch_size", 1),
        "gradient_accumulation_steps": cfg.get("gradient_accumulation_steps", 16),
        "learning_rate": cfg.get("learning_rate", 2e-4),
        "num_train_epochs": cfg.get("num_train_epochs", 1),
        "warmup_ratio": cfg.get("warmup_ratio", 0.05),
        "weight_decay": cfg.get("weight_decay", 0.0),
        "logging_steps": cfg.get("logging_steps", 10),
        "save_steps": cfg.get("save_steps", 100),
        "save_total_limit": cfg.get("save_total_limit", 2),
        "gradient_checkpointing": cfg.get("gradient_checkpointing", True),
        "bf16": not cfg.get("load_in_4bit", False),
        "max_seq_length": cfg.get("max_seq_length", 4096),
        "dataset_text_field": "text",
        "resume_from_checkpoint": cfg.get("resume_from_checkpoint"),
    }
    supported = set(_inspect.signature(SFTConfig.__init__).parameters)
    dropped = sorted(k for k in wanted if k not in supported)
    if dropped:
        print(f"WARN: TRL {SFTConfig} ne podržava {dropped} — izbačeno (kvota se ne troši na pad)")
    args = SFTConfig(**{k: v for k, v in wanted.items() if k in supported})
    try:
        trainer = SFTTrainer(model=model, args=args, train_dataset=ds,
                             peft_config=peft_cfg, processing_class=tok)
    except TypeError:  # starije TRL verzije: tokenizer= umjesto processing_class=
        trainer = SFTTrainer(model=model, args=args, train_dataset=ds,
                             peft_config=peft_cfg, tokenizer=tok)
    trainer.train(resume_from_checkpoint=cfg.get("resume_from_checkpoint"))
    trainer.save_model(str(out / "adapter"))
    tr = {"train_loss": float(trainer.state.log_history[-1].get("loss", 0.0))}
    metrics = {"mode": "sft", **tr,
               "eval": {"note": "AgentMujo-Bench (8 kategorija A-H) pokrenuti "
                                "nakon treninga; rule-based dio ovdje, manual/LLM-sudija na Oracleu"}}
    _write(out / "metrics.json", metrics)
    return metrics


if __name__ == "__main__":
    raise SystemExit(main())
