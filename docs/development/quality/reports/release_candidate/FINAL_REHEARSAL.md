# Final gameplay and presentation rehearsal

2026-11-20, Khalid. Runtime `de2d215`, Apple Silicon macOS 26.4.1, Python 3.13.16, pygame-ce 2.5.8 and SDL 2.32.10. The [runbook](../../../release/draft/DEMO.md) ties the presentation to this candidate.

## Corrections

- The Workshop now selects the profile it just saved. A second profile followed by Load Selected previously restored the first profile. The regression drives both buttons through the real Workshop and persistence service.
- Controls now exposes Save Preferences on the same screen as key remapping. The regression saves a remapped key through that button and verifies it in a fresh flow using the real store.

## Rehearsal outcomes

Each run used the production facility and an isolated profile. Human attempts used ordinary scripted keyboard input. Companion attempts started from the normal spawn with the selected Workshop policy and NEXUS memory off. Win, capture and retry came from committed simulation events.

| Mode and route | Seed | Outcome | Tick | Score |
| --- | ---: | --- | ---: | ---: |
| Human, Security approach and Research return | 1042 | Cargo extraction | 1221 | 76/A |
| Human, Research approach and Security return | 1042 | Entry extraction | 1520 | 76/A |
| Human, Security approach and sprint-only escape | 1042 | Vault Sentinel capture | 738 | 0/F |
| Companion, Balanced | 1042 | Cargo extraction | 2826 | 64/B |
| Companion, Rush | 1042 | Vault Sentinel capture | 1059 | 0/F |

Native Cocoa review also exercised fullscreen at 1470 × 923, four window sizes down to 1024 × 768, guide navigation, pointer mapping, UI profile save/load, persistence of remapped controls and high contrast, saved result history after reopening, and NEXUS reset confirmation. The 13 authored props were sampled at controlled neighboring starts with full production security. All transitioned as expected and their cues produced 36 mixer submissions. The main footage uses the normal entry point.

## Scope and evidence

| Requirements | Evidence |
| --- | --- |
| R01–R09 and R27 | Both Human exits, win/capture/retry, opening and epilogue, visible lockdown, real tools and cover. Native prop sampling and automated occlusion, noise, capture-order and geometry tests cover edge cases. |
| R10–R15 and R20 | Tagged evidence and live F2/F3 traces, deterministic guard and Companion integration tests, filtered observation checks, ordinary minimax and alpha-beta parity, and real NEXUS memory reset. |
| R16–R19 and R21–R22 | Real saved Workshop selections, seed/retry navigation, title history, accessibility and input persistence, and authoritative terminal grade evidence. |
| R23–R24 | 96 controlled policy cases, locked checks and freshly extracted Mac package. |
| R25–R26 | Independent publication gates. Exact physical Windows playthrough and public Mac download/Gatekeeper acceptance remain open. Public GitHub licensing and publication remain separate decisions. |

`uv run --locked python scripts/experiments/comparison.py --output-dir output/final-rehearsal/comparison` reproduced all 96 earlier run outcomes, elapsed ticks and fingerprints. Ghost won 2/24, Balanced 3/24, Rush 6/24 and Custom 3/24. There were 82 captures and zero runner caps. The tests include controlled scenario starts. Both settings fixes apply only to presentation and storage interaction.

The Interceptor parity sample reused the production route graph and scoring tree with a single exit goal. At guard tile `(59, 26)`, both chose the Research gate with value 0.255333. Plain minimax evaluated 23 leaves and alpha-beta evaluated 9. All four sampled locations agreed on the selected gate and value. In a separate production Rush deployment with memory enabled, the game observed three decoys before capture and persisted Verify Echo. Loading that memory changed the next attempt's fingerprint. Reset restored the baseline fingerprint. The three attempts all ended at tick 1059.

## Package, performance and footage

- `uv run --locked --all-extras --cache-dir .cache/uv python scripts/checks/run.py` passed the structure check, Ruff lint and format checks, strict mypy and all 338 tests.
- The Apple Silicon ZIP was built from clean runtime `de2d215`. Fresh extraction passed code signature verification and all nine frozen smoke checks with Cocoa display and audio ready. The archive is 114,115,962 bytes with SHA-256 `3d07181bcfd4f16161b2f50d8d96d4549916a31e22767b5d67035287f66c0755`.
- Hosted Windows x64 and macOS arm64 builds and frozen checks passed alongside the Linux headless job on the same runtime. [Candidate CI](https://github.com/khalid999devs/Echo_Heist/actions/runs/44628629059)
- Native profiling covered eight restarts across both modes and two resolutions, followed by a full Balanced win. The 95th-percentile frame time was 16.74 ms during infiltration and 16.75 ms in lockdown, including presentation. After warmup, the final six samples spanned 22.5 MB of resident memory. The short run used production security, with the teaching view and Python memory tracing off.
- The offline demo is 1:50 at 1280 × 720 with H.264 video and AAC audio. The finished MP4 decoded end to end and representative frames were visually reviewed. The same folder contains complete recordings of the Human Cargo win and both Companion outcomes.

## Delivery limits

The pace reference still needs human playtest timings. Both demonstrated Human wins received all ten pace points. Keep the approved score rules for the presentation. The verified fullscreen and audio checks describe this Mac. The room projector and its audio equipment require a local playback check before presenting.
