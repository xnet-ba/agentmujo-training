"""Source Registry v0 (arhitektura A): učitavanje i validacija izvora podataka."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REQUIRED = ("id", "name", "type", "url", "license", "access", "status", "categories")
ALLOWED_STATUS = {"approved", "pending", "blocked", "rejected"}
ALLOWED_ACCESS = {"public", "restricted", "internal", "restricted/per-dataset"}


def config_path(repo: Path) -> Path:
    return Path(repo) / "configs" / "sources.yaml"


def load_sources(repo: Path) -> list[dict[str, Any]]:
    p = config_path(repo)
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    src = data.get("sources", []) if isinstance(data, dict) else []
    return [x for x in src if isinstance(x, dict)]


def validate_sources(repo: Path) -> list[str]:
    issues: list[str] = []
    sources = load_sources(repo)
    if not sources:
        return ["nema izvora u configs/sources.yaml"]
    seen: set[str] = set()
    for i, s in enumerate(sources, 1):
        sid = str(s.get("id") or "").strip()
        if not sid:
            issues.append(f"izvor #{i}: nema id")
        elif sid in seen:
            issues.append(f"izvor #{i}: duplikat id '{sid}'")
        else:
            seen.add(sid)
        for f in REQUIRED:
            if f not in s or s.get(f) in (None, "", []):
                issues.append(f"izvor '{sid or i}': nema polje '{f}'")
        st = str(s.get("status") or "")
        if st not in ALLOWED_STATUS:
            issues.append(f"izvor '{sid}': status '{st}' nije dozvoljen")
        ac = str(s.get("access") or "")
        if ac and ac not in ALLOWED_ACCESS:
            issues.append(f"izvor '{sid}': access '{ac}' nije dozvoljen")
        cats = s.get("categories")
        if not isinstance(cats, list) or not cats:
            issues.append(f"izvor '{sid}': categories mora biti neprazna lista")
        url = str(s.get("url") or "")
        if url and not (url.startswith("http") or url.startswith("file:")):
            issues.append(f"izvor '{sid}': url mora biti http(s) ili file:")
    return issues


def scan_sources(repo: Path, only: list[str] | None = None, timeout: int = 8) -> list[dict[str, Any]]:
    """Provjeri dostupnost izvora (bez odobravanja licence)."""
    import urllib.request
    out: list[dict[str, Any]] = []
    for s in load_sources(repo):
        sid = str(s.get("id") or "")
        if only and sid not in only:
            continue
        url = str(s.get("url") or "")
        row = {"id": sid, "url": url, "status": s.get("status"), "reachable": False, "http": None, "error": ""}
        try:
            if url.startswith("file:"):
                p = Path(url[7:])
                if not p.is_absolute():
                    p = Path(repo) / p
                row["reachable"] = p.exists()
            elif url.startswith("http"):
                req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "agentmujo-dataset-factory/0.1"})
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    row["http"] = int(getattr(r, "status", 200))
                    row["reachable"] = 200 <= row["http"] < 400
            else:
                row["error"] = "nepodrzan url"
        except Exception as e:
            row["error"] = str(e)[:160]
        out.append(row)
    return out
