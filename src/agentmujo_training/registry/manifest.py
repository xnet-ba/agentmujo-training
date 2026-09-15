"""Experiment manifest — reproducibility zapis (v0.1 skeleton)."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass


@dataclass
class ExperimentManifest:
    experiment_id: str
    base_model: str
    base_revision: str
    dataset: str
    training_config: str
    git_commit: str
    seed: int
    hardware: str

    def checksum(self) -> str:
        blob = json.dumps(asdict(self), sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()[:16]
