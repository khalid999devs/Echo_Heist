# Khalid connected review handoff

2026-11-10. Branch `work/khalid-connected-review` from `df7dbdb`; user requested Mac P04/P05 visual/audio acceptance, P06 consumer refinement and current-game P07 usability/performance/memory review. Fingerprint remains **12**; no simulation, scoring, AI or approved melee rule changed.

## Delivered and verified

- Real native horizontal/vertical door close/open, both glass panes and physical crossing, once-only cues/mixer playback, Echo/EMP and truthful tool rejections; actual guard melee contact and recovery rejection. **22 screenshots**, production security enabled. Previously merged native canister/locker review is retained.
- Real Companion seed 1042 WIN, actual results/details, four Workshop blocks, explicit seed cancel/change preserving mode/policy, new deployment through protocol review, pause/settings fingerprint freeze, remapped Human movement, captions/contrast, confirmed Companion abort and four guide tabs. **21 screenshots**, four requested window sizes and actual fullscreen pointer mapping.
- Corrected Field Guide's stale planned-AI descriptions and missing physical Interceptor explanation. Failed Companion selection now points to the Workshop notice instead of saying the feature is coming later.
- Profiler now uses the production AI gateway in both modes, all 13 props and actual 64-simulation Companion traces. Four warmup cycles cover both modes/sizes. Separate traced restart and complete actual mission measurements replace unsupported Human-only performance assumptions.
- Locked full checks: **301 passed in 44.32 s**, structure/Ruff/format/strict mypy PASS. Native Cocoa and audio ready. [Detailed commands/results/limits](../../../../quality/reports/phase07/khalid/CONNECTED_REVIEW.md), [maintained evidence](../../../../quality/reports/phase07/khalid/EVIDENCE.json).

No production ExperienceGateway is present. Actual score/profile/history/preference persistence acceptance remains **NOT_RUN**, dependent on Suhita's P06-SR1/SR2/SR3. UI consumers truthfully remain unavailable/session-only where appropriate. No test-only backend was installed as a substitute. The [experience seam](../../../../architecture/integration/experience/PRESENTATION.md) remains ready.

## Run and reproduce

```sh
uv sync --locked --all-extras
uv run --locked echo-heist
uv run --locked python -m tests.fixtures.interactions.acceptance --output output/connected-review/props
uv run --locked python -m tests.fixtures.experience.live_capture --output output/connected-review/experience
uv run --locked python scripts/quality/profile_desktop.py --output output/connected-review/performance-final --frames-per-cycle 600 --complete-mission
uv run --locked python scripts/quality/profile_desktop.py --output output/connected-review/memory --cycles 16 --trace-memory --teaching
```

Run native profiling alone, with no other game/check workload. Review helpers open/close their own desktop windows and use temporary protocol data. C crouches; E interacts; Shift gives the timed sprint; Q Echo/F EMP/Space limited melee. Chapter → Companion → Workshop → Deploy is the actual AI run; F2 shows real decisions/director/interceptor, F3 real defenders. Field Guide is accessible from the title menu. Pause → Settings provides controls/accessibility.

## Boundaries and next connection

Khalid's P04/P05 Mac connected acceptance is ready for the shared gate record. Suhita still supplies current-build physical Windows gameplay/audio evidence and reconciles the P04/P05 combined gate; do not mark a missing platform run PASS. P06 real service wiring/relaunch/recovery must then be verified against the existing screens. Preserve her backend ownership and narrow shared Flow/Heist claims.

P07 current-build render/audio/usability/memory review is recorded. Untraced restart p95 total **16.754 ms**, one **255.286 ms** display-present outlier; full real Companion infiltration/lockdown p95 **16.729/16.777 ms** and actual alarm playback. Traced 16-restart retained Python growth **2.193 MiB**, short-run bounds pass, variable RSS. These measurements do not prove zero leaks, fixed FPS, policy fairness or full P07 completion. Ghost/Rush tuning, rare corridor blocking and scenario/save recovery remain Suhita's P07 work. P08 licensing/media/clean-machine builds/delivery are not claimed here.

All review implementation claims are released after this handoff. Raw screenshots/logs remain ignored under `output/connected-review`; existing player files are untouched.
