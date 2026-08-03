from __future__ import annotations

import tempfile
import traceback
from pathlib import Path
from xml.etree import ElementTree as ET

from .models import HotCue, TrackAnalysis
from .traktor_nml import export_collection


def run_self_test() -> int:
    error_log = Path(tempfile.gettempdir()) / "DawoCueTraktor-self-test-error.txt"
    try:
        import tkinter as tk

        import librosa  # noqa: F401
        import numpy as np
        import soundfile  # noqa: F401

        window = tk.Tk()
        window.withdraw()
        from .app import DawoCueApp

        DawoCueApp(window)
        window.update_idletasks()
        if not window.title().startswith("DawoCue for Traktor 4"):
            return 3
        window.destroy()

        with tempfile.TemporaryDirectory(prefix="dawocue_test_") as temp_dir:
            root = Path(temp_dir)
            sample_rate = 22050
            sample_count = sample_rate * 6
            timeline = np.arange(sample_count, dtype=np.float32) / sample_rate
            audio = 0.04 * np.sin(2 * np.pi * 440.0 * timeline)
            for beat_time in np.arange(0.5, 6.0, 0.5):
                start = int(beat_time * sample_rate)
                length = min(600, sample_count - start)
                audio[start : start + length] += 0.8 * np.hanning(length)
            wave_path = root / "audio_test.wav"
            soundfile.write(wave_path, audio, sample_rate)

            from .analyzer import analyze_audio

            analyzed = analyze_audio(wave_path)
            if analyzed.bpm <= 0 or len(analyzed.hotcues) != 8:
                return 4

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
        error_log.unlink(missing_ok=True)
        return 0
    except Exception:
        error_log.write_text(traceback.format_exc(), encoding="utf-8")
        return 1
