from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class JobMeta:
    """Metadata for a translation job: model identifier and API parameters."""

    model: str
    params: dict = field(default_factory=dict)
