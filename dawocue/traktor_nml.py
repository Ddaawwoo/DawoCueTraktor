from __future__ import annotations

import copy
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path, PureWindowsPath
from xml.etree import ElementTree as ET

from .models import TrackAnalysis


def _normal_path(path: Path) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


def _nml_location(path: Path) -> tuple[str, str, str]:
    windows_path = PureWindowsPath(str(path.resolve()))
    drive = windows_path.drive or ""
    directory_parts = windows_path.parent.parts
    if drive and directory_parts and directory_parts[0] == drive + "\\":
        directory_parts = directory_parts[1:]
    directory = "/:" + "/:".join(part.strip("\\/") for part in directory_parts if part.strip("\\/")) + "/"
    return drive, directory, windows_path.name


def _path_from_location(location: ET.Element) -> Path | None:
    volume = location.get("VOLUME", "")
    directory = location.get("DIR", "")
    filename = location.get("FILE", "")
    if not filename:
        return None
    path_bits = [part for part in directory.split("/:") if part]
    if volume:
        return Path(PureWindowsPath(volume + "\\", *path_bits, filename))
    return Path(PureWindowsPath(*path_bits, filename))


def new_collection() -> ET.ElementTree:
    root = ET.Element("NML", {"VERSION": "20"})
    ET.SubElement(root, "HEAD", {"COMPANY": "DawoCue", "PROGRAM": "DawoCue for Traktor 4"})
    ET.SubElement(root, "COLLECTION", {"ENTRIES": "0"})
    return ET.ElementTree(root)


def load_collection(path: str | Path | None) -> ET.ElementTree:
    if path is None:
        return new_collection()
    source = Path(path)
    tree = ET.parse(source)
    root = tree.getroot()
    if root.tag != "NML":
        raise ValueError("Vybraný soubor není kolekce NML.")
    return tree


def _collection(tree: ET.ElementTree) -> ET.Element:
    collection = tree.getroot().find("COLLECTION")
    if collection is None:
        collection = ET.SubElement(tree.getroot(), "COLLECTION", {"ENTRIES": "0"})
    return collection


def _find_entry(collection: ET.Element, track_path: Path) -> ET.Element | None:
    wanted = _normal_path(track_path)
    for entry in collection.findall("ENTRY"):
        location = entry.find("LOCATION")
        if location is None:
            continue
        existing_path = _path_from_location(location)
        if existing_path is not None and _normal_path(existing_path) == wanted:
            return entry
    return None


def _update_entry(entry: ET.Element, analysis: TrackAnalysis) -> None:
    entry.set("TITLE", analysis.path.stem)
    entry.set("MODIFIED_DATE", datetime.now().strftime("%Y/%m/%d"))
    entry.set("MODIFIED_TIME", datetime.now().strftime("%H:%M:%S"))

    location = entry.find("LOCATION")
    if location is None:
        location = ET.SubElement(entry, "LOCATION")
    volume, directory, filename = _nml_location(analysis.path)
    location.attrib.update({"DIR": directory, "FILE": filename, "VOLUME": volume, "VOLUMEID": ""})

    info = entry.find("INFO")
    if info is None:
        info = ET.SubElement(entry, "INFO")
    info.set("KEY", analysis.musical_key)
    info.set("PLAYTIME_FLOAT", f"{analysis.duration_seconds:.6f}")

    tempo = entry.find("TEMPO")
    if tempo is None:
        tempo = ET.SubElement(entry, "TEMPO")
    tempo.attrib.update({"BPM": f"{analysis.bpm:.6f}", "BPM_QUALITY": "100.000000"})

    for cue in list(entry.findall("CUE_V2")):
        try:
            slot = int(cue.get("HOTCUE", "-1"))
        except ValueError:
            slot = -1
        if 0 <= slot <= 7:
            entry.remove(cue)

    for cue in sorted(analysis.hotcues, key=lambda item: item.slot):
        ET.SubElement(
            entry,
            "CUE_V2",
            {
                "NAME": cue.name,
                "DISPL_ORDER": str(cue.slot),
                "TYPE": str(cue.cue_type),
                "START": f"{cue.time_seconds * 1000.0:.6f}",
                "LEN": "0.000000",
                "REPEATS": "-1",
                "HOTCUE": str(cue.slot),
            },
        )


def apply_analyses(tree: ET.ElementTree, analyses: list[TrackAnalysis]) -> ET.ElementTree:
    result = copy.deepcopy(tree)
    collection = _collection(result)
    for analysis in analyses:
        entry = _find_entry(collection, analysis.path)
        if entry is None:
            entry = ET.SubElement(collection, "ENTRY")
        _update_entry(entry, analysis)
    collection.set("ENTRIES", str(len(collection.findall("ENTRY"))))
    return result


def export_collection(
    source_path: str | Path | None,
    output_path: str | Path,
    analyses: list[TrackAnalysis],
) -> tuple[Path, Path | None]:
    output = Path(output_path).resolve()
    source = Path(source_path).resolve() if source_path else None
    if source is not None and _normal_path(source) == _normal_path(output):
        raise ValueError("Vstupní a výstupní NML nesmí být stejný soubor.")
    if not analyses:
        raise ValueError("Nejdříve analyzujte alespoň jednu skladbu.")

    tree = apply_analyses(load_collection(source), analyses)
    output.parent.mkdir(parents=True, exist_ok=True)
    backup: Path | None = None
    if source is not None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = output.with_name(f"{source.stem}_backup_{timestamp}{source.suffix}")
        shutil.copy2(source, backup)

    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile("wb", delete=False, dir=output.parent, suffix=".nml.tmp") as temp_file:
            temp_name = temp_file.name
            ET.indent(tree, space="  ")
            tree.write(temp_file, encoding="utf-8", xml_declaration=True)
        ET.parse(temp_name)
        os.replace(temp_name, output)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)
    return output, backup
