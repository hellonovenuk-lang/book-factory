# Visual Bible - The Runner’s Guide to Normal Conversation

> Reconstructed from the preserved 80-page PDF and its embedded illustrations.
> The original editable visual bible and approval history were not recovered.
> Review this text and the proposed references before `bookfactory lock visual`.

**Version:** v1 (bump on every lock)

## Medium and rendering

Fine pen-and-ink editorial drawing with restrained pencil-like grey shading.
The interior is monochrome on a warm off-white page. Characters are realistically
proportioned with gentle caricature in posture and expression, not flat icons.
The cover retains this line drawing and adds bold flat colour.

## Line style

Thin, variable dark outlines and small crosshatched or softly shaded areas for
hair, fabric folds and shadow. Faces retain particular noses, eyebrows and hair
silhouettes. Shoes, hands and watch are detailed enough to carry the social
joke. Avoid uniform vector strokes, heavy contour lines and digital gloss.

## Palette

The canonical values live in `style/design-tokens.json` and are what the
deterministic renderer uses. Describe intent here.

The interior uses ink `#1c1a17`, softer ink `#4a453e` and warm paper
`#fbf8f1` with restrained greys. Design-token accents are brick `#8c3b2e`,
soft tan `#e6d7c3` and rule `#c9bda8`; the preserved PDF often renders
chapter numerals grey. **Cover-only palette:** vivid coral `#ed5a3a`, bright
yellow `#f6dc45`, deep blue `#2445a2`, near-black and warm paper. Use large
flat areas and clear contrast for gift-book impact at small size. This cover
exception does not authorise recolouring preserved interior art.

## Characters

### alex — Alex, recurring runner

- **Build and face:** Adult, roughly thirty to forty, slim athletic build, narrow oval face, strong brows, lively eyes and a quick self-satisfied smile.
- **Hair:** Thick, short, dark curly hair lifted high at the front. Preserve that silhouette in every scene.
- **Clothing:** Light long-sleeved running top, dark mid-thigh shorts and ordinary running shoes when dressed to run. Some social scenes use dark trousers with the light top.
- **Accessory and expression:** Small fitness watch without recognisable branding; animated demonstration, delighted digression, momentary restraint and effortful listening.
- **Never:** Straight hair, beard, elite athlete physique, different facial outline, branded kit or readable race bib lettering generated in art.

### sam — Sam, partner

- **Build, face and hair:** Adult contemporary of Alex, average build, dark chin-length bob, defined brows and alert eyes.
- **Clothing and expression:** Simple light top with dark trousers or skirt; patient observation, mild weariness and relieved attention.
- **Never:** Generic grinning spectator, different haircut or cruel caricature.

### pat — Pat, colleague/acquaintance

- **Face and hair:** Adult, neat dark hair and dark moustache in the recovered conversation scenes.
- **Clothing and expression:** Light collared shirt and darker trousers; polite interest, uncertainty and an attempt to get a word in.
- **Never:** Dr Hughes’s grey hair, spectacles or clinician coat.

### dr-hughes — Dr Hughes, Service clinician

- **Face and hair:** Older adult, short greying hair, spectacles and a clean-shaven composed face.
- **Clothing and expression:** Light clinician’s coat over shirt and tie, clipboard or papers when needed; deadpan attention and measured intervention.
- **Never:** Medical branding, a new face or broad cartoon exaggeration.

## Composition

Interior scenes are generally wide, with whole figures or upper bodies, a few
contextual objects and ample white space. Alex is often the animated speaker
beside a more reserved listener. Gestures and paired sightlines carry one joke.
The front cover uses a larger social scene: Alex begins explaining a run to
someone who asked an ordinary question. Leave open space for separately
typeset title and author; do not embed those words in the drawing.

## Illustration edge treatment

Interior art tapers into pale background or sits on a clean white rectangle.
No drop shadow, fake aged-paper edge or soft digital mask. Cover figures may
sit on a crisp flat-colour field while preserving their ink edges.

## Backgrounds

Suggest a café table, office kettle, kitchen or living room with only the
props needed to read the joke: cup, chair, watch or shoes. No fitness-app
screens, race logos, route screenshots, charts or branded equipment.

## Typography rules

For a print book, also record cover composition, colour and actual artwork
placement. Cover art must match locked character and editorial references and
contain no lettering, logos or copied app interfaces. The full-wrap layout
sets title, author and back copy as real type. Include spine lettering only
when KDP's page-count and safe-margin rules allow legible type. Check the front
at an Amazon-size thumbnail.

**Cover direction:** A vivid, bold full-colour gift paperback on white paper
with matte finish. Make the title immediately legible and the social premise
obvious even as a thumbnail. Place a text-free editorial illustration at no
more than its native 300-DPI print size; the current planned placement is
3.4 × 5.1 inches and needs at least 1020 × 1530 native pixels. Preserve its
original generated file. Typeset title, Kieran Smith, and short back copy as
real selectable type. Reserve the KDP barcode area. At the recovered 80-page
count, the white-paper spine is 0.18016 inch wide; two 0.0625-inch fold
clearances leave about 0.055 inch, less than a legible 7-point letter. Use a
continuous colour spine without lettering unless final page count and KDP
preflight prove safe type will fit.

Set deterministically by the renderer; recorded here so art direction and
layout agree.

- Chapter number: display face, very large, accent colour.
- Chapter title: display face, sentence case.
- Internal headings: bold serif, sentence case and generous surrounding air.
- Body: readable book serif in natural paragraphs.
- Captions: small understated type set beneath the artwork, never drawn into it.
- Folio (page number): small grey number at the outer lower margin.

## Prohibited deviations

These are the failures that ruined the previous project. They are not style
preferences, they are rules.

- No text of any kind inside generated artwork.
- No page numbers, chapter numbers or headings drawn by an image model.
- No change of character clothing between pages without a spec note.
- No change of line weight or rendering medium between chapters.
- No new interior palette colours. Cover-only colours are specified above.
- No photorealism, no 3D render, no stock-illustration look.
