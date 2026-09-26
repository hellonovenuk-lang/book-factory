# Visual Bible - The Padel Addict's Guide to Talking About Anything Else

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
larger nose, expressive brows, a confident chin), in the tradition of
newspaper and magazine cartoon illustration. It is a companion to our *Golf
Addict's Guide* and *Runner's Guide*: the same fine ink and grey register,
with a younger cast and more modern settings (an open-plan office, a
nursery, a family car, a padel club seen from outside).

## Line style

Thin, confident black ink outlines with some variation in weight (heavier
under chins, in folds and at the ground line, lighter on faces). Hair, fabric
folds and shadows are shaded with soft grey wash and a little light
hatching. Outlines close around figures. Faces keep their particular noses,
brows and silhouettes from picture to picture. Hands and the objects that
carry the joke (a padel racket, a phone, a smartwatch, a racket bag, a
buggy) are drawn clearly enough to read at a glance. A padel racket is
always drawn correctly: a solid, perforated paddle-shaped face with a short
handle and no strings, so it never reads as a tennis racket. No uniform
vector strokes, no heavy comic-book outlines, no digital gloss, no
airbrushed gradients.

## Palette

The canonical values live in `style/design-tokens.json` and are what the
deterministic renderer uses. Describe intent here.

**Interior:** black ink `#1c1a17`, softer ink `#4a453e` and warm paper
`#fbf8f1`, with a range of neutral greys for the wash. Nothing else. The
renderer's accent tokens are set to greys (`#5f5a53`, `#e4e1dc`, rule
`#c4c0ba`) for the black and white interior and are used for typeset rules
and numerals only, never inside artwork.

**Cover:** big lettering only, decided at intake. There is no cover artwork,
so there are no cover-only artwork colours. The cover's type colours are set
in `cover/cover.json`.

## Characters

### josh - Josh, the padel addict

- **Age / build:** 31. Slim and fit in a gym-and-padel way, straight-backed, about five foot eleven. Carries himself like a man who has just won a point.
- **Face:** Narrow, pleased-with-himself face with a strong straight nose (slightly large, as caricature), bright eager eyes, animated eyebrows, and a wide confident grin with good teeth. Always looks like he is about to tell you something.
- **Hair:** Short dark-brown hair, faded short at the sides, a little longer and neatly textured on top, visible under the cap. No grey.
- **Beard:** A short, neat, well-trimmed dark beard along the jaw and chin with a matching moustache. Never stubble, never a long beard.
- **Smartwatch:** A chunky black sports smartwatch on his left wrist, in every picture, with a plain dark screen or a simple abstract graph shape, never readable numbers or letters.
- **Clothing (default):** A plain dark-grey sports cap with a curved peak, no logo, worn forwards. A fitted light-grey half-zip performance quarter-zip with a small plain padel-racket silhouette stitched on the left chest (a simple shape, no letters). Slim dark chinos. White trainers.
- **Clothing (variants allowed):** Office: the same quarter-zip over a shirt collar, or an open-necked shirt with the cap in his hand. Home at dawn: pyjama bottoms with the quarter-zip. Holiday: shorts, a plain T-shirt, sunglasses, cap still on. Sign-off only: a smart shirt and no cap. Every variant needs a spec note.
- **Proportions:** Head slightly large for the body, as caricature; hands expressive, often mid-gesture as if demonstrating a shot.
- **Expression range:** Evangelical enthusiasm mid-explanation, delighted at his phone, innocent surprise ("what?"), sheepish, trying hard to listen, and once or twice genuinely touched.
- **Never:** Older than about 35, grey hair, clean-shaven, a full or bushy beard, glasses, a dad bod, a mean or smug-villain look, a tennis racket with strings instead of a padel racket, readable writing on the watch, logos or brand names on the cap, clothes, racket, bag or shoes.

### lauren - Lauren, his wife (stakeholder: Home)

- **Age / build:** Early thirties. Average height, slim, capable and a little tired.
- **Face:** Oval face, fine features, dark eyes with a dry, knowing look: one eyebrow slightly raised, mouth pressed in patient restraint. Kind underneath.
- **Hair:** Mid-length straight light-brown hair, usually in a loose low ponytail with a few strands falling out.
- **Clothing (default):** A soft oversized jumper over leggings or jeans, trainers. Often holding Alfie on her hip, a mug, a towel, a notepad, or all of them.
- **Clothing (variants allowed):** A smart blouse and trousers for work or a dinner party; a sun hat and summer dress on holiday.
- **Proportions:** Realistic, slightly less caricatured than Josh.
- **Expression range:** Dry patience, arms folded, raised eyebrow, tired amusement, the occasional warm smile at him when he isn't looking.
- **Never:** Shrewish, shouting, cartoon nagging, rolling-pin clichés, a different hair colour or cut.

### mia - Mia, their daughter

- **Look:** Four. Round face, big serious eyes, dark hair in two short bunches, dungarees or a simple dress with trainers. Blunt, observant, often unimpressed.
- **Never:** A baby, older than about five, a different hairstyle, any logo or character print on her clothes.

### alfie - Alfie, their son

- **Look:** One. A chubby baby with wispy fair hair and a round face, in a plain babygro or a vest and soft trousers. Usually on Lauren's hip, in a high chair, in the bath or in a cot. Cannot walk yet.
- **Never:** Walking or standing unsupported, older than about eighteen months, any printed slogan or logo on his clothes.

### priya - Priya, Josh's boss (stakeholder: Work)

- **Look:** Late forties, British Indian, tall, upright and composed, with sharp intelligent eyes and a dry, unimpressed half-smile. Glossy dark shoulder-length hair with a few strands of grey. A tailored dark blazer over a plain top, smart trousers, simple earrings. When a tennis racket appears with her it is a strung tennis racket in a plain case.
- **Never:** Flustered, cartoonish, dressed casually in the office, holding a padel racket, any logo.

### graham - Graham, Lauren's dad (optional; only where a spec names him)

- **Look:** Seventy-one. Tall and thin, slightly stooped, a kind weathered face, neat white hair, reading glasses on a cord, a cardigan and a checked shirt. Uses a plain wooden walking stick since his hip operation.
- **Never:** Holding a racket willingly, sporty clothes.

### Extras (only where a spec names them)

- **The neighbour:** an older man in a gardening jumper with a watering can.
- **Gary, the heating engineer:** fifties, stocky, in plain navy work clothes. His van is plain, with no writing.
- **Colleagues:** a mixed, younger office team in smart-casual clothes, with laptops. No lanyards with writing.

## Composition

Interior pictures are wide scenes (about 3:2 landscape), whole figures or
upper bodies, a few props that carry the joke, and generous white space
around them, like the chapter openers in the *Golf Addict's Guide*. Josh is
the animated one; family and colleagues react. One clear joke per picture,
readable from gestures and sightlines alone. Chapter openers sit in the
lower half of a page under typeset chapter headings, so leave calm space at
the top of the picture.

## Illustration edge treatment

Interior art sits on plain white and fades out softly into the paper at its
edges, or is contained in a clean white rectangle. No hard box outline, no
drop shadow, no fake aged-paper edge, no vignette blur.

## Backgrounds

Only what the joke needs: a kitchen table, a bathroom with a bath, a
dawn-dark kitchen, an open-plan meeting room with a screen, a garden fence,
a resort pool with padel courts behind a fence, a family breakfast table.
Suggest the setting with a few ink lines and grey wash, then let it fade to
paper. British homes and places: a modern terraced or semi-detached house, a
family car, a nursery. Padel courts are shown as glass-walled boxes with a
low net, never a tennis court. Screens (phones, laptops, the meeting-room
screen, the smartwatch) show only plain light or abstract shapes, never
readable words, numbers or app interfaces. No readable signs, no logos, no
brands, no real padel clubs or players.

## Typography rules

For a print book, also record cover composition, colour and actual artwork
placement. Cover art must match locked character and editorial references and
contain no lettering, logos or copied app interfaces. The full-wrap layout
sets title, author and back copy as real type. Include spine lettering only
when KDP's page-count and safe-margin rules allow legible type. Check the front
at an Amazon-size thumbnail.

**Cover direction:** big lettering, decided at intake: a text-only full-wrap
paperback with no artwork. The title "The Padel Addict's Guide to Talking
About Anything Else" is set large and bold as real type, so it reads clearly
at Amazon thumbnail size, with the author (Kieran Smith) and short back copy
also real selectable type. White paper, matte finish. Reserve the KDP
barcode area. Spine lettering only if the final page count gives a spine
wide enough for legible type after KDP's fold clearances; otherwise a plain
spine.

Set deterministically by the renderer; recorded here so art direction and
layout agree.

- Chapter number: display face, very large, grey.
- Chapter title: display face, sentence case ("Phase One: Scoping").
- Internal headings: bold serif, sentence case, generous air above.
- Body: readable book serif in natural paragraphs.
- Captions: small understated type beneath the artwork, never drawn into it.
- Activity panels: the panel number and kind ("No. 01 · Assessment") set as small spaced capitals; tick boxes, score boxes, write-in lines and tables drawn by the renderer as real rules.
- Stakeholder feedback (Lauren and Priya): set apart as an indented note with a thin rule, in the body face.
- Folio (page number): small grey number at the outer lower margin.

## Prohibited deviations

These are the failures that ruined the previous project. They are not style
preferences, they are rules.

- No text of any kind inside generated artwork: no words, letters, numbers, signs, screens with writing, watch faces with digits, or signatures.
- No page numbers, chapter numbers or headings drawn by an image model.
- No brand logos anywhere, including on caps, clothes, rackets, balls, bags, shoes, cars and vans.
- A padel racket is always a solid perforated paddle, never a strung tennis racket (except Priya's tennis racket, which is always strung).
- No change of character clothing between pages without a spec note.
- No change of line weight or rendering medium between chapters.
- No colour in interior artwork.
- No photorealism, no 3D render, no stock-illustration look.
