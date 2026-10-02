# Visual Bible - The Newly Retired Man's Guide to Being Home All Day

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
larger nose, expressive brows, a set jaw), in the tradition of newspaper and
magazine cartoon illustration. It is a companion to our *Golf Addict's
Guide* and *Padel Addict's Guide*: the same fine ink and grey register, set
almost entirely in and around a comfortable British family home (kitchen,
garden, shed, loft, supermarket, nursery gate).

## Line style

Thin, confident black ink outlines with some variation in weight (heavier
under chins, in folds and at the ground line, lighter on faces). Hair, fabric
folds and shadows are shaded with soft grey wash and a little light
hatching. Outlines close around figures. Faces keep their particular noses,
brows and silhouettes from picture to picture. Hands and the objects that
carry the joke (a tape measure, a clipboard, a colander, a mug of tea, a
trolley, a spirit level, a plank) are drawn clearly enough to read at a
glance. No uniform vector strokes, no heavy comic-book outlines, no digital
gloss, no airbrushed gradients.

## Palette

The canonical values live in `style/design-tokens.json` and are what the
deterministic renderer uses. Describe intent here.

**Interior:** black ink `#1c1a17`, softer ink `#4a453e` and warm paper
`#fbf8f1`, with a range of neutral greys for the wash. Nothing else. The
renderer's accent tokens are set to greys (`#5f5a53`, `#e4e1dc`, rule
`#c4c0ba`) for the black and white interior and are used for typeset rules
and numerals only, never inside artwork.

**Cover:** a picture cover, decided at intake. The cover artwork may use
soft, muted full colour (warm kitchen and garden tones: cream, sage green,
soft brick, faded denim blue, honey wood), drawn in the same fine ink line
with watercolour-style washes, so the characters match the interior
exactly. No colour appears anywhere in the interior.

## Characters

### graham - Graham, the newly retired man

- **Age / build:** 66. Trim and fit, medium height (about five foot ten), straight-backed, brisk and purposeful. Looks like a man with a plan for the afternoon. Never frail.
- **Face:** A square, clean-shaven, lightly lined face with a strong slightly large nose (as caricature), a firm jaw, alert eyes and bushy, very expressive grey eyebrows. Usually mid-explanation or concentrating hard on something small.
- **Hair:** Short, neat, thick grey-white hair, side-parted, slightly receding at the temples. Never bald, never long.
- **Glasses:** Plain rectangular reading glasses with thin dark frames, pushed up on his forehead in every picture, except when he is reading or comparing something closely, when they are pulled down onto his nose.
- **Tape measure:** A small chunky retractable tape measure clipped to his belt on his right hip, in every picture, plain with no writing.
- **Clothing (default):** A zip-up fleece gilet (sleeveless) in a mid-grey, zipped two-thirds up, plain, no logo. Under it a pale checked or plain collared shirt with the sleeves rolled once. Belted beige chinos. Brown suede shoes or plain brown lace-ups.
- **Clothing (variants allowed):** Dawn and bedroom: the same shirt and gilet already on, fully dressed. Garden and shed: the same gilet with old work trousers and a pencil behind his ear. Treaty and final stage: the same gilet, relaxed. Every variant needs a spec note.
- **Proportions:** Head slightly large for the body, as caricature; hands expressive and busy, often holding a tool or gesturing.
- **Expression range:** Brisk enthusiasm, earnest concentration, pleased with a system, innocent puzzlement ("what?"), sheepish, and once or twice quietly content.
- **Never:** Frail, stooped, a walking stick, a hearing aid, a cardigan or slippers, a beard or moustache, bald, glasses on a cord, a flat cap, asleep in an armchair, logos or writing on anything he wears or carries.

### sue - Sue, Head of Household Operations

- **Age / build:** 63. Average height, slim, upright and capable, moves calmly. Very much in charge.
- **Face:** Oval face, fine features, kind lively eyes with a dry, knowing look: one eyebrow slightly raised, the corner of her mouth turned up in patient amusement.
- **Hair:** A neat chin-length silver-grey bob with a soft side fringe.
- **Clothing (default):** A soft striped Breton-style top or a plain jumper, dark jeans or slim trousers, simple flat shoes, small stud earrings. Often holding a mug of tea, the colander, a basket or a newspaper.
- **Clothing (variants allowed):** A dressing gown over pyjamas in the early morning; a light gardening jacket in the garden; a smart blouse at the Treaty table.
- **Proportions:** Realistic, slightly less caricatured than Graham.
- **Expression range:** Dry patience, raised eyebrow, amused restraint, arms folded, a warm private smile at him when he isn't looking.
- **Never:** Shrewish, shouting, nagging, rolling-pin clichés, frail, a different hair colour or cut, an apron as a "housewife" joke.

### ellie - Ellie, their granddaughter

- **Look:** Three. Round face, big determined eyes, curly light-brown hair in a single high pony tail with a bobble, a plain dress or dungarees with tights and small trainers. Always purposeful, often leading Graham by the hand or giving instructions. Carries a soft toy rabbit (plain, floppy-eared).
- **Never:** A baby, older than about four, a different hairstyle, any character print, logo or slogan on her clothes.

### biscuit - Biscuit, the family Labrador

- **Look:** An eleven-year-old yellow Labrador, solid and calm, with a greying muzzle, soft floppy ears and wise, slightly weary eyes. A plain collar with no tag writing. Usually lying in his basket, sitting watching Graham, or waiting by a door. Always reacting, never doing tricks.
- **Never:** A puppy, a different breed or colour, a cartoon anthropomorphic face, wearing clothes.

### Extras (only where a spec names them)

- **Other shoppers and parents:** ordinary British people of mixed ages, plain clothes, no writing on anything.
- **Ken next door:** late sixties, round and genial, a jumper, holding hedge shears.
- **Darren at the tip:** forties, stocky, in a plain high-visibility jacket with no writing.

## Composition

Interior pictures are wide scenes (about 3:2 landscape), whole figures or
upper bodies, a few props that carry the joke, and generous white space
around them, like the chapter openers in the *Golf Addict's Guide*. Graham
is the busy one; Sue, Ellie and Biscuit react. One clear joke per picture,
readable from gestures and sightlines alone. Chapter openers sit in the
lower half of a page under typeset chapter headings, so leave calm space at
the top of the picture.

## Illustration edge treatment

Interior art sits on plain white and fades out softly into the paper at its
edges, or is contained in a clean white rectangle. No hard box outline, no
drop shadow, no fake aged-paper edge, no vignette blur.

## Backgrounds

Only what the joke needs: a family kitchen with wall cupboards and a
kettle, a bedroom window at dawn, a half-built garden shed, a supermarket
aisle, a nursery gate, a sunny garden table. Suggest the setting with a few
ink lines and grey wash, then let it fade to paper. British homes and
places: a comfortable 1970s or 1980s semi-detached house, a lawn with a
fence, a family car on the drive. Packaging, tins, jars, papers, plans,
clipboards, calendars and screens show only plain shapes or blank lines,
never readable words, numbers, prices or logos. No readable signs, no shop
names, no brands.

## Typography rules

For a print book, also record cover composition, colour and actual artwork
placement. Cover art must match locked character and editorial references and
contain no lettering, logos or copied app interfaces. The full-wrap layout
sets title, author and back copy as real type. Include spine lettering only
when KDP's page-count and safe-margin rules allow legible type. Check the front
at an Amazon-size thumbnail.

**Cover direction:** a picture cover, decided at intake. One warm family
scene on the front panel (Graham at home doing something earnest and
unnecessary, with Sue and Biscuit reacting), in the same ink line with muted
colour washes, with a plain empty band of paper across the top for the
title. The title "The Newly Retired Man's Guide to Being Home All Day" is
set large and bold as real type over that band, so it reads clearly at
Amazon thumbnail size, with the subtitle, the author (Kieran Smith) and the
back copy also real selectable type. Matte finish. Reserve the KDP barcode
area. Spine lettering only if the final page count gives a spine wide enough
for legible type after KDP's fold clearances; otherwise a plain spine.

Set deterministically by the renderer; recorded here so art direction and
layout agree.

- Chapter number: display face, very large, grey.
- Chapter title: display face, sentence case ("Stage One: Welcome to the Household").
- Internal headings: bold serif, sentence case, generous air above.
- Body: readable book serif in natural paragraphs.
- Captions: small understated type beneath the artwork, never drawn into it.
- Activity panels: the panel number and kind ("No. 01 · Assessment") set as small spaced capitals; tick boxes, score boxes, write-in lines and tables drawn by the renderer as real rules.
- Notes from Household Operations (Sue): set apart as an indented note with a thin rule, in the body face.
- Folio (page number): small grey number at the outer lower margin.

## Prohibited deviations

These are the failures that ruined the previous project. They are not style
preferences, they are rules.

- No text of any kind inside generated artwork: no words, letters, numbers, signs, labels on tins or jars, writing on plans or clipboards, readable screens, clock or watch digits, or signatures.
- No page numbers, chapter numbers or headings drawn by an image model.
- No brand logos anywhere, including on clothes, tools, tins, trolleys, cars and vans.
- Graham always has the reading glasses on his forehead (or on his nose when reading), the grey fleece gilet and the tape measure on his belt.
- Nothing that reads as illness, frailty or old age: no walking sticks, hospital settings, pill boxes or armchair dozing.
- No change of character clothing between pages without a spec note.
- No change of line weight or rendering medium between chapters.
- No colour in interior artwork.
- No photorealism, no 3D render, no stock-illustration look.
