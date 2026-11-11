# P08-SR1 physical Windows QA (Suhita) — to be filled in

Status: **NOT_RUN.** This checklist needs a person at the physical Windows x64 desktop with display and audio; nothing below has been checked by the agent. Record the exact candidate commit, the result of each step and any issue, then fix owned logic issues on the branch.

Candidate: `work/suhita-p06-p08` at commit `________` (from `git rev-parse --short HEAD`). Machine: ________ (CPU/GPU/RAM, Windows version, display scale).

## Setup (PowerShell, from `E:\Echo_Heist`)

```powershell
git switch work/suhita-p06-p08
git status --short --branch
uv sync --locked --all-extras --python 3.13
New-Item -ItemType Directory -Force output/windows-p08
uv run --locked python scripts/checks/run.py *> output/windows-p08/checks.txt; $LASTEXITCODE
uv run --locked python scripts/experiments/comparison.py --output-dir output/windows-p08/sub --only s21-core-approach,s22-core-approach-late,s23-lockdown-core-chamber,s24-lockdown-north-exit
uv run --locked echo-heist --data-dir .local/qa-p08
```

The four-scenario comparison hash should be `2eb0c8e5ff8a6624d821884f467db1af8d393aacee38d718deb416f7c23673c0` (matched in the container and the Linux shell on this computer at commit `765a164`; later commits that change only documents keep it).

## Checklist

| # | Step | Expected | Result |
| --- | --- | --- | --- |
| 1 | First launch with a fresh `--data-dir` | Opening, menu; Human and Companion both available | |
| 2 | Human: play to a real win | Core theft, lockdown, extraction ending; results show score = 50 + stealth + pace, grade, encounters, tool counts | |
| 3 | Human: get spotted once, escape, win | Encounters 1, stealth 28, grade A or B; Ghost not awarded | |
| 4 | Human: get captured | 0 / F, no achievements; R retries the same seed; N asks for a new seed | |
| 5 | Pause → Abort | Confirmation, then 0 / F report | |
| 6 | Results → D → H | Saved history lists the runs newest first; relaunch keeps them | |
| 7 | Companion: Ghost, Balanced, Rush on one seed | Different visible decisions; win or capture; AI Master on a win | |
| 8 | Workshop → Saved Policies | Save, overwrite by same name, load, delete with confirmation; relaunch keeps them | |
| 9 | Workshop → reset NEXUS memory | Next attempt is the baseline | |
| 10 | Settings → Controls: remap, save, relaunch | Remap persists; invalid saves fall back with a notice | |
| 11 | Accessibility: captions, high contrast, reduced flash, volumes, window/fullscreen | All work and persist where offered | |
| 12 | Props: lockers, doors, glass, canisters | As in the P05 handoff; sounds audible and captioned | |
| 13 | Corrupt `policy-profiles.json` by hand, relaunch, open profiles | Notice "kept as …corrupt-…json", then a working empty list | |
| 14 | Downloaded Windows build (when Khalid publishes one) | Extract, launch, play to results; saves land in the user data folder | |
| 15 | Calibration timing | Note the in-game time of 2–3 of your own clean wins for the pace reference | |

## Issues found

| Issue | Severity | Owner | Fix commit |
| --- | --- | --- | --- |
| | | | |
