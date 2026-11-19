# Suhita: Windows setup and current-main handoff

## Current instructions — 2026-11-20

Read [Status](../../tracking/STATUS.md) and the [runnable release handoff](../../tracking/handoffs/khalid/day_04/RELEASE_CANDIDATE.md). Fetch current main while preserving local changes and unpublished commits. Use a new branch for newly assigned fixes.

Build the current Windows x64 candidate and run the physical P08 checklist. Include both exits, a capture and retry, a pursuit escaped through cover, stun audio and nearby guard reaction. Record the actual commit, archive hash and observed behavior.

The earlier dated instructions below are historical checkpoints. Their P04/P05 implementation queues, unavailable-Companion statements, old branch commands and fingerprint/test baselines are superseded by this section. Preserve their contracts and authorship. Windows setup commands remain usable; replace old data/output directory names with the current review name and omit creation of the merged work branch.

## Earlier checkpoint instructions

**2026-11-05 update:** SR1/SR2/SR3 are on `work/suhita-p04`, merged with current main; fingerprint is now **11**. Resume that branch and use the run/inspect block in the [SR handoff](../../tracking/handoffs/suhita/day_02/P04.md); the steps below remain the general setup reference.

Updated **2026-10-31**. [Repository](https://github.com/khalid999devs/Echo_Heist), native Windows x64 / PowerShell. PRs #2/#3/#4 are merged into **main**; the former Khalid branches are retired. Main includes the P04/P05/P06 presentation, approved limited melee and current-build delivery preparation. **246 tests / fingerprint 10** is the latest verified baseline; fetch and record the actual current commit. Read the [consolidation handoff](../../tracking/handoffs/khalid/day_03/MAIN.md) and [owner guide](../owners/SUHITA.md). **P01–P03 are complete; P04-SR1/SR2/SR3 is your next assignment.**

## Get the checkout safely

Inspect installed Git/uv and install only missing tools. Existing project WinGet paths:

```powershell
winget install --id Git.Git --exact --source winget
winget install --id astral-sh.uv --exact --source winget
```

Reopen the terminal if PATH needs refresh; do not change system-wide PowerShell execution policy. Clone if absent:

```powershell
git clone https://github.com/khalid999devs/Echo_Heist.git
Set-Location Echo_Heist
```

For an existing checkout, inspect status/remotes/local branches and unpushed commits before changing it. Preserve uncommitted/untracked files and unmerged work; no hard reset, clean or force push. On a clean checkout with no unique main commits:

```powershell
git status --short --branch
git fetch --prune origin
git switch main
git pull --ff-only origin main
git switch -c work/suhita-p04
```

If a meaningful `work/suhita-p04` already exists, preserve/resume it and merge `origin/main` normally rather than recreating it. Use a separate worktree if unrelated edits prevent switching safely. Only delete old local work branches after proving their tips are ancestors of current main and they contain no work to preserve. Your Windows checkout cannot be remotely cleaned from Khalid's Mac. Old handoff branch names are provenance; do not merge deleted `work/khalid-*` branches. Use Suhita's own Git identity/account; ask once if name/email is missing. Public clone does not prove push access.

## Verify the locked environment

Run sequentially, inspecting failures before dependent commands. Keep the lock; use an isolated user-data folder:

```powershell
uv python install 3.13
uv sync --locked --all-extras --python 3.13
uv run --locked python -c "import platform; assert platform.machine().lower() in {'amd64', 'x86_64'}, platform.machine(); print(platform.python_version(), platform.machine())"
uv run --locked python scripts/checks/run.py
uv run --locked python scripts/experiments/p03_evidence.py --output output/windows-p04/baseline-evidence.json
uv run --locked echo-heist --data-dir .local/suhita-p04
```

Recorded source baseline: 246 tests, structure/Ruff/format/strict mypy PASS, fingerprint 10, Python 3.13.16; record your own fetched version/count/results. Hosted Windows build/frozen dummy smoke passes but does not prove physical display/audio. Your earlier laptop showed 35–46-second resource loading against a 30-second smoke timeout; distinguish slow startup from crash and report a recurrence honestly.

Human smoke: cinematic loading → Chapter → Human → Launch → entry airlock → real two-floor mission. WASD/arrows move; C crouches; Shift sprints 3 s then recharges 4 s; E stairs/hold Core; Q Echo; F EMP; Space two-charge emergency stun; Tab paused map; Escape pause. Inspect controls remapping/captions/high contrast, both routes, Core/lockdown/extraction, capture/retry, pointer/fullscreen and audio. Current remaps/caption/contrast are session-only until the P06 persistence port connects; existing volumes/display settings persist. F3 shows real defender traces. Companion and saved scores/profiles/history remain unavailable until actual services connect. No separate sitting action exists.

## Implement P04 only

Follow AGENTS → START_HERE → SUHITA owner context. Read development hub, Status/claims, Workload, P04 specification, code rules, architecture/guard contracts, approved scoring/melee and blueprint pp. 10–14, 16–18. Read P04/P05/MELEE/P06 handoffs already in main and the autonomy/environment/experience presentation contracts. These define ready consumers and later work, not completed AI/persistence.

Claim P04-SR1/SR2/SR3 and exact shared composition files. Implement genuine Companion FSM/utility/observed-risk A*/bounded belief-only MCTS; Interceptor minimax/alpha-beta with physical post travel; evidence-limited NEXUS, versioned protocols/reset and first-launch deployment. Implement `AutonomyGateway` and supply `GameFlow(..., autonomy_gateway=gateway)` in startup composition with real actor IDs and metrics. `tests.fixtures.autonomy` is synthetic QA, never production AI. Preserve Human play, geometry/stairs/posture, applied melee/sprint, scenes/input/audio and P06 ports. No scene redesign or automatic P05/P06 implementation.

Prove actual autonomous win/capture, real MCTS stages/visits/rewards, alpha-beta correctness/pruning, legitimate evidence/coverage and deterministic memory reset. Preserve Human regressions. Record expected behavior versus actual failures and pending connected visual acceptance.

## Native package and handoff

When entry/runtime changes need packaging verification:

```powershell
uv run --locked --all-extras python scripts/packaging/build.py
uv run --locked --all-extras python scripts/packaging/smoke.py dist/EchoHeist/EchoHeist.exe --output-dir output/windows-p04/native-smoke
```

Use native display/audio for physical evidence, not mute/dummy. Retain the executable's complete support folder. Record actual Windows hardware/OS/commit/commands/archive hash/results under `docs/development/quality/reports/phase04/windows/`; large output stays ignored. Write `docs/development/tracking/handoffs/suhita/day_02/P04.md` with actual APIs/events, algorithm/run evidence and exact visual review steps. Use short natural commits with your identity and no assistant attribution; push `work/suhita-p04`, open a reviewable PR against main when permitted, then **stop at P04-SR1/SR2/SR3**. Khalid's real-data visual acceptance and the combined gate still apply. No self-merge, automatic P05 work, scoring-rule change, sub-agents or external teammate messages.

## Current starting prompt

```text
I'm Suhita on Windows x64. Safely reuse or clone
https://github.com/khalid999devs/Echo_Heist.git. Preserve local changes and unique
commits; fetch/prune, switch to main and pull --ff-only. PRs #5/#6 are already
merged. Delete old local work branches only after proving they are in main.

Read AGENTS.md, docs/development/workflow/START_HERE.md,
docs/development/workflow/owners/SUHITA.md, current STATUS.md/HANDOFFS.md, and
docs/development/quality/reports/phase05/review/INTEGRATION.md.
Main has real P04 AI/protocols and P05 interactive props, fingerprint 12,
301 tests. Do not reimplement them or resume the merged branches.

On a new review branch, finish outstanding current-build Windows/native P05
acceptance: doors, glass, canisters, lockers and both-mode tool/capture cues,
alongside Human and Companion launch, pause, outcomes, protocol/reset and audio.
Use actual production behavior; no synthetic fixture as algorithm evidence.
Record exact commands/results and fix reproducible issues within the claimed
boundary. Preserve approved scoring/melee, visuals and ownership. Run relevant
checks and native build/smoke, commit naturally, push and open a PR when ready.
Stop at that review boundary. P06 scoring/policy/profile/history/preferences
implementation requires its own assigned slice and existing contracts.
```
