# Eight implementation phases

P01 and P02 are DONE; P03 is IN_PROGRESS; P05 has only an early crouch subset IN_PROGRESS; P04/P06/P07/P08 are TODO. The user requires a complete functional initial draft after P08, within four development days. The earlier M0-M5 labels are retired for active implementation; EH task IDs remain as feature traceability anchors. Read the [runnable P02 integration handoff](../../tracking/handoffs/khalid/day_01/P02_INTEGRATION.md) and [current Status](../../tracking/STATUS.md) for the actual baseline.

| Phase | Day | Specification | Prerequisite | Integrator |
| --- | --- | --- | --- | --- |
| P01 | 1 | [Environment and foundation](foundation/PHASE_01.md) | Planning baseline | Khalid |
| P02 | 1 | [Playable Human heist and scene](foundation/PHASE_02.md) | P01 | Suhita planned; Khalid final review by user direction |
| P03 | 2 | [Fair perception and defenders](intelligence/PHASE_03.md) | P02 | Suhita; Khalid visual acceptance |
| P04 | 2 | [Companion strategy and NEXUS](intelligence/PHASE_04.md) | P03 | Suhita; Khalid visual acceptance |
| P05 | 3 | [Tools and environment](experience/PHASE_05.md) | P04 | Suhita |
| P06 | 3 | [Workshop, scoring and complete UI](experience/PHASE_06.md) | P05 | Khalid; Suhita behavior acceptance |
| P07 | 4 | [Integration and evidence](delivery/PHASE_07.md) | P06 | Khalid |
| P08 | 4 | [Complete working draft delivery](delivery/PHASE_08.md) | P07 | Khalid |

Ownership was revised on 2026-10-22: Khalid leads complex visuals/scenes; Suhita leads most logic. New **KR/SR** IDs define remaining P03-P08 work and supersede old future assignments; P01/P02 and completed subsets retain their history. Day labels preserve the original work sequence, not a new deadline guarantee.

Each phase contains independent owner slices, source pages, interfaces, file boundaries, required checks and its gate. Read the [workload allocation](../WORKLOAD.md) and the appropriate [owner guide](../../workflow/START_HERE.md) before claiming work. A completed owner slice is not the same as a completed phase.

Planning and phase status live in [Status](../../tracking/STATUS.md); feature anchors in [Backlog](../../tracking/BACKLOG.md); active claims and handoff evidence in [Handoffs](../../tracking/HANDOFFS.md). P08's gate covers every required functional feature. Later work refines the complete game rather than filling missing functionality.
