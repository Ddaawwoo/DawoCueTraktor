from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dawocue.models import HotCue, TrackAnalysis
from dawocue.traktor_nml import apply_analyses, export_collection, new_collection


def sample_analysis(path: Path) -> TrackAnalysis:
    return TrackAnalysis(
        path=path,
        duration_seconds=210.5,
        bpm=128.0,
        first_beat_seconds=0.25,
        musical_key="F#m",
        hotcues=[HotCue(index, f"CUE {index + 1}", index * 16.0, 4 if index == 0 else 0) for index in range(8)],
    )


class TraktorNmlTests(unittest.TestCase):
    def test_new_collection_contains_eight_cues_and_tempo(self) -> None:
        analysis = sample_analysis(Path("C:/Music/Test Track.mp3"))
        result = apply_analyses(new_collection(), [analysis])
        root = result.getroot()
        entry = root.find("./COLLECTION/ENTRY")
        self.assertEqual(root.get("VERSION"), "20")
        self.assertIsNotNone(entry)
        self.assertEqual(len(entry.findall("CUE_V2")), 8)
        self.assertEqual(entry.find("CUE_V2").get("HOTCUE"), "0")
        self.assertEqual(entry.find("TEMPO").get("BPM"), "128.000000")

    def test_existing_unrelated_content_is_preserved(self) -> None:
        tree = new_collection()
        root = tree.getroot()
        playlists = ET.SubElement(root, "PLAYLISTS")
        ET.SubElement(playlists, "NODE", {"NAME": "Můj playlist"})
        result = apply_analyses(tree, [sample_analysis(Path("C:/Music/Test.mp3"))])
        self.assertEqual(result.find("./PLAYLISTS/NODE").get("NAME"), "Můj playlist")

    def test_export_is_valid_xml_and_rejects_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "collection.nml"
            new_collection().write(source, encoding="utf-8", xml_declaration=True)
            output = root / "DawoCue Export.nml"
            written, backup = export_collection(source, output, [sample_analysis(root / "track.mp3")])
            self.assertEqual(ET.parse(written).getroot().tag, "NML")
            self.assertTrue(backup and backup.exists())
            with self.assertRaises(ValueError):
                export_collection(source, source, [sample_analysis(root / "track.mp3")])


if __name__ == "__main__":
    unittest.main()
