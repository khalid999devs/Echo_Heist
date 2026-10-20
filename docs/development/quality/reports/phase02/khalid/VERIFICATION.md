# P02-K1/K2 verification

Date: 2026-10-18. Owner: Khalid. Runtime source: clean commit `789da1099cfdf3cc7b6dd10fed0c502b23af06ae`, branch work/khalid-p02. Host: macOS 26.4.1 arm64, Python 3.13.16, pygame-ce 2.5.8, uv 0.12.22, PyInstaller 6.22.3. Dependencies/lock unchanged from P01.

## Automated behavior and structure

`uv run --locked python scripts/checks/run.py`: PASS. Authored 1,000-line/six-direct-file/test-placement/import rules, Ruff lint/format, strict mypy (38 source files) and **45 pytest cases** pass. `git diff --check` passes. Tests remain grouped under root tests; no test-per-file scaffolding was added. The core engine is 234 lines, diagnostic preview 231, human adapter 126 at this runtime commit.

Evidence covers continuous/normalized walk+sprint, substepped collision/sliding/corners/actor occupancy, stable action ordering, stale/duplicate/malformed intents, immutable own observations/noninterference, noise cadence, atomic timed core theft/lockdown, carrier-only extraction, capture telegraph/reach/escape, terminal freeze, abort, capture/extraction tie precedence, EMP cancel on completion tick/radius/stock/duration, melee single-target/reach/immunity/noise, bounded backward Echo/no actor authority/expiry, human event handling/remapping/focus clearing, objective updates, and rendered scripted win/capture. Existing resource/settings recovery tests remain passing.

This verifies T05/T08 mechanics in constructed maps and shared Human/Companion actor rules; it does not claim the complete autonomous T02 scenario, full perception/AI or final-map release acceptance. Environment object systems and scoring are not marked implemented.

## Native desktop input traces

Command actually run through real Cocoa:

```sh
uv run --locked python tests/smoke/desktop/test_human_preview.py --output output/phase02/native-preview
```

This test driver supplies pygame key events and a deterministic 100 ms render clock, while all gameplay runs through the real input adapter and Simulation. It does not inject a forced outcome. Both windows rendered and their screenshots were visually inspected; this is scripted native display evidence, not a human keyboard/feel or performance test.

| Trace | Actual result | Evidence |
| --- | --- | --- |
| Win, seed 1042 | 90 frames; 3 paused frames; WIN at tick 243; CORE_TAKEN/LOCKDOWN_STARTED/MISSION_ENDED exactly once | [win.json](win.json); local output/phase02/native-preview/win.png |
| Contact capture, seed 1042 | 90 frames; CAPTURED at tick 94 by contact-guard; one start/completion/end | [capture.json](capture.json); local output/phase02/native-preview/capture.png |

The final captured screenshot has no stale active wind-up warning/ring. The default standard app entry is deliberately still the P01 shell; this preview is launched explicitly, preserving Suhita's scene files.

## Native packaging regression

Commands actually run:

```sh
uv run --locked --all-extras python scripts/packaging/build.py
ditto -x -k dist/echo-heist-0.1.0a1-macos-arm64.zip output/phase02/extracted
uv run --locked --all-extras python scripts/packaging/smoke.py "output/phase02/extracted/Echo Heist.app" --mute --output-dir output/phase02/native-smoke
```

PASS: clean 789da10 arm64 build, ad-hoc signature verification, extracted ZIP, real Cocoa frozen desktop, isolated profile, unrelated cwd/system-only PATH, all eight source/frozen hash/resource/settings/frame/screenshot assertions. [Actual smoke summary](native-smoke.json).

Archive: 15,908,605 bytes; SHA-256 `4e3e573478614c44325ade331ae39ed8c7fc8da68c83b7e8f6cfd2b1e8b8f473`. Version remains 0.1.0a1. The prior P01 archive/manifest were preserved under ignored output/phase01/original-build before rebuilding. Current artifact is a bootstrap/continuous-physics regression build, not a packaged five-zone mission or packaged preview. Its manifest's NOT_RUN smoke field predates the separate passing summary. Local raw build files/reports/screenshots remain ignored; no signed/notarized public-release claim is made.

Updated headless seed 1042: five ticks, six events, final tile (0,0); state hash `2f3c494e6e290eb1097f1cfc7672aec968bb5152be129adaae42d37603935b80`, event hash `72b765df6af8e814e017a223899f9f11505145e62acf98381f8b975271ec639f`. These replace the old diagnostic hashes because real motion/noise/history now exist; they are not scored gameplay metrics.

## Hosted CI and remaining gate

[Run 39141181536](https://github.com/khalid999devs/Echo_Heist/actions/runs/39141181536), 789da10: all three jobs PASS. Linux x64 checks, Windows x64 checks/native build/frozen dummy smoke, macOS arm64 checks/native build/frozen dummy smoke. Source behavior suite includes the new rendered input traces on each runner. Hosted dummy-video execution is distinct from the local real-Cocoa traces above.

NOT_RUN: Suhita's own Windows interactive check, real five-zone map/scene integration, full P02 menu/result/retry/manual gate, active defenders, complete tools/environment effects, approved scoring and full-game primary download QA. Full P02 stays IN_PROGRESS. No P03 work or main merge occurred.
