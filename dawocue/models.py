from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class HotCue:
    slot: int
    name: str
    time_seconds: float
    cue_type: int = 0


@dataclass(slots=True)
class TrackAnalysis:
    path: Path
    duration_seconds: float
    bpm: float
    first_beat_seconds: float
    musical_key: str
    hotcues: list[HotCue] = field(default_factory=list)

    @property
    def display_name(self) -> str:
        return self.path.name
