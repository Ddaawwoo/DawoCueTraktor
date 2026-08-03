from __future__ import annotations

from pathlib import Path

from .models import HotCue, TrackAnalysis


KEY_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


def _estimate_key(chroma) -> str:
    import numpy as np

    major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
    pitch_energy = np.asarray(chroma).mean(axis=1)
    if not np.any(pitch_energy):
        return "Neznámá"

    candidates: list[tuple[float, str]] = []
    for root, name in enumerate(KEY_NAMES):
        candidates.append((float(np.corrcoef(pitch_energy, np.roll(major_profile, root))[0, 1]), name))
        candidates.append((float(np.corrcoef(pitch_energy, np.roll(minor_profile, root))[0, 1]), f"{name}m"))
    return max(candidates, key=lambda item: item[0])[1]


def _align_to_beat(seconds: float, first_beat: float, beat_length: float) -> float:
    if beat_length <= 0:
        return max(0.0, seconds)
    beat_number = round((seconds - first_beat) / beat_length)
    return max(0.0, first_beat + beat_number * beat_length)


def create_hotcues(duration: float, bpm: float, first_beat: float) -> list[HotCue]:
    beat_length = 60.0 / bpm if bpm > 0 else 0.5
    phrase = beat_length * 32
    candidates = [
        ("GRID", first_beat, 4),
        ("INTRO 2", first_beat + phrase, 0),
        ("PHRASE 3", first_beat + phrase * 2, 0),
        ("DROP / MAIN", duration * 0.33, 0),
        ("MIDDLE", duration * 0.50, 0),
        ("OUTRO START", max(first_beat, duration - phrase * 2), 0),
        ("OUTRO 2", max(first_beat, duration - phrase), 0),
        ("END MIX", max(first_beat, duration - beat_length * 8), 0),
    ]

    hotcues: list[HotCue] = []
    previous = -1.0
    for slot, (name, proposed, cue_type) in enumerate(candidates):
        aligned = min(max(0.0, _align_to_beat(proposed, first_beat, beat_length)), max(0.0, duration - 0.001))
        if aligned <= previous and previous + beat_length < duration:
            aligned = previous + beat_length
        previous = aligned
        hotcues.append(HotCue(slot=slot, name=name, time_seconds=aligned, cue_type=cue_type))
    return hotcues


def analyze_audio(path: str | Path) -> TrackAnalysis:
    import librosa
    import numpy as np

    audio_path = Path(path).resolve()
    y, sample_rate = librosa.load(str(audio_path), sr=22050, mono=True)
    duration = float(librosa.get_duration(y=y, sr=sample_rate))
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sample_rate, units="frames")
    bpm = float(np.asarray(tempo).reshape(-1)[0]) if np.asarray(tempo).size else 0.0
    beat_times = librosa.frames_to_time(beat_frames, sr=sample_rate)
    first_beat = float(beat_times[0]) if len(beat_times) else 0.0
    chroma = librosa.feature.chroma_cqt(y=y, sr=sample_rate)
    musical_key = _estimate_key(chroma)

    if bpm <= 0:
        bpm = 120.0
    hotcues = create_hotcues(duration, bpm, first_beat)
    return TrackAnalysis(
        path=audio_path,
        duration_seconds=duration,
        bpm=bpm,
        first_beat_seconds=first_beat,
        musical_key=musical_key,
        hotcues=hotcues,
    )
