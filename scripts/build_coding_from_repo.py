#!/usr/bin/env python3
"""Build coding samples from this Apache-2.0 repository's functions (source-grounded)."""
import ast, json
from pathlib import Path

ROOT = Path(".")
rows = []
for p in sorted(ROOT.rglob("*.py")):
    if ".git" in p.parts or "__pycache__" in p.parts:
        continue
    try:
        src = p.read_text(encoding="utf-8")
        tree = ast.parse(src)
    except Exception:
        continue
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        doc = ast.get_docstring(node) or ""
        first = doc.strip().splitlines()[0].strip() if doc.strip() else ""
        seg = ast.get_source_segment(src, node) or ""
        if not (80 <= len(seg) <= 1600):
            continue
        if node.name in {r["messages"][0]["content"].split("`")[1] for r in rows if "`" in r["messages"][0]["content"]}:
            continue
        rows.append({
            "id": f"amj-cd-{len(rows)+1:04d}", "version": "0.2.0", "language": "bs",
            "task": "coding", "difficulty": "medium",
            "messages": [
                {"role": "user", "content": (f"Napiši Python funkciju `{node.name}` prema opisu: {first}" if first else f"Napiši Python funkciju `{node.name}` (signature: {node.name}({', '.join(a.arg for a in node.args.args)})).")},
                {"role": "assistant", "content": "```python\n" + seg + "\n```"},
            ],
            "metadata": {"source": "own-repo", "license": "Apache-2.0", "file": str(p),
                         "verification_status": "source-grounded", "quality_tier": "SILVER"},
        })
        if len(rows) >= 30:
            break
    if len(rows) >= 30:
        break
out = Path("datasets/canonical/coding_repo_v0.1.jsonl")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
print("coding rows", len(rows), "->", out)
