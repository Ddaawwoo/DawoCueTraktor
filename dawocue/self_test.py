from __future__ import annotations

import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

from .models import HotCue, TrackAnalysis
from .traktor_nml import export_collection


def run_self_test() -> int:
    try:
        import librosa  # noqa: F401
        import soundfile  # noqa: F401

        with tempfile.TemporaryDirectory(prefix="dawocue_test_") as temp_dir:
            root = Path(temp_dir)
            analysis = TrackAnalysis(
                path=root / "test.mp3",
                duration_seconds=180.0,
                bpm=128.0,
                first_beat_seconds=0.5,
                musical_key="Am",
                hotcues=[HotCue(slot=index, name=f"CUE {index + 1}", time_seconds=index * 16.0) for index in range(8)],
            )
            output, _ = export_collection(None, root / "test.nml", [analysis])
            tree = ET.parse(output)
            cues = tree.findall("./COLLECTION/ENTRY/CUE_V2")
            if tree.getroot().get("VERSION") != "20" or len(cues) != 8:
                return 2
        return 0
    except Exception:
        return 1
