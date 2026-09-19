import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from agentmujo_training.agent import run  # noqa: E402
from agentmujo_training.policy import PolicyEngine  # noqa: E402
from agentmujo_training.tools import ToolRegistry  # noqa: E402


def _eng():
    return PolicyEngine(ToolRegistry.from_yaml(REPO / "configs" / "tools.yaml"))


def test_loop_single_tool_then_done():
    script = iter([
        "Provjeravam. <tool_call><function=service_status>\n<parameter=service>\nnginx\n</parameter>\n</function></tool_call>",
        "Nginx je aktivan.",
    ])
    tr = run("Status nginxa?", _eng(), chat_fn=lambda msgs: next(script))
    assert tr.stopped == "done"
    assert tr.steps[0]["tool"] == "service_status"
    assert tr.steps[0]["policy"] == "allow"
    assert "aktivan" in tr.final


def test_loop_blocks_dangerous():
    tr = run("Obriši disk.", _eng(),
             chat_fn=lambda msgs: "<tool_call><function=terminal>\n<parameter=command>\nrm -rf /\n</parameter>\n</function></tool_call>")
    assert tr.stopped.startswith("deny")
    assert tr.steps[0]["policy"] == "deny"


def test_loop_max_steps():
    tr = run("Radi.", _eng(), max_steps=2,
             chat_fn=lambda msgs: "<tool_call><function=cpu_usage></function></tool_call>")
    assert tr.stopped == "max_steps"
    assert len(tr.steps) == 2
