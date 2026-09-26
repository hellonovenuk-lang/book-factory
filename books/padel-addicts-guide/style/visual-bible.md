# Visual Bible - The Padel Addict's Guide to Talking About Anything Else

> Locked by `bookfactory lock visual`. Every illustration task generated after
> the lock points at the approved references listed in
> `style/reference-set.json`. A fresh agent with no conversation history must be
> able to produce on-style artwork from this file plus those references.

**Version:** v1 (bump on every lock)

## Medium and rendering

TODO - e.g. "Ink line with flat gouache-style fills, visible paper grain, no
gradients, no digital gloss."

## Line style

TODO - weight, consistency, whether outlines close, how texture is implied.

## Palette

The canonical values live in `style/design-tokens.json` and are what the
deterministic renderer uses. Describe intent here.

TODO

## Characters

### TODO-character-id - Name

- **Age / build:** TODO
- **Face:** TODO
- **Hair:** TODO
- **Clothing (default):** TODO
- **Clothing (variants allowed):** TODO
- **Proportions:** TODO
- **Expression range:** TODO
- **Never:** TODO (the things that drifted last time)

## Composition

TODO - typical crop, where the character sits in frame, how much air.

## Illustration edge treatment

TODO - e.g. "vignette with soft torn edge; never a hard rectangle; never a drop
shadow."

## Backgrounds

TODO

## Typography rules

For a print book, also record cover composition, colour and actual artwork
placement. Cover art must match locked character and editorial references and
contain no lettering, logos or copied app interfaces. The full-wrap layout
sets title, author and back copy as real type. Include spine lettering only
when KDP's page-count and safe-margin rules allow legible type. Check the front
at an Amazon-size thumbnail.

Set deterministically by the renderer; recorded here so art direction and
layout agree.

- Chapter number: display face, very large, accent colour.
- Chapter title: display face, sentence case.
- Internal headings: TODO
- Body: TODO
- Captions: TODO
- Folio (page number): TODO

## Prohibited deviations

These are the failures that ruined the previous project. They are not style
preferences, they are rules.

- No text of any kind inside generated artwork.
- No page numbers, chapter numbers or headings drawn by an image model.
- No change of character clothing between pages without a spec note.
- No change of line weight or rendering medium between chapters.
- No new palette colours.
- No photorealism, no 3D render, no stock-illustration look.
