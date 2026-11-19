# Player and reviewer guide

Use the desktop candidate and its matching build manifest. Keep each extracted bundle together.

## Install and start

Windows x64: extract the complete ZIP to a writable folder, retain the entire EchoHeist folder and open EchoHeist.exe. Python is not needed for the frozen build. Physical Windows gameplay/audio QA for this candidate is pending even if hosted build/smoke is green.

macOS Apple Silicon: extract the ZIP and open Echo Heist.app. Preserve the complete bundle; Python is not needed. Current packaging is ad-hoc signed and not notarized. Gatekeeper/download behavior on a clean Mac remains a release check; use the OS-supported per-app opening workflow appropriate to the tested macOS, never globally disable security. A native source/frozen smoke run does not prove that download flow.

Source: install Git and uv, clone the repository, check out the handoff branch, run `uv sync --locked --all-extras`, then `uv run --locked echo-heist`. Use Python 3.13 through the lock/environment. On Windows read `docs/development/workflow/setup/WINDOWS_SUHITA.md` for detailed bootstrap/troubleshooting.

## Mission

Play Chapter → Human → Launch Mission to control the operative. Choose Companion → Workshop → Deploy Companion to watch the autonomous robot run the same mission. Select a preset or edit the four policy blocks in the Workshop. Saved Policies keeps those settings between launches.

Take either stairway upstairs. Hold Interact beside the Core, then escape downstairs through the **Entry Airlock** or **Cargo Airlock**. Press Tab to see both exits and both stairways. The alarm and red lighting signal lockdown. After a guard confirms you, break sight at a corner or reach cover before recharging your sprint. A guard that saw you enter hiding can investigate that spot.

| Default control | Action |
| --- | --- |
| WASD / arrows | Move |
| C | Toggle crouch; move under a prepared desk clearance |
| Left Shift | Hold for up to 3 seconds sprint, then 4 seconds recharge; louder steps can attract guards |
| E | Use stairs, doors and lockers. Hold beside the Core |
| Q / F / Space | Echo / EMP / emergency stun |
| Tab | Facility map; freezes play |
| Escape | Pause/resume; settings, retry and confirmed abort are available here |
| F2 / F3 | Companion decision / guard diagnostic panels when applicable |

Melee has two charges and four seconds of recovery. A legal resisted hit still costs a charge and makes noise. Crouch to move through clearances beneath marked desks. Lockers conceal you when entered out of view. A hard sprint into breakable glass or a loose canister can make noise and draw a guard away.

Settings → Controls remaps the ten gameplay actions. Open Accessibility to choose sound captions and high-contrast HUD, and use Save Preferences to retain those choices and key bindings. Music, sound effects, window mode and reduced flashing use the general settings.

Results show the authoritative 50-point extraction, up to 40-point stealth and 10-point pace breakdown. A distinct confirmed encounter costs 12 stealth points. Capture or abort earns 0/F. Gadget counts are informational. R retries with the same seed, N lets you select a new seed, and D shows report details. Open Report from the title menu to browse saved attempts after a relaunch. Workshop → NEXUS Memory lets you turn adaptation on/off or clear learned memory before deploying again.

## Troubleshooting and evidence

For a bug record version, commit/hash, OS/architecture, seed, mode, steps and a screenshot/log. Test an extracted archive outside the source folder to distinguish missing resources from a development environment issue. User settings live in the platform application-data folder, outside the app bundle. Do not delete personal settings while debugging; preserve a copy for recovery. Current Mac default is `~/Library/Application Support/Echo Heist/`; Windows uses the platformdirs Echo Heist user-data path. The diagnostics report records the exact settings path.

Settings, preferences, profiles, history and NEXUS memory are separate JSON files in the same application-data folder. Back up that folder to transfer progress. Removing the game bundle or extracted folder leaves those files available for a future install.
