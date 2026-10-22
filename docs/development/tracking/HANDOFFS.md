# Work claims and runnable handoffs

P01 and P02 are complete. The [P01 handoff](handoffs/khalid/day_01/P01.md), [P02 integration handoff](handoffs/khalid/day_01/P02_INTEGRATION.md) and [phase specs](../planning/phases/README.md) define the accepted baseline and next owner slices. [Backlog](BACKLOG.md) maps shared feature anchors.

Suhita's original Windows x64 setup and branch workflow remain documented in [Windows setup](../workflow/setup/WINDOWS_SUHITA.md). Her `a98548a` source commit was accepted into the user-directed P02 integration review; she did not publish a separate P02 handoff or Windows interactive QA result on that branch.

## Current ownership and next handoff

Updated 2026-10-22 by Khalid's explicit request: [revised workload and transfer map](../planning/WORKLOAD.md). Khalid leads complex graphics/scenes; Suhita leads most gameplay logic. Future P03-P08 work uses **KR/SR** IDs; historical K/S IDs and authorship below remain preserved. Suhita next claims P03-SR1/SR2/SR3 from current main; Khalid next claims P03-KR1/KR2. This planning update claims neither runtime queue.

P03-P05 integration is led by Suhita with Khalid's visual acceptance; P06-P08 by Khalid with Suhita's behavior/platform evidence. The [Windows setup and full prompt](../workflow/setup/WINDOWS_SUHITA.md) now target P03, not the completed P02.

## Active claims

| Developer | Phase / slice | Branch or working-diff reference | Files currently claimed | State |
| --- | --- | --- | --- | --- |
| Khalid | User-requested ownership rebalance and current-state handoff | Documentation-only change on main after ec8ca48 | None; revised plans/owner guides ready | DONE; 149 tests/full checks and one-off document/ownership audit pass; no runtime slice or Suhita queue claimed |
| Khalid | User-requested cinematic opening/airlocks, boundary/audio fixes, facility variety, desktop icon and performance audit | Runtime 600698a; clean packages c2213c2; integration target main | None; [runnable handoff](handoffs/khalid/presentation/CINEMATIC_STARTUP.md) | DONE; 149 tests/full checks, both native wins/capture, 56 scene states, motion/performance/RSS review, nine-check native Mac app/ZIP and all three hosted jobs pass; matching Windows archive verified; shared phase gates and physical Windows QA unchanged |
| Khalid | User-requested materials/crouch/audio plus natural human gait and confirmed-pursuit speed | Verified runtime bac3502; main integration ab6d734 | None; [runnable handoff](handoffs/khalid/presentation/MATERIALS_AND_CROUCH.md) | DONE; 139 checks, both native route wins/capture, native Mac app/ZIP, matching Windows archive and all runtime/main hosted jobs pass; physical Windows QA and shared phase gates unchanged |
| Suhita | P03-SR1/SR2/SR3: fair sensing/reports/hiding-capture, Tracker A*/last-seen search, typed guard registry, geometry revision and replay evidence | `work/suhita-p03` from main a700359 | `core/contracts/security/model.py`, `core/contracts/observations.py`, `core/contracts/events.py`, `core/perception/`, `core/simulation/{engine,views,world,replay}.py`, `core/simulation/systems/{security,capture}.py`, `ai/navigation/`, `ai/guards/`, new `level/security.py`, new `diagnostics/guard_evidence.py`, new `scripts/experiments/`, grouped tests; **narrow scene claim:** `ui/scenes/heist.py` `HeistSession.__init__` security composition and the `_draw_lab` text lines only. No map JSON, art, camera or layout edits. [Contract](../architecture/integration/defenders/GUARD_CONTRACT.md); [handoff](handoffs/suhita/day_02/P03.md) | Owner slices DONE; claim released. Windows checks 188/189 (pre-existing smoke timeout), three route wins, exact replays. Shared P03 open for KR1/KR2 and the combined gate |
| Suhita | None; P02-S1/S2 technical work accepted in combined review | main includes original source a98548a | None | P02-S1/S2 DONE for phase gate; Windows interactive QA NOT_RUN |

This table is coordination metadata, not a distributed lock. When working in different checkouts, synchronize the relevant handoff/claim commits before editing shared files. Resolve conflicting claims before overlapping writes; do not assume a stale copy of this table proves exclusivity.

P02 integration boundary: [runtime contract](../architecture/integration/P02_RUNTIME.md). The original owner slices stayed separate; under the user's later explicit request Khalid reviewed/refined Suhita's scene/render files on a new integration branch. Her commits and authorship remain preserved in main; obsolete branch labels were removed in the cleanup below. `ui/presenters/objective.py` and `ui/input/human.py` continue to define the core/UI boundary.

## Ownership revision handoff — 2026-10-22

Khalid requested a clean current-state list and a graphics/logic rebalance. The [Status](STATUS.md) list, [Workload](../planning/WORKLOAD.md), P03-P08 specs, Backlog, owner/startup guides and [Windows handoff/prompt](../workflow/setup/WINDOWS_SUHITA.md) now agree. Completed work stays credited. New KR/SR IDs apply only to remaining work; Suhita may implement previously Khalid-authored core/AI logic, while shared scene/map changes require exact single-writer claims.

Remaining estimates: Khalid 48 / Suhita 60 points, reviewed against actual effort at phase gates. The former 80/80 estimate is historical, not an actual hours record. No runtime, scope, scoring, dependency lock or build artifact changed. Existing packages still name clean packaged source c2213c2 and runtime 600698a.

Actual verification on this documentation revision:

- `UV_CACHE_DIR="$PWD/.cache/uv" uv run --locked python scripts/checks/run.py`: PASS — structure, Ruff, format (226 files), mypy (108 source files), **149 tests in 19.04 seconds**.
- One-off local Markdown/ownership audit (`python3 /tmp/echo_rebalance_audit.py`, local helper, not an added test): PASS — changed links resolve, all 28 revised slice definitions have correct owners and points, every Backlog/owner reference is defined, phase totals sum to 48/60, no active stale P03-P08 owner IDs, Markdown-only diff.
- `git diff --check`: PASS. No native rebuild was required or claimed for these document-only changes; previous artifact/hardware results remain in the cinematic review.

Next: Suhita separately invokes her agent with the Windows guide's prompt, claims P03-SR1/SR2/SR3 and pushes work/suhita-p03; Khalid can claim P03-KR1/KR2. No agent was spawned or teammate messaged. Shared P03 status remains IN_PROGRESS until the combined gate passes.

## Repository branch cleanup

2026-10-22 follow-up: fast-forwarded `work/materials-and-crouch` into main at `ab6d734`, preserving its four implementation commits and evidence commit. Remote tip `bac3502` and local tip `ab6d734` were ancestors of main with zero unique commits missing. Deleted the remote label using its expected-tip lease, then the merged local branch; fresh remote/local listings show only main. The integrated main [run 39734108371](https://github.com/khalid999devs/Echo_Heist/actions/runs/39734108371) passes all three jobs. Runtime archives name their exact packaged source `bac3502`; later record-only commits do not alter it.

2026-10-21, explicitly requested by Khalid. Audited fresh remote refs against `main` at `a964448e2ba081655b710b040782a251cce2265f`. Every branch tip below was an ancestor of main with **zero commits missing**; there were no open pull requests. Deleted the eight remote branches in one atomic push with expected-tip leases, then pruned tracking refs and deleted the seven corresponding merged local branches. GitHub and this checkout now retain only the main branch. Commit history, source, authorship and build artifacts are preserved; no source rewrite or gameplay change was made.

| Removed historical branch | Preserved tip in main |
| --- | --- |
| work/chapter-and-route-balance | 8d2fffcb84cace352b09ffc21060cd630c4b7248 |
| work/complete-visual-scenes | b1be43bdc846787fe11a045323dc6909105b7a99 |
| work/facility-density | 3a544c9cbbd8ed7c2e8b015c010b9dcf4d39abdb |
| work/khalid-p02 | fd93224e43d37d43122ebb8aa8182505cfd2375e |
| work/p02-integration | 4389d6872eb6c48793583c8d87fa4bba73d0fac5 |
| work/stealth-vertical-slice | 3af9d9bba87ec73f2126bcac10ba7f08d6430e5e |
| work/suhita-p02 | a98548a7ba47a15bc4be81eab6e95be28edc6eee |
| work/two-floor-atmosphere | 641929e6d13343be00da21eb055e5d8a3c37fc45 |

Verification: `git merge-base --is-ancestor <tip> origin/main`, `git rev-list --count origin/main..<tip>` (all zero), `gh pr list --state open` (empty), `git ls-remote --heads origin` and `git branch --list` (main only after cleanup). Historical handoffs may still name the original feature branches; use their preserved commit IDs. Other developer checkouts can run `git fetch origin --prune`; future assigned work should start a fresh task branch from current main.

## Claim protocol

1. Resolve developer identity and earliest ready assigned slice. Read the actual prerequisite handoff, existing changes and relevant contracts.
2. Record slice, branch/diff and intended files. Each slice has one primary writer. Reserve a distinct adapter/presenter file when both owners work in the same subsystem.
3. Prefer separate owner branches/checkouts for concurrent work. Preserve unrelated changes; no force-reset/overwrite of the other owner's work. Keep changes small enough to integrate at the phase gate.
4. Implement and verify your behavior. A changed shared interface must include its contract update and consumer notes. If another owner must change a file, hand off that narrow dependency rather than editing it simultaneously.
5. Write your handoff and release the claim. The phase integrator combines both slices, reruns affected checks and records the phase gate.

Do not start a teammate agent or send external messages just because an owner is named in these documents. These files prepare each developer's separately invoked agent.

## Where to store completed handoffs

Create records only after real work under `tracking/handoffs/<owner>/day_01/`, `day_02/`, `day_03/`, or `day_04/`, using phase filenames such as `P02.md`. This keeps at most two normal phase records in each day directory. If a phase needs more than six records, group revisions under a subdirectory. Link the resulting evidence from Status/Backlog and this index.

- [Khalid / Day 1 / P01](handoffs/khalid/day_01/P01.md): DONE; runnable foundation, native Apple Silicon smoke, actual contract map and next-owner instructions.
- [Khalid / Day 1 / P02](handoffs/khalid/day_01/P02.md): original P02-K1/K2 handoff; core/tools/input/objective presenter, diagnostic native win/capture, 45 tests and three-platform CI at that time.
- [Combined P02 integration](handoffs/khalid/day_01/P02_INTEGRATION.md): Suhita's map/loader/scene plus Khalid's core and final visual/flow review; full Human phase gate and next P03 contract.
- [Suhita / Day 2 / P03](handoffs/suhita/day_02/P03.md): P03-SR1/SR2/SR3 DONE; registry, Tracker A*, fair hiding/capture, provenance, geometry revisions and replay, with Windows evidence. Shared P03 awaits KR1/KR2 and the combined gate.

## Handoff template

```text
Owner / phase / slices / status:
Branch, commit or exact working diff:
Prerequisite handoff and integrated baseline:
Implemented behavior and user-visible way to exercise it:
Changed files and actual import/entry-point paths:
Input/output contracts, object/event IDs and compatibility notes:
Exact launch/check/test/build commands actually run:
Outcomes and durable evidence (including NOT_RUN platform/manual checks):
Authored line/direct-file limits:
Unfinished behavior, blockers and known nonblocking defects:
Estimated vs actual effort and any agreed task transfer:
What the other owner/integrator must connect next:
```

Keep secrets and machine-local profile data out of the record. Include a seed/profile and controls for gameplay checks. Generated large logs/build/video artifacts are linked with version/hash rather than committed into the handoff tree.

## Shared task completion

Current consumer baseline: [cinematic/physical-fixture handoff](handoffs/khalid/presentation/CINEMATIC_STARTUP.md), [actual evidence](../quality/reports/cinematic_startup/REVIEW.md). Fingerprint-7, explicit physical bounds, 0.2-tile actor radius, startup ownership, pressure-door presentation and nonblocking music fades supersede the earlier descriptions. Runtime/source package references are exact in BUILD.json. Integration preserves the four separate implementation/review commits and adds the final delivery record; remove the temporary work branch only after ancestry/zero-unique/expected-tip checks. Shared P03-P08 are not marked complete by this refinement.

Latest consumer baseline: [grounded material/crouch handoff](handoffs/khalid/presentation/MATERIALS_AND_CROUCH.md), [actual evidence](../quality/reports/material_cohesion/REVIEW.md). Posture/clearance, fingerprint-6, material and explicit UI-feedback contracts supersede the previous subset deferral. Final natural-gait/pursuit runtime `bac3502` passes 139 cases, all three hosted jobs and native Mac app/ZIP checks. It supersedes intermediate 8a0dffd; [latest package evidence](../quality/reports/material_cohesion/verification/locomotion/BUILD.json). Only this user-requested subset is complete; the shared environment/AI/release gates remain open.

Latest consumer handoff: [responsive facility and audio](handoffs/khalid/presentation/SCENE_FINISH.md), with [actual evidence](../quality/reports/facility_finish/REVIEW.md). Full-window/safe-area mapping, equipment appearance/condition, revised HideSpot coordinates and listener-filtered tactical audio supersede prior presentation details. Clean runtime `28aff88` passes all three hosted jobs and both native Mac smoke checks. The follow-up is integrated with its original incremental history; only the temporary branch label is retired after ancestry verification. Windows interactive QA and later phase mechanics remain open.

An owner can mark their named slice DONE when its behavior/checks pass. A shared EH task remains TODO/IN_PROGRESS until every required slice in its Backlog mapping is complete and its feature acceptance passes. The integrator marks P01-P08 DONE only on the combined build and records exact evidence in Status. Missing primary archives or gameplay functionality keep P08 incomplete; public release is tracked separately.

- [Khalid / Day 2 / first stealth slice](handoffs/khalid/day_02/STEALTH_SLICE.md): one real Sentinel, physical room cluster, cinematic/compact UI, CC0 audio, 31 native screens, 89 tests and current native/CI build evidence. Shared P03 remains open.
- [Khalid / Day 2 / denser facility](handoffs/khalid/day_02/FACILITY_DENSITY.md): 23 compact rooms, 104 physical furnishings, slower movement and paused map; 96 tests, 38 native screens, both real route wins and a clean rebuilt Mac ZIP. Shared P03 and Windows interactive QA remain open.

- [Khalid / Day 2 / chapter and compact routes](handoffs/khalid/day_02/CHAPTER_AND_ROUTES.md): clear chapter/briefing/mode/Launch flow, 14-room compact research facility and faster movement; 97 tests, 38 native screens, both route wins and clean Mac build/native/hosted checks. Remaining shared phases and interactive Windows QA stay open.

- [Khalid / Day 2 / two-floor lab](handoffs/khalid/day_02/TWO_FLOOR_LAB.md): reciprocal stairs, approved timed sprint/recharge, cleaner UI, clinical lighting, soft shadows, native alpha correction and distinct extraction art; 111 tests, 38 native screens and clean Mac app/ZIP smoke. Shared phases and Windows interactive QA remain open.
