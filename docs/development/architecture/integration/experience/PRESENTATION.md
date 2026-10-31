# P06 experience consumer handoff

Owner: Khalid. Date: 2026-10-31. Branch: `work/khalid-p06-ui`, stacked on `work/khalid-p05-visuals` / `f50b08a`. User authorized these independent consumers before the shared P05 gate. Actual scoring, encounters, policy interpretation, persistence and final deployment remain Suhita's P06-SR1/SR2/SR3.

## Connection

Pass an `ExperienceGateway` to `GameFlow(..., experience_gateway=...)` alongside the separate existing `autonomy_gateway`. The desktop default passes neither; Human gameplay works, Companion stays unavailable, profiles/history do not pretend to save, and results remain explicitly unscored. A test gateway exists only under `tests/fixtures/experience` and is never imported by the application.

Contracts are in `core/contracts/experience/{model,ports}.py`; they import no pygame or storage code. Reuse existing `RunResult` rather than introducing a competing scoring result. The immutable wrapper is `RunReport(run_key, map_id, result, ticks_per_second, tools, achievements, policy_label)`.

| Port | Consumer and required behavior |
| --- | --- |
| `report(ResultRequest) -> RunReport or None` | Called once when an actual MissionEnd reaches Flow, outside drawing. Return only the authoritative result for this unique local run key/map/seed/mode/outcome/elapsed tick/rate/tool-count tuple. Return None when unavailable. Do not calculate encounters in the renderer. |
| `history() -> tuple[RunReport, ...]` | Explicit H/button fetch only, at most 100 unique run keys, newest first. Browsing is read-only and never deploys a historical run. |
| `profiles() -> tuple[SavedProfile, ...]` | Explicit browser refresh, at most 32 unique stable profile IDs; validate/recover the saved schema in your adapter. |
| `save_profile(name, PolicySelection) -> SavedProfile` | Names bounded to 24 printable characters; save current four-enum draft, return only after actual save succeeds. Decide overwrite/name-conflict semantics in the backend; signal errors truthfully. |
| `delete_profile(profile_id)` | Called only after a second Delete/Enter/click confirmation. Escape cancels. |
| `preferences() -> DesktopPreferences` | Read once at construction; invalid/conflicting/reserved assignments recover to default controls with a notice. |
| `save_preferences(DesktopPreferences)` | Explicit save only. On failure keep functional session preferences and show error; do not display saved success. |

Expected operational/data errors must be translated to `ExperienceUnavailable` (or ValueError for invalid data). Never silently discard a damaged profile/history file, write partial settings or report successful IO before it completes. Disk paths, atomic writes, versions, recovery/backups and migrations belong to SR.

A gateway may obtain results from its shared runtime/service registry. `ResultRequest` contains legitimate end metadata and real own committed tool usage, not an observation dump or fabricated detection total. Runtime `StepResult.terminal` is also supported when no ExperienceGateway is installed; its data must match the same request. Abort handling now retains that terminal value as well. If an experience gateway is installed it is authoritative; None/error does not silently substitute another provider's result.

`RunReport` validates supplied component sums, approved ranges/ranks, win-only unique achievements and metadata before display. These are boundary assertions, not an implementation of encounter lifetime, pace calculation or achievements. UI never infers score from guard states, event counts, wall time or gizmo animation. Fingerprint schema remains **10**; no physics/AI/scoring mutation is added here.

## Preferences and input

`DesktopPreferences` holds immutable `KeyAssignment(action, tuple[keycodes])`, sound captions and high-contrast HUD. Existing `SettingsStore` continues to persist music/SFX, fullscreen/window size and reduced flashing; new remaps/caption/contrast persist only if SR supplies the port. Combine these in your versioned adapter without losing the old preferences. Default current-session new preferences reset on relaunch, and the UI says saving is unavailable.

Ten editable actions: up/down/left/right/sprint/interact/echo/emp/melee/crouch. Escape, Enter, Tab, F2, F3 and F11 remain reserved. Duplicate cross-action bindings are rejected; movement arrow aliases remain unless the chosen primary duplicates its own alias. Use `ui/input/configuration.bindings_for` for the desktop adapter; cache is bounded to 32 immutable preference snapshots. Capturing a key suppresses gameplay; Escape/focus loss/resize cancel capture. Live hints and objective prompts use actual bindings. Resuming/retrying preserves current session preferences and clears held input.

Captions consume only own actions, global lockdown and listener-permitted heard IDs. Visible foreign glass/door actions are not automatically audible. Deduplication retains at most 256 IDs; hearing/caption rendering creates no noise or detection. Pause freezes simulation-tick caption lifetimes. High contrast adds opaque HUD backplates without changing world visibility or AI observations.

## Navigation

- Briefing and Workshop: N or visible Seed button, bounded 0..2147483647; cancel never changes a queued run. Apply edits the next deployment only.
- Workshop: P or Saved Policies. N enters a name; S saves; arrows browse; L loads into the draft; Delete then Enter/Delete confirms deletion. No load changes an active Simulation or bypasses deployment validation.
- Results: D details, H saved reports inside details, arrows browse, Escape closes. R preserves last deployment; Companion returns through policy/protocol review. N asks for another seed and preserves mode/policy. A missing Companion runtime never silently launches Human.
- Settings: Controls/Accessibility subpages have mouse and arrow/Tab/Enter navigation. Escape cancels capture, returns a subpage to General, then returns to the paused mission/menu. Sound captions/high contrast work now; Save Preferences is intentionally unavailable without its backend.
- An unavailable report still displays actual outcome/time/seed/tool usage. Approved score/rank/encounter/achievement fields show unavailable, never zero-filled success.

## Required connected acceptance

Suhita should preserve these contracts while completing shared P04/P05 first. Then connect actual scores/encounters, all policy translations/presets and named profile recovery, history/settings persistence and atomic seed/policy/reset deployment. Verify real S/A/B/C/F, team encounter expiry/reacquisition, both modes, restart/relaunch, failed writes and corrupt data. Replace fixed fixture evidence with real backend run evidence before closing P06. The independent review and local draft media are linked from the P06 handoff; shared P04–P08 gates stay open.
