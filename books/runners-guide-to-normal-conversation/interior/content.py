"""Interior content for the v4 layout proposal, in reading order.

Every word of copy comes from the preserved v3 interior
(releases/interior-v3-publication-draft.pdf). The layout adds only
structure: activity panels, tick boxes, write-in lines, score boxes and
tables. Labels that are new furniture rather than copy (activity kinds,
"Score", "Day 1-7", the "Notes" page) are listed in interior/README.md.

build_interior.py turns this into HTML with the helpers below.
"""

from html import escape

TITLE = "The Runner’s Guide to Normal Conversation"


# ---------------------------------------------------------------- helpers

PB = '<div class="pb"></div>'


def P(text, cls=None):
    c = f' class="{cls}"' if cls else ""
    return f"<p{c}>{text}</p>"


def H(title, id=None):
    i = f' id="{id}"' if id else ""
    return f"<h2{i}>{title}</h2>"


def section(title, *body, cls="topic"):
    return f'<section class="{cls}">{H(title)}{"".join(body)}</section>'


def activity(kind, title, *body, instr=None, note=None, cls=""):
    head = f'<div class="tab">{kind}</div><h3>{title}</h3>'
    if instr:
        head += f'<div class="instr">{instr}</div>'
    foot = f'<div class="act-note">{note}</div>' if note else ""
    return (f'<div class="actwrap"><section class="activity {cls}">{head}{"".join(body)}{foot}'
            f'</section></div>')


def checklist(items, cls=""):
    lis = "".join(f'<tr><td class="bx"><span class="box"></span></td><td>{t}</td></tr>' for t in items)
    return f'<table class="check {cls}">{lis}</table>'


def ticks(items, start=1):
    """Numbered statements with a tick box on the right, for scored tests."""
    rows = "".join(
        f'<tr><td class="n">{n}</td><td class="t">{t}</td><td class="bx"><span class="box"></span></td></tr>'
        for n, t in enumerate(items, start))
    return f'<table class="ticks">{rows}</table>'


def numbered(items, cls=""):
    rows = "".join(f'<tr><td class="n">{n}</td><td class="t">{t}</td></tr>' for n, t in enumerate(items, 1))
    return f'<table class="numbered {cls}">{rows}</table>'


def score(label="Score", out_of=None):
    tail = f'<span class="outof">/ {out_of}</span>' if out_of else ""
    return f'<div class="score"><span class="lab">{label}</span><span class="scorebox"></span>{tail}</div>'


def lines(n, label=None):
    lab = f'<div class="line-label">{label}</div>' if label else ""
    return lab + "".join('<div class="wline"></div>' for _ in range(n))


def field(label, n=1):
    return f'<div class="field"><div class="flabel">{label}</div>{"".join(chr(10) + "<div class=wline></div>" for _ in range(n))}</div>'


def table(headers, rows, cls="", widths=None):
    cols = ""
    if widths:
        cols = "<colgroup>" + "".join(f'<col style="width:{w}">' for w in widths) + "</colgroup>"
    th = "".join(f"<th>{h}</th>" for h in headers)
    trs = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<table class="grid {cls}">{cols}<thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>'


def casenote(text, label="Case note"):
    return f'<aside class="casenote"><div class="cn-lab">{label}</div>{text}</aside>'


def say(text):
    """A line of dialogue or a sample answer, set as a quoted example."""
    return f'<p class="say">{text}</p>'


def fig(name, width_in, cls=""):
    return f'<figure class="{cls}"><img src="art/{name}.png" style="width:{width_in}in"></figure>'


def chapter(num, title, art, art_w, sub=None, lead=None, id=None):
    s = f'<div class="ch-sub">{sub}</div>' if sub else ""
    l = f'<p class="ch-lead">{lead}</p>' if lead else ""
    return (f'<section class="opener" id="{id}">'
            f'<div class="ch-num">{num}</div>'
            f'<h1 class="ch-title">{title}</h1>{s}{l}'
            f'<figure class="ch-art"><img src="art/{art}.png" style="width:{art_w}in"></figure>'
            f'</section><div class="ch-mark" data-ch="{escape(title)}"></div>')


# ---------------------------------------------------------------- content

CHAPTERS = [
    ("ch1", "Referral and Diagnosis"),
    ("ch2", "Identifying Your Triggers"),
    ("ch3", "Basic Conversation Rehabilitation"),
    ("ch4", "Life Outside the Training Plan"),
    ("ch5", "Equipment, Economics and Other Symptoms"),
    ("ch6", "Advanced Social Exposure"),
    ("ch7", "Relapse Prevention and Conditional Discharge"),
]


def front_matter():
    toc = "".join(
        f'<li><a href="#{cid}"><span class="toc-n">{n}</span>{t}</a></li>'
        for n, (cid, t) in enumerate(CHAPTERS, 1))
    toc += '<li class="toc-cert"><a href="#certificate"><span class="toc-n">★</span>Certificate of conditional discharge</a></li>'
    return f"""
<section class="halftitle front">
  <div class="ht-title">The Runner’s Guide to Normal Conversation</div>
  <div class="ht-rule"></div>
  <p>A rehabilitation manual for people who can run for three hours but cannot
  answer “How was your weekend?” in under twenty minutes.</p>
</section>

<section class="titlepage front">
  <div class="tp-title">The<br>Runner’s<br>Guide to<br>Normal<br>Conversation</div>
  <div class="tp-rule"></div>
  <p class="tp-sub">For recreational runners referred by a partner, friend,
  relative or colleague who only asked a simple question.</p>
  <div class="tp-author">Kieran Smith</div>
</section>

<section class="notice front">
  <div class="notice-stamp">Notice to the patient</div>
  <div class="notice-big">This manual has been issued because people close to
  you have noticed a pattern.</div>
  <p>The pattern may involve pace, distance, shoes, fuelling, race entries,
  recovery scores, weather conditions, a calf that is “basically fine” or a run
  described as easy despite requiring two gels and a lift home.</p>
  <p>Receipt of this manual does not confirm that you have a problem. Your
  immediate attempt to compare the problem with last Tuesday’s tempo session
  probably does.</p>
  <p>Keep the manual somewhere visible. Do not place it beneath the foam roller,
  inside the drawer of race numbers or beside the unopened cookbooks purchased
  when you briefly became interested in carbohydrate periodisation.</p>
</section>

<section class="conditions front">
  <h2 class="fm-h">Conditions of treatment</h2>
  <p>The Normal Conversation Rehabilitation Service offers social guidance, not
  medical or training advice. Continue running if running makes you happy.
  Continue resting if a qualified professional tells you to rest. The Service
  has no opinion on your cadence.</p>
  <p>Any resemblance to a runner you know is intentional in the general sense
  and accidental in every legally useful sense.</p>
  <p>Brand names appear only where ordinary runners use them in ordinary
  speech. No brand has approved the programme. Several would prefer you to
  remain exactly as you are.</p>
  <div class="copyright">© 2026 Kieran Smith</div>
</section>

<section class="contents front">
  <h2 class="fm-h">Contents</h2>
  <ol class="toc">{toc}</ol>
</section>

<section class="front intake">
{activity("Intake form", "Patient identification",
    field("1. Name"),
    field("2. Preferred race distance"),
    '<div class="field"><div class="flabel">3. Answer crossed out because you began listing all distances</div>'
    + checklist(["Yes", "Not yet"], "inline") + '</div>',
    field("4. Date of most recent ordinary conversation"),
    field("5. Person who bought you this book"),
    '<div class="field"><div class="flabel">6. Their probable motive</div>'
    + checklist(["Concern", "Revenge", "Secret Santa budget", "All three"], "inline") + '</div>',
    instr="Complete honestly, in pen",
    note="Before beginning, remove your watch and place it face-down. If this "
         "instruction has caused anxiety, place a sleeve over it instead. Early "
         "treatment must remain realistic.")}
</section>
"""


def chapter_1():
    return "".join([
        chapter("01", "Referral and Diagnosis", "art-p007", 4.23,
                sub="Identify Runner’s Conversational Capture and calculate severity.", id="ch1"),
        section("Reason for referral",
            P("You have been referred because running has expanded beyond the time in which you are physically running.", "first"),
            P("It now occupies breakfast, weekends, online activity, family logistics and the first twelve minutes of any conversation with a person careless enough to ask how you are. Friends know which toenail is causing concern. Colleagues know your target race. Your partner can distinguish a recovery run from an easy run but wishes they could not."),
            P("No single behaviour caused the referral. The Service acts when the behaviours form a training block."),
            P("Common referral sources include a colleague trapped beside the kettle, a partner who has moved a holiday twice, and a family group chat containing more route screenshots than photographs of family members.")),
        '<section class="topic casefile">'
        '<div class="cf-tab">Patient file</div>'
        + H("Case file: Alex") +
        P("Alex is a recreational runner of ordinary talent and exceptional administrative commitment.", "first") +
        P("On referral, Alex owned two formal outfits and eleven garments described as layers. Their watch had recorded a stressful afternoon during their own birthday meal. They had entered three races, complained about having too many races and entered a fourth while explaining the problem to Sam.") +
        P("Asked why running came up so often, Alex said it did not. Alex then supplied examples from five recent conversations to prove this, all of which were about running.") +
        P("Dr Hughes recorded the patient as cooperative, articulate and likely to convert treatment into content.") +
        '</section>',
        section("The ordinary question test",
            P("A normal person hears: “Did you have a nice weekend?”", "first"),
            P("They say: “Yes, thanks. Quiet one. How about you?”", "cont"),
            P("You hear the same question and begin at 06:15 on Sunday. You explain the porridge, the weather app, the missing sock, the first three kilometres, the decision not to chase pace, the pace you accidentally chased, the headwind near the retail park and the reason the final average was not representative."),
            P("The question has not been answered. It has been outlived.", "kicker")),
        activity("Diagram", "The conversational capture cycle",
            '<table class="cycle">'
            + "".join(
                f'<tr class="{ "hot" if n == 2 else ""}"><td class="cn"><span>{n}</span></td>'
                f'<td class="ct"><b>{t}</b><br><span class="cd">{d}</span></td></tr>'
                + ('<tr class="arrow"><td class="cn">↓</td><td></td></tr>' if n < 5 else "")
                for n, t, d in [
                    (1, "Innocent prompt", "Somebody mentions weather, traffic, breakfast, holidays, knees, shoes or Sunday."),
                    (2, "Private association", "You remember a run."),
                    (3, "Unnecessary disclosure", "You say, “That reminds me…”"),
                    (4, "Data release", "Pace, distance and route become available to the public."),
                    (5, "False encouragement", "The listener nods once. You interpret this as a request for kilometre splits."),
                ])
            + '</table>',
            instr="The earliest reliable intervention point is Stage Two",
            note="Once your phone is unlocked, the civilian has little chance."),
        PB,
        activity("Assessment", "Initial severity assessment",
            ticks([
                "Your watch has vibrated during a funeral, wedding ceremony or disciplinary meeting.",
                "You own more running shoes than shoes suitable for the rest of your life.",
                "A partner has said, “I wasn’t asking about the run.”",
                "You have described rain as “actually quite refreshing” while visibly shivering.",
                "You have uploaded an activity before removing your wet clothes.",
                "You have used a minor injury to begin a forty-minute monologue about training load.",
                "You know a colleague’s 10 km PB but not the name of their partner.",
                "You have booked a holiday after checking whether the hotel is near a flat route.",
                "You have called 15 km “nothing silly”.",
                "You are reading these statements while disagreeing with the scoring methodology.",
            ]),
            score("Score", 10),
            instr="Award one point for each true statement", cls="roomy",
            note="Record the score before proceeding."),
        activity("Results", "Severity results",
            '<table class="gauge"><thead><tr><th colspan="2">0–5 points</th><th colspan="2">6–10 points</th></tr></thead><tbody><tr>'
            '<td class="g1"><div class="band">0–2</div><b>Social runner.</b> You remain able to discuss films, food and events that happened to other people.</td>'
            '<td class="g2"><div class="band">3–5</div><b>Conversational drift.</b> Running enters unrelated subjects, usually within four minutes.</td>'
            '<td class="g3"><div class="band">6–8</div><b>Established capture.</b> Friends have stopped asking follow-up questions. You interpret this as admiration.</td>'
            '<td class="g4"><div class="band">9–10</div><b>Full annexation.</b> Your personality now has a weekly mileage target.</td>'
            '</tr></tbody></table>',
            note="Treatment is recommended before race season."),
        activity("Checklist", "Before proceeding",
            checklist(["Answer “Did you have a nice weekend?” using no numbers.",
                       "Repeat without the words run, legs, route, session or easy.",
                       "Record the baseline conversation honestly.",
                       "Accept the severity score without changing the methodology."], "ruled"),
            note="Patients who reply “Define nice” should return to the beginning of the exercise."),
        activity("Field exercise", "Baseline conversation recording",
            P("Have a five-minute conversation with a willing adult. Do not tell them this is an assessment; runners perform unnaturally when they know a result will be recorded."),
            P("Afterwards, mark every topic that appeared.", "strong"),
            checklist(["The other person’s day", "News", "Family", "Work", "Food",
                       "A shared plan", "Running", "The difference between chip time and gun time",
                       "Why your current pace is misleading", "The camber on one particular road"], "ruled"),
            field("Duration of conversation"),
            note="If the final four topics occupied more than half the conversation, the baseline has been "
                 "established. If the other person left before five minutes, record the duration honestly. "
                 "Do not pause the clock while they make tea."),
    ])


def chapter_2():
    return "".join([
        chapter("02", "Identifying Your Triggers", "art-p017", 3.79,
                sub="Watches, Strava, clothing, weather, food and race entries.", id="ch2"),
        section("The wrist device",
            P("The fitness watch began as a tool. It now sits at the centre of a small constitutional arrangement.", "first"),
            P("You consult it when waking, walking, eating and waiting for a lift. It informs you that you slept badly, which surprises you despite having been awake for most of it checking whether you were asleep. It assigns a recovery score to a body you have inhabited for decades."),
            P("At formal events, the watch remains. Suits, dresses and carefully chosen jewellery must negotiate around a black rubber strap and a face displaying an urgent green number.")),
        section("Strava confirmation behaviour",
            fig("art-p020", 3.7),
            P("A run occurs twice: first on the road, then properly once uploaded.", "first"),
            P("You may claim the post is a private record. This does not explain the title, the photograph, the weather commentary or the twelve minutes spent deciding whether ‘Morning miles’ looked too pleased with itself.")),
        activity("Exercise", "First intervention",
            '<table class="meals"><tr>'
            '<td><div class="meal">Meal 1</div><span class="box"></span><p>During one meal this week, keep the watch beneath the table line.</p></td>'
            '<td><div class="meal">Meal 2</div><span class="box"></span><p>During the next, avoid checking it.</p></td>'
            '<td><div class="meal">Meal 3</div><span class="box"></span><p>During the third, listen when Sam says the story is not finished.</p></td>'
            '</tr></table>'),
        activity("Reference", "Activity-title translation guide",
            table(["Activity title", "Translation"], [
                ["‘Easy miles’", "The pace was slower than hoped and witnesses may have noticed."],
                ["‘Back at it’", "Forty-eight hours have passed since the previous upload."],
                ["‘Bit of a leg loosener’", "The legs were consulted after the decision had already been made."],
                ["‘No heroics’", "Some heroics were attempted."],
                ["‘Lovely morning for it’", "The photograph came out well."],
                ["‘Watch had a moment’", "The result is excellent except for the part measured by the watch."],
            ], widths=["38%", "62%"]),
            note="The Service does not require you to stop posting. It asks that you wait until your breathing "
                 "returns to normal and decide whether the public needs to know about the headwind."),
        section("Technical clothing migration",
            fig("art-p023", 3.6),
            P("Running kit reproduces in cupboards.", "first"),
            P("First comes a pair of shorts. Then winter tights, summer tights, a vest, another vest that is lighter, socks for long runs, socks for races and a jacket whose principal feature is that water enters it in a more expensive manner."),
            P("Over time, technical clothing moves into civilian settings. You wear a race T-shirt to the supermarket, a quarter-zip on video calls and compression socks on a flight long enough to justify mentioning them.")),
        activity("Exercise", "Wardrobe audit",
            numbered(["Open the wardrobe and identify one outfit that cannot be explained by a future run.",
                      "If none exists, purchase trousers before further shoes."]),
            field("Outfit identified")),
        section("Weather interpretation",
            fig("art-p025", 3.0),
            P("Non-runners experience weather as a condition.", "first"),
            P("You experience it as a session variable.", "cont"),
            P("Rain is cooling. Wind is resistance. Frost is ‘fine once you get moving’. Heat is an opportunity to practise hydration. A yellow warning means the route will be quieter."),
            P("The Service recognises your resilience. The people watching you run through horizontal sleet in five-inch shorts recognise something else."),
            P("When somebody says, ‘Awful weather,’ reply, ‘It really is.’"),
            P("Do not add ‘although’. Nothing helpful has ever followed ‘although’ in this context.")),
        section("Food and race-entry triggers",
            '<h4>Food conversion</h4>',
            P("Food retains several non-running purposes. It can taste good. It can mark an occasion. It can be shared without being assigned a function.", "first"),
            P("During conversational capture, all food becomes fuel. Breakfast is pre-run fuel, lunch is recovery fuel, dinner is carb loading and cake is permitted because of something happening on Sunday."),
            P("Practise eating one banana without announcing when the carbohydrates will become available."),
            P("Then attend a restaurant and order the meal you want. The waiter does not need your start time."),
            '<h4>Race-entry response</h4>',
            P("A race entry produces immediate calm followed by months of avoidable logistics.", "first"),
            P("The date enters every calendar. Hotels are inspected. Trains become unreliable in advance. A plan is downloaded, adapted and discussed. Family events near race weekend acquire provisional status."),
            P("Check the household calendar. Check the races already entered. Ask the person whose birthday appears on the date. Wait twenty-four hours. Do not treat the wait as a taper."),
            casenote("Alex completed the protocol successfully and entered the race after twenty-three hours. The Service recorded partial comprehension.")),
        activity("Exercise", "The kudos interval",
            checklist(["After uploading an activity, place the phone in another room for ten minutes.",
                       "Do not retrieve the phone because you need water. Water is available in several rooms and has never required a password.",
                       "Advanced patients may leave a run untitled for one hour. Dr Hughes describes this as ‘social altitude training’ and accepts that few are ready."]),
            P("Patients often report a sensation that somebody may have acknowledged the run during this period. This is possible. The acknowledgement will survive.", "after")),
    ])


def chapter_3():
    return "".join([
        chapter("03", "Basic Conversation Rehabilitation", "art-p027", 4.14, id="ch3"),
        section("The two-sentence limit",
            P("For the first week, any account of a run must end after two sentences.", "first"),
            P("A sentence remains one sentence even when joined by ‘and’. Patients have attempted to place an entire half-marathon inside a semicolon. Punctuation cannot be used to evade treatment.")),
        activity("Method", "A controlled disclosure",
            P("You may share running news when it matters to you. Recovery does not require secrecy; it requires proportion."),
            P("Use this structure:", "strong"),
            '<table class="pills"><tr>'
            '<td><span>1</span>State the news.</td><td><span>2</span>State why you care.</td>'
            '<td><span>3</span>Stop.</td><td><span>4</span>Let the listener choose whether to ask more.</td>'
            '</tr></table>',
            P("Example:", "strong"),
            say("‘I got a place in the London Marathon. I’ve wanted to do it for years, so I’m delighted.’"),
            P("This is complete. Training volume, charity targets, hotel availability and the ballot system remain available if requested."),
            note="An expression of warmth is a response, not informed consent for the route plan."),
        section("Receive a compliment without supplying data",
            P("At some point, a kind person will say that you are looking well. They are offering a compliment. They have not requested your resting heart rate.", "first"),
            P("Begin with the words ‘Thank you.’ Stop there.", "kicker"),
            P("You may notice a powerful urge to explain that your watch disagrees because your training readiness is only 46. This sensation is common and will pass. Do not raise your wrist. Do not describe last night’s sleep score. The person complimenting you has already taken a considerable social risk and should not be made to interpret a coloured semicircle."),
            casenote("One patient successfully accepted a compliment at a wedding, then ruined the result by adding that the suit felt loose because marathon training had ‘melted the last bit off’. Progress was recorded as administrative only.")),
        section("‘Fine, thanks’",
            P("The phrase ‘Fine, thanks’ contains two words and one complete answer.", "first"),
            P("You may find this suspiciously brief. Normal conversation relies on such compression. People often exchange broad summaries before deciding whether detail is required."),
            '<table class="script"><tr><td class="who">Pat</td><td>How are you?</td></tr>'
            '<tr><td class="who">You</td><td>Fine, thanks. How are you?</td></tr></table>',
            P("Pause. Pat may now answer. Resist the impulse to use the pause for a calf update. If Pat asks whether you have been running, you may say yes. This is not permission to locate the activity.")),
        activity("Spot the difference", "Acceptable and not yet acceptable",
            table(["Acceptable", "Not yet acceptable"], [
                ["‘I went for a run before breakfast. It was good, thanks.’",
                 "‘I went for a run before breakfast and kept it easy because Tuesday took more out of me than expected, although the middle section came out quicker once I found a rhythm and the watch lost signal under the trees, so the average…’"],
            ], cls="vs", widths=["40%", "60%"]),
            note="Dr Hughes will stop you at ‘Tuesday’."),
        activity("Spot the fault", "The return question",
            P("Conversational recovery depends on returning attention to the other person."),
            P("After one statement about yourself, ask a relevant question about them. Listen to the answer without scanning it for entry points."),
            '<table class="script"><tr><td class="who">Sam</td><td>We went to York at the weekend.</td></tr>'
            '<tr><td class="who">You</td><td>Was it good?</td></tr></table>',
            P("The following responses fail the exercise:", "strong"),
            '<table class="fails">' + "".join(f'<tr><td class="x">✗</td><td>{t}</td></tr>' for t in [
                "‘I ran York once.’", "‘York is flatter than people think.’",
                "‘Did you go near the racecourse?’", "‘I’ve always said it would be a good marathon city.’",
                "‘How many steps did you do?’"]) + '</table>',
            note="The question belongs to Sam. Allow York to remain unmeasured."),
        activity("Self-test", "Has the conversation become a run report?",
            ticks([
                "You have said ‘nothing serious’ immediately before naming a distance longer than the listener’s commute.",
                "The other person now knows where the headwind started.",
                "You have drawn a hill in the air with one finger.",
                "A question about Sunday lunch has reached kilometre 14.",
                "You used the phrase ‘on tired legs’ about an activity nobody asked you to do.",
                "The listener has looked towards a door, window or passing colleague.",
                "You are holding your phone sideways to improve the visibility of a graph.",
                "Nobody else has spoken since the warm-up.",
            ]),
            score("Ticks", 8),
            '<table class="key">'
            '<tr><td class="k">0–1</td><td>Normal conversation remains possible. Continue under observation.</td></tr>'
            '<tr><td class="k">2–4</td><td>Moderate conversational capture. Place the watch face-down and ask where the other person went at the weekend.</td></tr>'
            '<tr><td class="k">5–7</td><td>Severe episode. End the account before the gel strategy.</td></tr>'
            '<tr><td class="k">8</td><td>This was not a conversation. You delivered unauthorised commentary over a trapped civilian.</td></tr>'
            '</table>',
            instr="Tick every statement that applies."),
        activity("Seven-day challenge", "Forbidden conversions",
            P("For seven days, do not convert the following topics into running."),
            table(["They mention", "You must not mention"], [
                ["A new café", "Its distance from your house"],
                ["Their bad knee", "Your physio"],
                ["A holiday", "Heat acclimatisation"],
                ["A road closure", "The year the half-marathon used that route"],
                ["Breakfast", "Pre-run digestion"],
                ["New shoes", "Carbon plates"],
                ["Sunday", "The long run"],
                ["A watch", "Your watch"],
            ], cls="arrowed roomy", widths=["42%", "58%"]),
            '<table class="days"><tr>' + "".join(
                f'<td><span class="box"></span><div>Day {d}</div></td>' for d in range(1, 8)) + '</tr></table>',
            note="If somebody mentions an actual race, ordinary restrictions are relaxed for three minutes. "
                 "A timer may be used, provided it is not the watch."),
        section("Listening posture",
            fig("art-p035", 4.2),
            '<div class="steps">'
            + "".join(f'<p>{t}</p>' for t in ["Lower the wrist.", "Turn your body towards the speaker.",
                                              "Keep the phone out of your hand.",
                                              "Allow your face to respond to their words rather than to a vibration from an app."])
            + '</div>',
            P("These actions may feel theatrical. For non-runners they form part of listening."),
            casenote("Sam reports that Alex’s early listening posture resembled waiting for a pedestrian crossing. Improvement followed once Alex stopped bouncing gently on the toes ‘to stay loose’.")),
        activity("Cut-out card", "Emergency stop phrases",
            P("When you detect a run report already in progress, use one of the following."),
            '<ul class="phrases">' + "".join(f"<li>{t}</li>" for t in [
                "‘Sorry, I’ve gone into the splits.’",
                "‘You only asked whether I was free on Sunday.’",
                "‘That is more detail than the story needed.’",
                "‘I’ll spare you the shoe explanation.’",
                "‘Please continue with your own news.’"]) + "</ul>",
            note="Say the phrase once. Do not turn the self-correction into a funny story about how much you "
                 "talk about running. That story is also about running.", cls="cutout"),
        activity("Stage review", "Stage Three assessment",
            checklist(["For the first week, any account of a run must end after two sentences.",
                       "Begin with the words ‘Thank you.’ Stop there.",
                       "After one statement about yourself, ask a relevant question about them. Listen to the answer without scanning it for entry points.",
                       "Lower the wrist.",
                       "Keep the phone out of your hand.",
                       "Let the listener choose whether to ask more."], "numbered-check"),
            note="An expression of warmth is a response, not informed consent for the route plan."),
    ])


def chapter_4():
    return "".join([
        chapter("04", "Life Outside the Training Plan", "art-p039", 3.65, id="ch4"),
        section("Re-entry",
            P("You are now ready to re-enter places where nobody has been assigned a pace.", "first"),
            P("This stage covers restaurants, offices, weddings, family holidays and other environments that continue to operate despite having no start gantry. You will practise arriving without having run there, choosing food for its taste and allowing somebody else’s weekend to remain about them."),
            P("Early exposure can be disorientating. Restaurants may provide no secure area for a hydration vest. Hotel receptionists often do not know the elevation profile of the bypass. At weddings, the people dressed alike near the front are usually members of the wedding party, not pacers."),
            P("Before attending any social event, remove one piece of technical clothing. Advanced patients may attempt trousers with no zipped rear pocket.")),
        section("The office kitchen",
            fig("art-p041", 3.0, "right"),
            P("The office kitchen is a high-risk environment because innocent prompts occur near witnesses.", "first"),
            '<table class="script"><tr><td class="who">Pat</td><td>You’re in early.</td></tr></table>',
            P("A healthy response might concern traffic, workload or sleep."),
            P("Your current response begins, ‘Had to get ten in before the first call.’"),
            P("Enter the kitchen after a morning run. Make tea. If asked why your hair is wet, answer truthfully in six words or fewer."),
            '<table class="answers"><tr><td class="ok">✓</td><td><b>Suggested answer:</b> ‘I ran in. It was raining.’</td></tr>'
            '<tr><td class="x">✗</td><td><b>Unsuitable answer:</b> ‘I ran in, but kept it properly easy because…’</td></tr></table>',
            P("Six words have passed. Drink the tea.", "kicker")),
        activity("Checklist", "Meetings",
            P("Your colleagues have accepted the fitness watch. They have not accepted it as a second chair."),
            P("During a meeting:", "strong"),
            checklist(["Disable lap alerts.",
                       "Do not interpret stress notifications aloud.",
                       "Do not stand because the watch instructed you to move.",
                       "Do not announce that your body battery fell during finance.",
                       "Do not refer to the meeting as mental endurance work."]),
            P("If a calendar invitation clashes with training, move the training privately. The department does not need to know that threshold has been displaced.", "after"),
            casenote("Pat once received an email titled ‘Tuesday reshuffle’ and assumed a project deadline had changed. It concerned intervals.")),
        activity("Exercise", "Restaurants",
            P("A menu is not a fuelling plan with prices."),
            P("Choose something because you would like to eat it. Avoid interviewing the waiter about the dry weight of the rice. A meal can contain carbohydrates without becoming carb loading; the distinction is important to everybody except your digestive system."),
            P("Complete one meal without saying:", "strong"),
            '<table class="fails">' + "".join(f'<tr><td class="x">✗</td><td>{t}</td></tr>' for t in [
                "‘I’ve earned this.’", "‘I need the salt.’", "‘Good recovery food.’",
                "‘This might sit a bit heavy tomorrow.’", "‘I’m not normally this bad.’"]) + '</table>',
            note="You are eating chips, Alex. No governing body has opened an inquiry."),
        section("Weddings and formal occasions",
            fig("art-p044", 3.6),
            P("Formalwear creates three common difficulties.", "first"),
            numbered(["First, the fitness watch does not match. You will wear it anyway and explain that the data streak cannot be broken for a wedding.",
                      "Second, a relative may ask about ‘all the running’. Treat this as a courtesy question, not a keynote invitation.",
                      "Third, the dance floor will affect your step count. Do not circle the room at 23:52 to reach a round number. People remember that."], "plain"),
            P("Allow the watch battery to fall below 20 per cent without asking the venue for a charger."),
            P("If the bride offers one, the failure has already become visible.")),
        section("Holidays",
            fig("art-p045", 3.4),
            P("A holiday is a temporary visit to another place. It need not become an overseas training camp.", "first"),
            P("Before booking accommodation, each member of the party may name two essential features. ‘Near a flat, well-lit 10 km loop’ counts as one of yours, not one of everyone’s."),
            P("On arrival, refrain from saying the roads look runnable. Roads generally are.")),
        activity("Checklist", "Holiday morning protocol",
            P("If you choose to run:", "strong"),
            checklist(["Leave without waking the room.",
                       "Return at the agreed time.",
                       "Do not describe the route before coffee.",
                       "Do not behave as though you discovered the town.",
                       "Remember that Sam also had a morning."]),
            casenote("Alex passed steps one and two in Lisbon. The report on cobbles compromised steps three to five.")),
        section("Shopping",
            fig("art-p047", 3.8),
            P("Every purchase need not support running.", "first"),
            P("When choosing a car, boot capacity may be discussed without arranging imaginary muddy shoes inside it."),
            P("When choosing a home, distance to a park may matter. It must not erase the roof, boiler or feelings of the other buyer."),
            P("When choosing a kettle, there is no race-day model.", "kicker")),
        activity("Quiz", "Buying-decision check",
            P("Ask:", "strong"),
            '<table class="yesno"><thead><tr><th></th><th></th><th>Yes</th><th>No</th></tr></thead><tbody>'
            + "".join(f'<tr><td class="n">{n}</td><td class="t">{t}</td><td class="bx"><span class="box"></span></td><td class="bx"><span class="box"></span></td></tr>'
                      for n, t in enumerate([
                          "Would I want this if I stopped running for one month?",
                          "Have I described it as an investment?",
                          "Does the claimed saving involve seconds?",
                          "Am I comparing £12 of normal spending with £180 of running spending?",
                          "Did a person in a vest review it online?"], 1))
            + '</tbody></table>',
            score("Yes answers", 5),
            note="Three yes answers require a twenty-four-hour pause."),
        section("Family events",
            P("Family events are fixed points, not obstacles placed by people who failed to consult your plan.", "first"),
            P("If a long run and a birthday lunch occupy the same morning, available solutions include running earlier, running shorter, moving the run or missing it. ‘Arrive during pudding in compression tights’ has been removed from the approved list."),
            P("Never ask an entire family to move Christmas lunch because you need four hours between food and running. Christmas has seniority."),
            casenote("Dr Hughes accepts that turkey can be dry. This does not make it performance nutrition.")),
        activity("Field exercise", "Other people’s weekends",
            P("Ask somebody what they did at the weekend."),
            P("While they answer, keep attention on their account. Do not rank the activities by training benefit."),
            P("If they walked, it was a walk. If they cycled, it was a cycle. If they did nothing, they did not have a recovery day unless they choose that term."),
            P("At the end, ask one follow-up question drawn from what they actually said."),
            field("Their weekend, in their words", 5),
            field("Your follow-up question", 2),
            note="Do not reward yourself by explaining your Sunday run. The exercise is complete when the "
                 "conversation ends and your route remains unknown."),
    ])


def chapter_5():
    return "".join([
        chapter("05", "Equipment, Economics and Other Symptoms", "art-p051", 4.33, id="ch5"),
        section("The shoe rotation",
            P("One pair became two because wet shoes need time to dry. Two became three because faster sessions require a different response. Three became five because mileage must be distributed across foam compounds.", "first"),
            P("You now maintain a shoe rotation with greater care than some people maintain friendships.", "kicker")),
        activity("Worksheet", "Inventory classification",
            P("For each pair, record:", "strong"),
            '<table class="grid fill"><thead><tr><th>Purchase price</th><th>Current mileage</th><th>Intended session</th>'
            '<th>Reason it cannot yet be discarded</th><th>Whether the reason includes gardening</th></tr></thead><tbody>'
            + "<tr><td></td><td></td><td></td><td></td><td></td></tr>" * 6 + "</tbody></table>",
            note="Shoes retired ‘for gardening’ but stored in their original box remain active members of the rotation."),
        section("Carbon-plated economics",
            '<table class="grid vs"><colgroup><col style="width:38%"><col style="width:62%"></colgroup>'
            '<thead><tr><th>Normal purchase</th><th>Carbon-plated shoe</th></tr></thead><tbody><tr>'
            '<td>A normal purchase loses value when it costs more.</td>'
            '<td>A carbon-plated shoe gains value because the price can be divided by a hoped-for improvement that has not happened yet.</td>'
            '</tr></tbody></table>',
            P("You may say the shoe will ‘pay for itself on race day’. No organiser currently offers a cash prize for finishing three minutes faster than your previous attempt. The phrase has been suspended.")),
        activity("Pattern test", "Comparative reasoning test",
            table(["", "Item", "Price", "Reaction"], [
                ["1", "Airport sandwich", "£9", "Outrage. Civilisation is collapsing."],
                ["2", "Race photograph", "£24", "Expensive, but the feet are both off the ground."],
                ["3", "Daily shoes", "£140", "Sensible. High mileage."],
                ["4", "Race shoes", "£220", "Investment."],
                ["5", "Partner’s suggested hotel upgrade", "£35", "We only sleep there."],
            ], cls="numcol roomy", widths=["7%", "33%", "13%", "47%"]),
            note="The patient should study the pattern until discomfort begins."),
        activity("Exercise", "The watch upgrade",
            P("Your current watch measures time, distance, heart rate, elevation, sleep, recovery and several things you cannot define without opening the app."),
            P("The new watch measures all of these more brightly."),
            P("Before upgrading, write down the decision the new metric will change. ‘It will be useful to know’ is not a decision. ‘Battery life’ is accepted only if your present watch is regularly dying rather than merely reaching 38 per cent."),
            field("The decision the new metric will change", 3),
            casenote("Alex justified an upgrade using maps, then continued running the same loop from home.")),
        section("Gels in civilian locations",
            P("Energy gels appear gradually around a household.", "first"),
            P("One enters a kitchen drawer. Two live in the car. An expired citrus gel remains in a coat pocket because throwing it away would waste 22 grams of carbohydrate."),
            P("Partners may mistake these for food. Clarify only if asked."),
            fig("art-p057", 3.9)),
        activity("Search and dispose", "Disposal exercise",
            P("Find every gel that is:", "strong"),
            checklist(["expired,", "a flavour you actively dislike,", "left over from a race two years ago,",
                       "damaged,", "kept ‘for emergencies’ in a building containing a kitchen."]),
            '<div class="tally"><span class="lab">Gels found</span>' + '<span class="tallybox"></span>' * 1 + '</div>',
            note="Dispose of them. Do not consume all five during the exercise to avoid waste."),
        activity("Worksheet", "Race fees",
            P("Race entries occupy a protected part of the budget where normal arithmetic cannot reach them."),
            P("The fee pays for a closed road, a measured route, medical support, a medal, timing and the privilege of doing publicly what you often do free. This can be worthwhile. The problem begins when entering becomes the treatment for feeling uncertain about the races already entered."),
            P("List every confirmed event. Beside each, record travel, accommodation, food and the conversation in which Sam first heard about it.", "strong"),
            '<table class="grid fill"><thead><tr><th>Event</th><th>Travel</th><th>Accommo&shy;dation</th><th>Food</th>'
            '<th>Where Sam first heard</th></tr></thead><tbody>'
            + "<tr><td></td><td></td><td></td><td></td><td></td></tr>" * 5 + "</tbody></table>",
            note="If the final column says ‘confirmation email’, apologise before entering another."),
        section("Domestic kit and marginal gains",
            fig("art-p053", 3.8),
            '<h4>Domestic kit boundary</h4>',
            P("Running objects require a defined habitat.", "first"),
            '<table class="answers"><tr><td class="ok">✓</td><td>Suitable locations include one drawer, one shelf, one basket and one negotiated section of the hallway.</td></tr>'
            '<tr><td class="x">✗</td><td>Unsuitable locations include every radiator, the backs of dining chairs, the oven handle, the bathroom floor and Sam’s side of the bed.</td></tr></table>',
            P("A hydration vest hanging from a bedroom door may appear harmless. At 03:00 its silhouette resembles a small tactical intruder and has consequences for the whole household."),
            '<h4>Marginal gains at home</h4>',
            P("The phrase marginal gain allows a tiny possible benefit to defeat a large obvious inconvenience.", "first"),
            P("Examples include preparing beetroot in a white kitchen, wearing nasal strips that frighten the children and going to bed at 20:45 while insisting the household continue normally in silence."),
            P("Before introducing a marginal gain, calculate the domestic loss. A two-second improvement does not automatically outrank sharing a Friday evening. The Service has checked.")),
    ])


def chapter_6():
    return "".join([
        chapter("06", "Advanced Social Exposure", "art-p061", 3.55, id="ch6"),
        section("When somebody else runs",
            P("Another person may run.", "first"),
            P("This can occur without reducing the significance of your own running. You are not required to establish who runs farther, earlier, faster or with less cushioning."),
            P("When they share a result, say ‘Well done.’", "kicker"),
            P("Do not immediately ask whether the course was short. Do not inspect their activity for pauses. Do not explain that your own result happened during a heavier training week."),
            P("The words ‘Well done’ remain accurate even when their watch model is inferior.")),
        section("The faster runner",
            fig("art-p063", 3.4),
            P("Exposure to a faster recreational runner may produce defensive context.", "first"),
            P("Common symptoms include mentioning age categories, elevation, recent illness, accumulated fatigue, a missing pacer and the fact that you were ‘never really racing it’."),
            '<div class="steps">'
            + "".join(f'<p>{t}</p>' for t in ["Listen to the result.", "Congratulate the runner.",
                                              "Allow the number to remain smaller than yours."])
            + '</div>',
            P("If asked about your own PB, answer. If not asked, the record remains safe where it is."),
            casenote("Dr Hughes notes that a personal best survives periods in which it is not spoken aloud.")),
        activity("Phrasebook", "The non-runner who says running is boring",
            P("Some people do not enjoy running. Rehabilitation requires you to treat this as preference rather than error."),
            '<table class="grid vs avoid"><colgroup><col style="width:60%"><col style="width:40%"></colgroup>'
            '<thead><tr><th>Avoid</th><th>Say</th></tr></thead><tbody><tr><td>'
            + '<table class="fails">' + "".join(f'<tr><td class="x">✗</td><td>{t}</td></tr>' for t in [
                "‘You’re going too fast.’", "‘You need proper shoes.’", "‘Once you get past the first month…’",
                "‘Have you tried parkrun?’", "‘It’s more mental than physical.’",
                "A personal history beginning during lockdown."]) + '</table>'
            + '</td><td class="say-cell"><span class="ok">✓</span> ‘Fair enough.’</td></tr></tbody></table>',
            note="This phrase may feel like abandoning a recruitment opportunity. The other person experiences it as lunch."),
        section("Injury conversation",
            P("An injury is painful, frustrating and capable of making running occupy even more conversation than running did.", "first"),
            P("You may tell close people how you feel. You may ask for support. The Service distinguishes this from issuing daily tissue updates to colleagues."),
            P("When resting, do not introduce yourself as ‘currently injured’. Your name remains available."),
            fig("art-p065", 4.2)),
        activity("Reference", "Injury disclosure levels",
            '<table class="levels"><tr><td class="lv">Close circle</td><td>'
            '<p><b>Partner or close friend:</b> Feelings, diagnosis, plans and reasonable detail.</p>'
            '<p><b>Running friend:</b> The above, plus speculation neither of you is qualified to make.</p></td></tr>'
            '<tr><td class="lv">Everybody else</td><td>'
            '<p><b>Colleague:</b> ‘My calf is playing up.’</p>'
            '<p><b>Person delivering a parcel:</b> No disclosure.</p></td></tr></table>',
            note="When resting, do not introduce yourself as ‘currently injured’. Your name remains available."),
        activity("Exercise", "The test run",
            P("A test run is a short, cautious attempt to assess recovery."),
            P("It is not twelve miles with a faster final section."),
            P("Before leaving, state the maximum duration aloud to Sam. Return at that time. If pain appears, stop. Do not negotiate with the pain using promises about pace."),
            P("Afterwards, describe the outcome once."),
            '<table class="log"><tr><td>Maximum duration stated</td><td class="wl"></td><td>Time returned</td><td class="wl"></td></tr></table>',
            casenote("Alex’s first test run lasted 74 minutes because the calf ‘needed enough data’. Dr Hughes requested a second opinion from the calf.")),
        section("Bad-weather group conversation",
            fig("art-p068", 4.3),
            P("During severe weather, runners gather around one central question: whether going out proves admirable commitment or poor judgement.", "first"),
            P("You are not required to answer publicly."),
            P("If official advice says avoid unnecessary travel, do not post a windswept photograph with the words ‘No excuses’. The fire service has other uses for its afternoon."),
            P("A treadmill session does not require an apology. A rest day does not require quotation marks."),
            P("Weather cannot see your activity and will not feel defeated.", "kicker")),
        activity("Checklist", "Race week",
            P("Race week narrows the conversational field."),
            P("You may become interested in forecasts that do not yet exist, carbohydrate sources you do not normally eat and the exact health of your throat. Every person who coughs becomes an active threat."),
            P("Race-week limits", "strong"),
            checklist(["One weather update per day.",
                       "One shoe decision, reversible only for actual damage.",
                       "No public throat reports.",
                       "No asking colleagues whether the office feels warm.",
                       "No announcing the final toilet visit.",
                       "No use of ‘the hay is in the barn’ unless you own either."]),
            note="Sam may withdraw conversational services forty-eight hours before the start."),
        section("After the race and other people’s big news",
            '<h4>After the race</h4>',
            P("A race deserves celebration. It does not require a director’s commentary before the medal is cool.", "first"),
            P("Use the three-stage debrief."),
            '<table class="stages">'
            '<tr><td class="sn">1</td><td><b>Immediate:</b> ‘I’m pleased. It was hard.’</td></tr>'
            '<tr><td class="sn">2</td><td><b>Later, to interested people:</b> the best moment, the difficult moment, the result.</td></tr>'
            '<tr><td class="sn">3</td><td><b>To running friends who explicitly ask:</b> full operational release.</td></tr></table>',
            P("Do not confuse social-media engagement with a request for stage three. A thumbs-up from Pat means well done, not ‘What happened at mile 19?’"),
            '<h4>Someone else’s big news</h4>',
            P("This is the final advanced exposure.", "first"),
            P("A friend announces an engagement, promotion, pregnancy, new home or major achievement."),
            P("Your task is to respond to their news without calculating how it affects:"),
            '<ul class="dash two-col">' + "".join(f"<li>{t}</li>" for t in [
                "weekend availability,", "the local route,", "race travel,", "alcohol before a long run,",
                "the date of the spring marathon,", "access to a spare room near an event."]) + "</ul>",
            casenote("Alex congratulated Pat on a new job and waited eleven full minutes before asking whether the office had showers. This remains Alex’s strongest recorded result.")),
    ])


def chapter_7():
    return "".join([
        chapter("07", "Relapse Prevention and Conditional Discharge", "art-p071", 3.4, id="ch7"),
        activity("Checklist", "Early warning signs",
            P("Relapse rarely begins with a full race report. It returns through small permissions."),
            checklist(["You start wearing the watch in the bath.",
                       "You call one run ‘a little leg loosener’.",
                       "You check kudos while somebody is speaking.",
                       "You buy shoes before admitting the old pair is fine.",
                       "You hear the word Sunday and inhale to speak."], "ruled"),
            P("Choose one person authorised to signal the return of symptoms. Agree on a neutral phrase such as ‘You’re doing the thing.’ Do not ask them to define the thing. You know.", "after"),
            field("Person authorised to signal"),
            fig("art-p075", 3.4)),
        section("The ‘just an easy one’ intervention",
            fig("art-p073", 4.5),
            P("The phrase appears modest. It contains distance, pace and a pre-emptive defence against an accusation nobody made.", "first"),
            P("When you feel it approaching, choose one alternative:"),
            '<table class="options">' + "".join(
                f'<tr><td class="bx"><span class="box round"></span></td><td>{t}</td></tr>'
                for t in ["‘I went for a run.’", "‘I was out for a bit.’", "‘Yes, it was nice.’", "Silence."]) + '</table>',
            P("If the distance matters, the other person will ask."),
            P("If they do not ask, place it carefully back inside yourself.", "kicker")),
        activity("Examination · Part A", "Final examination: short answers",
            P("Complete the following without assistance.", "strong"),
            "".join(f'<div class="q"><div class="qn">{n}</div><div class="qt">{t}</div>{lines(k)}</div>' for n, t, k in [
                (1, "Pat asks, ‘Busy weekend?’ Maximum answer before returning the question: two sentences.", 3),
                (2, "Sam suggests a hotel with no obvious running route. Name three relevant features before opening a map.", 3),
                (3, "Another runner shares a faster PB. Write the two-word response.", 1),
                (4, "Your watch describes your sleep as poor. You feel fine. Choose which source controls the first ten minutes of your morning.", 2),
                (5, "Rain is forecast. Discuss it without using the words refreshing, skin or waterproof.", 3),
            ]),
            instr="Part A: Short answers", cls="exam"),
        activity("Examination · Part B", "Final practical assessment",
            checklist(["Place your watch face-down for fifteen minutes.",
                       "Ask another person about their week.",
                       "Listen until they finish.",
                       "Ask one follow-up question.",
                       "Do not turn the result into an activity."]),
            score("Tasks completed", 5)),
        activity("Results", "Results",
            '<table class="results">'
            '<tr><td class="rk">Five successful tasks</td><td>Conditional discharge approved. You may return to normal conversation with monthly self-assessment.</td></tr>'
            '<tr><td class="rk">Three or four</td><td>Discharge approved under supervision. Sam retains emergency interruption powers.</td></tr>'
            '<tr><td class="rk">One or two</td><td>Repeat Stage Three. Remove Strava from the home screen for seven days.</td></tr>'
            '<tr><td class="rk">Zero</td><td>You have probably challenged the validity of the examination. Return to referral.</td></tr>'
            '</table>',
            note="No result affects race eligibility, which is fortunate because you entered another one during Part B."),
        """
<section class="certificate" id="certificate">
 <div class="cert-outer"><div class="cert-inner">
  <div class="cert-org">Normal Conversation Rehabilitation Service</div>
  <div class="cert-title">Certificate of<br>conditional discharge</div>
  <p class="cert-c">This certifies that</p>
  <div class="cert-name"></div>
  <p class="cert-c">has completed the Normal Conversation Rehabilitation Programme and demonstrated a temporary ability to:</p>
  <ul class="cert-list">
   <li>answer a simple question,</li><li>leave the wrist alone,</li><li>hear another person’s news,</li>
   <li>eat without fuelling,</li><li>experience weather privately,</li>
   <li>and describe a run using fewer words than the run contained steps.</li>
  </ul>
  <p class="cert-c">Discharge remains conditional upon continued avoidance of unsolicited split analysis.</p>
  <table class="cert-sign"><tr>
   <td><div class="sig">Dr Hughes</div><div class="sig-l">Signed</div></td>
   <td><div class="sig"></div><div class="sig-l">Date</div></td></tr></table>
  <p class="cert-next"><b>Next review:</b> The moment somebody says, ‘Did you get out this morning?’</p>
 </div></div>
</section>
""",
        activity("Cut-out card", "Emergency conversation card",
            P("Keep this page available during high-risk social situations."),
            '<table class="ifthen">' + "".join(f'<tr><td class="if">{a}</td><td class="then">{b}</td></tr>' for a, b in [
                ("If asked how you are", "‘Fine, thanks. How are you?’"),
                ("If asked about the weekend", "‘Good, thanks. Fairly quiet. What did you do?’"),
                ("If asked whether you ran", "‘Yes, I did.’ Wait."),
                ("If somebody mentions a race", "Ask about their experience before describing yours."),
                ("If your watch vibrates", "Nothing in the conversation has changed."),
                ("If you begin drawing a hill in the air", "Lower the hand and apologise."),
                ("If all measures fail", "‘I’ve made this about running again. Please continue.’"),
            ]) + '</table>', cls="cutout card"),
        section("Guidance for partners, friends and colleagues",
            fig("art-p079", 4.3),
            P("Recovery requires calm boundaries.", "first"),
            '<ul class="permits">' + "".join(f"<li>{t}</li>" for t in [
                "You may interrupt a split report.", "You may refuse to inspect a graph.",
                "You may schedule lunch without consulting the long-range forecast.",
                "You may treat race shoes as shoes when they are blocking the hallway."]) + "</ul>",
            P("Avoid debating whether the obsession is rational. The patient has charts and more free time than you realise."),
            P("Reward genuine progress by continuing the conversation. Do not reward it with running equipment."),
            P("If the patient goes seven days without saying ‘just an easy one’, acknowledge the achievement quietly. Public recognition may be uploaded.")),
        """
<section class="finalnote">
  <h2 class="fn-h">Final case note</h2>
  <figure><img src="art/art-p080.png" style="width:3.2in"></figure>
  <p class="first">Alex completed the programme at 15:42 on a Thursday.</p>
  <p>During the closing conversation, Alex asked Dr Hughes about the weekend and listened to the entire answer. The watch remained beneath a sleeve. No route was shown. No pace was supplied.</p>
  <p class="kicker">Discharge was approved.</p>
  <p>Alex walked home, recorded the activity, titled it ‘Easy one after a big block’ and added that recovery is as important as training.</p>
  <p class="kicker">The Service will reopen the file on Monday.</p>
  <div class="colophon">
    <div class="col-h">Colophon</div>
    <p>Issued by the Normal Conversation Rehabilitation Service.</p>
    <p>No kilometres were discussed during typesetting.</p>
    <p>One was nearly mentioned in the acknowledgements and has been removed.</p>
  </div>
</section>
""",
    ])


def notes_page():
    return '<section class="notes"><h2 class="fn-h">Notes</h2>' + lines(21) + "</section>"


def body():
    return "".join([front_matter(), '<div class="mainmatter">',
                    chapter_1(), chapter_2(), chapter_3(), chapter_4(),
                    chapter_5(), chapter_6(), chapter_7(), "</div>"])
