# Published foundation and Windows CI evidence

Recorded 2026-10-18. User authorized publication to [khalid999devs/Echo_Heist](https://github.com/khalid999devs/Echo_Heist). main tracks origin/main; the original incremental history is preserved. A fresh public clone into ignored `output/github-handoff-check` succeeded, included the Windows handoff and showed all nine commits through 99a8658. Subsequent source fix and evidence commits extend that history normally. No P02 implementation was started.

## Actual hosted verification

[Successful run 39136504276](https://github.com/khalid999devs/Echo_Heist/actions/runs/39136504276), commit `a5d1400c4695b4efdc72c2dcae6e6f7c6e33242a`, conclusion **success**:

| Job | Actual result | Scope |
| --- | --- | --- |
| headless-checks / Ubuntu 24.04 x64 | PASS | Structure, Ruff lint/format, strict mypy, all 21 tests |
| windows-x64 / Windows 2022 x64 | PASS | Same checks/tests, native PyInstaller build, frozen headless and SDL dummy desktop smoke, uploaded artifact |
| macos-arm64 / macOS 14 arm64 | PASS | Same checks/tests, native PyInstaller build/signature verification, frozen headless and SDL dummy desktop smoke, uploaded artifact |

The workflow verifies interpreter architecture before installing locked dependencies. The frozen smoke helper compares source/frozen deterministic state/event hashes, verifies both processes are frozen, packaged resources, settings save, 12 rendered frames and screenshot output. A zero exit requires all eight assertions to pass. These are automated native executable checks using **dummy video**, not interactive hardware/display acceptance.

The same combined local check command passed after the settings fix on Khalid's macOS 26.4.1 arm64/Python 3.13.16: structure, lint, format, 24 typed source modules and 21 tests. `git diff --check` passed. No dependency/lock or gameplay contract changes were needed.

## First-run failures and corrections

1. [Run 39136206109](https://github.com/khalid999devs/Echo_Heist/actions/runs/39136206109), bac6e36: workflow validation failed before jobs. GitHub rejected runner.temp in job-level env. Commit 99a8658 uses the permitted github.workspace context for the ignored cache path. [Official context availability](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts#context-availability) documents that restriction.
2. [Run 39136343623](https://github.com/khalid999devs/Echo_Heist/actions/runs/39136343623), 99a8658: Linux and Mac passed; Windows failed the existing unavailable-storage test (20 passed, one failed). Windows reported a regular-file settings ancestor as FileNotFoundError, causing load to claim writable defaults. Commit a5d1400 validates the nearest existing ancestor is a directory and reports unavailable storage consistently. The original regression test remains intact and passes on all three runners.

These failures remain in real history; no tests were skipped to obtain the successful run. Public posting was explicitly authorized; source-license selection remains pending and no license grant was added.

## Runnable Windows handoff

Use [Suhita's Windows guide](../../../workflow/setup/WINDOWS_SUHITA.md) for a source checkout and reproducible native build. The successful run also exposes `foundation-windows-x64` and `foundation-macos-arm64` in its Actions artifacts. Download the Windows artifact from the run page, extract its platform ZIP, then keep the complete EchoHeist folder when opening EchoHeist.exe. Artifacts are subject to GitHub retention/access; the committed source/build commands remain the reproducible handoff.

Build manifests are created before the smoke step, so their initial native_smoke NOT_RUN field is a build-time snapshot. The uploaded `output/native-smoke/summary.json` and the successful smoke step provide the subsequent execution result.

Downloaded the Windows artifact and verified its ZIP bytes against its manifest locally: `echo-heist-0.1.0a1-windows-x64.zip`, 17,220,787 bytes, SHA-256 `f299d73ef6e55ae7d1b9a03af49de622e4a6ad38e5a6da9be4c2df15719de617`. The clean build used Windows Server 2022 AMD64, Python 3.13.16 and PyInstaller 6.22.3; signing is unsigned. Copied the actual [Windows smoke summary](windows-native-smoke.json) from that artifact into this report folder. The executable was exercised on the hosted Windows runner, not on Khalid's Mac.

The Windows manifest's lock SHA-256 is `f7e94248badd117c651bc96c4d74b8886477ab7d7e1b1b4e214b44c7e8c5aefe`. It exactly matches the local tracked lock converted from LF to CRLF; the local LF hash remains `f4961e410a9a17247044750ab300d4ec277bc16970487ac4bd2046db23e264d5`. This is checkout line-ending variation, not different resolved dependencies. The build reports a clean working tree.

Still NOT_RUN: Suhita's own Windows interactive source/frozen desktop inspection, clean downloaded Windows installation/security prompts, full-game behavior and release hardware coverage. Local Mac real-Cocoa evidence from the original P01 build is recorded separately in [VERIFICATION](VERIFICATION.md); do not conflate it with hosted dummy-video checks. P02 remains TODO for both owners until separately claimed.
