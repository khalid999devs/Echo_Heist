# Suhita: Windows setup and current P03 handoff

Updated **2026-10-22**. Repository: [khalid999devs/Echo_Heist](https://github.com/khalid999devs/Echo_Heist). Use **native Windows x64 / PowerShell**, not WSL for desktop QA. P01/P02 are complete. Your next assignment is **P03-SR1/SR2/SR3**, with most gameplay logic now yours and complex graphics/scenes Khalid's. The [owner guide](../owners/SUHITA.md) and [revised workload](../../planning/WORKLOAD.md) replace the original P02 start instructions.

## 1. Inspect prerequisites and checkout

Check `git --version` and `uv --version`. Install only missing tools, using official installers; these WinGet IDs are the existing project setup path:

```powershell
winget install --id Git.Git --exact --source winget
winget install --id astral-sh.uv --exact --source winget
```

Reopen the terminal after installation if PATH needs refreshing. Official references: [Git for Windows](https://git-scm.com/install/windows), [uv](https://docs.astral.sh/uv/getting-started/installation/). Do not alter system-wide PowerShell execution policy.

If absent, clone into a new directory:

```powershell
git clone https://github.com/khalid999devs/Echo_Heist.git
Set-Location Echo_Heist
```

For an existing checkout, inspect `git status --short --branch`, `git remote -v` and local commits first. Preserve local changes and never reset/overwrite them. Fetch `git fetch origin --prune`; if the checkout is clean and this is a fresh assignment, create the branch directly from the fetched main:

```powershell
git switch -c work/suhita-p03 origin/main
```

If that branch already exists, inspect/resume it and integrate current main with a normal merge as needed. A clean separate worktree is an alternative when unrelated local edits would be disturbed. Deleted `work/suhita-p02` is historical; its work is already merged. Verify main includes the cinematic/fixture handoff and this revised queue before claiming work.

Use Suhita's own Git identity/account. If identity is absent, request her name/email once; never borrow Khalid's credentials or invent identity. Read-only public clone access does not prove push access.

## 2. Reproduce the locked source baseline

Run sequentially and inspect each exit code before dependent commands; PowerShell may otherwise continue after a native command fails.

```powershell
uv python install 3.13
uv sync --locked --all-extras --python 3.13
uv run --locked python -c "import platform; assert platform.machine().lower() in {'amd64', 'x86_64'}, platform.machine(); print(platform.python_version(), platform.machine())"
uv run --locked echo-heist --headless --seed 1042 --report output/windows-p03/baseline-headless.json
uv run --locked python scripts/checks/run.py
uv run --locked echo-heist --data-dir .local/suhita-profile
```

The recorded baseline has **149 passing tests**, structure/Ruff/format/strict types and Python 3.13.16. Record your actual fetched commit/count/version; do not edit the lock to make reproduction easier. The headless diagnostic alone is not full gameplay acceptance.

Expected desktop: animated loading/core emblem → cinematic chapter menu → Play / Human / Launch → pressure-door entrance → real two-floor Human heist. WASD moves; **C** crouches/creeps; Shift sprints three seconds then recharges four; E uses stairs/hold at Core; Q Echo; F EMP; Space stun; Tab map; Esc pause. Inspect both routes, real core theft/lockdown/extraction and capture/retry. Companion/Workshop screens are currently previews. There is no separate seated action.

Inspect keyboard/mouse, window/fullscreen, audio and muted behavior. The latest recorded Mac QA and Windows hosted dummy-video smoke do not prove your physical Windows display/audio works. Use `--mute` to isolate an audio failure and record it. Data lives in the isolated `.local` profile above; do not copy Mac `.venv`, `.app` or ZIP files to Windows.

## 3. Retrieve context and implement the current slice

Read root AGENTS, START_HERE, your owner guide, development hub, current Status/claims, Workload, **P03**, code rules, architecture/data contracts, approved scoring and PDF pp. 6-11, 16-18. Retrieve the accepted P02 handoff, first Sentinel contract and then the superseding [cinematic/physical-fixture handoff](../../tracking/handoffs/khalid/presentation/CINEMATIC_STARTUP.md) / [scene contract](../../architecture/integration/SCENE_PRESENTATION.md).

Claim P03-SR1/SR2/SR3 and exact files. Finish fair perception/report/capture gaps; implement Tracker A* and legitimate last-seen search; complete validated patrol/chokepoint/geometry revision integration and replay evidence. Reuse Sentinel BFS/FSM/fuzzy, fingerprint-7 geometry, crouch, stair and sprint behavior. Current `can_walk` tiles are conservative; never replace precise fixture bounds with the old invisible barriers.

You own logic under core/AI/level registry/persistence and meaningful tests. Khalid owns complex rendering, art, animation, camera and scene layouts. Narrow functional wiring in shared scene roots is permitted with a clear claim and consumer contract. Do not rewrite the visual game, add fake AI, inspect privileged hidden state or implement P04 algorithms ahead of its gate.

## 4. Native verification when packaging is affected

After a passing source baseline, build/run native checks when code/resource/entry-point changes require a package check:

```powershell
uv run --locked --all-extras python scripts/packaging/build.py
uv run --locked --all-extras python scripts/packaging/smoke.py dist/EchoHeist/EchoHeist.exe --output-dir output/windows-p03/native-smoke
```

The current smoke tool has **nine** checks; inspect its actual summary rather than hard-coding a future count. Native display/audio requires running without `--dummy-video` and without `--mute`. A separate muted run is useful recovery evidence, not audio proof. Open the executable interactively and inspect normal gameplay too. Preserve `EchoHeist.exe` **with its support files**, not the executable alone.

Outputs are `dist/EchoHeist/`, a versioned Windows ZIP and manifest. Record Windows/hardware/Python/commit/commands, archive hash and actual results under `docs/development/quality/reports/phase03/windows/` when produced; keep large captures/logs/builds in ignored output/dist. Packaging or hardware unavailable means NOT_RUN, not a reason to stop independent pure-logic work.

## 5. Handoff and stop

Run appropriate checks plus real default-security win/capture/regression scenarios. Record `docs/development/tracking/handoffs/suhita/day_02/P03.md`: implemented behavior, APIs/files, test results, exact visible inspection steps, Windows evidence and remaining Khalid visual dependencies. Update your revised slices only; the shared P03 gate needs both owners and integrated evidence.

Make short natural commits with your identity and no assistant attribution. Push when your own access permits:

```powershell
git push -u origin work/suhita-p03
```

If push is denied, keep local commits and report the access blocker. Keep main for integration; no force-push or destructive cleanup. **Stop after P03-SR1/SR2/SR3.** Do not silently continue P04, claim Khalid's work complete or send external teammate messages.

## Ready-to-paste starting prompt

```text
I'm Suhita, on Windows x64.

Clone https://github.com/khalid999devs/Echo_Heist.git, or safely reuse the
existing checkout and preserve local changes. Fetch current main.

Read AGENTS.md, docs/development/workflow/START_HERE.md,
docs/development/workflow/owners/SUHITA.md and
docs/development/workflow/setup/WINDOWS_SUHITA.md. Follow their context
sequence to retrieve the blueprint, revised WORKLOAD, current Status/claims,
P03, latest cinematic/fixture handoff, contracts, code rules and scoring.

The split has changed: I own most gameplay logic; Khalid owns complex
visuals/scenes. P01/P02 are complete. Set up and verify the locked Windows
environment, then create or resume work/suhita-p03 from current main.
Claim and finish only P03-SR1, P03-SR2 and P03-SR3: remaining fair perception,
Tracker A*/defender behavior, registry/geometry integration and replay proof.
Reuse verified Sentinel, collision, crouch, stair and sprint behavior.
Preserve Khalid's graphics and make only claimed functional scene wiring.

Run meaningful checks and real gameplay scenarios; record actual Windows
results, a runnable handoff and the exact steps for me to inspect the game.
Use my Git identity, make short natural commits without assistant attribution,
and push my branch when access permits. Keep main for integration.

Stop at my P03 boundary. Do not start P04 or close the shared P03 gate until
Khalid's visual slices and combined verification are complete. Do not change
approved scoring rules, spawn agents or send external teammate messages.
```
