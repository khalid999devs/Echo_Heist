# Suhita: Windows setup and first implementation handoff

Update 2026-10-21: the [latest scene presentation handoff](../../tracking/handoffs/khalid/day_02/SCENE_PRESENTATION.md) adds timed stairs, new scene names, Workshop/Companion designs and current Windows/Mac build evidence. Read it and Status before continuing. The older P02 prompts below remain historical; do not reimplement completed P02 work or treat preview AI deployment as implemented.

Update 2026-10-20: the original P02 branch/start prompts below are historical. The [integrated P02 handoff](../../tracking/handoffs/khalid/day_01/P02_INTEGRATION.md) is the current gameplay baseline; read [Status](../../tracking/STATUS.md) before claiming P03 work. The PowerShell environment, build and smoke commands remain useful for Windows x64 checks.

Prepared by Khalid on 2026-10-18. Repository: [khalid999devs/Echo_Heist](https://github.com/khalid999devs/Echo_Heist). Platform: **Windows x64**, using PowerShell and native Windows Python, not WSL. P01 is complete. Your first assignment is **P02-S1 and P02-S2**; P02-K1/K2 belong to Khalid. This guide prepares your workstation; it does not transfer P01 implementation ownership to you.

The foundation now passes Windows x64 checks/native build/frozen smoke in hosted CI; see [actual GitHub evidence](../../quality/reports/phase01/GITHUB_CI.md). Its video driver was dummy, so your own interactive Windows desktop check remains necessary. That report links the downloadable Windows artifact too; use source for development.

## 1. Install only missing prerequisites

Inspect `git --version` and `uv --version` first. If either command is unavailable, use its corresponding command below in PowerShell, then reopen the terminal so PATH refreshes:

```powershell
winget install --id Git.Git --exact --source winget
winget install --id astral-sh.uv --exact --source winget
```

Official installation references: [Git for Windows](https://git-scm.com/install/windows), [uv installation](https://docs.astral.sh/uv/getting-started/installation/). If WinGet is unavailable, follow those official installers. Do not change system-wide PowerShell execution policy. No separate pygame installation or virtual-environment activation is needed. The P01 tool baseline used uv 0.12.22; the project accepts uv >=0.8 and the dependency versions come from uv.lock.

## 2. Clone and isolate your work

Run in your chosen projects directory. If the repository is already present, inspect its remote, branch and working changes before using it; do not clone over it or reset it.

```powershell
git clone https://github.com/khalid999devs/Echo_Heist.git
Set-Location Echo_Heist
git status --short
git remote -v
git switch -c work/suhita-p02
```

Use the existing owner branch if resuming it. A public clone requires no GitHub login. Pushing requires your own account's write access; cloning successfully does not prove that access. Never use Khalid's credentials or change Git identity to his. If a commit identity is missing, ask Suhita for her own name/email rather than inventing one.

## 3. Reproduce the locked foundation

From the repository root:

```powershell
uv python install 3.13
uv sync --locked --all-extras --python 3.13
uv run --locked python -c "import platform; assert platform.machine().lower() in {'amd64', 'x86_64'}, platform.machine(); print(platform.python_version(), platform.machine())"
uv run --locked echo-heist --headless --seed 1042 --report output/windows-baseline/headless.json
uv run --locked python scripts/checks/run.py
uv run --locked echo-heist --data-dir .local/suhita-profile
```

Run commands sequentially and inspect each exit code; PowerShell can continue after a native command fails. Stop the dependent step on a nonzero exit. The lock must stay unchanged during reproduction. Python must be 3.13 on x64; a different system Python can remain installed. If uv cannot download Python because of machine/network policy, record the actual error and use an available native x64 Python 3.13 explicitly.

Expected baseline: deterministic five-tick MOVE/WAIT diagnostic, then passing structure/lint/format/strict typing and **21 tests at the original P01 baseline**. Later changes can increase that count. The desktop shows the foundation card and bundled mark at 1280 x 720. Escape/window close exits and prints a JSON diagnostic with resources/settings results. This is the intended shell, not a playable mission. Try `--mute` if audio prevents launch; report the real outcome.

`--data-dir .local/suhita-profile` isolates your development settings. Without it, settings use the Windows application-data directory chosen by platformdirs; the exit JSON prints the actual settings_path. Generated output and .local are ignored by Git. Do not copy Mac .venv, .app or ZIP files to Windows.

## 4. Verify the native Windows baseline

These commands build on Windows itself and run the complete frozen folder outside the checkout with isolated user data:

```powershell
uv run --locked --all-extras python scripts/packaging/build.py
uv run --locked --all-extras python scripts/packaging/smoke.py dist/EchoHeist/EchoHeist.exe --mute --output-dir output/windows-baseline/native-smoke
```

Expected outputs: `dist/EchoHeist/EchoHeist.exe` **plus its support files**, `dist/echo-heist-0.1.0a1-windows-x64.zip` and its build manifest. The smoke summary should have all eight checks true. Inspect `output/windows-baseline/native-smoke/summary.json` and the desktop report/screenshot. Open `dist/EchoHeist/EchoHeist.exe` interactively as well, inspect the visible card and close it normally. Keep the whole folder or ZIP when transferring it.

Do not use `--dummy-video` for the native desktop claim; that option is only a separate CI check. Record commands, commit, Windows version/architecture, Python/uv versions, pass/fail and manual observations under `docs/development/quality/reports/phase02/windows/BASELINE.md` **after running them**. Keep large reports/screenshots/builds under ignored output/dist; include relevant hashes or summaries in the tracked report. This guide contains expected behavior, not Windows execution evidence. If native packaging is unavailable, leave it NOT_RUN and continue independent owned map/UI work when the source foundation works.

## 5. Retrieve your full implementation context

Read in this order before claiming files:

1. Root [AGENTS.md](../../../../AGENTS.md), [START_HERE](../START_HERE.md), [your owner guide](../owners/SUHITA.md) and [development hub](../../README.md).
2. [Status](../../tracking/STATUS.md), [active claims](../../tracking/HANDOFFS.md) and [P01 actual handoff](../../tracking/handoffs/khalid/day_01/P01.md), including its actual import paths and limitations.
3. [P02 specification](../../planning/phases/foundation/PHASE_02.md), [workload](../../planning/WORKLOAD.md), [scope](../../planning/V1_SCOPE.md), [code rules](../CODE_RULES.md), [codebase](../../architecture/CODEBASE.md), [contracts](../../architecture/DATA_CONTRACTS.md) and [approved scoring](../../planning/SCORING.md).
4. The source PDF pages 2-7 and 15-17 in `docs/idea`. Its text export is a reading aid. Inspect actual code/tests and current Git differences; planned APIs are not necessarily implemented APIs.

User overrides remain four development days/eight phases, named ownership and approved scoring. All required features must work by P08. Later polish does not defer required mechanics. Further scoring-rule changes need a chat proposal and explicit approval first.

## 6. Implement your P02 slices

| Slice | Your deliverable | Primary files |
| --- | --- | --- |
| P02-S1 | Five-zone Tiled greybox; two branches/cross-link; readable scene/camera; basic menu/mode/heist/results/pause views and object/actor presentation | Packaged map resources, `ui/scenes/`, `ui/render/` |
| P02-S2 | Typed Tiled JSON loader; object/property validation; unique anchors; movement/vision/sound geometry; branch and lockdown return connectivity checks | `level/io/`, grouped map-loader tests under root `tests/` |

Package paths are relative to `src/echo_heist/`. Claim exact intended files and your branch in HANDOFFS before editing. Synchronize current remote owner/handoff records and check for overlapping work; a branch-local claim alone cannot lock another checkout. Use existing core contract values. The loader returns validated static data, never live Simulation mutations. Put packaged maps in meaningful resource subdirectories, loaded through the existing resource service.

The route is Entry/Extraction -> Service Wing -> upper Security Control/lower Research Floor -> Core Chamber, plus the cross-link. Supply stable Spawn/Exit/Core IDs, cover/hide markers, geometry tags and patrol/chokepoint data. Follow P02 for precise acceptance; explain the map ID, schema, screen path, controls and inspection route in your handoff.

Khalid retains `core/simulation/`, `core/abilities/`, `ui/input/` and objective/interaction prompt presentation. Coordinate `app.py`, shared contract changes and any shared scene entry point through a narrow handoff; do not overwrite them silently. Do not take over his movement, mission, capture, tool or input rules just to make your scene appear complete.

When his implementation is available, integrate real actions, snapshots and events. Until then, finish your independently valid map/loader/view work and document the exact consumer interface needed. Any scene preview must be explicitly diagnostic. Never simulate theft/extraction/capture success in a widget or present placeholder AI/scoring as completed behavior. P01's tile movement is diagnostic, not final physics. Companion stays visibly in development until P04.

Use at most 1,000 lines per authored file and six maintained direct files per directory, including initializers/dotfiles. Group by responsibility before exceeding limits. Keep meaningful importer/geometry/route tests in the grouped root tests tree; avoid tests for every wrapper or cosmetic screen change.

## 7. Verify, hand off and stop

Run the combined checks after implementation, plus meaningful map validation and real scene inspection. Save exact results; do not mark a manual/platform check passed because it is merely configured. Recheck native packaging when resource/entry-point changes affect it. Write `docs/development/tracking/handoffs/suhita/day_01/P02.md` with changed files, actual schema/interfaces/IDs, branch/commits, commands, evidence, integration dependencies and the next action Khalid needs.

Update only your slices and relevant tracking, release completed file claims, and keep shared EH tasks open until both owners' requirements pass. You are P02's integrator, but the **whole phase stays incomplete until Khalid's slices are integrated and the Human win/capture gate is verified**. Stop after P02-S1/S2 and the integration possible with the available baseline; do not start P03.

Make genuine incremental commits using short natural messages and your own configured Git identity. Include no assistant/model attribution. Review `git diff` and `git status` before staging specific paths. Push your work branch when your own account has access:

```powershell
git push -u origin work/suhita-p02
```

If access is denied, retain the local commits and record the blocker; Khalid must grant your account collaborator access or arrange a fork contribution. Never force-push, publish credentials or push unfinished owner work directly to main. At the shared phase gate, integrate through the agreed review/merge process with checks; both owners' tracking changes may need reconciliation.

## Ready-to-paste starting prompt

```text
I'm Suhita, working on Windows x64.

Clone https://github.com/khalid999devs/Echo_Heist.git into this workspace,
or reuse its existing checkout while preserving local changes. Install
missing prerequisites from official sources as needed.

Read AGENTS.md, docs/development/workflow/owners/SUHITA.md and
docs/development/workflow/setup/WINDOWS_SUHITA.md. Follow their startup
sequence to retrieve the blueprint, current tracking, P01 handoff,
P02 specification, contracts, code rules and approved scoring.

Set up the locked Windows environment and verify the foundation. Work on
work/suhita-p02. Claim and implement only P02-S1 and P02-S2: the five-zone
map, typed loader/validation, scenes, camera and basic UI flow. Respect
Khalid's simulation/input ownership and document integration dependencies.

Run the appropriate checks, guide me through the visible result, and record
actual Windows results and my runnable handoff. Make short natural commits
with my own Git identity and push my branch when access permits. Preserve
main for integration. Stop at my P02 slice boundary; the full phase needs
both owners' work and verified Human win/capture behavior.
```
