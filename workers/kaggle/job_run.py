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
        elif cfg.get("mode") == "dpo":
            metrics = _train_dpo(cfg, out)
        else:
            metrics = _train_lora(cfg, out)

        manifest = {**meta, "config": cfg, "metrics": metrics,
                    "finished_at": _utcnow(), "status": "done",
                    "env": {"python": platform.python_version(),
                            "torch": torch.__version__,
                            "cuda": torch.version.cuda, "gpu": status["gpu"],
                            **_lib_versions()}}
        _write(out / "manifest.json", manifest)
        _write(out / "metrics.json", metrics)
        status.update({"status": "done", "finished_at": manifest["finished_at"], "error": None})
        _write(out / "status.json", status)
        print(f"JOB {meta['job_id']} DONE")
        return 0
    except Exception as e:
        import traceback as _tb
        (out / "error_traceback.txt").write_text(_tb.format_exc()[-20000:])
        status.update({"status": "failed", "finished_at": _utcnow(),
                       "error": f"{type(e).__name__}: {e}"})
        _write(out / "status.json", status)
        print(f"JOB {meta.get('job_id', '?')} FAILED: {e}")
        return 1


def _lib_versions() -> dict:
    out = {}
    for lib in ("transformers", "peft", "trl", "accelerate", "datasets"):
        try:
            out[lib] = __import__(lib).__version__
        except Exception:
            out[lib] = None
    return out


def _summarize_history(log_history: list[dict]) -> dict:
    """Train/eval krivulje iz trainer loga — osnova za overfitting detekciju."""
    tr = [e["loss"] for e in log_history if e.get("loss") is not None]
    ev = [e["eval_loss"] for e in log_history if e.get("eval_loss") is not None]
    out = {"train_loss": float(tr[-1]) if tr else 0.0,
           "train_loss_mean": float(sum(tr) / len(tr)) if tr else 0.0}
    if ev:
        out["eval_loss_final"] = float(ev[-1])
        out["eval_loss_min"] = float(min(ev))
        if tr:
            out["train_eval_gap"] = round(float(ev[-1]) - float(tr[-1]), 4)
    return out


def _resolve_adapter(path: str) -> str:
    """Vrati dir sa adapter_config.json; ako zadana putanja ne postoji,
    pretrazi /kaggle/input/**/outputs/adapter (kernel output mount varira)."""
    import glob as _glob
    from pathlib import Path as _P
    if (_P(path) / "adapter_config.json").exists():
        return path
    cands = sorted(_glob.glob("/kaggle/input/**/outputs/adapter", recursive=True))
    cands = [c for c in cands if (_P(c) / "adapter_config.json").exists()]
    if not cands:
        raise ValueError(f"adapter nije pronadjen: {path} (ni glob /kaggle/input/**/outputs/adapter)")
    if len(cands) > 1:
        print(f"WARN: vise adaptera {cands} — uzimam prvi")
    print(f"INFO: adapter resolve {path} -> {cands[0]}")
    return cands[0]


def _train_lora(cfg: dict, out: Path) -> dict:
    """Minimalni LoRA SFT (TRL) sa resume podrškom; vraća metrike."""
    import sys as _sys
    from pathlib import Path as _P
    _sys.path.insert(0, str(_P(__file__).resolve().parents[2] / "src"))
    from agentmujo_training.training import sample_to_chatml
    from datasets import load_dataset
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import LoraConfig
    from trl import SFTTrainer, SFTConfig
    import inspect as _inspect

    tok = AutoTokenizer.from_pretrained(cfg["model_name"], trust_remote_code=True)
    # Eksplicitni json load preko hf:// (deterministicki, imun na repo builder
    # inference razlike medju verzijama datasets liba); fallback na repo stil.
    from datasets import load_dataset
    repo, rev = cfg["dataset"], cfg.get("dataset_revision") or "main"
    data_glob = cfg.get("data_file", "data/*.jsonl")
    try:
        ds = load_dataset("json", split=cfg.get("split", "train"),
                          data_files=f"hf://datasets/{repo}@{rev}/{data_glob}")
    except Exception as e:
        print(f"WARN: hf:// load pao ({e}) — fallback na repo stil")
        ds = load_dataset(repo, revision=cfg.get("dataset_revision"),
                          split=cfg.get("split", "train"))
    if cfg.get("max_samples"):
        ds = ds.select(range(min(cfg["max_samples"], len(ds))))
    # Validacija na zamrznutom valid splitu (overfitting detekcija).
    eval_ds = None
    if cfg.get("eval_file"):
        from datasets import load_dataset as _load
        if cfg["eval_file"].startswith("hf://"):
            eval_ds = _load("json", split="train", data_files=cfg["eval_file"])
        else:
            eval_ds = _load("json", split="train", data_files=cfg["eval_file"])
        from agentmujo_training.training import sample_to_chatml as _c2  # noqa: već importano gore
        eval_ds = eval_ds.map(lambda r: {"text": tok.apply_chat_template(
            _c2(r), tokenize=False, add_generation_prompt=False)},
            remove_columns=[c for c in eval_ds.column_names if c != "text"])
    # Kanonski messages[] -> nativni Qwen chat tekst (tool_calls u <tool_call> XML).
    # add_generation_prompt=False: uzorci su kompletne konverzacije sa finalnim odgovorom.
    # (sys.path je postavljen na vrhu funkcije.)
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
    if cfg.get("base_adapter"):
        # Faza 2+: nastavak treninga na postojecem adapteru.
        # Putanja varira (/kaggle/input/notebooks/... vs /kaggle/input/...),
        # pa se nedostajuca putanja trazi globom po /kaggle/input.
        from peft import PeftModel
        adapter_path = _resolve_adapter(cfg["base_adapter"])
        model = PeftModel.from_pretrained(model, adapter_path, is_trainable=True)
        peft_cfg = None
        print(f"INFO: nastavljam sa adaptera {adapter_path}")
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
        "loss_type": cfg.get("loss_type", "nll"),
        "eval_strategy": "steps" if eval_ds is not None else "no",
        "eval_steps": cfg.get("eval_steps", 25),
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
                             eval_dataset=eval_ds,
                             peft_config=peft_cfg, processing_class=tok)
    except TypeError:  # starije TRL verzije: tokenizer= umjesto processing_class=
        trainer = SFTTrainer(model=model, args=args, train_dataset=ds,
                             eval_dataset=eval_ds,
                             peft_config=peft_cfg, tokenizer=tok)
    trainer.train(resume_from_checkpoint=cfg.get("resume_from_checkpoint"))
    trainer.save_model(str(out / "adapter"))
    tr = _summarize_history(trainer.state.log_history)
    metrics = {"mode": "sft", **tr,
               "eval": {"note": "AgentMujo-Bench (8 kategorija A-H) pokrenuti "
                                "nakon treninga; rule-based dio ovdje, manual/LLM-sudija na Oracleu"}}
    _write(out / "metrics.json", metrics)
    return metrics


def _train_dpo(cfg: dict, out: Path) -> dict:
    """DPO preferencije nad SFT adapterom (TRL), vraća metrike.
    Dataset: {prompt, chosen, rejected} (agentmujo-dpo-01).
    Počinje sa base_adaptera (obicno najbolji joint adapter)."""
    import sys as _sys
    from pathlib import Path as _P
    _sys.path.insert(0, str(_P(__file__).resolve().parents[2] / "src"))
    from datasets import load_dataset
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import LoraConfig, PeftModel
    from trl import DPOTrainer, DPOConfig
    import inspect as _inspect

    DPO_SYSTEM = ("Ti si AgentMujo, asistent za administraciju Linux servera. "
                  "Odgovaraj na bosanskom jeziku (ijekavica). "
                  "Za zadatke sa alatom odgovori kanonskim formatom.")
    tok = AutoTokenizer.from_pretrained(cfg["model_name"], trust_remote_code=True)
    repo, rev = cfg["dataset"], cfg.get("dataset_revision") or "main"
    data_glob = cfg.get("data_file", "data/*.jsonl")
    try:
        ds = load_dataset("json", split=cfg.get("split", "train"),
                          data_files=f"hf://datasets/{repo}@{rev}/{data_glob}")
    except Exception as e:
        print(f"WARN: hf:// load pao ({e}) — fallback na repo stil")
        ds = load_dataset(repo, revision=cfg.get("dataset_revision"),
                          split=cfg.get("split", "train"))
    if cfg.get("max_samples"):
        ds = ds.select(range(min(cfg["max_samples"], len(ds))))

    def _fmt(row):
        base = [{"role": "system", "content": DPO_SYSTEM},
                {"role": "user", "content": row["prompt"]}]
        return {"prompt": tok.apply_chat_template(base, tokenize=False, add_generation_prompt=True),
                "chosen": row["chosen"], "rejected": row["rejected"]}
    ds = ds.map(_fmt, remove_columns=[c for c in ds.column_names if c not in ()])
    ds = ds.remove_columns([c for c in ds.column_names if c not in ("prompt", "chosen", "rejected")])

    model = AutoModelForCausalLM.from_pretrained(
        cfg["model_name"], trust_remote_code=True,
        torch_dtype="bfloat16", device_map="auto")
    if not cfg.get("base_adapter"):
        raise ValueError("DPO trazi base_adapter (SFT polaziste)")
    adapter_path = _resolve_adapter(cfg["base_adapter"])
    model = PeftModel.from_pretrained(model, adapter_path, is_trainable=True)
    print(f"INFO: DPO sa adaptera {adapter_path}")
    peft_cfg = LoraConfig(r=cfg.get("lora_r", 16), lora_alpha=cfg.get("lora_alpha", 32),
                          lora_dropout=cfg.get("lora_dropout", 0.05),
                          target_modules=cfg.get("target_modules",
                                                 ["q_proj", "k_proj", "v_proj", "o_proj"]),
                          task_type="CAUSAL_LM")
    wanted = {
        "output_dir": str(out / "checkpoints"), "seed": cfg.get("seed", 42),
        "per_device_train_batch_size": cfg.get("per_device_train_batch_size", 1),
        "gradient_accumulation_steps": cfg.get("gradient_accumulation_steps", 16),
        "learning_rate": cfg.get("learning_rate", 5e-6),
        "num_train_epochs": cfg.get("num_train_epochs", 1),
        "warmup_ratio": cfg.get("warmup_ratio", 0.05),
        "weight_decay": cfg.get("weight_decay", 0.0),
        "logging_steps": cfg.get("logging_steps", 5),
        "save_steps": cfg.get("save_steps", 30),
        "save_total_limit": cfg.get("save_total_limit", 2),
        "gradient_checkpointing": cfg.get("gradient_checkpointing", True),
        "bf16": True,
        "beta": cfg.get("beta", 0.1),
        "max_length": cfg.get("max_seq_length", 4096),
        "max_prompt_length": cfg.get("max_prompt_length", 1024),
    }
    supported = set(_inspect.signature(DPOConfig.__init__).parameters)
    dropped = sorted(k for k in wanted if k not in supported)
    if dropped:
        print(f"WARN: TRL {DPOConfig} ne podržava {dropped} — izbačeno")
    args = DPOConfig(**{k: v for k, v in wanted.items() if k in supported})
    try:
        trainer = DPOTrainer(model=model, args=args, train_dataset=ds,
                             peft_config=peft_cfg, processing_class=tok)
    except TypeError:
        trainer = DPOTrainer(model=model, args=args, train_dataset=ds,
                             peft_config=peft_cfg, tokenizer=tok)
    trainer.train()
    trainer.save_model(str(out / "adapter"))
    tr = _summarize_history(trainer.state.log_history)
    metrics = {"mode": "dpo", **tr,
               "eval": {"note": "DPO reward/loss ovdje; bench na Oracleu nakon mergea"}}
    _write(out / "metrics.json", metrics)
    return metrics


if __name__ == "__main__":
    raise SystemExit(main())
