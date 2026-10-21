# Interior prop atlas provenance

Date: 2026-10-21. Mode: built-in `image_gen.imagegen`, new generation with `transparent_background=true`; no image edit or CLI fallback. No reference image was supplied to this generation. The owner's concept screenshots informed the art direction; they are not shipped runtime assets.

Adopted unchanged PNG: `src/echo_heist/resources/assets/tiles/interior-props.png`, 1536×1024 RGBA. SHA256: `f00247bd034261457ec6b899666c45203f47b3cf28442676ad89b569e6d88dff`.

Generated source: `/Users/khalid999devs/.codex/generated_images/01a14ef6-d91a-7fb3-bc50-12047aa1b20a/exec-e458eac5-0c52-4c07-8552-c4dd912fb937.png`. The repository copy is the durable runtime asset; that machine-local source path is provenance only.

The renderer reads six 512×512 cells, trims transparent bounds and fits/rotates each sprite within its validated map footprint. Row-major order: engineering desk, planter, laboratory bench, pump, shelf, stair gangway. The existing original atlas is retained for other furnishings. No downloaded third-party asset or new attribution requirement was identified; final owner asset/license review remains pending.

## Exact generation prompt

```text
Use case: stylized-concept. Asset type: runtime furniture sprite atlas for ECHO HEIST, an illustrated 2D top-down industrial sci-fi stealth game. Create ONE transparent PNG atlas with exactly SIX separate isolated props arranged in a clean uniform 3-column by 2-row grid, each prop centered in its own cell with ample empty transparent padding; nothing crosses a cell. No background, no floor, no ground plane, no labels, no text, no borders, no grid lines. Camera is nearly overhead orthographic, slight front face visible for depth, game-ready cutouts, clear detailed materials readable when scaled small. Realistic charcoal steel, brushed silver, muted teal/cyan screens, amber work lights, lush green leaves; subtle tiny contact shadows, restrained light bloom, same lighting on every prop. Row 1 left: a compact two-monitor engineering desk with control keyboard and swivel chair, wide footprint. Row 1 center: a long steel trough planter with two different lush bushy tropical plants, wide footprint. Row 1 right: a laboratory workbench with microscope, glass sample tubes and small analytical machine, wide footprint. Row 2 left: an industrial air handling/pump machine with two metal pipes, valves and amber status light, square footprint. Row 2 center: a freestanding metal storage shelf with boxes, folded supplies, tool cases and small bottles, wide footprint. Row 2 right: a short narrow metal access stair/gangway with four clearly visible treads, industrial side rails and yellow safety edges, seen nearly top down, portrait footprint. These are usable individual game sprites, NOT a room image and NOT a UI mockup. Preserve genuinely transparent empty space everywhere outside the six objects. High quality detailed 3D-rendered game art.
```
