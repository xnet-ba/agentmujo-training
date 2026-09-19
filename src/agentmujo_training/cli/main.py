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
    # Kaggle auth — samo postojanje, nikada vrijednosti.
    # Mehanizmi (noviji prvi): KAGGLE_API_TOKEN / ~/.kaggle/access_token
    # (moderni KGAT_ Bearer), zatim legacy kaggle.json / KAGGLE_USERNAME+KEY.
    import os
    kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
    access_token = Path.home() / ".kaggle" / "access_token"
    if os.environ.get("KAGGLE_API_TOKEN") or access_token.exists():
        print("  kaggle auth: API-TOKEN PRISUTAN (KAGGLE_API_TOKEN ili ~/.kaggle/access_token)")
    elif kaggle_json.exists():
        print("  kaggle auth: LEGACY PRISUTAN (~/.kaggle/kaggle.json)")
    elif os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY"):
        print("  kaggle auth: LEGACY ENV PRISUTAN (KAGGLE_USERNAME/KAGGLE_KEY postavljeni)")
    else:
        print("  kaggle auth: NEDOSTAJE (KAGGLE_API_TOKEN ili kaggle.json; "
              "vidi docs/KAGGLE_WORKER.md)")
    # GPU — očekivan samo na workeru, WARN na Oracleu
    try:
        import torch
        if torch.cuda.is_available():
            print(f"  gpu: {torch.cuda.get_device_name(0)} (worker režim)")
        else:
            print("  gpu: NEMA (očekivano na Oracleu; obavezno na Kaggle workeru)")
    except ImportError:
        print("  gpu: neprovjereno (torch nije instaliran — OK za Oracle control plane)")
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
    report = validate_file(args.input, set(reg.names()), reg.validate_call,
                           allow_duplicates=getattr(args, "allow_duplicates", False))
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


def cmd_job_create(args) -> int:
    """Generira training/jobs/<job_id>/{config.yaml,metadata.json,README.md}."""
    import datetime as dt
    import shutil as _sh
    import yaml
    src = Path(args.config)
    cfg = yaml.safe_load(src.read_text(encoding="utf-8"))
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    job_id = args.job_id or f"qwen35-fc-{stamp}-001"
    if not args.job_id:  # inkrement dok ne nađemo slobodan ID
        n = 1
        while (REPO_ROOT / "training" / "jobs" / job_id).exists():
            n += 1
            job_id = f"qwen35-fc-{stamp}-{n:03d}"
    jdir = REPO_ROOT / "training" / "jobs" / job_id
    jdir.mkdir(parents=True)
    _sh.copy(src, jdir / "config.yaml")
    meta = {"job_id": job_id, "created_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "base_model": cfg.get("model_name"), "base_revision": cfg.get("model_revision"),
            "dataset": cfg.get("dataset"), "dataset_revision": cfg.get("dataset_revision"),
            "training_config": args.config, "seed": cfg.get("seed", 42),
            "worker": "kaggle-ephemeral", "status": "created"}
    (jdir / "metadata.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    (jdir / "README.md").write_text(
        f"# Job {job_id}\n\n1. `amj job validate {job_id}`\n"
        f"2. Notebook na Kaggle GPU: `training/notebooks/qwen35_2b_training.ipynb`\n"
        f"3. `python workers/kaggle/job_run.py --job-dir training/jobs/{job_id}`\n"
        f"4. `amj artifacts fetch {job_id}`\n", encoding="utf-8")
    print(f"job: {jdir}")
    return 0


def _job_dir(job_id: str) -> Path:
    return REPO_ROOT / "training" / "jobs" / job_id


def cmd_job_status(args) -> int:
    jdir = _job_dir(args.job_id)
    for f in ("metadata.json", "outputs/status.json", "outputs/metrics.json"):
        p = jdir / f
        if p.exists():
            print(f"--- {f} ---")
            print(p.read_text(encoding="utf-8")[:2000])
        else:
            print(f"--- {f}: NEMA ---")
    return 0


def cmd_job_validate(args) -> int:
    jdir = _job_dir(args.job_id)
    errors = []
    for f in ("config.yaml", "metadata.json", "README.md"):
        if not (jdir / f).exists():
            errors.append(f"nedostaje: {f}")
    try:
        import yaml
        cfg = yaml.safe_load((jdir / "config.yaml").read_text(encoding="utf-8"))
        for k in ("model_name", "dataset", "output_dir", "lora_r", "seed"):
            if k not in cfg:
                errors.append(f"config bez ključa: {k}")
        if not cfg.get("dataset_revision"):
            print("WARN: dataset_revision nije pinovan (pinovati SHA prije runa)")
    except Exception as e:
        errors.append(f"config nečitljiv: {e}")
    if errors:
        print("FAIL job validate:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"PASS job {args.job_id}")
    return 0


def cmd_artifacts_fetch(args) -> int:
    jdir = _job_dir(args.job_id)
    out = jdir / "outputs"
    if getattr(args, "from_hf", None):
        print(f"Preuzimanje adaptera sa Huba: {args.from_hf} -> {out}/adapter")
        print("(izvršiti na Oracleu uz hf login: hf download ... --local-dir ...)")
        return 2  # namjerno ne automatski bez eksplicitne potvrde operatora
    found = sorted([p.name for p in out.iterdir()]) if out.exists() else []
    print(f"lokalni artefakti ({jdir}): {found or 'nema outputs/ — job još nije vraćen'}")
    return 0 if found else 1


def cmd_evaluate(args) -> int:
    return cmd_benchmark_run(argparse.Namespace(cases=args.cases))


def cmd_policy_check(args) -> int:
    sys.path.insert(0, str(REPO_ROOT / "src"))
    import json as _json
    from agentmujo_training.policy import PolicyEngine, execute
    from agentmujo_training.tools import ToolRegistry
    reg = ToolRegistry.from_yaml(REPO_ROOT / "configs" / "tools.yaml")
    eng = PolicyEngine(reg)
    try:
        call = _json.loads(args.call)
        tool, call_args = call.get("tool", ""), call.get("arguments", {})
    except Exception as e:
        print(f"FAIL: neispravan JSON poziva: {e}")
        return 2
    d = eng.decide(tool, call_args)
    print(f"odluka: {d.verdict} ({d.reason})")
    r = execute(tool, call_args, d, dry_run=not args.execute,
                confirmed=args.confirmed)
    print(f"izvrsavanje: ok={r.ok} dry_run={r.dry_run}")
    if r.output:
        print(r.output[:1000])
    if r.reason:
        print(f"razlog: {r.reason}")
    return 0 if (d.verdict != "deny") else 1


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
        print("upotreba: amj {doctor|model list|dataset validate|dataset stats|dataset split|tools validate|benchmark run|job create|job status|job validate|artifacts fetch|evaluate|train|experiment show|publish|model quantize}")
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
        allow_dup = "--allow-duplicates" in args
        rest = [x for x in args if x != "--allow-duplicates"]
        ns = argparse.Namespace(input=rest[3] if rest[2:3] == ["--input"] else (rest[2] if len(rest) > 2 else ""),
                                allow_duplicates=allow_dup)
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
        return cmd_benchmark_run(argparse.Namespace(cases=d.get("--cases", "benchmark/cases_v0.4.jsonl")))
    if args[:2] == ["job", "create"]:
        # amj job create --config <yaml> [--job-id <id>]
        d = dict(zip(args[2::2], args[3::2]))
        return cmd_job_create(argparse.Namespace(config=d.get("--config", ""), job_id=d.get("--job-id")))
    if args[:2] == ["job", "status"]:
        return cmd_job_status(argparse.Namespace(job_id=args[2] if len(args) > 2 else ""))
    if args[:2] == ["job", "validate"]:
        return cmd_job_validate(argparse.Namespace(job_id=args[2] if len(args) > 2 else ""))
    if args[:2] == ["artifacts", "fetch"]:
        d = dict(zip(args[2::2], args[3::2])) if len(args) > 2 else {}
        job = args[2] if len(args) > 2 and not args[2].startswith("--") else d.get("--job-id", "")
        return cmd_artifacts_fetch(argparse.Namespace(job_id=job, from_hf=d.get("--from-hf")))
    if args[:2] == ["policy", "check"]:
        # amj policy check '{"tool":"service_status","arguments":{"service":"nginx"}}' [--execute] [--confirmed]
        import json as _json
        call = args[2] if len(args) > 2 and args[2].startswith("{") else "{}"
        return cmd_policy_check(argparse.Namespace(
            call=call, execute="--execute" in args, confirmed="--confirmed" in args))
    if args[:2] == ["evaluate", "run"] or args[:1] == ["evaluate"]:
        rest = args[2:] if args[:1] == ["evaluate"] else args[2:]
        d = dict(zip(rest[::2], rest[1::2])) if rest else {}
        return cmd_evaluate(argparse.Namespace(cases=d.get("--cases", "benchmark/cases_v0.4.jsonl")))
    if args[:1] in (["train"], ["publish"], ["experiment"], ["model"]):
        print("`amj " + " ".join(args[:2]) + "` je gate-ovan u v0.1 (vidi docs/TEST_PLAN.md).")
        return 2
    print(f"nepoznata komanda: {args}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
