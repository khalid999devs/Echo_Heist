# P08-SR1 physical Windows QA (Suhita)

Status: **PARTIAL — automated native checks (2026-11-16) and 9 of 15 in-game steps (2026-11-16/17) run; Human wins, props and calibration remain.** The in-game steps were driven on the physical desktop (real display and audio) by the agent at the user's request. Human wins, props and calibration still need Suhita playing. Hosted CI on `187800c` passed (Linux headless, Windows x64 and macOS arm64 build/frozen smoke).

Candidate: `work/suhita-p06-p08` at **`59ed6ff`** (merge of main `34d68cf`; the records commit follows). Machine: HP laptop, 12th Gen Intel Core i5-1235U, 7.7 GB RAM, Intel UHD Graphics, Realtek HD audio, Windows NT 10.0.26300 x64, uv 0.13.1, CPython 3.13.16. Logs: `output/windows-p08/` (ignored).

### Automated native results (`.local/p08/2-qa.ps1`)

| Step | Result |
| --- | --- |
| Fast-forward to `59ed6ff`, `uv sync --locked --all-extras` | PASS |
| `scripts/checks/run.py` | structure, Ruff, format, mypy PASS; pytest **327 passed, 1 failed** in 503 s. The failure is `tests/smoke/desktop/test_bootstrap.py` hitting its 30 s limit (issue 1) |
| Four-scenario comparison | 16/16 runs identical to the recorded CSV; hash `1e724571…ca526b1` at `59ed6ff`, equal to the Linux shell's. With `765a164` substituted it is the recorded `2eb0c8e5…` |
| `scripts/packaging/build.py` | PASS: `dist/EchoHeist/EchoHeist.exe` and platform ZIP |
| `scripts/packaging/smoke.py` (frozen, real `windows` video driver) | **9/9 PASS**, audio `ready`, same state/event hashes; startup 35.5 s (issue 1) |

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

The comparison hash includes the short commit ID, so it changes with every commit. At `765a164` the four-scenario hash was `2eb0c8e5ff8a6624d821884f467db1af8d393aacee38d718deb416f7c23673c0`; on a later commit, recompute it with that commit ID substituted, or compare the 16 runs (outcome, ticks, score, grade, encounters, fingerprint) with `docs/development/quality/experiments/policy-comparison-runs.csv`. After merging main (`59ed6ff`) both checks still match: the merge brought no simulation, AI or data change.

## Checklist

| # | Step | Expected | Result |
| --- | --- | --- | --- |
| 1 | First launch with a fresh `--data-dir` | Opening, menu; Human and Companion both available || PASS (packaged build, default user-data folder with no earlier history or profiles): loading, title, briefing; Human and Companion offered; Report disabled until a run ends |
| 2 | Human: play to a real win | Core theft, lockdown, extraction ending; results show score = 50 + stealth + pace, grade, encounters, tool counts || NOT_RUN (needs a player) |
| 3 | Human: get spotted once, escape, win | Encounters 1, stealth 28, grade A or B; Ghost not awarded || NOT_RUN (needs a player) |
| 4 | Human: get captured | 0 / F, no achievements; R retries the same seed; N asks for a new seed || PASS (2026-11-17, separate QA save folder): a Service Wing Sentinel captured the operative at 01:12 → CAPTURED 0 / F, encounters 1, no achievement labels; N opens the seed dialog offering 1043; Retry returns to the briefing on seed 1042. Two further attempts to reach the Service Wing props on that seed were also captured, so props stay open |
| 5 | Pause → Abort | Confirmation, then 0 / F report || PASS: confirmation, then ABORTED 0 / F, 0/50, 0/40, 0/10, encounters 0, tools 0/0/0, seed 1042 |
| 6 | Results → D → H | Saved history lists the runs newest first; relaunch keeps them || PASS: details, then saved history newest first (Companion win, Human abort); after quit, relaunch and one more abort, history shows 3 entries in order |
| 7 | Companion: Ghost, Balanced, Rush on one seed | Different visible decisions; win or capture; AI Master on a win || PARTIAL: Balanced seed 1042 WIN at 01:22, 76 / A = 50 + 16 (two encounters) + 10, AI MASTER / SPEEDRUNNER, Echo 3 EMP 1 Stun 2; live MCTS panel showed 64 simulations. Ghost/Rush not run natively (covered by the 96-run comparison) |
| 8 | Workshop → Saved Policies | Save, overwrite by same name, load, delete with confirmation; relaunch keeps them || PASS: save "QA Balanced", overwrite with Ghost under the same name (one entry), load restores Ghost values over Rush, kept after relaunch, delete asks to confirm, list empty afterwards |
| 9 | Workshop → reset NEXUS memory | Next attempt is the baseline || PASS: after the win NEXUS showed "Verify Echo" (3 Echo decoys seen); confirmed reset returns to Baseline / no active protocol, still baseline after relaunch |
| 10 | Settings → Controls: remap, save, relaunch | Remap persists; invalid saves fall back with a notice || PASS: Echo Q→R, Save Preferences, relaunch keeps R; Restore Defaults returns Q. Invalid-file fallback not tried by hand (automated tests cover it) |
| 11 | Accessibility: captions, high contrast, reduced flash, volumes, window/fullscreen | All work and persist where offered || PARTIAL: captions shown in play ("[Lockdown alarm]"); high-contrast HUD ON persists after relaunch; window resize re-lays out correctly. Reduced flash, volumes and fullscreen not exercised |
| 12 | Props: lockers, doors, glass, canisters | As in the P05 handoff; sounds audible and captioned || NOT_RUN (needs a player) |
| 13 | Corrupt `policy-profiles.json` by hand, relaunch, open profiles | Notice "kept as …corrupt-…json", then a working empty list || NOT_RUN by hand (the user-data folder is outside the connected project folder); automated quarantine tests pass |
| 14 | Downloaded Windows build (when Khalid publishes one) | Extract, launch, play to results; saves land in the user data folder || PARTIAL: the locally built package ran to results and saved in the user-data folder; no published download yet |
| 15 | Calibration timing | Note the in-game time of 2–3 of your own clean wins for the pace reference || NOT_RUN (needs Suhita's own clean wins) |

## Issues found

| Issue | Severity | Owner | Fix commit |
| --- | --- | --- | --- |
| 1. Startup resource preparation is slow on this laptop: frozen build 35.5 s; source `--smoke-frames 2` 54–72 s for **every** commit tried (old main `1136788`, `87302a9`, main `34d68cf`, this branch) while a stray helper process also loaded the CPU. P04's run on the same laptop started in 6.2 s. The 30 s `test_bootstrap` limit therefore fails here for main too. The merge did not change startup (Linux shell: main 10.4–15.2 s, branch 9.5–14.8 s) | Medium (P07 performance) | Khalid (startup presentation); shared smoke-test limit | — |
| 2. Controls screen says "Applied for this session." although the remap is saved by Save Preferences and persists | Low (copy) | Khalid | — |
| 3. Title Report button is disabled after relaunch even though saved history exists; history is reachable only from a result's D → H | Low (UX) | Khalid | — |
| 4. Draft player guide still says remaps/captions are session-only and Companion/saved profiles unavailable | Low (docs, P08-KR2) | Khalid | — |
