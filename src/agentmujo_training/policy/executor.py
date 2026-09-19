"""Executor — izvrsava SAMO allow/ potvrdjene pozive.

Sigurnosna pravila:
- default je DRY-RUN (nista se ne izvrsava, vraca se opis akcije).
- Stvarno izvrsavanje: samo allow-klasa + eksplicitni `--execute`,
  kroz whitelistu preslikanih read-only komandi, sa timeoutom.
- confirmation_required bez dokaza o potvrdi -> odbija se.
- deny -> nikad.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Any

# Allow-klasa preslikana na konkretne read-only komande. Sve ostalo: odbij.
ALLOW_COMMANDS: dict[str, list[str]] = {
    "service_status": ["systemctl", "is-active"],
    "service_logs": ["journalctl", "-u"],
    "disk_usage": ["df", "-h"],
    "memory_usage": ["free", "-h"],
    "cpu_usage": ["nproc"],
    "process_list": ["ps", "aux", "--sort=-%cpu"],
    "network_status": ["ip", "-brief", "addr"],
}


@dataclass
class ExecResult:
    ok: bool
    output: str
    dry_run: bool
    reason: str = ""


def _build_argv(tool: str, arguments: dict[str, Any]) -> list[str] | None:
    if tool == "service_status":
        return ["systemctl", "is-active", str(arguments.get("service", ""))]
    if tool == "service_logs":
        return ["journalctl", "-u", str(arguments.get("service", "")),
                "-n", str(arguments.get("lines", 50)), "--no-pager"]
    if tool == "disk_usage":
        return ["df", "-h", str(arguments.get("path", "/"))]
    if tool == "memory_usage":
        return ["free", "-h"]
    if tool == "cpu_usage":
        return ["nproc"]
    if tool == "process_list":
        return ["ps", "aux", "--sort=-%cpu"]
    if tool == "network_status":
        return ["ip", "-brief", "addr"]
    if tool == "port_check":
        return ["ss", "-ltnp"]
    return None


def execute(tool: str, arguments: dict[str, Any] | None, decision,
            dry_run: bool = True, confirmed: bool = False,
            timeout_s: int = 30) -> ExecResult:
    """Izvrsi poziv prema odluci Policy Enginea."""
    arguments = arguments or {}
    if decision.verdict == "deny":
        return ExecResult(False, "", dry_run, f"deny: {decision.reason}")
    if decision.verdict == "confirmation_required" and not confirmed:
        return ExecResult(False, "", dry_run, "potrebna eksplicitna potvrda operatora")
    argv = _build_argv(tool, arguments)
    if argv is None:
        return ExecResult(False, "", dry_run, f"nema mapiranja za alat: {tool}")
    if dry_run:
        return ExecResult(True, f"[dry-run] {' '.join(argv)}", True, "dry-run")
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout_s)
        return ExecResult(r.returncode == 0, (r.stdout or "")[-2000:], False,
                          "" if r.returncode == 0 else (r.stderr or "")[-500:])
    except subprocess.TimeoutExpired:
        return ExecResult(False, "", False, f"timeout {timeout_s}s")
