"""Content for the synthetic demo book.

A small, complete, deliberately synthetic project: two chapters, front and back
matter, and one of every important page type. It exists to prove the machinery
end to end before real artwork is migrated in.
"""

BRIEF = """# Book Brief - The Reluctant Gardener

**Book id:** `demo-book`
**Format:** 6x9, colour interior
**Target page count:** 24 (synthetic fixture; a real title runs 60-120)

## The idea in one sentence

A straight-faced field manual for the person who did not want a garden, did not
ask for a garden, and now owns one.

## Target buyer

The partner, sibling or grown-up child of someone who moved house in the last
eighteen months and inherited a lawn they resent. The buyer finds it funny
because they live with the resentment daily.

## Gift recipient

Someone who bought a shed before they bought a spade. Opened at Christmas, in
front of the family, ideally by a man who has recently said the phrase "I'll get
to it in spring" out loud more than four times.

## Recognition trigger

1. Owns three watering cans and no watering can that works.
2. Refers to a specific weed by name, with genuine hatred.
3. Has a bag of compost in the boot of the car from last April.
4. Bought a strimmer with more power than the garden requires.
5. Describes any surviving plant as "doing quite well, actually", every time.
6. Stands at the window looking at the garden without going into it.

## Humour angle

The frame is a civil-service field manual: clipped, procedural, entirely
serious about an absurd subject. The comedy comes from institutional language
applied to a man standing in a wet garden holding a mug.

## Commercial rationale

Sits in the Christmas gift-humour shelf alongside parody manuals and
observational gift books. Search terms are gardening gift, funny gardening book,
gift for dad. Price point 8.99 to 12.99. The format repeats: the same manual
frame works for DIY, fishing, cycling and golf, which is the point.

## Constraints

Nothing that mocks the recipient's competence in front of their family beyond
affection. No swearing stronger than mild. Nothing about money worries. The
recipient must finish the book feeling seen, not got at.

## Visual concept (first thoughts)

Ink line with flat muted fills. Field-manual diagrams that look official and
explain nothing useful. Earthy palette. One recurring figure, seen mostly from
behind, holding a mug.
"""

CONCEPT = """# Concept - The Reluctant Gardener

## Premise

An official manual issued to a person who has come into possession of a garden
against their wishes. Written in the register of an institution that believes
this is a serious matter.

## Structure of the book

Two parts in this fixture. Part one assesses the situation. Part two describes
the minimum viable response. A real title extends the same shape across six to
eight parts of escalating denial.

## Recurring characters

| ID | Name | Who they are | Why they recur |
| -- | ---- | ------------ | -------------- |
| subject | The Subject | The reluctant owner. Seen from behind, holding a mug. | He is the reader, and the reader knows it. |
| inspector | The Inspector | The manual's unseen authority, represented by a clipboard. | The institutional voice made visible. |

## Running jokes

- The mug. Never put down, never drunk from.
- Equipment bought in a burst of enthusiasm, still in packaging.
- The phrase "doing quite well, actually" applied to visibly dying plants.

## What this book is NOT

Not a real gardening guide. Not sentimental about nature. Not a book that ends
with the subject learning to love the garden.
"""

AUDIENCE = """# Audience - The Reluctant Gardener

## Primary buyer

Aged 30 to 60, buying for a partner or parent, spending under 15 pounds, wants
the recipient to laugh within ten seconds of opening it.

## Primary recipient

Aged 35 to 70. Owns a garden. Has a complicated relationship with it.

## Buying occasions

Christmas, Father's Day, a housewarming for a property with a lawn, retirement.

## Comparable titles

| Title | What it does well | What we do differently |
| ----- | ----------------- | ---------------------- |
| Parody field manuals | The straight-faced institutional voice | Ours has a recurring character the reader recognises |
| Observational gift humour | Specific, recognisable behaviour | Ours is illustrated throughout, not a text block with cartoons |

## Sensitivities

Avoid implying the recipient is lazy in a way their family will repeat back to
them for a decade. The joke is the garden, not the person's character.
"""

OUTLINE = """# Outline - The Reluctant Gardener

## Front matter

- Half title
- Notice of issue and disclaimer
- Contents
- Epigraph

## Chapters

### Chapter 1 - Assessment of the Situation
**Job:** Establish the frame and diagnose the reader.
**Best joke:** The severity scale, on which every reader scores badly.
**Page budget:** 8 pages.

### Chapter 2 - The Minimum Viable Response
**Job:** Official guidance that solves nothing.
**Best joke:** The comparison of two identical approaches, one of which is
recommended for no stated reason.
**Page budget:** 10 pages.

## Back matter

- Certificate of partial compliance
- Colophon
"""

VOICE_BIBLE = """# Humour / Voice Bible - The Reluctant Gardener

**Version:** v1

## The voice in one paragraph

Institutional, clipped, entirely straight. The manual believes in itself. It
never winks at the reader and never admits the situation is funny. Sentences are
short because the form is short. Warmth arrives only by accident, in the detail
the manual bothers to record.

## Reference points

Civil-service guidance notes. Wartime information leaflets. The instruction
sheet inside a flat-pack wardrobe. Dry British stand-up delivered without a
smile.

## Rules - do

- Be specific. Name the weed. Name the brand of shed. Give the exact number of
  watering cans.
- Base every joke on behaviour a real person has actually performed.
- Let the reader arrive at the joke one beat before the sentence ends.
- Keep the institutional register intact even when the content is absurd.
- Use full sentences and complete paragraphs.
- Mild rudeness is permitted where the manual would plausibly be rude.

## Rules - do not

- No motivational language of any kind.
- No corporate register.
- No sentimental ending where the subject learns to love the garden.
- Never break the frame to explain a joke.
- Do not stack short single-sentence paragraphs for emphasis.
- Do not open two consecutive sections with the same construction.
- No rhetorical questions used as filler.

## Banned phrases

- little did he know
- the humble spade
- a labour of love
- green-fingered

## Person, tense, address

Third person, present tense, referring to the reader as "the subject". The
manual addresses an inspector, not the reader, and the reader is reading over
the inspector's shoulder.

## Spelling and conventions

- British English throughout.
- Numbers under ten spelled out except in measurements and section numbers.
- Section numbering in the form 1.1, 1.2. The manual is fastidious about this.

## Approved sample

The sample in `manuscript/writing-sample.md` is the calibration reference.
"""

VISUAL_BIBLE = """# Visual Bible - The Reluctant Gardener

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
"""

WRITING_SAMPLE = """# Writing Sample - The Reluctant Gardener

## Sample 1 - a typical internal passage

The subject will be observed at the kitchen window between seven and nine in
the morning, holding a mug, looking at the garden. This is not planning. No
plan results from it. The behaviour is understood to be a form of negotiation
with an opponent who does not know the negotiation is happening.

Inspectors should note that the garden is winning, and has been winning since
March.

## Sample 2 - a structured bit

**Severity scale.** Score one point for each statement the subject would agree
with.

- There is a bag of compost in the car.
- The strimmer has a power rating the subject can quote from memory.
- A plant is described as doing quite well, actually.
- The shed was purchased before any tool was purchased.

A score of two indicates a situation within normal limits. A score of four
indicates the subject has begun buying equipment instead of gardening, which is
the terminal form.

## Sample 3 - a chapter opener

Every garden arrives with a previous owner's opinions still in it. Bulbs in the
wrong place. A path to nowhere. A shrub that was clearly somebody's favourite
and is now nobody's problem but the subject's.

The manual begins here because the subject begins here: at the back door, in
October, holding a mug, waiting for the situation to resolve itself.

## Operator notes

The register is right. Keep the inspector addressed rather than the reader. The
mug does a lot of work and should stay.
"""

MANUSCRIPT = """# The Reluctant Gardener

A field manual issued to persons who have come into possession of a garden.

## Chapter 1 - Assessment of the Situation

### 1.1 Scope

This manual applies to any person who has acquired a garden through purchase of
a property, inheritance, or the decision of another member of the household.
It does not apply to persons who wanted one.

Every garden arrives with a previous owner's opinions still in it. Bulbs in the
wrong place. A path to nowhere. A shrub that was clearly somebody's favourite
and is now nobody's problem but the subject's.

### 1.2 The Window Observation

The subject will be observed at the kitchen window between seven and nine in
the morning, holding a mug, looking at the garden. This is not planning. No
plan results from it. The behaviour is understood to be a form of negotiation
with an opponent who does not know the negotiation is happening.

Inspectors should note that the garden is winning, and has been winning since
March.

### 1.3 Initial Severity Assessment

Score one point for each statement the subject would agree with. A score of two
indicates a situation within normal limits. A score of four indicates the
subject has begun buying equipment instead of gardening.

### 1.4 The Equipment Phase

The equipment phase begins with a strimmer and ends with a second strimmer. It
is characterised by purchases that exceed the requirements of the garden by a
factor the subject can justify at length and cannot defend briefly.

A shed purchased before any tool has been purchased is diagnostic.

### 1.5 Terminology

The subject will develop a vocabulary for the garden that is precise about
enemies and vague about everything else. Bindweed will be named. The shrub by
the fence will remain "that one".

## Chapter 2 - The Minimum Viable Response

### 2.1 Principles

The manual does not recommend enthusiasm. Enthusiasm in month one produces a
raised bed in month two and a covered raised bed in month nine. The minimum
viable response is the smallest action that prevents the situation from
becoming visible to neighbours.

### 2.2 The Ninety Minute Protocol

Ninety minutes, once a fortnight, between April and September. The subject will
argue that this is insufficient. The subject has not done ninety minutes once a
fortnight, so the argument is theoretical.

### 2.3 Comparison of Approaches

Two approaches are available. They are functionally identical. The manual
recommends the second, for reasons it does not give, because a manual that gives
reasons invites discussion.

### 2.4 The Mowing Question

A lawn mown once looks mown for nine days. A lawn mown twice looks mown for
eighteen days and has cost the subject one film. This is the only arithmetic in
the manual and the subject is advised to do it honestly.

### 2.5 Recording Progress

Progress is recorded by photograph, from the kitchen window, in the same light,
once a month. The subject will discover that nothing has changed and that this
is, in its way, a result.

### 2.6 Conclusion of Guidance

The garden will outlast the subject's interest in it, the subject's equipment,
and in all likelihood the subject. The manual considers this an acceptable
outcome and closes here.
"""


def _spec(**kwargs) -> dict:
    """Small helper so the page table below stays readable."""
    illustration = kwargs.pop("illustration", None)
    layout = kwargs.pop("layout", None)
    spec = {"copy": kwargs}
    if illustration:
        spec["illustration"] = illustration
    if layout:
        spec["layout"] = layout
    return spec


def _art(asset_id: str, concept: str, placement: str = "full_page",
         characters=None, scene: str | None = None) -> dict:
    return {
        "asset_id": asset_id,
        "concept": concept,
        "scene": scene or concept,
        "characters": characters or ["subject"],
        "references": ["ref-character-main", "ref-page-editorial"],
        "placement": placement,
        "embedded_text": False,
    }


#: The page plan. Order here is the order of the book.
PAGES = [
    {
        "title": "Half title",
        "type": "front_matter",
        "spec": _spec(heading="The Reluctant Gardener",
                      layout={"show_page_number": False, "show_running_head": False}),
    },
    {
        "title": "Notice of issue",
        "type": "front_matter",
        "spec": _spec(
            eyebrow="Notice of issue",
            heading="Conditions of use",
            body=["This manual is issued to the holder of a garden and to no other person. "
                  "It confers no expertise and creates no obligation to garden.",
                  "The publisher accepts no responsibility for outcomes arising from the "
                  "advice contained in these pages, including but not limited to the "
                  "purchase of a second strimmer."],
            footnote="First edition. Printed on paper that has seen a shed.",
            layout={"show_page_number": False, "show_running_head": False}),
    },
    {
        "title": "Contents",
        "type": "contents",
        "spec": _spec(
            eyebrow="Field manual",
            heading="Contents",
            items=[
                {"label": "Epigraph", "page": 2},
                {"label": "1. Assessment of the Situation", "page": 3},
                {"label": "1.3 Initial severity assessment", "page": 6},
                {"label": "2. The Minimum Viable Response", "page": 11},
                {"label": "2.3 Comparison of approaches", "page": 15},
                {"label": "Certificate of partial compliance", "page": 21},
            ]),
    },
    {
        "title": "Epigraph",
        "type": "quote",
        "spec": _spec(quote="The garden is not a project. The garden is a tenant who was "
                            "here first and has no intention of leaving.",
                      attribution="Section 0.1, purpose of this manual"),
    },

    # ---- Chapter 1 -----------------------------------------------------
    {
        "title": "Assessment of the Situation",
        "type": "chapter_opener",
        "chapter": 1,
        "spec": _spec(
            eyebrow="Chapter one",
            heading="Assessment of the Situation",
            subheading="In which the subject discovers that the garden came with opinions.",
            body=["Every garden arrives with a previous owner's opinions still in it. Bulbs "
                  "in the wrong place. A path to nowhere. A shrub that was clearly somebody's "
                  "favourite and is now nobody's problem but the subject's."]),
    },
    {
        "title": "Scope of the manual",
        "type": "editorial_illustration",
        "chapter": 1,
        "assets": ["p006-scope"],
        "spec": _spec(
            eyebrow="1.1",
            heading="Scope",
            body=["This manual applies to any person who has acquired a garden through "
                  "purchase of a property, inheritance, or the decision of another member of "
                  "the household. It does not apply to persons who wanted one.",
                  "Where a garden has been acquired deliberately, the subject is outside the "
                  "scope of this document and beyond the sympathy of its authors."],
            caption="Fig. 1.1 - The garden, as inherited.",
            illustration=_art("p006-scope",
                              "A neglected suburban back garden seen from the kitchen door, "
                              "flat colour, ink line, nobody in frame.",
                              placement="top")),
    },
    {
        "title": "The window observation",
        "type": "text_illustration",
        "chapter": 1,
        "assets": ["p007-window"],
        "spec": _spec(
            eyebrow="1.2",
            heading="The window observation",
            body=["The subject will be observed at the kitchen window between seven and nine "
                  "in the morning, holding a mug, looking at the garden. This is not planning. "
                  "No plan results from it.",
                  "The behaviour is understood to be a form of negotiation with an opponent "
                  "who does not know the negotiation is happening.",
                  "Inspectors should note that the garden is winning, and has been winning "
                  "since March."],
            caption="Fig. 1.2 - The subject, at the window, holding the mug.",
            illustration=_art("p007-window",
                              "The subject from behind at a kitchen window, mug in hand, "
                              "garden visible through the glass.",
                              placement="bottom")),
    },
    {
        "title": "Initial severity assessment",
        "type": "checklist",
        "chapter": 1,
        "spec": _spec(
            eyebrow="1.3",
            heading="Initial severity assessment",
            subheading="Score one point per statement the subject would agree with",
            items=[
                {"label": "There is a bag of compost in the car.",
                 "note": "Purchased in April. Still in the boot."},
                {"label": "The strimmer's power rating can be quoted from memory."},
                {"label": "A plant is described as doing quite well, actually.",
                 "note": "The plant is visibly not doing quite well."},
                {"label": "The shed was purchased before any tool was purchased."},
                {"label": "One specific weed is referred to by name, with feeling."},
                {"label": "There are three watering cans and no working watering can."},
            ],
            footnote="Two points: within normal limits. Four points: the subject has begun "
                     "buying equipment instead of gardening."),
    },
    {
        "title": "The equipment phase",
        "type": "editorial_illustration",
        "chapter": 1,
        "assets": ["p009-equipment"],
        "spec": _spec(
            eyebrow="1.4",
            heading="The equipment phase",
            body=["The equipment phase begins with a strimmer and ends with a second "
                  "strimmer. It is characterised by purchases that exceed the requirements of "
                  "the garden by a factor the subject can justify at length and cannot defend "
                  "briefly."],
            caption="Fig. 1.3 - Equipment, as stored.",
            illustration=_art("p009-equipment",
                              "A shed interior with boxed tools still in packaging, stacked "
                              "against one wall.",
                              placement="top", characters=[])),
    },
    {
        "title": "Anatomy of the acquisition",
        "type": "diagram",
        "chapter": 1,
        "assets": ["p010-anatomy"],
        "spec": _spec(
            eyebrow="1.4.1",
            heading="Anatomy of an equipment acquisition",
            items=[
                {"label": "Trigger", "note": "A neighbour's lawn, seen on a Sunday."},
                {"label": "Research", "note": "Four evenings. Comparison of nine models."},
                {"label": "Purchase", "note": "The most powerful model, in the sale."},
                {"label": "Deployment", "note": "Once, for eleven minutes."},
                {"label": "Storage", "note": "Original packaging, retained for resale."},
            ],
            caption="Fig. 1.4 - All labelling on this diagram is typeset, not drawn. "
                    "Generated artwork carries no words anywhere in this book.",
            illustration=_art("p010-anatomy",
                              "An unlabelled schematic of a strimmer broken into five parts, "
                              "flat colour, technical-manual style, no text of any kind.",
                              placement="top", characters=[])),
    },
    {
        "title": "On terminology",
        "type": "quote",
        "chapter": 1,
        "spec": _spec(quote="Bindweed will be named. The shrub by the fence will remain "
                            "that one.",
                      attribution="Section 1.5, terminology"),
    },
    {
        "title": "Summary of chapter one",
        "type": "text_illustration",
        "chapter": 1,
        "assets": ["p012-summary"],
        "spec": _spec(
            eyebrow="1.6",
            heading="Summary of assessment",
            body=["The subject owns a garden, did not want a garden, and has responded by "
                  "buying a shed. This is the ordinary course of events and requires no "
                  "intervention beyond the guidance that follows.",
                  "Inspectors completing this section should record the severity score and "
                  "proceed to chapter two without discussing the score with the subject."],
            caption="Fig. 1.5 - The mug, at rest.",
            illustration=_art("p012-summary",
                              "A single mug on a windowsill, cold, half full, flat colour.",
                              placement="spot", characters=[])),
    },

    # ---- Chapter 2 -----------------------------------------------------
    {
        "title": "The Minimum Viable Response",
        "type": "chapter_opener",
        "chapter": 2,
        "spec": _spec(
            eyebrow="Chapter two",
            heading="The Minimum Viable Response",
            subheading="In which the manual declines to recommend enthusiasm.",
            body=["Enthusiasm in month one produces a raised bed in month two and a covered "
                  "raised bed in month nine. The minimum viable response is the smallest "
                  "action that prevents the situation from becoming visible to neighbours."]),
    },
    {
        "title": "Principles of response",
        "type": "editorial_illustration",
        "chapter": 2,
        "assets": ["p014-principles"],
        "spec": _spec(
            eyebrow="2.1",
            heading="Principles",
            body=["The manual sets a low bar deliberately. A low bar is cleared. A high bar "
                  "is photographed, discussed, and left where it fell.",
                  "Where the subject proposes a water feature, inspectors should record the "
                  "proposal and take no further action."],
            caption="Fig. 2.1 - A raised bed, month nine.",
            illustration=_art("p014-principles",
                              "A raised vegetable bed overtaken by weeds, netting collapsed, "
                              "flat colour, ink line.",
                              placement="top", characters=[])),
    },
    {
        "title": "The ninety minute protocol",
        "type": "diagnostic_test",
        "chapter": 2,
        "spec": _spec(
            eyebrow="2.2",
            heading="The ninety minute protocol",
            subheading="To be completed by the subject, honestly, in pen",
            items=[
                {"label": "How many fortnights since the last ninety minutes?",
                 "options": ["One", "Three", "I do not measure time that way"]},
                {"label": "What prevented the most recent attempt?",
                 "options": ["Rain", "Forecast rain", "Rain the previous Tuesday"]},
                {"label": "Which task was performed instead?",
                 "options": ["Tidying the shed", "Researching a mower", "Standing at the window"]},
                {"label": "Was the mug present throughout?",
                 "options": ["Yes", "Yes", "Yes"]},
            ],
            footnote="Scoring: any answer in the third column indicates the subject has "
                     "replaced gardening with the contemplation of gardening. This is "
                     "common and is not, by itself, a cause for concern."),
    },
    {
        "title": "Guidance on frequency",
        "type": "text_illustration",
        "chapter": 2,
        "assets": ["p016-frequency"],
        "spec": _spec(
            eyebrow="2.2.1",
            heading="Guidance on frequency",
            body=["Ninety minutes, once a fortnight, between April and September. The subject "
                  "will argue that this is insufficient. The subject has not done ninety "
                  "minutes once a fortnight, so the argument is theoretical.",
                  "A lawn mown once looks mown for nine days. A lawn mown twice looks mown "
                  "for eighteen days and has cost the subject one film. This is the only "
                  "arithmetic in the manual and the subject is advised to do it honestly."],
            caption="Fig. 2.2 - Ninety minutes, as spent.",
            illustration=_art("p016-frequency",
                              "The subject from behind, standing in long grass, not working, "
                              "mug in hand.",
                              placement="bottom")),
    },
    {
        "title": "Comparison of approaches",
        "type": "comparison",
        "chapter": 2,
        "spec": _spec(
            eyebrow="2.3",
            heading="Comparison of approaches",
            subheading="Two available approaches, assessed",
            columns=[
                {"title": "Approach A",
                 "items": ["Ninety minutes once a fortnight",
                           "Two tools, both owned",
                           "No new purchases",
                           "Visible from the neighbour's window",
                           "Sustainable across a season"]},
                {"title": "Approach B",
                 "items": ["Ninety minutes once a fortnight",
                           "Two tools, both owned",
                           "No new purchases",
                           "Visible from the neighbour's window",
                           "Sustainable across a season"]},
            ],
            footnote="The manual recommends Approach B. Reasons are not given. A manual that "
                     "gives reasons invites discussion."),
    },
    {
        "title": "Seasonal obligations",
        "type": "checklist",
        "chapter": 2,
        "spec": _spec(
            eyebrow="2.4",
            heading="Seasonal obligations",
            subheading="The complete list, in full",
            items=[
                {"label": "April - cut the grass once.",
                 "note": "The first cut is ceremonial and may be photographed."},
                {"label": "June - cut the grass again.",
                 "note": "Enthusiasm at this point is a warning sign."},
                {"label": "August - cut the grass, or do not.",
                 "note": "August is understood to be a negotiation."},
                {"label": "October - move the furniture into the shed."},
                {"label": "February - look at the garden from the window."},
            ],
            footnote="No other obligation exists. Any additional task the subject performs is "
                     "voluntary and should not be mentioned to the household, who will come to "
                     "expect it."),
    },
    {
        "title": "Recording progress",
        "type": "editorial_illustration",
        "chapter": 2,
        "assets": ["p019-recording"],
        "spec": _spec(
            eyebrow="2.5",
            heading="Recording progress",
            body=["Progress is recorded by photograph, from the kitchen window, in the same "
                  "light, once a month. The subject will discover that nothing has changed and "
                  "that this is, in its way, a result."],
            caption="Fig. 2.3 - The same view, twelve months apart.",
            illustration=_art("p019-recording",
                              "Two near-identical views of the same garden side by side, "
                              "flat colour, no text.",
                              placement="top", characters=[])),
    },
    {
        "title": "The tool inventory",
        "type": "diagram",
        "chapter": 2,
        "assets": ["p020-inventory"],
        "spec": _spec(
            eyebrow="2.5.1",
            heading="Recommended tool inventory",
            items=[
                {"label": "One spade", "note": "Any spade. The spade is not the problem."},
                {"label": "One pair of shears", "note": "Sharpened once, in year one."},
                {"label": "One mower", "note": "The one already owned."},
                {"label": "One mug", "note": "Non-negotiable."},
            ],
            body=["Equipment beyond this list is permitted but will not improve the garden. "
                  "It will improve the shed, which the subject may consider sufficient."],
            caption="Fig. 2.4 - The inventory, unlabelled in artwork and labelled in type.",
            illustration=_art("p020-inventory",
                              "Four garden tools laid out flat in a row, top-down view, "
                              "flat colour, no words anywhere.",
                              placement="top", characters=[])),
    },
    {
        "title": "Conclusion of guidance",
        "type": "quote",
        "chapter": 2,
        "spec": _spec(quote="The garden will outlast the subject's interest in it, the "
                            "subject's equipment, and in all likelihood the subject.",
                      attribution="Section 2.6, conclusion of guidance"),
    },
    {
        "title": "Closing statement",
        "type": "closing",
        "chapter": 2,
        "assets": ["p022-closing"],
        "spec": _spec(
            eyebrow="End of guidance",
            heading="The manual closes here",
            body=["The inspector's work is complete. The subject remains at the window.",
                  "This is considered an acceptable outcome."],
            illustration=_art("p022-closing",
                              "A wide view of the garden at dusk, the subject small and far "
                              "off, seen from behind.",
                              placement="top")),
    },

    # ---- Back matter ---------------------------------------------------
    {
        "title": "Certificate of partial compliance",
        "type": "certificate",
        "spec": _spec(
            eyebrow="Issued under section 2.6",
            heading="Certificate of Partial Compliance",
            body=["This certifies that the holder has read a manual about their garden, which "
                  "is more than the garden expected."],
            items=["Name of subject", "Date of issue", "Signature of inspector"]),
    },
    {
        "title": "Colophon",
        "type": "front_matter",
        "spec": _spec(
            eyebrow="Colophon",
            heading="About this edition",
            body=["Set in a serif face at ten and a half point. Pages composed "
                  "deterministically from page specifications; artwork generated separately "
                  "and approved before use.",
                  "This is a synthetic demonstration book. It exists to prove the production "
                  "system works before real artwork is migrated into it."],
            footnote="Book Factory demo fixture",
            layout={"show_running_head": False}),
    },
]

#: Page ids are assigned in order, so this is the page that gets revised later.
REVISION_PAGE_TITLE = "Guidance on frequency"
