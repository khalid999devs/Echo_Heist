# Phase 1 verification

Date: 2026-10-18, Asia/Dhaka. Owner: Khalid. Version: 0.1.0a1. Native runtime build commit: 61a00a09003dcba85e5f000491778197aff81559. Host: macOS 26.4.1 / arm64, Python 3.13.16. This report covers P01 foundation behavior, not the complete game.

## Executed checks

| Check | Actual result |
| --- | --- |
| Locked project environment | PASS; uv resolves 22 packages, installs the local editable package and required native dependencies |
| Fresh locked isolated environment | PASS; offline sync into output/phase01/locked-env, then complete checks and all 21 cases pass again |
| Structure limits | PASS; authored files <=1,000 lines, maintained direct files <=6; test code grouped under root tests |
| Structure negative probes | PASS; rejects a 1,001-line unknown text suffix, a seventh direct file and a relative AI import of simulation implementation |
| Ruff lint / format | PASS |
| mypy strict | PASS; 24 source files |
| pytest | PASS; 21 cases in four purposeful files, no cosmetic or per-wrapper tests |
| Headless imports | PASS; core/seed fixture does not import pygame |
| Immutable observation boundary | PASS; unseen guard changes do not change permitted observations; snapshots retain old values |
| Fresh built-wheel installation | PASS; installed wheel + two runtime dependencies in isolated output/phase01/wheel-env |
| Installed-wheel launch outside repo | PASS; headless and two-frame dummy desktop run from /private/tmp, resources/settings work |
| Source real Cocoa window | PASS; 12 frames at 1280x720, muted, packaged SVG/JSON and writable settings |
| Native app build/signature | PASS; Mach-O arm64; ad-hoc codesign --verify --deep --strict succeeds |
| Extracted native ZIP smoke | PASS; all eight checks in [raw summary](native-smoke.json) |
| CI YAML | PARSED locally; three-target workflow configured, hosted execution NOT_RUN |
| Windows x64 wheel resolution | PASS; locked dependencies resolve using binary wheels only |
| Windows native build/runtime | NOT_RUN; no Windows host/remote runner used |
| Public download/quarantine flow | NOT_RUN; local smoke artifact only |

The first attempted real window launch inside the filesystem sandbox could not access macOS displays. Retrying the same source/frozen app with the required native display access succeeded. SDL dummy-video tests passed separately; they are not substituted for the real Cocoa check.

## Purposeful test coverage

- Core: repeatable state/events, independent RNG namespaces, stale/future action rejection, blocked/unsupported actions, duplicate-order determinism, old immutable snapshots and hidden-state noninterference.
- Persistence: isolated data path/round trip, malformed/invalid JSON recovery, defaults for missing fields, future-schema preservation, failed atomic replacement and unavailable storage.
- Desktop smoke: source installation from unrelated cwd, packaged resources, unavailable audio fallback and persisted settings through SDL dummy video.

## Commands used

```sh
uv sync --python python3.13 --extra dev --extra build
uv run --locked --all-extras python scripts/checks/run.py
uv run --locked --all-extras echo-heist --headless --seed 1042 --report output/phase01/headless.json
uv run --locked --all-extras echo-heist --smoke-frames 12 --mute --data-dir .local/phase01/profile --report output/phase01/source-desktop.json --screenshot output/phase01/source-desktop.png
uv build --offline --wheel --out-dir output/phase01/wheels
uv venv output/phase01/wheel-env --python python3.13
uv pip install --offline --python output/phase01/wheel-env/bin/python output/phase01/wheels/echo_heist-0.1.0a1-py3-none-any.whl
uv run --locked --all-extras python scripts/packaging/build.py
ditto -x -k dist/echo-heist-0.1.0a1-macos-arm64.zip output/phase01/extracted
uv run --locked --all-extras python scripts/packaging/smoke.py "output/phase01/extracted/Echo Heist.app" --output-dir output/phase01/frozen-smoke --mute
```

Agent executions used a project-local UV_CACHE_DIR to keep cache writes in the workspace. The fresh wheel's absolute entry point was invoked from /private/tmp, with --data-dir/--report under output/phase01. The native helper removes PYTHONPATH/PYTHONHOME, uses system-only PATH and a temporary unrelated cwd. Frozen reports confirm `runtime.frozen=true` and `video_driver=cocoa`.

Final fresh-lock reproduction set `UV_PROJECT_ENVIRONMENT=output/phase01/locked-env`, ran `uv sync --locked --all-extras --offline --python python3.13`, then the same combined check command. It created a new environment, installed 19 actual-host packages from the 22-package universal resolution and passed the 21 cases. This is separate from the wheel-only installation probe.

Windows dependency verification exported the real lock with `uv export --locked --all-extras --no-emit-project`, then compiled those pinned requirements for x86_64-pc-windows-msvc / Python 3.13 with `--only-binary :all:`. Its output is retained locally under output/phase01/windows-wheel-check.txt; no Windows code was executed.

## Native artifact and reproducibility

Archive: dist/echo-heist-0.1.0a1-macos-arm64.zip. Size: 15,881,354 bytes. SHA-256: `7b85a032fb11bda79407721cb3c76f5a2bb821267681a1511f1fd602117a3508`.

Lock SHA-256: `f4961e410a9a17247044750ab300d4ec277bc16970487ac4bd2046db23e264d5`.

For seed 1042, source, fresh wheel and native executable agree:

- State hash: `e3b0e0e38c39aed03058cd5a3a78fc443478bf24cf1a60d11a4ebad97f9677cd`
- Event hash: `c34f95493eab29ee1820748f6b9cd160a1deed2d1736b8ee337185aed755ee69`
- Five diagnostic ticks/events, final tile (0, 0), namespace RNG sample 400326.

PyInstaller: 6.22.3/hooks 2026.8. Signing: ad-hoc, not Developer ID/notarized. ZIP preserves the app bundle via ditto; extraction and subsequent execution succeeded. Generated large artifacts/captures/profile data stay ignored. Build-time manifest records the clean source commit and initial pre-test NOT_RUN smoke state; this report/raw summary records the subsequent PASS.

## Follow-up boundary

P01 is complete and hands a runnable package/contracts to Suhita. P02-S1/S2 can start without redoing setup. The mission, Tiled importer, final physics, perception/AI, Workshop, approved scoring implementation and production scenes belong to their later assigned phases. T01-T08 remain NOT_RUN for the full game. Remote hosting, source-license selection, Windows execution and wider platform/download checks remain explicitly pending.
