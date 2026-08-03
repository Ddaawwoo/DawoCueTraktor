from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .analyzer import analyze_audio
from .models import TrackAnalysis
from .traktor_nml import export_collection


AUDIO_TYPES = [
    ("Hudební soubory", "*.mp3 *.wav *.flac *.aiff *.aif *.ogg *.m4a"),
    ("Všechny soubory", "*.*"),
]


class DawoCueApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("DawoCue for Traktor 4 – MVP 0.2")
        self.root.geometry("1020x650")
        self.root.minsize(850, 520)

        self.paths: list[Path] = []
        self.analyses: dict[str, TrackAnalysis] = {}
        self.source_nml = tk.StringVar()
        self.output_nml = tk.StringVar()
        self.status = tk.StringVar(value="Přidejte skladby a spusťte analýzu.")
        self._build_ui()

    def _build_ui(self) -> None:
        style = ttk.Style()
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))

        header = ttk.Frame(self.root, padding=14)
        header.pack(fill="x")
        ttk.Label(header, text="DawoCue for Traktor 4", font=("Segoe UI", 20, "bold")).pack(side="left")
        ttk.Button(header, text="Přidat skladby", command=self.add_tracks).pack(side="right", padx=(8, 0))
        self.analyze_button = ttk.Button(header, text="Analyzovat vše", style="Accent.TButton", command=self.analyze_all)
        self.analyze_button.pack(side="right")

        columns = ("file", "bpm", "key", "duration", "state")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", selectmode="browse")
        headings = {"file": "Skladba", "bpm": "BPM", "key": "Tónina", "duration": "Délka", "state": "Stav"}
        widths = {"file": 440, "bpm": 90, "key": 90, "duration": 90, "state": 170}
        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], anchor="w" if column in ("file", "state") else "center")
        self.tree.pack(fill="both", expand=True, padx=14)
        self.tree.bind("<Double-1>", self.edit_selected)

        export = ttk.LabelFrame(self.root, text="Bezpečný export do Traktoru", padding=12)
        export.pack(fill="x", padx=14, pady=14)
        ttk.Label(export, text="Původní collection.nml:").grid(row=0, column=0, sticky="w")
        ttk.Entry(export, textvariable=self.source_nml).grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Button(export, text="Vybrat", command=self.choose_source).grid(row=0, column=2)
        ttk.Label(export, text="Nová exportní kopie:").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(export, textvariable=self.output_nml).grid(row=1, column=1, sticky="ew", padx=8, pady=(8, 0))
        ttk.Button(export, text="Vybrat", command=self.choose_output).grid(row=1, column=2, pady=(8, 0))
        ttk.Button(export, text="Exportovat kopii NML", style="Accent.TButton", command=self.export_nml).grid(row=2, column=1, sticky="e", pady=(12, 0))
        export.columnconfigure(1, weight=1)

        ttk.Label(self.root, textvariable=self.status, padding=(14, 0, 14, 12)).pack(fill="x")

    def add_tracks(self) -> None:
        selected = filedialog.askopenfilenames(title="Vyberte skladby", filetypes=AUDIO_TYPES)
        known = {str(path).casefold() for path in self.paths}
        for name in selected:
            path = Path(name).resolve()
            if str(path).casefold() in known:
                continue
            self.paths.append(path)
            known.add(str(path).casefold())
            self.tree.insert("", "end", iid=str(path), values=(path.name, "–", "–", "–", "Čeká"))
        self.status.set(f"Ve frontě je {len(self.paths)} skladeb.")

    def analyze_all(self) -> None:
        if not self.paths:
            messagebox.showinfo("DawoCue", "Nejdříve přidejte alespoň jednu skladbu.")
            return
        self.analyze_button.configure(state="disabled")
        threading.Thread(target=self._analyze_worker, daemon=True).start()

    def _analyze_worker(self) -> None:
        errors: list[str] = []
        for index, path in enumerate(self.paths, start=1):
            self.root.after(0, self._set_row_state, path, f"Analyzuji {index}/{len(self.paths)}…")
            try:
                analysis = analyze_audio(path)
                self.analyses[str(path)] = analysis
                self.root.after(0, self._show_analysis, analysis)
            except Exception as exc:
                errors.append(f"{path.name}: {exc}")
                self.root.after(0, self._set_row_state, path, "Chyba")
        self.root.after(0, self._analysis_finished, errors)

    def _set_row_state(self, path: Path, state: str) -> None:
        values = list(self.tree.item(str(path), "values"))
        values[-1] = state
        self.tree.item(str(path), values=values)

    def _show_analysis(self, analysis: TrackAnalysis) -> None:
        minutes, seconds = divmod(int(analysis.duration_seconds), 60)
        self.tree.item(
            str(analysis.path),
            values=(analysis.path.name, f"{analysis.bpm:.2f}", analysis.musical_key, f"{minutes}:{seconds:02d}", "Hotovo – dvojklik pro úpravu"),
        )

    def _analysis_finished(self, errors: list[str]) -> None:
        self.analyze_button.configure(state="normal")
        self.status.set(f"Hotovo: {len(self.analyses)} skladeb, chyb: {len(errors)}.")
        if errors:
            messagebox.showwarning("Některé skladby se nepodařilo analyzovat", "\n".join(errors[:10]))

    def edit_selected(self, _event=None) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        analysis = self.analyses.get(selected[0])
        if analysis is None:
            messagebox.showinfo("DawoCue", "Tuto skladbu je nejdříve potřeba analyzovat.")
            return
        CueEditor(self.root, analysis)

    def choose_source(self) -> None:
        name = filedialog.askopenfilename(title="Původní collection.nml", filetypes=[("Traktor NML", "*.nml")])
        if name:
            self.source_nml.set(name)
            if not self.output_nml.get():
                source = Path(name)
                self.output_nml.set(str(source.with_name("DawoCue Export.nml")))

    def choose_output(self) -> None:
        name = filedialog.asksaveasfilename(title="Uložit bezpečnou kopii", defaultextension=".nml", filetypes=[("Traktor NML", "*.nml")])
        if name:
            self.output_nml.set(name)

    def export_nml(self) -> None:
        if not self.source_nml.get() or not self.output_nml.get():
            messagebox.showinfo("DawoCue", "Vyberte původní collection.nml i cestu pro novou kopii.")
            return
        try:
            output, backup = export_collection(self.source_nml.get(), self.output_nml.get(), list(self.analyses.values()))
        except Exception as exc:
            messagebox.showerror("Export se nezdařil", str(exc))
            return
        backup_text = f"\nZáloha vstupu: {backup}" if backup else ""
        messagebox.showinfo("Export je hotový", f"Nová kolekce: {output}{backup_text}\n\nImportujte ji v Traktoru přes Import Another Collection.")


class CueEditor(tk.Toplevel):
    def __init__(self, parent: tk.Misc, analysis: TrackAnalysis) -> None:
        super().__init__(parent)
        self.analysis = analysis
        self.title(f"Hot Cues – {analysis.path.name}")
        self.resizable(False, False)
        self.entries: list[tuple[tk.StringVar, tk.StringVar]] = []
        frame = ttk.Frame(self, padding=14)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Slot", font=("Segoe UI", 9, "bold")).grid(row=0, column=0)
        ttk.Label(frame, text="Čas v sekundách", font=("Segoe UI", 9, "bold")).grid(row=0, column=1)
        ttk.Label(frame, text="Název", font=("Segoe UI", 9, "bold")).grid(row=0, column=2)
        for row, cue in enumerate(analysis.hotcues, start=1):
            time_var = tk.StringVar(value=f"{cue.time_seconds:.3f}")
            name_var = tk.StringVar(value=cue.name)
            self.entries.append((time_var, name_var))
            ttk.Label(frame, text=str(cue.slot + 1)).grid(row=row, column=0, padx=8, pady=4)
            ttk.Entry(frame, textvariable=time_var, width=18).grid(row=row, column=1, padx=8, pady=4)
            ttk.Entry(frame, textvariable=name_var, width=34).grid(row=row, column=2, padx=8, pady=4)
        ttk.Button(frame, text="Uložit změny", command=self.save).grid(row=10, column=2, sticky="e", pady=(12, 0))
        self.transient(parent)
        self.grab_set()

    def save(self) -> None:
        try:
            for cue, (time_var, name_var) in zip(self.analysis.hotcues, self.entries):
                value = float(time_var.get().replace(",", "."))
                if not 0 <= value <= self.analysis.duration_seconds:
                    raise ValueError(f"Čas slotu {cue.slot + 1} je mimo délku skladby.")
                cue.time_seconds = value
                cue.name = name_var.get().strip() or f"CUE {cue.slot + 1}"
        except ValueError as exc:
            messagebox.showerror("Neplatná hodnota", str(exc), parent=self)
            return
        self.destroy()


def run_app() -> None:
    root = tk.Tk()
    DawoCueApp(root)
    root.mainloop()
