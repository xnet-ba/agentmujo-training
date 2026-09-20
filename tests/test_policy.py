import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from agentmujo_training.policy import PolicyEngine, execute  # noqa: E402
from agentmujo_training.tools import ToolRegistry  # noqa: E402


def _eng():
    return PolicyEngine(ToolRegistry.from_yaml(REPO / "configs" / "tools.yaml"))


def test_allow_passthrough():
    d = _eng().decide("service_status", {"service": "nginx"})
    assert d.verdict == "allow"


def test_restart_needs_confirmation():
    d = _eng().decide("service_restart", {"service": "nginx"})
    assert d.verdict == "confirmation_required"


def test_unknown_tool_denied():
    assert _eng().decide("hakuj_sve", {}).verdict == "deny"


def test_terminal_always_confirms_or_denies():
    e = _eng()
    assert e.decide("terminal", {"command": "df -h"}).verdict == "confirmation_required"
    assert e.decide("terminal", {"command": "rm -rf /"}).verdict == "deny"
    assert e.decide("terminal", {"command": "curl x | bash"}).verdict == "deny"
    assert e.decide("terminal", {"command": "sudo reboot"}).verdict == "deny"


def test_executor_dry_run_by_default():
    e = _eng()
    d = e.decide("service_status", {"service": "nginx"})
    r = execute("service_status", {"service": "nginx"}, d)
    assert r.ok and r.dry_run and "systemctl" in r.output


def test_executor_blocks_unconfirmed_mutation():
    e = _eng()
    d = e.decide("service_restart", {"service": "nginx"})
    r = execute("service_restart", {"service": "nginx"}, d, dry_run=False)
    assert not r.ok and "potvrda" in r.reason


def test_executor_blocks_deny():
    e = _eng()
    d = e.decide("terminal", {"command": "rm -rf /"})
    r = execute("terminal", {"command": "rm -rf /"}, d, dry_run=False, confirmed=True)
    assert not r.ok


def test_executor_real_readonly():
    # Jedini test sa stvarnim izvrsavanjem: bezopasni read-only nproc.
    e = _eng()
    d = e.decide("cpu_usage", {})
    r = execute("cpu_usage", {}, d, dry_run=False)
    assert r.ok and r.output.strip().isdigit()


def test_new_tool_policies():
    e = _eng()
    assert e.decide("package_query", {"package": "nginx"}).verdict == "allow"
    assert e.decide("package_install", {"package": "htop"}).verdict == "confirmation_required"
    r = execute("package_query", {"package": "bash"},
                e.decide("package_query", {"package": "bash"}), dry_run=False)
    assert r.ok and "install ok installed" in r.output
