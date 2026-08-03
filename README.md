# DawoCue for Traktor 4 – MVP 0.2

Samostatná česká Windows aplikace pro přípravu BPM, tóniny a osmi Hot Cue bodů a pro bezpečný export do kopie Traktor `collection.nml`.

## Nejjednodušší cesta bez Pythonu

Pokud máte Git a účet GitHub, použijte návod [NAVOD_GIT_CZ.md](NAVOD_GIT_CZ.md). GitHub sestaví samostatný soubor `DawoCueTraktor.exe` za vás.

## Co aplikace umí

- přidat více souborů MP3, WAV, FLAC, AIFF, OGG nebo M4A,
- odhadnout BPM, první beat a tóninu pomocí knihovny librosa,
- navrhnout osm Hot Cue bodů zarovnaných na beaty a fráze,
- ručně upravit čas i název každého bodu,
- načíst existující `collection.nml` a zachovat jeho ostatní obsah,
- aktualizovat nebo přidat vybrané skladby,
- exportovat změny do nové bezpečné kopie NML,
- vytvořit vedle exportu zálohu vstupní kolekce.

> Traktor musí být při práci s kolekcí zavřený. Doporučený postup je exportovanou kolekci nejprve importovat přes **Import Another Collection**. Aplikace nevytváří proprietární waveform cache Traktoru; Traktor si ji může dopočítat při prvním načtení skladby.

## Spuštění ze zdrojových souborů

Tato možnost vyžaduje Python 3.11:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Ve Windows lze také spustit `run_windows.bat`.

## Testy

```powershell
py -3.11 -m unittest discover -s tests -v
```

## Sestavení EXE ručně

```powershell
py -3.11 -m pip install -r requirements-build.txt
py -3.11 -m PyInstaller --noconfirm --clean DawoCueTraktor.spec
$process = Start-Process -FilePath ".\dist\DawoCueTraktor.exe" -ArgumentList "--self-test" -Wait -PassThru
$process.ExitCode
```

Výsledkem je jeden soubor `dist\DawoCueTraktor.exe`.

## Bezpečnost dat

Aplikace odmítne použít stejný soubor jako vstup i výstup. Přesto mějte vlastní zálohu celé složky Traktoru. Formát NML není kompletně veřejně specifikován a první export je vhodné otestovat na malé kolekci.
