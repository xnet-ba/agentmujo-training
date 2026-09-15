.PHONY: install install-train test lint validate-tools validate-datasets benchmark-help doctor

install:
	pip install -e ".[dev]"

install-train:
	pip install -e ".[train,eval]"

test:
	pytest -q

lint:
	ruff check src tests || true

doctor:
	python -m agentmujo_training.cli.main doctor

validate-tools:
	python -m agentmujo_training.cli.main tools validate --registry configs/tools.yaml

validate-datasets:
	python -m agentmujo_training.cli.main dataset validate --input datasets/canonical/function_calling_v0.1.jsonl
	python -m agentmujo_training.cli.main dataset validate --input datasets/canonical/agentic_terminal_v0.1.jsonl

benchmark-help:
	python -m agentmujo_training.cli.main benchmark run --help
