# Production asset and attribution register

Blueprint basis: pp. 2-4, 19. Status: no production assets have been imported or licensed in this planning pass. Required interaction features stay in scope even if optional decorative assets are cut.

## Minimum production set

| ID | Asset group | Minimum content | Status |
| --- | --- | --- | --- |
| A01 | Facility tiles | Five zones, floors, opaque walls, tagged glass, cover, doors, cabinets, upper/lower route cues | TODO |
| A02 | Intruders | Operative and Companion silhouettes; idle/move/hide/tool/strike/core/captured states; shared collision dimensions | TODO |
| A03 | Defenders | Distinct Sentinel, Tracker, Interceptor; move/scan/alert/disabled/stun/grab cues | TODO |
| A04 | Mission anchors | Entry/exit beacon, core plinth idle/pickup/empty, carried-core indication | TODO |
| A05 | Interactions | Intact/shattered glass rack, rolling canister, doors and hiding feedback | TODO |
| A06 | Effects | Echo ghost/trail, EMP ring, capture telegraph, clear suspicion/contact/lockdown states | TODO |
| A07 | Audio | 6-10 gameplay cues, one loopable ambience/music layer, source event mapping and separate volumes | TODO |
| A08 | Interface | Legible font, status icons, mode/Workshop/results panels, non-color cues and critical subtitles | TODO |
| A09 | Narrative | Short opening/contact/theft/win copy and replication-seed epilogue | TODO |
| A10 | Release media | Icon, cover art, representative screenshots and gameplay video | TODO |

The PDF's compressed release checklist mentions four actor silhouettes, while its detailed animation list distinguishes the operative, Companion and three guard types. Follow the detailed readability requirement: five recognizable actor identities, with shared animation bases where practical.

## Per-asset record

For each imported or original item record: stable ID, runtime path, source/author URL, origin (original/third-party/generated), exact license text or license URL, modification notes, required attribution, download/version date, and reviewer. Store any required redistribution license notices with shipped assets and generate release credits from the register.

Prefer original work or CC0/permissive assets with documented redistribution rights. Free availability alone does not establish a license. Include fonts, audio, icons and bundled dependencies in the review. Original assets need authorship/provenance too. Generated art must have its origin and any reference permissions recorded before release.

Use consistent logical dimensions, actor pivots and atlas naming. Greybox first; collision/vision/sound geometry belongs to explicit map data, never inferred from sprite pixels. Gameplay audio is emitted from committed simulation events; cosmetic ambience cannot alert guards. Test readability and reduced flashing after asset replacement.
