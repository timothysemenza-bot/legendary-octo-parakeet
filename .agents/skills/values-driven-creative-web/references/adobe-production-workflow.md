# Adobe Production Workflow

## Outputs to Produce

1. Photography and stills
- Tool: Photoshop
- Output: web-optimized `.jpg` / `.webp`
- Method: one color-grade preset, consistent crop ratios

2. Iconography and brand shapes
- Tool: Illustrator
- Output: `icons.svg` sprite or individual SVGs
- Method: 24x24 grid, stroke consistency, single color token

3. Motion loops
- Tool: After Effects or Premiere
- Output: muted, loop-friendly `.mp4` (8-12s)
- Method: low-motion camera movement, no abrupt cuts

4. UI micro-animation
- Tool: After Effects + Bodymovin
- Output: Lottie `.json`
- Method: short loops, low complexity, svg renderer-safe

## Technical Targets

- Hero videos: <= 4 MB each
- Lottie JSON: <= 800 KB each
- Card images: 1600px wide source, export quality 72-82%
- Portraits: square crop, 600x600+

## Naming Convention

Use exact destination names from site implementation, e.g.:
- `hero-loop.mp4`
- `portal-loop.mp4`
- `learning-pulse.json`
- `network-flow.json`
- `portal-engagement.json`

## UX Guardrails

- Motion should support comprehension, not distract.
- Visuals must match audience values and modest professionalism.
- Avoid generic stock that conflicts with organizational identity.
