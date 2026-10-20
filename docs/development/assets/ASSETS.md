# Production asset and attribution register

Blueprint basis: pp. 2-4, 19. P02 now ships original generated scene, floor, bulkhead, prop and actor art, plus code-drawn gameplay overlays. Required interaction features stay in scope even if optional decorative assets are cut.

P01 foundation asset: [original SVG mark](../../../src/echo_heist/resources/assets/branding/mark.svg), with package-owned bootstrap JSON. This is a simple project-authored development graphic, not an imported third-party asset or finished scene art. It is exercised in source, wheel and native builds. Final production-art/source licensing and owner credits remain pending before public release; minimum production rows below remain TODO.

## Minimum production set

| ID | Asset group | Minimum content | Status |
| --- | --- | --- | --- |
| A01 | Facility tiles | Five zones, floors, opaque walls, tagged glass, cover, doors, cabinets, upper/lower route cues | IN_PROGRESS; P02 illustrated floor/bulkhead/room props, glass/cover motifs; doors and interactive effects later |
| A02 | Intruders | Operative and Companion silhouettes; idle/move/hide/tool/strike/core/captured states; shared collision dimensions | IN_PROGRESS; Human top-down idle/walk/sprint frame strip with facing and dossier portrait; remaining states later |
| A03 | Defenders | Distinct Sentinel, Tracker, Interceptor; move/scan/alert/disabled/stun/grab cues | IN_PROGRESS; P02 guard post sprite strip; distinct type silhouettes and actual patrols later |
| A04 | Mission anchors | Entry/exit beacon, core plinth idle/pickup/empty, carried-core indication | IN_PROGRESS; P02 reactor inset, extraction pad, animated beacons and carried-core light |
| A05 | Interactions | Intact/shattered glass rack, rolling canister, doors and hiding feedback | TODO |
| A06 | Effects | Echo ghost/trail, EMP ring, capture telegraph, clear suspicion/contact/lockdown states | IN_PROGRESS; P02 Echo/EMP event rings, capture telegraph and lockdown border; richer P03-P05 feedback later |
| A07 | Audio | 6-10 gameplay cues, one loopable ambience/music layer, source event mapping and separate volumes | TODO |
| A08 | Interface | Legible font, status icons, mode/Workshop/results panels, non-color cues and critical subtitles | IN_PROGRESS; bundled Oxanium family, P02 title/briefing/HUD/results and keyed minimap; Workshop/accessibility later |
| A09 | Narrative | Short opening/contact/theft/win copy and replication-seed epilogue | TODO |
| A10 | Release media | Icon, cover art, representative screenshots and gameplay video | IN_PROGRESS; P02 review screenshots only |

The PDF's compressed release checklist mentions four actor silhouettes, while its detailed animation list distinguishes the operative, Companion and three guard types. Follow the detailed readability requirement: five recognizable actor identities, with shared animation bases where practical.

## Per-asset record

| ID | Runtime path | Origin / date | Modification and use | Attribution / review |
| --- | --- | --- | --- | --- |
| A01-ART | `resources/assets/scenes/title-facility.png` | Generated with the built-in OpenAI imagegen tool on 2026-10-20 using owner-provided concept images as mood references; SHA256 `51b0fbb4357e3b644d05956b42a1e8e064e0cbcd61d3d4245cc140f02a21d91f` | Original 2.5D facility illustration; scaled behind title/briefing, cropped for outcome screen. It is illustration, not the collision map or a live gameplay feed. | No third-party download or required credit identified. Owner to confirm rights to supplied visual references before public release. |
| A02-ART | `resources/assets/characters/operative-dossier.png` | Generated with the built-in OpenAI imagegen tool on 2026-10-20; SHA256 `b2acd19d61ad782c2ce27aac5f6ec38925779c404988c837e60daecb34929f0e` | Cropped/resized transparent operative illustration for Human briefing. | No third-party download or required credit identified; owner review pending. |
| A01-TILES | `resources/assets/tiles/facility-floor.png`, `bulkhead.png`, `facility-props.png` | Original OpenAI imagegen outputs generated 2026-10-20 from prompts using the owner's supplied concept as mood reference; SHA256 respectively `e39537085ea96f5e75768f620f9f6cdbb6039dfb53335f312905b1761637cdf6`, `9c4660067a32beed5b55f5fdb02d2776b619078bccbe15100cf69ed0a5499fef`, `7871974ce691c94de759c91a1a74f9f8ce04ecc31e8f0d50c6932c7d5e79ce74` | Textured tile surfaces and cropped six-prop atlas decorate the Tiled map. Props occupy known blocked cells; none define collision. | No third-party download or required credit identified; owner review pending. |
| A02-MOTION | `resources/assets/characters/operative-motion.png` | Original OpenAI imagegen four-frame strip generated 2026-10-20; SHA256 `ebd63ed6cfd83876f33f9b78178452946fb9c08ef1a9ca6ba401b4b4bf15d855` | Top-down Human idle/walk/sprint presentation with facing derived from committed position deltas. | No third-party download or required credit identified; owner review pending. |
| A03-MOTION | `resources/assets/characters/guard-motion.png` | Original OpenAI imagegen four-frame strip generated 2026-10-20; SHA256 `92f3ec59f965d59329b49533ad476de19108b677ab32e46523c5a161bc89dc51` | P02 stationary guard post art and idle light. Patrol motion awaits P03 simulation; this strip can support it then. | No third-party download or required credit identified; owner review pending. |
| A01-CODE | `ui/render/motifs.py`, `ui/render/world.py` | Original project code, P02 integration on 2026-10-20 | Draws tagged glass/cover, actors, anchors and lights from validated map/snapshot atop the illustrated tile layers. No visual pixel controls collision or AI sensing. | Project-authored; no external asset license. |
| A08-FONT | `resources/assets/fonts/Oxanium-{Regular,SemiBold,Bold}.ttf` and `OFL.txt` | Severin Meyer's [Oxanium upstream](https://github.com/sevmeyer/oxanium), pinned commit `a8f39e0c71186190027a093e9001459410192d1e`, downloaded 2026-10-20. SHA256 Regular `2b9c2a53ee0a8248ab901463838cc81075b410724046a09683b3cc91870fe52a`, SemiBold `e2d77ec4ee67b0152166adf5d6393360550a012c2066e0d4589053e14a733cdc`, Bold `15a44f661fd962c64cabe069a5f9f6fab85a412188f028d3e04da2ff917e37cc`, license `fe17c0f2581d71b4e1ea7e636e7f4877c29223e11bb1dd1a871e8c3f2a86336b` | Unmodified TrueType files used for all menu/HUD/result text; redistributable with included [SIL OFL 1.1](https://github.com/sevmeyer/oxanium/blob/master/OFL.txt) notice. | Credit: Oxanium by Severin Meyer / Oxanium Project Authors. Keep bundled OFL text in public builds. |

The above records cover new P02 assets. Later phases must finish the remaining rows and release credits. The generated art does not grant permission to redistribute the owner's reference images themselves; those images are not bundled.

For each imported or original item record: stable ID, runtime path, source/author URL, origin (original/third-party/generated), exact license text or license URL, modification notes, required attribution, download/version date, and reviewer. Store any required redistribution license notices with shipped assets and generate release credits from the register.

Prefer original work or CC0/permissive assets with documented redistribution rights. Free availability alone does not establish a license. Include fonts, audio, icons and bundled dependencies in the review. Original assets need authorship/provenance too. Generated art must have its origin and any reference permissions recorded before release.

Use consistent logical dimensions, actor pivots and atlas naming. Greybox first; collision/vision/sound geometry belongs to explicit map data, never inferred from sprite pixels. Gameplay audio is emitted from committed simulation events; cosmetic ambience cannot alert guards. Test readability and reduced flashing after asset replacement.
