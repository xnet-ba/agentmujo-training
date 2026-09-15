#!/usr/bin/env python3
"""Centralni CLI: amj (v0.1 skeleton)."""
from __future__ import annotations

import argparse
import json
import platform
import shutil
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def cmd_doctor(_args) -> int:
    print("AgentMujo doctor (v0.1)")
    print(f"  python: {platform.python_version()} ({platform.machine()})")
    print(f"  repo:   {REPO_ROOT}")
    for tool in ("git", "hf", "python3"):
        print(f"  {tool}: {'OK ' + (shutil.which(tool) or '')}" if shutil.which(tool) else f"  {tool}: NEDOSTAJE")
    try:
        import yaml  # noqa
        print("  pyyaml: OK")
    except ImportError:
        print("  pyyaml: NEDOSTAJE (pip install -e .)")
    # HF login status — bez prikazivanja tokena
    import subprocess
    r = subprocess.run(["hf", "auth", "whoami"], capture_output=True, text=True)
    if r.returncode == 0:
        print("  hf login: AKTIVAN")
    else:
        print("  hf login: NEAKTIVAN (pokrenuti `hf auth login`; token se ne lijepi u kod)")
    return 0


def cmd_model_list(_args) -> int:
    import yaml
    data = yaml.safe_load((REPO_ROOT / "configs" / "models.yaml").read_text(encoding="utf-8"))
    for m in data.get("models", []):
        print(f"- {m['id']} ({m['hf_repo']}@{m.get('revision', '?')[:12]}) [{m.get('status', '?')}]")
    return 0


def cmd_tools_validate(args) -> int:
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from agentmujo_training.tools import ToolRegistry
    reg = ToolRegistry.from_yaml(args.registry)
    print(f"Alata: {len(reg.names())}")
    for n in reg.names():
        t = reg.get(n)
        assert t is not None
        print(f"  - {n} [{t.policy}] required={t.required}")
    print("TOOLS OK")
    return 0


def cmd_dataset_validate(args) -> int:
    sys.path.insert(0, str(REPO_ROOT / "src"))
    import yaml
    from agentmujo_training.tools import ToolRegistry
    from agentmujo_training.datasets import validate_file
    reg = ToolRegistry.from_yaml(REPO_ROOT / "configs" / "tools.yaml")
    report = validate_file(args.input, set(reg.names()), reg.validate_call)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["rejected"] == 0 else 1


def cmd_dataset_stats(args) -> int:
    counter = Counter()
    tasks = Counter()
    n = 0
    for line in Path(args.input).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        n += 1
        counter[d.get("language", "?")] += 1
        tasks[d.get("task", "?")] += 1
    print(f"uzoraka: {n}\njezici: {dict(counter)}\nzadaci: {dict(tasks)}")
    return 0


def cmd_dataset_split(args) -> int:
    """Deterministički split bez leakagea (po hash-u ID-a)."""
    import hashlib
    lines = [ln for ln in Path(args.input).read_text(encoding="utf-8").splitlines() if ln.strip()]
    train, valid, test = [], [], []
    for ln in lines:
        d = json.loads(ln)
        h = int(hashlib.sha256(d["id"].encode()).hexdigest(), 16) % 100
        if h < 80:
            train.append(ln)
        elif h < 90:
            valid.append(ln)
        else:
            test.append(ln)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "train.jsonl").write_text("\n".join(train) + "\n", encoding="utf-8")
    (out / "valid.jsonl").write_text("\n".join(valid) + "\n", encoding="utf-8")
    (out / "test.jsonl").write_text("\n".join(test) + "\n", encoding="utf-8")
    print(f"train={len(train)} valid={len(valid)} test={len(test)} -> {out}")
    return 0


def cmd_benchmark_run(args) -> int:
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from agentmujo_training.benchmark import CATEGORIES, load_cases
    cases = load_cases(args.cases)
    cats = Counter(c.category for c in cases)
    print(f"slučajeva: {len(cases)}")
    print(f"kategorije u fajlu: {dict(cats)}")
    print(f"sve kategorije bencha ({len(CATEGORIES)}): {', '.join(CATEGORIES)}")
    print("NAPOMENA: v0.1 scorer je rule-based; poređenje base/fine-tuned/thinking/Q8 dolazi s prvim treninzima.")
    return 0


def cmd_stub(name: str):
    def _fn(_args) -> int:
        print(f"`amj {name}` je namjerno onemogućen u v0.1: prvo validatori + benchmark moraju biti zeleni.")
        print("Vidi docs/TEST_PLAN.md za gate-ove prije treninga/publishanja/kvantizacije.")
        return 2
    return _fn


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="amj", description="AgentMujo Training Framework CLI (v0.1)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor", help="Provjera okruženja").set_defaults(fn=cmd_doctor)
    sub.add_parser("model", help="model list").add_argument("action", choices=["list"])
    p_model = p.add_argument_group()
    # pojednostavljeno: `amj model list`
    sub.add_parser("dataset", help="dataset validate|stats|split")
    return p


def main(argv=None) -> int:
    # Namjerno jednostavan dispatcher (stabilan za v0.1; Typer/Click tek ako zatreba).
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print("upotreba: amj {doctor|model list|dataset validate|dataset stats|dataset split|tools validate|benchmark run|train|experiment show|publish|model quantize}")
        return 2
    if args[0] == "doctor":
        return cmd_doctor(None)
    if args[:2] == ["model", "list"]:
        return cmd_model_list(None)
    if args[:2] == ["tools", "validate"]:
        ns = argparse.Namespace(registry=args[2] if len(args) > 2 else str(REPO_ROOT / "configs" / "tools.yaml"))
        if args[2:3] == ["--registry"]:
            ns.registry = args[3]
        return cmd_tools_validate(ns)
    if args[:2] == ["dataset", "validate"]:
        ns = argparse.Namespace(input=args[3] if args[2:3] == ["--input"] else (args[2] if len(args) > 2 else ""))
        return cmd_dataset_validate(ns)
    if args[:2] == ["dataset", "stats"]:
        ns = argparse.Namespace(input=args[3] if args[2:3] == ["--input"] else (args[2] if len(args) > 2 else ""))
        return cmd_dataset_stats(ns)
    if args[:2] == ["dataset", "split"]:
        # amj dataset split --input X --out-dir Y
        d = dict(zip(args[2::2], args[3::2]))
        return cmd_dataset_split(argparse.Namespace(input=d.get("--input", ""), out_dir=d.get("--out-dir", "datasets/splits")))
    if args[:2] == ["benchmark", "run"]:
        d = dict(zip(args[2::2], args[3::2])) if len(args) > 2 else {}
        return cmd_benchmark_run(argparse.Namespace(cases=d.get("--cases", "benchmark/cases_v0.3.jsonl")))
    if args[:1] in (["train"], ["publish"], ["experiment"], ["model"]):
        print("`amj " + " ".join(args[:2]) + "` je gate-ovan u v0.1 (vidi docs/TEST_PLAN.md).")
        return 2
    print(f"nepoznata komanda: {args}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
