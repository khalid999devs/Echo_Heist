# Work claims and runnable handoffs

Baseline: no implementation claims or handoffs exist. P01 belongs to Khalid; Suhita's first implementation phase is P02 after the runnable foundation handoff. The [phase specs](../planning/phases/README.md) define owner slices and [Backlog](BACKLOG.md) maps shared feature anchors.

## Active claims

| Developer | Phase / slice | Branch or working-diff reference | Files currently claimed | State |
| --- | --- | --- | --- | --- |
| Khalid | P01-K1, then K2/K3 | main; incremental local commits | Foundation package, root configuration, checks, packaging and P01 tracking | IN_PROGRESS |
| Suhita | None | None | None | Waiting for P01 foundation; preparation allowed |

This table is coordination metadata, not a distributed lock. When working in different checkouts, synchronize the relevant handoff/claim commits before editing shared files. Resolve conflicting claims before overlapping writes; do not assume a stale copy of this table proves exclusivity.

## Claim protocol

1. Resolve developer identity and earliest ready assigned slice. Read the actual prerequisite handoff, existing changes and relevant contracts.
2. Record slice, branch/diff and intended files. Each slice has one primary writer. Reserve a distinct adapter/presenter file when both owners work in the same subsystem.
3. Prefer separate owner branches/checkouts for concurrent work. Preserve unrelated changes; no force-reset/overwrite of the other owner's work. Keep changes small enough to integrate at the phase gate.
4. Implement and verify your behavior. A changed shared interface must include its contract update and consumer notes. If another owner must change a file, hand off that narrow dependency rather than editing it simultaneously.
5. Write your handoff and release the claim. The phase integrator combines both slices, reruns affected checks and records the phase gate.

Do not start a teammate agent or send external messages just because an owner is named in these documents. These files prepare each developer's separately invoked agent.

## Where to store completed handoffs

Create records only after real work under `tracking/handoffs/<owner>/day_01/`, `day_02/`, `day_03/`, or `day_04/`, using phase filenames such as `P02.md`. This keeps at most two normal phase records in each day directory. If a phase needs more than six records, group revisions under a subdirectory. Link the resulting evidence from Status/Backlog and this index.

No completed records are present yet.

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
