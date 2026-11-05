# Approved emergency melee balance

Approved by Khalid in chat on **2026-10-30**: “okay apply them for me,” following the explicit two-charge/four-second proposal. This overrides unlimited melee on blueprint p. 8. The source PDF is preserved. Approved scoring is unchanged.

- Every fresh Human/Companion attempt starts with **two melee stun charges**. Charges never refill during the attempt.
- A reachable valid strike consumes one charge and starts **four seconds of Simulation-tick recovery**. The existing single-target **1.5-second stun** and **two-second recovery immunity** remain.
- A guard resisting an otherwise legal strike still costs the charge/recovery and creates its impact noise. Empty, cooling-down, stale, malformed or unreachable actions spend nothing and create no impact noise.
- Every valid impact emits exactly one existing **MELEE NoiseEvent, radius six tiles**, whether it stuns or is resisted. Acoustic occlusion still applies.
- Guards who legitimately hear the clang may investigate its original impact location and retain that evidence for approximately **five seconds** using the existing versioned sensor memory (150 ticks at 30 Hz). This does not reveal a moving player's future/current position, globally alert unheard guards, create confirmed visual detection, or reset/extend old evidence through replay.
- The HUD displays actual remaining charges and recovery time. Restart resets both; pause does not advance the timer. Both controller types receive the same immutable inventory and recovery fields.

Khalid is explicitly authorized to implement this narrow P05-SR1 balance subset and its HUD/testing/handoff, despite the normal graphics/logic split. Suhita retains all other P04/P05 gameplay ownership. Full phase gates remain open.
