import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from agentmujo_training.training import (  # noqa: E402
    render_tool_calls, sample_to_chatml, sample_to_text)


def test_render_tool_call_format():
    tc = [{"name": "service_restart", "arguments": {"service": "nginx"}}]
    out = render_tool_calls(tc)
    assert "<tool_call>" in out and "</tool_call>" in out
    assert "<function=service_restart>" in out
    assert "<parameter=service>\nnginx\n</parameter>" in out


def test_sample_roundtrip_nativan():
    s = {"messages": [
        {"role": "user", "content": "Restartuj nginx."},
        {"role": "assistant", "content": "Restartujem.",
         "tool_calls": [{"name": "service_restart", "arguments": {"service": "nginx"}}]},
        {"role": "tool", "content": "{\"result\": \"ok\"}"},
        {"role": "assistant", "content": "Gotovo."}]}
    text = sample_to_text(s)
    assert "<function=service_restart>" in text
    assert "<tool_response>" in text
    assert text.count("<|im_start|>assistant") == 2  # kompletna konverzacija, bez trailing prompta
    chatml = sample_to_chatml(s)
    assert chatml[1]["role"] == "assistant" and "<tool_call>" in chatml[1]["content"]
    assert chatml[2] == {"role": "user", "content": "<tool_response>\n{\"result\": \"ok\"}\n</tool_response>"}
