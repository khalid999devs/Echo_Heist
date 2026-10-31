# Player and reviewer guide

Development build, not finished V1. Prefer the version/commit/hash in the matching build manifest. Do not combine files from different archives.

## Install and start

Windows x64: extract the complete ZIP to a writable folder, retain the entire EchoHeist folder and open EchoHeist.exe. Python is not needed for the frozen build. Physical Windows gameplay/audio QA for this candidate is pending even if hosted build/smoke is green.

macOS Apple Silicon: extract the ZIP and open Echo Heist.app. Preserve the complete bundle; Python is not needed. Current packaging is ad-hoc signed and not notarized. Gatekeeper/download behavior on a clean Mac remains a release check; use the OS-supported per-app opening workflow appropriate to the tested macOS, never globally disable security. A native source/frozen smoke run does not prove that download flow.

Source: install Git and uv, clone the repository, check out the handoff branch, run `uv sync --locked --all-extras`, then `uv run --locked echo-heist`. Use Python 3.13 through the lock/environment. On Windows read `docs/development/workflow/setup/WINDOWS_SUHITA.md` for detailed bootstrap/troubleshooting.

## Mission

Play Chapter → choose Human → Launch Mission. Enter via the ground-floor service wing. Take the Security route or Research cover route upstairs. Hold Interact beside the Core, then return to the ground-floor extraction point. The alarm and red lighting signal lockdown. Echo/EMP/stun are tools for escape; they do not award or directly deduct score.

| Default control | Action |
| --- | --- |
| WASD / arrows | Move |
| C | Toggle crouch; move under a prepared desk clearance |
| Left Shift | Hold for up to 3 seconds sprint, then 4 seconds recharge; louder steps can attract guards |
| E | Interact/hold at stairs or Core |
| Q / F / Space | Echo / EMP / emergency stun |
| Tab | Facility map; freezes play |
| Escape | Pause/resume; settings, retry and confirmed abort are available here |
| F2 / F3 | Companion decision / guard diagnostic panels when applicable |

Melee has two charges per run and four seconds recovery, without refill. A legal resisted hit still costs a charge and makes noise. A missed/invalid attempt spends nothing. Its short stun is an emergency opening, not unlimited combat. Crouch and the prepared under-desk clearances work now; full locker/door/glass/canister lifecycles still await their SR implementation.

Settings → Controls remaps ten gameplay actions for the current session. Menus keep Escape/Enter/Tab and diagnostic keys reserved. Settings → Accessibility controls sound captions/high-contrast HUD. Existing music/SFX/window/reduced-flash settings persist. New remap/caption/contrast preferences need Suhita's persistence adapter to survive relaunch; the current build clearly labels saving unavailable. Audio-muted play remains usable.

Results: R retry preserves the deployment seed/policy; N chooses another seed. D shows details; H retrieves history only with a real history provider. Unavailable scoring displays a dash. Companion and saved profiles stay unavailable until their real runtime/services connect. A labeled QA fixture is never a playable AI mode.

## Troubleshooting and evidence

For a bug record version, commit/hash, OS/architecture, seed, mode, steps and a screenshot/log. Test an extracted archive outside the source folder to distinguish missing resources from a development environment issue. User settings live in the platform application-data folder, outside the app bundle. Do not delete personal settings while debugging; preserve a copy for recovery. Current Mac default is `~/Library/Application Support/Echo Heist/`; Windows uses the platformdirs Echo Heist user-data path. The diagnostics report records the exact settings path.

The final release needs verified minimum OS/hardware versions, Windows/Mac physical playback, full V1 save locations and uninstall/recovery instructions after SR persistence is integrated. Those claims remain pending.
