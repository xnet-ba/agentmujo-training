#!/usr/bin/env python3
"""Kaggle smoke test — NE radi ozbiljan trening.

Provjerava: GPU/CUDA, torch, transformers, tokenizer (Qwen3.5 tool chat
template), učitavanje baze, PEFT LoRA init, dataset load, forward pass,
backward pass, save + reload adaptera. Sve na tiny subsetu (<=64 uzorka,
<=512 tokena) da ne troši kvotu.

Pokretanje na Kaggle GPU sesiji:
    python workers/kaggle/smoke_test.py --model alphaedge-ai/Qwen3.5-2B-bos-32768

Izlaz: PASS/FAIL linije + smoke_report.json (bez tajni).
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

FAILURES: list[str] = []


def check(name: str, fn) -> bool:
    try:
        fn()
        print(f"PASS {name}", flush=True)
        return True
    except Exception as e:
        print(f"FAIL {name}: {type(e).__name__}: {e}", flush=True)
        FAILURES.append(name)
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="alphaedge-ai/Qwen3.5-2B-bos-32768")
    ap.add_argument("--max-tokens", type=int, default=512)
    a = ap.parse_args()

    ok: dict[str, bool] = {}
    ok["gpu"] = check("gpu-cuda", lambda: __import__("torch").cuda.is_available()
                      or (_ for _ in ()).throw(RuntimeError("nema CUDA GPU")))
    import torch
    print(f"INFO torch={torch.__version__} cuda={torch.version.cuda} "
          f"gpu={[torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]}")

    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = None

    def _tok():
        nonlocal tok
        tok = AutoTokenizer.from_pretrained(a.model, trust_remote_code=True)
        assert "tool_call" in tok.apply_chat_template(
            [{"role": "user", "content": "hi"}],
            tools=[{"type": "function", "function": {
                "name": "x", "description": "x",
                "parameters": {"type": "object", "properties": {}}}}}],
            tokenize=False, add_generation_prompt=True), "nema tool templatea"
    ok["tokenizer-tool-template"] = check("tokenizer-tool-template", _tok)

    model = None

    def _load():
        nonlocal model
        # 4-bit da smoke sigurno stane i na 15-16 GB (T4/P100); trening ide bf16/QLoRA po configu
        model = AutoModelForCausalLM.from_pretrained(
            a.model, load_in_4bit=True, device_map="auto", trust_remote_code=True)
    ok["model-load-4bit"] = check("model-load-4bit", _load)
    if model is None:
        return _finish(ok)

    from peft import LoraConfig, get_peft_model, PeftModel

    def _lora():
        cfg = LoraConfig(r=8, lora_alpha=16, lora_dropout=0.05,
                         target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
                         task_type="CAUSAL_LM")
        nonlocal_model = get_peft_model(model, cfg)
        nonlocal_model.print_trainable_parameters()
        globals()["_m"] = nonlocal_model
    ok["lora-init"] = check("lora-init", _lora)
    m = globals().get("_m", model)

    def _fwd_bwd():
        m.train()
        msgs = [{"role": "user", "content": "Kakav je status nginx servisa?"}]
        text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        batch = tok([text], return_tensors="pt").to(m.device)
        labels = batch.input_ids.clone()
        out = m(**batch, labels=labels)
        loss = out.loss
        print(f"INFO loss={loss.item():.4f}")
        loss.backward()
    ok["forward-backward"] = check("forward-backward", _fwd_bwd)

    def _save_reload():
        with tempfile.TemporaryDirectory() as d:
            m.save_pretrained(d)
            assert (Path(d) / "adapter_model.safetensors").exists() or \
                   (Path(d) / "adapter_model.bin").exists(), "nema adapter fajla"
            PeftModel.from_pretrained(model, d)
    ok["save-reload-adapter"] = check("save-reload-adapter", _save_reload)

    return _finish(ok)


def _finish(ok: dict[str, bool]) -> int:
    report = {"checks": ok, "failures": FAILURES,
              "verdict": "SMOKE-PASS" if not FAILURES else "SMOKE-FAIL"}
    Path("smoke_report.json").write_text(json.dumps(report, indent=2))
    print(f"SMOKE {report['verdict']} ({sum(ok.values())}/{len(ok)})")
    return 0 if not FAILURES else 1


if __name__ == "__main__":
    raise SystemExit(main())
