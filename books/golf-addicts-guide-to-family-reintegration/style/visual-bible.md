# Visual Bible - The Golf Addict's Guide to Family Reintegration

> Locked by `bookfactory lock visual`. Every illustration task generated after
> the lock points at the approved references listed in
> `style/reference-set.json`. A fresh agent with no conversation history must be
> able to produce on-style artwork from this file plus those references.

**Version:** v1 (bump on every lock)

## Medium and rendering

Classic British editorial caricature: fine pen-and-ink drawing with soft grey
wash shading, on plain warm off-white paper. The interior is black and white
only: black ink and greys, no colour at all. Figures are realistically
proportioned with gentle caricature in the face and posture (a slightly
larger nose, expressive brows, a belly that is there but not grotesque),
in the tradition of newspaper and magazine cartoon illustration. It sits
beside our *Runner's Guide to Normal Conversation* as a companion: the same
fine ink and grey register, with a touch more caricature and warmth. The
cover alone adds muted flat colour (see Palette).

## Line style

Thin, confident black ink outlines with some variation in weight (heavier
under chins, in folds and at the ground line, lighter on faces). Hair, fabric
folds and shadows are shaded with soft grey wash and a little light
hatching. Outlines close around figures. Faces keep their particular noses,
brows and silhouettes from picture to picture. Hands and the objects that
carry the joke (a golf club, an umbrella, barbecue tongs, a French stick) are
drawn clearly enough to read at a glance. No uniform vector strokes, no heavy
comic-book outlines, no digital gloss, no airbrushed gradients.

## Palette

The canonical values live in `style/design-tokens.json` and are what the
deterministic renderer uses. Describe intent here.

**Interior:** black ink `#1c1a17`, softer ink `#4a453e` and warm paper
`#fbf8f1`, with a range of neutral greys for the wash. Nothing else. The
renderer's accent tokens print as greys in the black and white interior and
are used for typeset rules and numerals only, never inside artwork.

**Cover only:** muted flat colour over the same ink drawing: fairway green
`#5b7a4a`, sand `#d9c7a0`, cream `#f4ecd8`, soft navy `#2f3e56` and a
brick red `#8c3b2e` for small accents. Large flat areas with clear contrast,
so the scene reads at Amazon thumbnail size. These colours never appear in
the interior.

## Characters

### dave - Dave, the golfer under reintegration

- **Age / build:** Late thirties. Broad, solid, the start of a dad bod (a small belly over his belt), sturdy legs. About five foot ten.
- **Face:** Round, cheerful, ruddy face (shown with light grey wash on the cheeks and nose), a large rounded nose, thick dark eyebrows, small bright eyes, faint laughter lines, a hint of stubble, a wide confident grin. He looks like a geezer: pleased with himself and likeable.
- **Hair:** Short dark-brown hair, cropped at the sides and back, visible under the cap. No grey.
- **Clothing (default):** A plain light-grey golf cap with a curved peak, no logo, always on his head. A plain mid-grey quarter-zip pullover over a white collared polo shirt, collar out. Light tan chino trousers. One white golf glove poking out of his back pocket, always.
- **Clothing (variants allowed):** Outdoors on the course: golf shoes and a golf bag on his shoulder. Indoors: plain slip-on shoes. Formal occasions (wedding): a dark suit and tie, still with the cap on. Holiday: shorts and a short-sleeved polo, cap still on. Graduation: a gown and mortarboard worn over the cap. Every variant needs a spec note.
- **Proportions:** Head slightly large for the body, as caricature; hands big and expressive.
- **Expression range:** Delighted mid-story, mid-swing concentration, innocent surprise ("what?"), mock outrage about the 7th, sheepish, and once or twice genuinely touched.
- **Never:** Without the cap (except where a spec says so), older than about forty, grey hair, a full beard or moustache, glasses, a slim or athletic build, a mean or drunk look, branded clothing, logos on the cap, shirt, bag or clubs.

### sue - Sue, his wife and case sponsor

- **Age / build:** Late thirties. Slim, small (about five foot four), quick and capable, slightly frazzled.
- **Face:** Oval face, fine features, a dry, knowing expression: one eyebrow slightly raised, mouth pressed in patient restraint. Kind, tired eyes.
- **Hair:** Shoulder-length dark hair twisted up in a claw clip, with loose strands falling out.
- **Clothing (default):** A long soft cardigan over a plain T-shirt, dark jeans, trainers. Often holding a cold mug of tea, a child, a school bag, or all three.
- **Clothing (variants allowed):** A smart dress and jacket for the wedding; a sun hat and light summer clothes on holiday.
- **Proportions:** Realistic, slightly less caricatured than Dave.
- **Expression range:** Dry patience, arms folded, raised eyebrow, tired amusement, the occasional warm smile at him when he isn't looking.
- **Never:** Shrewish, shouting, cartoonish nagging, curlers or rolling pin clichés, a different haircut.

### alfie - Alfie, their son

- **Look:** Six, small and wiry, tousled light hair, gap-toothed grin, striped T-shirt and shorts or school jumper. Competitive and cheeky, copies his dad's stance.
- **Never:** Older than six, a different hair colour, a football club badge or any logo.

### poppy - Poppy, their daughter

- **Look:** Four, round-faced, hair in two short bunches, dungarees or a simple dress, often on Sue's hip or holding her hand. Wide-eyed and blunt.
- **Never:** A baby, older than four, a different hairstyle.

### biscuit - Biscuit, the family dog

- **Look:** A medium-sized scruffy terrier cross, light coat with a darker patch over one eye, one ear up and one ear flopped over, stubby wagging tail. Mischievous.
- **Never:** A different breed, size or markings.

### keith - Keith, from Dave's four-ball (optional; only where a spec names him)

- **Look:** Sixties, tall and thin, weathered face, thin grey moustache, a golf visor, loudly patterned golf trousers (checks or diamonds, no logos), polo shirt.
- **Never:** Confused with Dave; never wears a cap.

## Composition

Interior pictures are wide scenes (about 3:2 landscape), whole figures or
upper bodies, a few props that carry the joke, and generous white space
around them, like the chapter openers in the *Runner's Guide*. Dave is the
animated one; the family react. One clear joke per picture, readable from
the gestures and sightlines alone. Chapter openers sit in the lower half of a
page under typeset chapter headings, so leave calm space at the top of the
picture.

The front cover is a larger scene: Dave at the Sunday roast table, mid-swing
with a French stick, while Sue, Alfie and Poppy stare at him and Biscuit eyes
the roast. Leave clear open space in the upper part for the
separately typeset title and author. Never draw those words.

## Illustration edge treatment

Interior art sits on plain white and fades out softly into the paper at its
edges, or is contained in a clean white rectangle. No hard box outline, no
drop shadow, no fake aged-paper edge, no vignette blur. Cover figures sit on
a crisp flat-colour field and keep their ink edges.

## Backgrounds

Only what the joke needs: a doorway, a kitchen table, a garage wall of golf
gear, a beach with a windbreak, a church step. Suggest the setting with a few
ink lines and grey wash, then let it fade to paper. British homes and places:
terraced or semi-detached houses, a Sunday roast, a kettle, a Cornish beach.
No readable signs, no TV screens showing anything readable, no logos, no
brands, no real golf courses or clubhouses.

## Typography rules

For a print book, also record cover composition, colour and actual artwork
placement. Cover art must match locked character and editorial references and
contain no lettering, logos or copied app interfaces. The full-wrap layout
sets title, author and back copy as real type. Include spine lettering only
when KDP's page-count and safe-margin rules allow legible type. Check the front
at an Amazon-size thumbnail.

**Cover direction:** A bold but muted full-colour gift paperback, white
paper, matte finish. The title must read clearly at thumbnail size, and the
Sunday roast scene must make the premise obvious. The text-free cover
illustration is placed at no more than its native 300-DPI size. Title,
author (Kieran Smith) and short back copy are real selectable type. Reserve
the KDP barcode area. Spine lettering only if the final page count gives a
spine wide enough for legible type after KDP's fold clearances; otherwise a
plain colour spine.

Set deterministically by the renderer; recorded here so art direction and
layout agree.

- Chapter number: display face, very large, grey.
- Chapter title: display face, sentence case ("Stage One: Arrival").
- Internal headings: bold serif, sentence case, generous air above.
- Body: readable book serif in natural paragraphs.
- Captions: small understated type beneath the artwork, never drawn into it.
- Activity panels: the panel number and kind ("No. 01 · Assessment") set as small spaced capitals; tick boxes, score boxes, write-in lines and tables drawn by the renderer as real rules.
- Sue's case notes: set apart as an indented note with a thin rule, in the body face.
- Folio (page number): small grey number at the outer lower margin.

## Prohibited deviations

These are the failures that ruined the previous project. They are not style
preferences, they are rules.

- No text of any kind inside generated artwork: no words, letters, numbers, signs, scorecards with writing, or signatures.
- No page numbers, chapter numbers or headings drawn by an image model.
- No brand logos anywhere, including on caps, shirts, golf bags, clubs, balls and umbrellas.
- No change of character clothing between pages without a spec note.
- No change of line weight or rendering medium between chapters.
- No colour in interior artwork. Cover-only colours are specified above.
- No photorealism, no 3D render, no stock-illustration look.
