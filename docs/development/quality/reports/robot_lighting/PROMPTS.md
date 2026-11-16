# Robot directional art provenance

2026-11-10. Built-in image_gen, transparent background, reference-based generation.
Reference images: existing project `characters/defenders.png` and `characters/companion.png`.
They supplied character identities/style, rather than being overwritten.

Selected original: `01a14ef6-d91a-7fb3-bc50-12047aa1b20a/exec-5359f369-731c-4aa5-bd95-e72698f394f1.png`.
Preserved RGBA PNG in `src/echo_heist/resources/assets/characters/robots/turnarounds.png`.
SHA256 `355b6f0b5c4a8d03f6d1f72db783a2faff10fa47b20eaefa513bd78f5d25fb27`, 1,469,896 bytes.
The runtime slices the sixteen neutral views, preserves scale per role, and prepares
articulated pose tables. The preserved source atlas is unchanged.
Owner release/licensing review remains part of P08; no third-party downloads were introduced.

## Exact generation prompt (line wrapping only)

```text
Use case: game sprite production. Create ONE transparent RGBA robot turnaround atlas for
ECHO HEIST, a realistic dark sci-fi research-facility top-down cutaway game. Input images
are STYLE/IDENTITY REFERENCES ONLY: first is the existing three defender designs, second
is the existing friendly companion. Rebuild these four robots as consistent rig-ready
full-body NEUTRAL standing turnarounds, preserving their identities, colors and realistic
metal materials. EXACT grid: FOUR equal-width columns, FOUR equal-height rows, sixteen
figures total. Row 1 stocky dark gray Sentinel, circular yellow central eye and yellow
details. Row 2 slim dark gray Tracker, orange visor, two antennae. Row 3 heavy angular
black Interceptor, red rectangular visor. Row 4 small ivory/tan companion with cyan face
eyes and short antenna. Every row shows SAME robot from four directions. Column 1 BACK
facing north/away, column 2 RIGHT PROFILE facing east, column 3 FRONT facing south/toward
viewer, column 4 LEFT PROFILE facing west. Use identical orthographic camera, elevated 35
degrees looking downward, suitable for 2.5D overhead game; NO camera change between cells.
Neutral weight-balanced standing stance, both feet planted level, arms relaxed slightly
away from torso, hands beside hips, clear joint separations and leg separation for
skeletal cutouts. Maintain same character proportions and identical height within each
row. Keep each entire figure including antenna/feet inside its own cell with broad
transparent gutters, horizontally centered, feet on identical baseline within each row.
Crisp detailed premium 3D game render, restrained diffuse overhead studio lighting, NO
ground shadow, NO glow spill outside silhouette, no floor, no background, no contact sheet
labels, no letters, no numbers, no borders, no UI. Transparent background. Prefer square
2048px or larger atlas, perfectly uniform 4 by 4 grid. This will be sliced by code at
exact quarter image coordinates; no overlaps between cells.
```
