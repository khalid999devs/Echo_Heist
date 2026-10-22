# Proposal artwork and provenance

Prepared **2026-10-22** for the 17-slide blue edition. The original game assets remain unchanged. Slide 1 uses the game's original blue cinematic facility, as Khalid requested. Main academic slides retain white backgrounds and cool blue/cyan components.

## Existing game artwork

| Source under `src/echo_heist/resources/assets/` | Use |
| --- | --- |
| `scenes/title-facility.png` | Original blue cinematic cover background |
| `characters/operative-dossier.png` | Human mode illustration |
| `characters/companion.png` | Companion mode / planning poses, cropped natively |
| `characters/defenders.png` | Sentinel, Tracker and Interceptor poses, cropped natively |
| `branding/concepts/core.png` | Story/mission objective emblem |
| `branding/mark.svg` | Original Echo identity mark; native SVG-to-PNG preview conversion for compatibility |

These are illustrations, not proof that every proposed algorithm already runs. Runtime evidence uses the separate four-screenshot set documented in [Suhita's handoff](SUHITA_HANDOFF.md). No screenshot was painted over to invent telemetry.

## New supporting illustration

- Method: **built-in image-generation tool**, not CLI/API fallback.
- Purpose: white-background research-lab concept illustration on slide 3. It is not a game capture or proof of a real-time 3D renderer.
- Saved workspace asset: `output/proposal-deck/build/redesign/assets/white-lab-diorama.png`.
- Pack location: `artwork/presentation/white-lab-diorama.png`.
- The original blue game cover remains on slide 1. This new illustration supplies a quieter academic composition elsewhere.

Exact generation prompt:

> Use case: stylized-concept. Create one widescreen 16:9 editorial illustration for an academic presentation about ECHO HEIST, a futuristic top-down stealth game. A beautifully crafted high-key 3D-rendered cutaway research laboratory on a clean pure white seamless background. Compose a compact detailed lab diorama entirely on the RIGHT HALF of the canvas, with a cyan luminous experimental energy core, glass partitions, white gray research benches, tasteful plants, a dark armored helmeted human infiltrator and one small friendly ivory robot with a cyan face near the lower right. Fine graphite structural details, restrained teal and warm amber task lighting, realistic materials and elegant soft contact shadows. The LEFT HALF is empty pure white negative space for separately editable presentation text; softly fade the edges of the laboratory into white so the image blends with a white slide, no hard rectangular photo boundary. The diorama should occupy rightmost 55 percent, clear right-side silhouette. A polished premium game concept illustration with academic clarity, inviting and slightly playful while still sophisticated. No text, letters, numbers, charts, arrows, emblems, watermarks or UI. This is concept artwork, not a screenshot.

## Editing boundaries

Keep diagrams, tables, labels and copy native and editable. Use proportional image scaling and native crops; keep adjacent sprite poses outside the crop. Retain current/planned/preview labels and the explicit illustrative status of the pruning example. Do not flatten algorithm explanations into generated art.
