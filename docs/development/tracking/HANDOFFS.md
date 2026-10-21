# Work claims and runnable handoffs

P01 and P02 are complete. The [P01 handoff](handoffs/khalid/day_01/P01.md), [P02 integration handoff](handoffs/khalid/day_01/P02_INTEGRATION.md) and [phase specs](../planning/phases/README.md) define the accepted baseline and next owner slices. [Backlog](BACKLOG.md) maps shared feature anchors.

Suhita's original Windows x64 setup and branch workflow remain documented in [Windows setup](../workflow/setup/WINDOWS_SUHITA.md). Her `a98548a` source commit was accepted into the user-directed P02 integration review; she did not publish a separate P02 handoff or Windows interactive QA result on that branch.

## Active claims

| Developer | Phase / slice | Branch or working-diff reference | Files currently claimed | State |
| --- | --- | --- | --- | --- |
| Khalid | User-directed first stealth vertical slice, beginning P03-K1/K2 | work/stealth-vertical-slice | core/perception and security contracts/systems, ai/navigation and guards, ui/audio and compact scene/HUD, room data, audio/visual resources and milestone records | IN_PROGRESS; full P03 and later phases remain open |
| Suhita | None; P02-S1/S2 technical work accepted in combined review | work/suhita-p02 at a98548a | None | P02-S1/S2 DONE for phase gate; Windows interactive QA NOT_RUN |

This table is coordination metadata, not a distributed lock. When working in different checkouts, synchronize the relevant handoff/claim commits before editing shared files. Resolve conflicting claims before overlapping writes; do not assume a stale copy of this table proves exclusivity.

P02 integration boundary: [runtime contract](../architecture/integration/P02_RUNTIME.md). The original owner slices stayed separate; under the user's later explicit request Khalid reviewed/refined Suhita's scene/render files on a new integration branch. Her branch and authorship remain intact. `ui/presenters/objective.py` and `ui/input/human.py` continue to define the core/UI boundary.

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

An owner can mark their named slice DONE when its behavior/checks pass. A shared EH task remains TODO/IN_PROGRESS until every required slice in its Backlog mapping is complete and its feature acceptance passes. The integrator marks P01-P08 DONE only on the combined build and records exact evidence in Status. Missing primary archives or gameplay functionality keep P08 incomplete; public release is tracked separately.
