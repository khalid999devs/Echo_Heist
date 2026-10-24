# PR #1 review and runnable handoff

2026-10-24, Khalid. [PR #1](https://github.com/khalid999devs/Echo_Heist/pull/1), `work/suhita-p03`. Reviewed original head `ed2239690aae28575bf8d1a9efb60d2296844cff` against main `dba2e9ad83a366947c2cffe3e1fbd982ef3c0045`. Fixes are `c562fffc61327fea129b255b9ad26d6dd95a62f6`; Suhita's original commits/authorship are retained. Work was isolated in `/tmp/echo-heist-pr-1`; the main checkout stayed unchanged.

**Decision: fixes pushed; leave the PR open.** The logic regressions below are fixed and verified. The PR description explicitly requests no merge until Khalid's P03-KR1/KR2 and the combined gate pass. Those slices remain open under the [phase specification](../../../../planning/phases/intelligence/PHASE_03.md). This review does not claim their completion or start P04.

## Findings fixed

| Issue reproduced | Correction and regression evidence |
| --- | --- |
| A Sentinel or Tracker seeing someone enter cover before identification completed ignored the witnessed entry | Both controllers investigate the actual HIDE_ENTRY cue, preserving its ID/time and their last sighting. This does not grant confirmed identity. Parameterized regression covers both controllers. |
| An adjacent guard inspecting witnessed cover could reveal a concealed intruder through a physical partition | Exact physical reach is now required before revelation. A sensor/capture regression verifies that a blocking partition prevents both sight and capture. |
| Different queued geometry changes with the same reason had identical fingerprints | The full pending map and reason enter the canonical state. A regression distinguishes two queued maps with identical reason text. |
| A geometry revision applied after controller decisions, leaving one tick of stale paths and sight | Geometry and current visual sensing now refresh before decisions/action validation. An existing route test now checks the first revised tick; a new test verifies lost sight does not advance identification and an already-heard sound retains provenance. |
| The evidence script accepted any no-tool outcome | Both careless scenarios now explicitly require CAPTURED, alongside the three required WIN outcomes and all replay checks. |

The first four regression cases (two controller cases, barrier, pending hash) failed on the original implementation. The first-tick geometry checks also failed before the timing correction. The final focused set passes **37 cases**. No scoring, map/art, dependency lock, camera or deferred P04/P05 mechanics changed. [Updated contract](../../../../architecture/integration/defenders/GUARD_CONTRACT.md).

## Actual checks

macOS 26.4.1 arm64, CPython 3.13.16, pygame-ce 2.5.8, locked dependencies. From the isolated checkout:

```sh
uv sync --locked --extra dev --extra build --cache-dir /tmp/echo-heist-review-uv
uv run --locked --cache-dir /tmp/echo-heist-review-uv python scripts/checks/run.py
uv run --locked --cache-dir /tmp/echo-heist-review-uv python scripts/experiments/p03_evidence.py --output output/pr-review/fixed/evidence.json
```

- Original PR baseline: structure, Ruff/format, strict mypy and **189 tests PASS** (54.06 s).
- Fixed runtime: structure, Ruff/format (245 files), strict mypy (115 source files), **194 tests PASS** (21.83 s), including desktop smoke. Five meaningful cases were added and the existing geometry test strengthened.
- Targeted command: `.venv/bin/python -m pytest -q tests/unit/intelligence tests/integration/perception tests/unit/core/geometry tests/integration/replay`: **37 PASS** (1.91 s).
- `git diff --check` and the structure checker PASS after the contract/record changes.
- Original and fixed evidence: upper-tools WIN/1514 ticks; lower-tools WIN/1581; cross-tools WIN/1603; upper-no-tools CAPTURED/1174; lower-no-tools CAPTURED/349. All five replays match. Outcomes, ticks, event chains and final fingerprints are unchanged between original and fixed runs. These scenarios do not exercise pending geometry; dedicated regressions cover it.

## Native packaging and limited visual inspection

```sh
uv run --locked --cache-dir /tmp/echo-heist-review-uv python scripts/packaging/build.py
uv run --locked --cache-dir /tmp/echo-heist-review-uv python scripts/packaging/smoke.py "dist/Echo Heist.app" --output-dir output/pr-review/native-app
ditto -x -k dist/echo-heist-0.1.0a1-macos-arm64.zip output/pr-review/extracted
uv run --locked --cache-dir /tmp/echo-heist-review-uv python scripts/packaging/smoke.py "output/pr-review/extracted/Echo Heist.app" --output-dir output/pr-review/native-zip
```

- Clean source commit **c562fff**, manifest `working_tree_dirty=false`; ad-hoc signed Mac app and ZIP built successfully. Both app and fresh extraction pass **9/9** checks on native Cocoa with audio ready. Exact archive/lock hashes and results are in [EVIDENCE.json](EVIDENCE.json).
- Captured and inspected title, briefing, entry and F3 diagnostics at 1280×720 on Cocoa through actual menu clicks. All four registry guards appear. Initial PATROL text fits the existing panel, but these interim single-line diagnostics are not KR1's required complete cue/search/fuzzy presentation. Other guard states, both-deck cue alignment, interactive hiding/win and fullscreen were **not** accepted as a completed visual gate here.
- Local generated logs, full route reports, four PNGs and build archives are under ignored `output/pr-review/` and `dist/` in this worktree. Compact durable evidence is committed beside this report.
- The fixes' [PR CI run 40103390736](https://github.com/khalid999devs/Echo_Heist/actions/runs/40103390736) and [push run 40103386584](https://github.com/khalid999devs/Echo_Heist/actions/runs/40103386584) both PASS all three jobs: Linux headless checks, Windows x64 and macOS arm64. Primary-platform jobs build and pass frozen dummy-video smoke. GitGuardian PASS. These runs test c562fff; subsequent review-record commits do not change runtime.
- No physical Windows session was run by this review. Suhita's earlier [Windows record](../windows/VERIFICATION.md) remains historical, including her machine's existing 30 s startup timeout. CI is not a substitute for her interactive retest.

## Resume on Windows

Suhita should preserve local changes before switching/pulling; do not reset them. On a clean existing branch:

```powershell
git fetch origin
git switch work/suhita-p03
git pull --ff-only origin work/suhita-p03
uv sync --locked --all-extras --python 3.13
uv run --locked python scripts/checks/run.py
uv run --locked python scripts/experiments/p03_evidence.py --output output/windows-p03-reviewed/evidence.json
uv run --locked echo-heist --data-dir .local/suhita-p03-reviewed
```

Inspect C crouch/under-desk entry both unseen and witnessed, break contact behind a wall, then capture interruption/retry. Keep actual results separate from the previous Windows run. If her existing smoke timeout repeats, record the measured result instead of claiming it passed.

## Next integration action

1. Khalid completes **P03-KR1/KR2** against these reviewed logic changes: readable guard states/capture/heard-cue feedback, genuine sensor/search/fuzzy diagnostics, and both-deck geometry/art alignment. Incorporate `work/suhita-p03` into the dedicated visual branch as its dependency; do not overwrite the logic or mark shared P03 complete early.
2. Suhita, the P03 integrator, combines the visual changes, runs the affected checks and shared phase gate with Khalid's visual acceptance, and records the exact integrated commit.
3. Merge PR #1 into main after those requirements and current CI pass. P04 then becomes ready. No main merge, branch deletion or P04 work was performed in this review.
