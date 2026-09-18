# Visual Bible - The Reluctant Gardener

**Version:** v1

## Medium and rendering

Ink line with flat, matte fills. Visible paper tone beneath. No gradients, no
digital gloss, no drop shadows. Everything should look printed on slightly
cheap paper by an organisation with a small budget.

## Line style

Single weight, confident, with occasional overshoot at corners. Outlines close.
Texture is implied with sparse hatching, never with noise or airbrush.

## Palette

Canonical values live in `style/design-tokens.json`. Warm off-white paper,
near-black ink, one brick-red accent, one sage green, one clay neutral. No
colour outside this set appears anywhere in the book.

## Characters

### subject - The Subject

- **Age / build:** Late forties, average build, slightly rounded shoulders.
- **Face:** Almost never shown. Seen from behind or in three-quarter rear view.
- **Hair:** Short, greying at the sides.
- **Clothing (default):** Fleece gilet over a checked shirt, dark trousers,
  indoor shoes worn outdoors.
- **Clothing (variants allowed):** A waterproof coat, unzipped, in rain scenes.
- **Proportions:** Realistic, seven heads tall. Not cartoon-proportioned.
- **Expression range:** Not applicable. Posture carries the feeling.
- **Never:** Shown smiling at the garden. Shown without the mug. Shown kneeling.

### inspector - The Inspector

- **Represented by:** A clipboard, a pen, and a pair of hands. Never a face.
- **Never:** Given a body, a name badge, or a personality.

## Composition

The subject occupies the lower third, seen from behind, with the garden filling
the frame in front of him. Generous air above. Nothing is centred exactly.

## Illustration edge treatment

Soft irregular edge, as if printed slightly off-register. Never a hard
rectangle. Never a border rule. Never a drop shadow.

## Backgrounds

Flat paper tone with one wash of colour at most. No skies, no weather effects,
no gradients.

## Typography rules

Set deterministically by the renderer.

- Chapter number: display serif, very large, brick red.
- Chapter title: display serif, sentence case.
- Internal headings: display serif, 17pt.
- Body: serif, 10.5pt on 1.44 leading, justified.
- Captions: sans, 8.5pt, centred beneath the artwork.
- Folio: sans, 8.5pt, outer edge.

## Prohibited deviations

- No text of any kind inside generated artwork.
- No page numbers, chapter numbers or headings drawn by an image model.
- No change of the subject's clothing between pages without a spec note.
- No change of line weight or medium between chapters.
- No new palette colours.
- No photorealism, no 3D render, no stock-illustration look.
