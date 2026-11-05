# Suhita: Windows setup and current-main handoff

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

## Starting prompt

```text
I'm Suhita, working on Windows x64.

Clone https://github.com/khalid999devs/Echo_Heist.git or safely reuse my checkout.
Inspect and preserve local changes and unpushed/unmerged work. Fetch/prune, switch
cleanly to main and pull --ff-only; then create work/suhita-p04. If that branch
already contains work, preserve/resume it and merge origin/main instead. Never
hard-reset, clean or delete unmerged work. Use my Git identity.

Read AGENTS.md, docs/development/workflow/START_HERE.md,
docs/development/workflow/owners/SUHITA.md and
docs/development/workflow/setup/WINDOWS_SUHITA.md.
Follow their context sequence for the blueprint, hub, Status/HANDOFFS, WORKLOAD,
P04 specification, code rules, architecture/data contracts and approved scoring/melee.
Read docs/development/tracking/handoffs/khalid/day_03/MAIN.md and P06.md,
day_03/P05.md and MELEE.md, day_02/phase04/P04.md, plus the autonomy,
environment and experience PRESENTATION.md contracts under
docs/development/architecture/integration/.

Main already includes merged PRs #2/#3/#4: the Human game, polished scenes/audio,
Companion/NEXUS/Lab and prop/tool presentation, limited melee, result/profile
interfaces, seed/retry and session controls/accessibility. Baseline is 246 tests,
fingerprint 10. Retired Khalid branches are unnecessary. These merges do not
implement the missing AI, environment lifecycles, score engine or persistence.

Verify the locked Windows environment and actual launch/audio. Check claims, then
claim and complete only P04-SR1/SR2/SR3: genuine Companion FSM/utility/A*/belief-only
MCTS; Interceptor minimax/alpha-beta and physical travel; evidence-limited NEXUS,
versioned protocols/reset and functional first-launch deployment. Implement
AutonomyGateway and wire it to the existing GameFlow/startup. Preserve Khalid's
visuals, experience ports, Human behavior and approved sprint/melee rules. No
hidden-state cheats, replayed Human paths, fake metrics or production QA fixtures.

Keep files <=1000 lines, <=6 direct files/directory, with necessary tests under
root tests/. Verify actual autonomous win/capture, algorithm traces, fairness,
reset/retry and Human regressions; run appropriate checks and native Windows
build/smoke. Record actual results and a runnable P04 handoff, guide my visible
inspection, make short natural commits without assistant attribution, push my
branch and open a reviewable PR to main when access permits.

Later work is P05 environment/tool completion, P06 scoring/policy/persistence,
then P07/P08 evidence and Windows acceptance. Stop after my P04 SR slices; leave
shared visual acceptance open. Do not start later phases, self-merge, redesign
scenes, change scoring rules, spawn agents or message teammates externally.
```
