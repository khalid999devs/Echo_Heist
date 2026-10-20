# Production asset and attribution register

Blueprint basis: pp. 2-4, 19. P02 now ships original generated facility backdrop/operative dossier art and code-drawn facility/actor motifs. Required interaction features stay in scope even if optional decorative assets are cut.

P01 foundation asset: [original SVG mark](../../../src/echo_heist/resources/assets/branding/mark.svg), with package-owned bootstrap JSON. This is a simple project-authored development graphic, not an imported third-party asset or finished scene art. It is exercised in source, wheel and native builds. Final production-art/source licensing and owner credits remain pending before public release; minimum production rows below remain TODO.

## Minimum production set

| ID | Asset group | Minimum content | Status |
| --- | --- | --- | --- |
| A01 | Facility tiles | Five zones, floors, opaque walls, tagged glass, cover, doors, cabinets, upper/lower route cues | IN_PROGRESS; P02 floor/wall/glass/cover motifs, doors and final effects later |
| A02 | Intruders | Operative and Companion silhouettes; idle/move/hide/tool/strike/core/captured states; shared collision dimensions | IN_PROGRESS; Human top-down motif and dossier portrait only |
| A03 | Defenders | Distinct Sentinel, Tracker, Interceptor; move/scan/alert/disabled/stun/grab cues | TODO |
| A04 | Mission anchors | Entry/exit beacon, core plinth idle/pickup/empty, carried-core indication | TODO |
| A05 | Interactions | Intact/shattered glass rack, rolling canister, doors and hiding feedback | TODO |
| A06 | Effects | Echo ghost/trail, EMP ring, capture telegraph, clear suspicion/contact/lockdown states | TODO |
| A07 | Audio | 6-10 gameplay cues, one loopable ambience/music layer, source event mapping and separate volumes | TODO |
| A08 | Interface | Legible font, status icons, mode/Workshop/results panels, non-color cues and critical subtitles | IN_PROGRESS; P02 title/briefing/HUD/results, remaining Workshop/accessibility later |
| A09 | Narrative | Short opening/contact/theft/win copy and replication-seed epilogue | TODO |
| A10 | Release media | Icon, cover art, representative screenshots and gameplay video | IN_PROGRESS; P02 review screenshots only |

The PDF's compressed release checklist mentions four actor silhouettes, while its detailed animation list distinguishes the operative, Companion and three guard types. Follow the detailed readability requirement: five recognizable actor identities, with shared animation bases where practical.

## Per-asset record

| ID | Runtime path | Origin / date | Modification and use | Attribution / review |
| --- | --- | --- | --- | --- |
| A01-ART | `resources/assets/scenes/title-facility.png` | Generated with the built-in OpenAI imagegen tool on 2026-10-20 using owner-provided concept images as mood references; SHA256 `51b0fbb4357e3b644d05956b42a1e8e064e0cbcd61d3d4245cc140f02a21d91f` | Original 2.5D facility illustration; scaled behind title/briefing, cropped for outcome screen. It is illustration, not the collision map or a live gameplay feed. | No third-party download or required credit identified. Owner to confirm rights to supplied visual references before public release. |
| A02-ART | `resources/assets/characters/operative-dossier.png` | Generated with the built-in OpenAI imagegen tool on 2026-10-20; SHA256 `b2acd19d61ad782c2ce27aac5f6ec38925779c404988c837e60daecb34929f0e` | Cropped/resized transparent operative illustration for Human briefing. In-game operative remains a code-drawn top-down silhouette. | No third-party download or required credit identified; owner review pending. |
| A01-CODE | `ui/render/motifs.py`, `ui/render/world.py` | Original project code, P02 integration on 2026-10-20 | Draws tagged floor/wall/glass/cover, actor silhouettes, anchors and lights from validated map/snapshot. No visual pixel controls collision or AI sensing. | Project-authored; no external asset license. |

The above records cover new P02 assets. Later phases must finish the remaining rows and release credits. The generated art does not grant permission to redistribute the owner's reference images themselves; those images are not bundled.

For each imported or original item record: stable ID, runtime path, source/author URL, origin (original/third-party/generated), exact license text or license URL, modification notes, required attribution, download/version date, and reviewer. Store any required redistribution license notices with shipped assets and generate release credits from the register.

Prefer original work or CC0/permissive assets with documented redistribution rights. Free availability alone does not establish a license. Include fonts, audio, icons and bundled dependencies in the review. Original assets need authorship/provenance too. Generated art must have its origin and any reference permissions recorded before release.

Use consistent logical dimensions, actor pivots and atlas naming. Greybox first; collision/vision/sound geometry belongs to explicit map data, never inferred from sprite pixels. Gameplay audio is emitted from committed simulation events; cosmetic ambience cannot alert guards. Test readability and reduced flashing after asset replacement.
