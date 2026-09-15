import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from agentmujo_training.tools import ToolRegistry  # noqa: E402


def test_registry_loads():
    reg = ToolRegistry.from_yaml(REPO / "configs" / "tools.yaml")
    assert "terminal" in reg.names()
    assert reg.get("service_restart").policy == "confirmation_required"
    assert reg.get("service_status").policy == "allow"


def test_high_level_preferred_over_terminal():
    reg = ToolRegistry.from_yaml(REPO / "configs" / "tools.yaml")
    # restart nginx mora biti validan high-level poziv
    assert reg.validate_call("service_restart", {"service": "nginx"}) == []
    # nepoznat tool se odbija
    assert reg.validate_call("nepostojeci", {}) != []


def test_argument_validation():
    reg = ToolRegistry.from_yaml(REPO / "configs" / "tools.yaml")
    assert any("required" in e or "missing" in e for e in reg.validate_call("service_restart", {}))
    assert reg.validate_call("port_check", {"port": "80"}) != []  # port mora biti int
