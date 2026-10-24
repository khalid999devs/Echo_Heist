# Suhita: Windows setup and P04 handoff

Updated **2026-10-25**. Repository: [khalid999devs/Echo_Heist](https://github.com/khalid999devs/Echo_Heist). Use native Windows x64 / PowerShell for desktop QA. **P01-P03 are complete; P04-SR1/SR2/SR3 are next.** You lead logic and Khalid leads complex visuals. Read the [owner guide](../owners/SUHITA.md), [P03 combined handoff](../../tracking/handoffs/khalid/day_02/phase03/P03.md), [P04 specification](../../planning/phases/intelligence/PHASE_04.md) and Khalid's new [P04 presentation handoff](../../tracking/handoffs/khalid/day_02/phase04/P04.md) on `work/khalid-p04`.

## Inspect and create the checkout

Check Git and uv; install only missing tools through their official installers. Existing project WinGet path:

```powershell
winget install --id Git.Git --exact --source winget
winget install --id astral-sh.uv --exact --source winget
```

[Git for Windows](https://git-scm.com/install/windows), [uv installation](https://docs.astral.sh/uv/getting-started/installation/). Reopen the terminal if PATH needs refreshing. Do not change system-wide PowerShell execution policy.

Clone if absent:

```powershell
git clone https://github.com/khalid999devs/Echo_Heist.git
Set-Location Echo_Heist
```

For an existing checkout inspect status, remotes and local commits first. Preserve local changes; never reset/overwrite them. On a clean checkout for this new assignment:

```powershell
git status --short --branch
git fetch origin --prune
git switch -c work/suhita-p04 origin/main
git merge --no-ff origin/work/khalid-p04
```

If P04 already exists, inspect/resume it and merge current main and Khalid's presentation branch normally as needed. Inspect its handoff/claims before resolving overlaps; never force/reset away local work. Main is still the P03 baseline, so fetching main alone does not retrieve the new port/screens. A separate worktree is appropriate when unrelated edits must be preserved. P02/P03 branches are historical; do not redo their completed work. Verify main contains the schema-9 P03 handoff before dependent implementation. Use Suhita's own Git identity/account; ask her name/email once only if missing. Public clone access does not prove push access.

## Verify the locked source baseline

Run sequentially and inspect exit codes before dependent commands; PowerShell may otherwise continue after failure.

```powershell
uv python install 3.13
uv sync --locked --all-extras --python 3.13
uv run --locked python -c "import platform; assert platform.machine().lower() in {'amd64', 'x86_64'}, platform.machine(); print(platform.python_version(), platform.machine())"
uv run --locked python scripts/checks/run.py
uv run --locked python scripts/experiments/p03_evidence.py --output output/windows-p04/baseline-evidence.json
uv run --locked echo-heist --data-dir .local/suhita-p04
```

Recorded baselines: **195 tests on main / 207 on Khalid's P04 presentation branch**, structure/Ruff/format/strict types PASS, Python 3.13.16, fingerprint **9**; record your actual fetched commit/version/count. Keep the dependency lock. Suhita's earlier Windows laptop had a 30-second smoke timeout with 35-46-second resource loading; record a recurrence honestly. Hosted Windows checks/build/frozen dummy smoke pass; that does not prove your physical display/audio or packaged playthrough.

Desktop: cinematic loading → Chapter → Play / Human / Launch → pressure-door entrance → actual two-floor mission. WASD/arrows move; C crouches/creeps; Shift uses 3-second sprint / 4-second recharge; E stairs/hold Core; Q Echo; F EMP; Space stun; Tab paused map; Esc pause. F3 opens real defender teaching data; 1-4 or tabs select guards. Inspect both routes, core/lockdown/extraction, capture/interrupt/retry, witnessed/unseen cover, pointer alignment and audio/window/fullscreen. New Workshop controls are ready, but Companion deployment stays unavailable until your real gateway advertises it. With that gateway, F2 shows the actual Companion/NEXUS/Interceptor records; 1-3 or tabs select them. No separate sitting action exists.

Use an isolated profile; do not copy Mac environments/apps to Windows. A muted run can isolate audio failure but cannot prove audio works.

## Implement P04 only

Retrieve AGENTS, START_HERE, your owner guide, development hub, current Status/claims, Workload, P04, code rules, architecture/guard contracts, approved scoring and blueprint pp. 10-14, 16-18. Retrieve the schema-9 P03 handoff plus historical physical fixture/stair/posture contracts.

Claim **P04-SR1/SR2/SR3**. Implement Companion FSM/utility/observed-risk A*/real bounded belief-only MCTS; Interceptor minimax/alpha-beta and physical movement; evidence-limited NEXUS, versioned protocols/reset and functional first-launch deployment. Use `core/contracts/autonomy/` and the [integration port](../../architecture/integration/autonomy/PRESENTATION.md): implement `AutonomyGateway`, connect `GameFlow(..., autonomy_gateway=gateway)` in startup composition, and return actual runtime actor IDs/metrics/reset results. Do not import `tests.fixtures.autonomy` into production; it is synthetic visual QA only. Preserve the verified Sentinel/Tracker, geometry, hiding, Human mode, input/audio and cinematic flow. No hidden-state cheats, recorded path pretending to be AI, scene redesign or P05 lifecycle work.

## Packaging and handoff

When code/resource/entry changes require a native package check:

```powershell
uv run --locked --all-extras python scripts/packaging/build.py
uv run --locked --all-extras python scripts/packaging/smoke.py dist/EchoHeist/EchoHeist.exe --output-dir output/windows-p04/native-smoke
```

Inspect actual smoke results; nine checks currently exist. Native audio/display requires no mute/dummy-video. Open the executable with its support files and inspect gameplay; never ship the EXE alone. Record actual platform/hardware/commit/commands/hash/results under `docs/development/quality/reports/phase04/windows/` when produced. Large artifacts stay in ignored output/dist; unavailable hardware/builds remain NOT_RUN.

Record `docs/development/tracking/handoffs/suhita/day_02/P04.md` with APIs/files, real autonomous win/failure/search evidence, tests, visual dependencies and exact inspection steps. Commit naturally with your own identity and push `work/suhita-p04` when access permits. Keep main for integration; no force push. Stop after P04 SR slices. KR1/KR2 and combined acceptance are required before closing P04; no automatic P05 work, scoring-rule change, spawned agent or external teammate message.

## Starting prompt

```text
I'm Suhita, on Windows x64.
Clone https://github.com/khalid999devs/Echo_Heist.git or safely reuse my checkout,
preserving local changes. Fetch current main and verify it contains the P03
schema-9 combined handoff. Retrieve and normally merge origin/work/khalid-p04
into my work branch to use Khalid's new port/screens; preserve any local work.

Read AGENTS.md, docs/development/workflow/START_HERE.md,
docs/development/workflow/owners/SUHITA.md and
docs/development/workflow/setup/WINDOWS_SUHITA.md.
Follow their context sequence for Status/claims, blueprint, Workload, P04,
P03 handoff/guard contracts, code rules and approved scoring.
Read docs/development/tracking/handoffs/khalid/day_02/phase04/P04.md and
docs/development/architecture/integration/autonomy/PRESENTATION.md.

Set up and verify the locked Windows environment. Create/resume work/suhita-p04,
check claims, then implement only P04-SR1/SR2/SR3: real Companion FSM/utility/A*/
belief-only MCTS, Interceptor minimax/alpha-beta, evidence-limited NEXUS,
protocol persistence/reset and functional deployment. Preserve existing Human
play, Sentinel/Tracker, visuals, geometry, stairs, posture and audio/input.
Implement AutonomyGateway and connect it at GameFlow; expose actual immutable
metrics. Claim narrow composition wiring, preserve Khalid's UI and do not use
the scripted QA fixture as a controller or algorithm evidence.

Prove real autonomous win/capture and algorithm execution, run meaningful
checks, record actual Windows results and a runnable handoff, then guide me
through inspecting it. Use my Git identity and short natural commits without
assistant attribution; push my branch when access permits. Keep main for
integration. Stop at my P04 slices; do not start P05, change scoring rules,
spawn agents or send external teammate messages.
```
