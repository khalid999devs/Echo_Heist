# P04/P05 merged-main handoff

Khalid, 2026-11-10. User requested review, fixes on Suhita's branches and merge. Original commits and authorship are preserved.

| PR | Reviewed head | Merge into main |
| --- | --- | --- |
| [#5 Companion / Interceptor / NEXUS](https://github.com/khalid999devs/Echo_Heist/pull/5) | a390f8a | 21630e5 |
| [#6 physical environment](https://github.com/khalid999devs/Echo_Heist/pull/6) | 25481a8 | bf3db94 |

`bf3db94` has exactly the reviewed P05 source tree. Current fingerprint is **12**. [P04 review](../../phase04/review/REVIEW.md) and [P05 review](REVIEW.md) contain actual commands, findings and limitations.

## Working result

- Real Companion FSM/utility/A*/bounded belief-only MCTS; physical Interceptor minimax/alpha-beta; evidence-limited NEXUS and persisted protocol/reset. Production startup connects the gateway; Companion is available.
- Simulation-owned three doors, two glass panes, three canisters and five lockers; once-only cues and geometry revisions. Both-mode tool/capture edge regressions and fresh-press interactions are implemented.
- Review fixes: keep the chosen MCTS action visible in the four-row panel; move native Mac CI to supported macos-15; avoid duplicate branch/PR artifact uploads and explicitly report unavailable archives. Validation/build/smoke failures still fail CI.

## Actual verification

- Locked full checks: **301 tests**, structure, Ruff, formatting and strict mypy pass. No production behavior changed after that run; merges preserve the reviewed tree.
- Four-seed P05 evidence matches Suhita's exact hash: `062772779518e25736670732ada894902afc80c97bbc561fe83a855e07862d7e`.
- Native Mac production UI: real Companion 1042 wins at tick 2463; seed 4 is captured at 1180; actual MCTS/Interceptor/NEXUS, pause, outcomes, learned protocol and confirmed reset inspected in 14 screens. Human production input rolls a canister and enters/leaves a locker, including held-E safety, in four additional screens. Cocoa and audio ready.
- Both reviewed heads pass Windows x64/macOS arm64 native build + frozen smoke and Linux headless CI. Merged main runtime [run 42758498870](https://github.com/khalid999devs/Echo_Heist/actions/runs/42758498870) also passes all three jobs. Hosted smoke is not physical Windows gameplay QA.
- Hosted archive storage was full. Existing archives were preserved. An upload warning does not mean a new downloadable artifact was delivered; validation and availability remain separately reported.

## Resume safely

Fetch main, preserve local/unpushed work, switch to main and fast-forward. Retired work branches are historical references, not dependencies. Run `uv run --locked echo-heist`; Chapter → Companion launches the real controller. F2 shows actual decision/Interceptor/NEXUS tabs. Human: WASD/arrows, C crouch, Shift timed sprint, fresh E props/stairs, hold E Core, Q Echo, F EMP, Space limited melee. Preserve existing controls/remapping and both-floor routes.

P04/P05 code is merged and P04 real-data visual review is recorded. Shared phase records remain conservative until their integration lead signs off every combined gate; this merge does not silently close them. Remaining P05 acceptance includes complete native door/glass/ability cue review and current-build physical Windows gameplay. P06 authoritative scoring/encounters, editable saved policies/profiles, history and remap/caption/contrast persistence remain unimplemented; use its existing presentation contract when assigned. Do not rewrite implemented AI or props.

P07 still needs policy balance, rare narrow-corridor body-block hardening, complete fairness/performance/memory/usability acceptance. Ghost/Rush are weaker than Balanced; one Ghost evidence case reaches the test runner's cap, not a game timeout. P08 final platform QA, licensing/media and delivery remain separate. No scoring or approved melee rule was changed by this review. All review implementation claims are released. Both merged work branches were removed locally and on origin only after their tips were proven ancestors of main; no unmerged work was deleted.
