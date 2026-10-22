# Khalid and Suhita: remaining workload and delivery

Revised **2026-10-22**, explicitly requested by Khalid. This replaces the original future-work allocation: **Khalid leads complex visual graphics and scenes; Suhita leads most gameplay logic.** P01/P02 credit, completed commits and verified refinements remain historical facts. The eight phases, required V1 scope and approved scoring are unchanged.

## Responsibility and balance

- **Khalid:** environment/art direction, assets, lighting/materials, character animation, camera, UI layouts, scene transitions, sound presentation, visual usability, rendering performance and desktop packaging. His substantive nonvisual work is display/input integration, resource/build engineering, profiling and shared architecture review.
- **Suhita:** perception, guard navigation/behavior, Companion planning/MCTS, Interceptor/minimax, NEXUS, abilities, environment lifecycles, scoring, Workshop/profile/history persistence and deterministic evidence. Her presentation work is narrow functional wiring of real data/actions into existing screens and Windows gameplay QA; complex graphics stay with Khalid.
- Both own tests and documentation for their changes. Simulation is the only authority for gameplay mutation; renderers/audio consume events and immutable views. Suhita's logic ownership includes fixing existing core modules previously written by Khalid.

The original **80/80 whole-project estimate is retired**, not an actual time record. Khalid has already delivered all P01, substantial P02/core integration and extensive visual/build refinements; Suhita's original P02 contribution remains credited. Actual historical hours were not logged, so exact lifetime equality cannot be claimed.

The **remaining estimate is 48 Khalid / 60 Suhita points**, including verification, integration and handoffs. The modest extra remaining logic allocation compensates for Khalid's completed foundation/refinement work. This is a provisional route toward equal total effort, not a measured equality or an instruction to add unnecessary art. Reuse finished scenes; charge only missing connections, needed adaptations and evidenced defects.

| Phase | Original work block | Khalid remaining | Suhita remaining | Integration lead |
| --- | --- | --- | --- | --- |
| P01 | Day 1 / foundation | 0 — DONE, original 12 | 0 — no P01 assignment | Khalid, complete |
| P02 | Day 1 / Human heist | 0 — DONE, original 8 | 0 — DONE, original 12 | Complete combined review |
| P03 | Day 2 / defenders | 5 — cues, diagnostics, geometry review | 12 — fair sensing, Tracker, registry, replay | Suhita; Khalid verifies visuals |
| P04 | Day 2 / autonomous AI | 7 — Companion/Lab/NEXUS presentation | 18 — Companion, MCTS, Interceptor, NEXUS | Suhita; Khalid verifies visuals |
| P05 | Day 3 / interactions | 9 — tools/props animation, sound and scene fit | 10 — tool rules and environment lifecycles | Suhita; Khalid verifies visuals |
| P06 | Day 3 / complete flow | 9 — Workshop, settings, results and full UI | 9 — profiles, scoring, persistence and deployment | Khalid; Suhita verifies behavior |
| P07 | Day 4 / integration | 9 — UX/accessibility, render performance | 6 — fairness/replay/AI evidence and recovery | Khalid; both verify candidate |
| P08 | Day 4 / delivery | 9 — builds, Mac QA, demo/media and handoff | 5 — Windows gameplay QA and experiment report | Khalid; both verify delivery |
| Remaining | Six open phase gates | **48** | **60** | Shared functional result |

Days are the original four-development-day sequence, not a claim that the target was met or a new four-day countdown. Work began 2026-10-18; on 2026-10-22 P03 is still open after requested refinements. Resume by dependencies and report actual progress. Do not cut required mechanics to make a date appear achieved.

## Revised slice IDs and preserved history

New remaining-work IDs use **KR / SR**, for example `P03-KR1` and `P03-SR1`. K/S is the current owner; R identifies this rebalance. Existing `P03-K1` through `P08-S3` references in dated handoffs describe the original assignment and completed subsets; **do not claim them for new work**. P01/P02 IDs stay unchanged. The active phase specs and Backlog use the revised IDs.

| Phase | How unfinished original responsibilities transfer |
| --- | --- |
| P03 | Original K1/K2 logic → SR1/SR2; S1 registry and behavioral S3 fixtures → SR3; K3/S2 visuals → KR1; map/visible integration review → KR2 |
| P04 | Original K1 Companion → SR1; K2 Interceptor and S1 dispatch → SR2; S2 protocols → SR3; K3/S3 presentation → KR1/KR2; functional deployment wiring → SR3 |
| P05 | Original K1 tools → SR1; S1 lifecycle and behavioral S3 checks → SR2; K2 HUD/input → KR1; S2 art/effects and S3 provenance/audio presentation → KR2 |
| P06 | Original K1 scoring → SR1; S1 policy/profile logic → SR2; functional settings/history/deployment from S2/S3 → SR3; K2/S2/S3 screens → KR1/KR2/KR3 |
| P07 | Original K1 fairness/replay/search → SR1; S1 scenario registry, backend recovery and algorithm explanation accuracy → SR2; original K2/K3/S2 presentation → KR1; rendering/resource/audio performance → KR2 |
| P08 | Original K1 builds → KR1; K2 source handoff and S3 media → KR2; native Mac UX → KR1; Windows UX → SR1; S2 comparison/evidence → SR2 |

Completed early crouch, Sentinel, materials, startup and airlock work is reused, never reimplemented to satisfy an old task description. A new slice covers only its remaining acceptance gap.

## File ownership and handoff seams

| Area | Primary writer | Other owner's integration seam |
| --- | --- | --- |
| `core/`, `ai/`, future `workshop/`, persistence, behavioral tests | Suhita | Khalid reviews contracts and consumes typed snapshots/events; targeted resource/display persistence remains his claimed slice |
| `ui/render/`, scene design/layout/animation, `ui/startup/`, `ui/audio/`, visual/audio assets | Khalid | Suhita supplies actual values/events and verifies observable feedback; no scene redesign required for logic |
| `level/model.py`, `level/io/`, patrol/chokepoint registry | Suhita | Khalid supplies placement/geometry requirements; agree schemas before changing the map |
| Packaged map JSON, level authoring/calibration scripts | Khalid for composition; explicitly shared for behavior metadata | Claim exact files before edits; Suhita can add required patrol/object metadata with a narrow claim while preserving coordinates/art/route IDs |
| `ui/scenes/heist.py`, `flow.py`, app/resources/settings glue | One named writer at a time | Suhita may wire controllers/deployment/results into current screens; Khalid owns drawing/layout; claim exact methods/files and hand off before overlapping work |
| Packaging, display/render profiling and presentation QA drivers | Khalid | Suhita provides Windows results and logic/search regressions; native platform claims require actual runs |

No blanket prohibition on the other owner's directory may prevent necessary integration. Record a narrow claim, update the changed contract and avoid simultaneous writes. Do not duplicate a scene, importer or controller to bypass a shared file.

## Execution order and effort review

1. **Now:** Suhita starts P03-SR1 → SR2 → SR3 from current main on `work/suhita-p03`. Khalid can prepare P03-KR1/KR2 on `work/khalid-p03` using existing real Sentinel data while the Tracker contract is finalized.
2. Publish the typed guard/registry/event contract first. Both branches use it; Suhita wires the runtime and Khalid connects/refines the visible cues. No placeholder search metrics or hidden-state shortcuts.
3. Integrate P03 and verify its shared gate before starting P04 logic. Apply the same pattern through P08. Agents stop at the explicitly requested owner/phase boundary.
4. At each phase gate record actual active effort if known, remaining estimates, blockers and files touched. If forecasts differ by more than about 20%, transfer a bounded **unstarted** slice (for example a fixture/persistence task to Khalid or integration QA to Suhita), update its owner/context, and keep the primary specialisms above. Never invent historical hours.
5. Both developers test their own work. Neither becomes the other person's cleanup queue. Reuse finished art and working rules; prioritize missing required functionality over optional visual expansion.

P08 closes only with all R01-R27 functionality, both modes, real algorithms, environment/tools, policies, scores, persistence, verified primary archives and evidence. Public itch.io release/license/platform gates remain separately recorded. See the [phase specs](phases/README.md) and [current status](../tracking/STATUS.md).
