# P05-SR1/SR2 verification (Suhita)

2026-11-09. Branch `work/suhita-p05`, runtime **`10fca5d`** (from `work/suhita-p04` c99984e, which already contains main 1136788). [Handoff](../../../../tracking/handoffs/suhita/day_03/P05.md), [runtime contract](../../../../architecture/integration/environment/RUNTIME.md), [compact evidence](EVIDENCE.json).

## Where each check actually ran

| Environment | What ran | Result |
| --- | --- | --- |
| Locked `uv sync --locked --all-extras --python 3.13` on the Linux shell of Suhita's computer (CPython 3.13.16, pygame-ce 2.5.8, SDL dummy video/audio), on `E:\Echo_Heist` | `scripts/checks/structure.py`, `ruff check .`, `ruff format --check .`, `mypy` (project config) | PASS (175 source files) |
| same | Full `pytest` in two parts (`tests/unit` + audio/persistence/replay/perception/smoke: 223; `tests/integration/mission` + `presentation`: 77) | **300 passed** |
| same | `p05_evidence.py --seeds 4` | deterministic hash `0627727795…7862d7e` |
| Agent Linux container (CPython 3.13.17, non-locked Ruff/mypy) | Non-pygame suites while developing; `p05_evidence.py --seeds 4` | same hash `0627727795…7862d7e`; PASS |
| same | `p05_evidence.py --seeds 12` (72 Companion attempts, 4 Human routes, scripted lifecycle) | numbers below, raw hash `46f1db7f…393656`, 210 s |
| Physical Windows x64 desktop (display/audio) | Interactive play, native package | **NOT_RUN** by the agent; commands in the handoff |
| Hosted CI | Runs on push | NOT_RUN until Suhita pushes the branch |

The full run was split because one shell call is limited to about three minutes; together the two parts are the whole `tests/` tree (299 passed + 1 earlier failure, fixed in `9b89afd`, then all 300 passed).

## Behavior evidence (actual runs)

- **Facility props** (packaged map): doors `door-cross-link` (38,18), `door-core-north` (50,13–14), `door-core-south` (50,29–30); glass `glass-research-rack` (37,24), `glass-research-cell` (33,29); canisters at (17,27), (24,13), (36,22); lockers `hide-1`…`hide-5`. All live from tick 0: doors open, glass intact, lockers empty.
- **Human routes with props**: upper/upper, lower→upper, cross→upper **WIN**; blind lower→lower **CAPTURED**, identical to P04.
- **Scripted Human lifecycle** (seed 1042, 240-tick wait for the service patrol): bump kicks `canister-service-1` to (17,28) with one `METAL` NoiseEvent and one impact cue; `hide-2` offered as `HideSpot`, entered (`hidden_in = hide-2`), left with E; cues `CANISTER_IMPACT`, `HIDE_ENTER`, `HIDE_LEAVE` in order.
- **Companion with vs without props**, 12 seeds × 3 presets: identical outcomes and tick counts for all 36 pairs. Balanced 9 WIN / 3 CAPTURED; Rush 3/9; Ghost 1 WIN / 10 CAPTURED / 1 runner cap. In those 36 prop runs the Companion bumped one canister once and never entered a locker (its locker rule needs a recent threat with no guard in view). Repeating Balanced seed 1 gives the same fingerprint.
- **Native-resolution scene captures** (dummy video, actual `HeistSession.draw` on the packaged map): open and closed core-north door, intact and shattered research glass, an occupied locker with the operative hidden and "E Leave cover", a rolling canister, and "E Use door"/"E Break glass" prompts. Images were reviewed in this session under ignored `output/p05/shots/`; they are layout evidence, not the KR visual acceptance.

## Tests added (all in the 300)

- `tests/unit/core/environment/`: closed door blocks body and sight but still routes; guard push opens silently; door never closes on a body (refusal and bounce); glass once by sprint or E, walkable afterwards; deterministic fingerprints; canister rolls four tiles with one clang linked to its cue, monotone committed travel; kick into a wall is one clang; locker conceal/leave by move or E, one occupant, hidden intruder not contact-captured, crouch refused.
- `tests/unit/core/abilities/test_tool_edges.py` (both controllers): T05 EMP on the completion tick cancels and disables, Echo keeps grab and report; melee reach from desk clearance (fails on the old code); no strike through a closed door; stale tool spends nothing; tools from a locker.
- `tests/integration/perception/test_environment_hearing.py`: T03 with real glass behind a wall (both controllers): the guard investigates the glass tile, gets no sighting or intruder position; an out-of-reach clang is not heard.
- `tests/integration/mission/test_environment_mission.py`: props live from tick 0 through the real gateway, Human route outcomes unchanged, Companion WIN (seed 1) and CAPTURED (seed 4) repeat exactly with fresh NEXUS memory.
- `tests/unit/presentation/test_human_input.py`: held E enters a locker once; a fresh press leaves.

## Not verified here

Physical Windows play/audio, Khalid's connected KR1/KR2 acceptance of the props in the real scene, hosted CI and packaging. The combined P04 gate was still open when this P05 work started at the user's request.
