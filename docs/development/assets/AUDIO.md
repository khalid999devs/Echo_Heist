# Music and event cue integration

Date: 2026-10-21. Runtime: `ui/audio/`, connected by `ui/bootstrap.py` after the committed scene/simulation update. Source selection: CC0 recordings from [SRG774](https://opengameart.org/content/dark-sci-fi-audio-pack), [rubberduck](https://opengameart.org/content/50-cc0-sci-fi-sfx), and [Kenney](https://kenney.nl/assets/impact-sounds). Packaged [credits and license notices](../../../src/echo_heist/resources/assets/audio/CREDITS.md) and [per-file manifest](../../../src/echo_heist/resources/assets/audio/manifest.json) retain authors, original archive members, hashes and download date.

| Context/event | Audio |
| --- | --- |
| Title, briefing, Settings | `title.ogg`, quiet background level |
| Infiltration | `sector.ogg`, ambient bed below tactical cues |
| Confirmed pursuit | `pulse.ogg`; context is supplied by actual committed guard state |
| Mandatory lockdown | `urgent.ogg`, entry alarm cue and continuous siren on dedicated channel 2 |
| Results | `transmission.ogg`; victory cue only for an actual WIN event |
| Selection / screen navigation | Quiet hover and terminal confirmation |
| Committed walk/sprint NoiseEvent | Concrete step sample, louder for sprint |
| Committed Echo / EMP / melee | Hologram / electrical / metal impact cues |
| Sighting confirmed / capture started | Security warning tone |

Scene-presentation revision: Workshop/Guide/Companion designs use title music; successful extraction/epilogue use transmission. Stair start/arrival each play a footstep. The reused CC0 alarm loops independently of alerts/tools; pause/map freeze it, SFX volume mutes it, leaving live lockdown stops it. Tests cover the loop lifecycle and volume independently of music. [Current actual native evidence](../quality/reports/scene_presentation/REVIEW.md) supersedes the older timing/counts below; subjective speaker/mix and interactive Windows checks remain pending.

Pursuit music now consumes the live Sentinel's actual CHASE/SEARCH state. Playback never emits a hidden simulation noise or changes guard knowledge. UI sounds and background music cannot alert robots.

Tracks stream from packaged in-memory resource bytes, independent of cwd. Music switches with a 250 ms fade-out and 700 ms fade-in. Ordinary SFX use bounded channels; UI and security cues have reserved channels. Event IDs deduplicate repeated delivery and reset on a genuinely new run. Music ducks while paused. Separate music/SFX sliders apply immediately and persist through SettingsStore; unavailable devices and `--mute` preserve silent gameplay.

Actual checks: all 89 tests plus structure/Ruff/strict types PASS. The audio integration case decodes all 16 shipped assets and checks context selection, event deduplication, pause ducking and independent volumes using SDL dummy audio. A 90-frame native Cocoa startup on the Mac reported `audio=ready`, 16 assets loaded, `music_track=title`, settings saved and no runtime error. This proves playback initialization, not subjective mix approval or Windows speaker quality.

The native audio-enabled Human playthrough exercised title, infiltration, pursuit, lockdown and result music, loaded all 16 assets and emitted 108 event/UI cues during a genuine WIN. Exact performance/evidence scope: [current review](../quality/reports/phase02/presentation/REVIEW.md).
