import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from agentmujo_training.agent import parse_call, run  # noqa: E402
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


def test_parse_multi_arg_int_coercion():
    tool, args, status = parse_call(
        "<tool_call>\n<function=service_logs>\n<parameter=service>\nnginx\n</parameter>\n"
        "<parameter=lines>\n25\n</parameter>\n</function>\n</tool_call>")
    assert status == "ok" and tool == "service_logs"
    assert args == {"service": "nginx", "lines": 25}
    tool, args, status = parse_call(
        "<tool_call><function=port_check><parameter=port>443</parameter></function></tool_call>")
    assert status == "ok" and args == {"port": 443} and isinstance(args["port"], int)


def test_parse_incomplete_and_malformed():
    assert parse_call("... <tool_call>\n<function=cpu_usage>")[2] == "incomplete"
    assert parse_call("samo tekst bez poziva")[2] == "none"
    assert parse_call("<tool_call></tool_call>")[2] == "malformed"
    assert parse_call("<parameter=x>\n1\n</parameter>")[2] == "malformed"


def test_loop_invalid_args_deny():
    tr = run("Status?", _eng(),
             chat_fn=lambda msgs: "<tool_call><function=service_status></function></tool_call>")
    assert tr.stopped.startswith("deny: nevalidan poziv")
    assert tr.steps[0]["policy"] == "invalid"


def test_loop_unknown_tool_deny():
    tr = run("Mem?", _eng(),
             chat_fn=lambda msgs: "<tool_call><function=memory_limit><parameter=limit>2</parameter></function></tool_call>")
    assert tr.stopped.startswith("deny")


def test_loop_incomplete_recovers():
    script = iter([
        "<tool_call><function=cpu_usage>",
        "<tool_call><function=cpu_usage></function></tool_call>",
        "Gotovo.",
    ])
    tr = run("Cpu?", _eng(), chat_fn=lambda msgs: next(script))
    assert tr.stopped == "done"
    assert tr.steps[0]["policy"] == "incomplete"
