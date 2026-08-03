# Jak získat Windows EXE, když máte jen Git

Python do počítače instalovat nemusíte. Projekt nahrajete na GitHub a jeho servery vytvoří samostatný `DawoCueTraktor.exe`.

## 1. Vytvořte prázdný repozitář

1. Přihlaste se na [github.com](https://github.com/).
2. Klikněte na **New repository**.
3. Zadejte například název `DawoCueTraktor`.
4. Nezaškrtávejte přidání README, licence ani `.gitignore`.
5. Klikněte na **Create repository** a zkopírujte zobrazenou HTTPS adresu.

## 2. Nahrajte projekt pomocí Gitu

Rozbalte tento ZIP. Ve složce projektu klikněte pravým tlačítkem a otevřete **Git Bash Here**. Zadejte postupně:

```bash
git init
git add .
git commit -m "DawoCue for Traktor"
git branch -M main
git remote add origin SEM_VLOZTE_HTTPS_ADRESU_REPOZITARE
git push -u origin main
```

Místo `SEM_VLOZTE_HTTPS_ADRESU_REPOZITARE` vložte adresu z GitHubu, například:

```bash
git remote add origin https://github.com/VASE_JMENO/DawoCueTraktor.git
```

Pokud Git při prvním commitu požádá o jméno a e-mail, nastavte je podle pokynů, které vypíše, a příkaz `git commit` zopakujte.

## 3. Nechte GitHub vytvořit EXE

1. Otevřete na GitHubu nahraný repozitář.
2. Klikněte na záložku **Actions**.
3. Otevřete workflow **Sestavit Windows EXE**.
4. Pokud se sestavení nespustilo automaticky, klikněte na **Run workflow** a potvrďte zeleným tlačítkem.
5. Počkejte, až se zobrazí zelená fajfka.
6. Otevřete hotové sestavení a dole v části **Artifacts** stáhněte `DawoCue-Traktor-Windows`.
7. Stažený ZIP rozbalte a spusťte `DawoCueTraktor.exe`.

GitHub nejprve automaticky otestuje práci s NML. Potom vytvoří EXE a ještě ho spustí v kontrolním režimu. Artefakt je na GitHubu dostupný 30 dní; stažený EXE zůstane samozřejmě váš.

## Když Windows zobrazí SmartScreen

Program není komerčně digitálně podepsaný, takže Windows může zobrazit upozornění. Pokud jste EXE sestavili ve svém repozitáři z tohoto projektu, zvolte **Další informace** a potom **Přesto spustit**.

## Použití aplikace

1. Klikněte na **Přidat skladby**.
2. Klikněte na **Analyzovat vše**.
3. Dvojklikem na skladbu případně upravte časy a názvy Hot Cue bodů.
4. Vyberte původní `collection.nml`.
5. Zvolte jiný soubor jako bezpečný export.
6. Klikněte na **Exportovat kopii NML**.
7. Export načtěte v Traktoru přes **Import Another Collection**.

Typická cesta ke kolekci je:

```text
C:\Users\VAŠE_JMÉNO\Documents\Native Instruments\Traktor 4.x.x\collection.nml
```

Při exportu mějte Traktor zavřený a původní kolekci nemažte.
