#!/usr/bin/env python3
"""Merge baze + LoRA adaptera u pune tezine (za GGUF konverziju).

Upotreba: python quantization/merge_adapter.py --base <hf-dir-ili-repo> \
  --adapter <adapter-dir> --out <merged-dir> [--dtype bf16]

Radi na CPU (potrebno ~8 GB RAM-a za 2B bf16). Izlaz: kompletan HF dir
spreman za convert_hf_to_gguf.py.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float32"])
    ap.add_argument("--revision", default=None,
                    help="pinovana HF revizija baze (mora odgovarati trening bazi)")
    ap.add_argument("--rm-base-after-load", action="store_true",
                    help="obrisi --base dir nakon ucitavanja u RAM (stednja diska; samo za jednokratne dir-ove, NIKAD za HF cache)")
    ap.add_argument("--force", action="store_true",
                    help="preskoci provjeru podudaranja baze adaptera (samo za rucne izuzetke)")
    a = ap.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    # Guard (2026-11-19): adapter nosi base_model_name_or_path iz treninga +
    # lineage.json (mode + merge_rule). Pogresna baza = tiha katastrofa
    # (joint10/11 double-count: tool 0.867->0.167; 2B-DPO missing-r6: tool 0.8->0.0).
    # Pravilo: SFT nastavak -> CISTA baza (continued-LoRA nosi cijelu lozu);
    # DPO (merge_and_unload prije treninga) -> STACKED merged-base.
    import json as _json
    import re as _re

    def _read_json(p):
        try:
            return _json.loads(Path(p).read_text())
        except Exception:
            return {}

    def _slug(s):
        return _re.sub(r"[^a-z0-9]", "", str(s).lower().split("/")[-1])

    try:
        _ap = a.adapter
        if "/" in _ap and not Path(_ap).is_dir():
            try:
                from huggingface_hub import hf_hub_download as _dl
                _ap = _dl(_ap, "adapter_config.json")
                _lin = None  # Hub adapteri: osloni se na slug provjeru
            except Exception:
                _ap = None
                _lin = {}
        else:
            _lin = _read_json(str(Path(_ap) / "lineage.json"))
            _ap = str(Path(_ap) / "adapter_config.json")
        _acfg = _read_json(_ap) if _ap else {}
        want = _acfg.get("base_model_name_or_path") or ""
        lin_mode = (_lin or {}).get("mode", "")
        if want and not a.force:
            got = a.base
            got_lin = {}
            if Path(got).is_dir():
                got_lin = _read_json(str(Path(got) / "lineage.json"))
                # Merged dir nosi porijeklo: rjesavaj rekurzivno do HF ID-a.
                while got_lin.get("mode") == "merged" and got_lin.get("base"):
                    got = got_lin["base"]
                    got_lin = _read_json(str(Path(got) / "lineage.json")) if Path(got).is_dir() else {}
                if not got_lin:
                    got = _read_json(str(Path(a.base) / "config.json")).get("_name_or_path") or got
            if _slug(want) != _slug(got):
                raise SystemExit(
                    f"[merge] STOP: adapter je treniran na '{want}', a --base je '{a.base}' "
                    f"(rijeseno '{got}'). Uz --force zaobilazis provjeru.")
            is_local_base = Path(a.base).is_dir()
            if lin_mode == "sft" and is_local_base:
                raise SystemExit(
                    f"[merge] STOP: SFT nastavak (lineage mode=sft) nosi cijelu lozu — "
                    f"merge MORA na CISTU bazu, ne na lokalni '{a.base}' "
                    f"(double-count brbljanje, joint10/11). Uz --force zaobilazis.")
            if lin_mode == "dpo" and not is_local_base:
                raise SystemExit(
                    f"[merge] STOP: DPO adapter (lineage mode=dpo) je svjeza delta nad "
                    f"merged-baseom — merge MORA na lokalni merged dir, ne na cistu '{a.base}' "
                    f"(gubitak loze, 2B-DPO slucaj). Uz --force zaobilazis.")
            print(f"[merge] baza OK: adapter<->{want} (lineage mode={lin_mode or '?'})", flush=True)
    except SystemExit:
        raise
    except Exception as e:
        print(f"[merge] WARN: provjera baze nije uspjela ({e}) — nastavljam", flush=True)

    dtype = torch.bfloat16 if a.dtype == "bfloat16" else torch.float32
    print(f"[merge] baza: {a.base} | adapter: {a.adapter} | dtype: {a.dtype}", flush=True)
    base = AutoModelForCausalLM.from_pretrained(
        a.base, dtype=dtype, device_map="cpu", trust_remote_code=True,
        revision=a.revision)
    tok = AutoTokenizer.from_pretrained(a.base, trust_remote_code=False,
                                        revision=a.revision)
    if a.rm_base_after_load:
        import shutil as _sh
        assert Path(a.base).is_dir() and "huggingface" not in str(Path(a.base).resolve()), \
            "rm-base-after-load dozvoljen samo za jednokratne dir-ove"
        _sh.rmtree(a.base)
        print(f"[merge] baza obrisana sa diska (težine u RAM-u)", flush=True)
    model = PeftModel.from_pretrained(base, a.adapter)
    merged = model.merge_and_unload()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    merged.save_pretrained(out)
    tok.save_pretrained(out)
    import datetime as _dt
    (out / "lineage.json").write_text(
        _json.dumps({"mode": "merged", "base": a.base, "adapter": a.adapter,
                     "revision": a.revision, "dtype": a.dtype,
                     "created_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")},
                    indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[merge] gotovo: {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
