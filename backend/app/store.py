from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass
class DatasetArtifact:
    dataset_id: str
    raw: pd.DataFrame
    cleaned: pd.DataFrame | None = None
    features: pd.DataFrame | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class InMemoryStore:
    def __init__(self) -> None:
        self._datasets: dict[str, DatasetArtifact] = {}

    def put(self, artifact: DatasetArtifact) -> None:
        self._datasets[artifact.dataset_id] = artifact

    def get(self, dataset_id: str) -> DatasetArtifact:
        if dataset_id not in self._datasets:
            raise KeyError(dataset_id)
        return self._datasets[dataset_id]


store = InMemoryStore()
