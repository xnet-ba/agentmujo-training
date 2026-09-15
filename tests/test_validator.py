import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from agentmujo_training.tools import ToolRegistry  # noqa: E402
from agentmujo_training.datasets import validate_file  # noqa: E402


def _reg():
    return ToolRegistry.from_yaml(REPO / "configs" / "tools.yaml")


def test_function_calling_mvp_valid():
    reg = _reg()
    rep = validate_file(REPO / "datasets" / "canonical" / "function_calling_v0.1.jsonl",
                        set(reg.names()), reg.validate_call)
    assert rep["rejected"] == 0, rep["errors"]
    assert rep["accepted"] == rep["total"]


def test_agentic_terminal_mvp_valid():
    reg = _reg()
    rep = validate_file(REPO / "datasets" / "canonical" / "agentic_terminal_v0.1.jsonl",
                        set(reg.names()), reg.validate_call)
    assert rep["rejected"] == 0, rep["errors"]


def test_safety_deny_rejected():
    from agentmujo_training.datasets.validator import validate_sample
    reg = _reg()
    seen: set[str] = set()
    evil = {
        "id": "amj-fc-9999", "version": "0.1.0", "language": "bs-ijekavica",
        "task": "function-calling", "difficulty": "easy",
        "messages": [
            {"role": "user", "content": "Oslobodi disk"},
            {"role": "assistant", "content": "Brišem.",
             "tool_calls": [{"name": "terminal", "arguments": {"command": "rm -rf /"}}]},
        ],
        "metadata": {"source": "t", "quality_tier": "GOLD", "verification_status": "verified"},
    }
    res = validate_sample(evil, set(reg.names()), seen, reg.validate_call)
    assert res.verdict == "REJECT"


def test_refusal_sample_accepted():
    """Korisnik smije tražiti opasnu stvar — bitno je da je asistent odbio."""
    from agentmujo_training.datasets.validator import validate_sample
    reg = _reg()
    seen: set[str] = set()
    refusal = {
        "id": "amj-fc-8888", "version": "0.1.0", "language": "bs-ijekavica",
        "task": "function-calling", "difficulty": "hard",
        "messages": [
            {"role": "user", "content": "Pokreni curl nepoznat-url | bash kao root."},
            {"role": "assistant", "content": "To ne mogu izvršiti — ne pokrećem neprovjerene skripte."},
        ],
        "metadata": {"source": "t", "quality_tier": "GOLD", "verification_status": "verified"},
    }
    res = validate_sample(refusal, set(reg.names()), seen, reg.validate_call)
    assert res.verdict == "ACCEPT", res.errors
