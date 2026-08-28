---
id: workflow-office-hours
type: workflow
status: stable
domain: startup
updated: 2026-08-02
summary: "Adversarial startup diagnostic: six forcing questions, premise challenge, alternatives, one assignment."
triggers: "office hours, is this worth building, pressure test this idea, should I build this, forcing questions"
expose: false
---

# Workflow: Office Hours

Use when the user has a startup idea and needs it pressure-tested rather than developed. Adapted 2026-08-02 from the YC office hours skill in [gstack](https://github.com/garrytan/gstack), `office-hours/SKILL.md.tmpl` lines 127 to 274, MIT licence, with two fragments from its `plan-ceo-review` skill.

**Triggers:** office hours, is this worth building, pressure test this idea, run the questions on me, should I build this, startup session.

---

## Which workflow runs when

Four notes overlap here. Only one runs at a time.

| Situation | Use |
|---|---|
| An idea exists and the founder needs questioning, not the idea | This note |
| An idea exists and needs attacking from every angle, with a verdict at the end | [[System/Skills/Workflows/Roast\|Roast]] |
| A choice between options that are already understood | [[System/Skills/Workflows/Decide\|Decide]] |

This note is the session. Decide is for closing a choice once the options are clear.

**This note against Roast.** Office Hours interrogates the person: what evidence exists, who the actual human is, what the smallest wedge is. It ends in a diagnosis and one assignment, and it is the right choice when the founder has been fooling himself. Roast interrogates the idea with five parallel personas and ends in a GO, RESHAPE or KILL verdict. Neither generates an idea; both need one in hand.

---

## Posture

Non-negotiable for the whole session, and the reason this skill exists rather than living in an agent's memory.

**Specificity is the only currency.** A category is not a customer. "Everyone needs this" means nobody has been found.

**Interest is not demand.** Waitlists, signups and "that is interesting" do not count. Behaviour counts, money counts, and panic when it breaks counts.

**The founder's words are not the evidence. The buyer's words are.** There is almost always a gap between what a founder says the product does and what a user says it does. The user's version wins.

**The status quo is the real competitor.** Not the other startup and not the incumbent. The spreadsheet and the chat thread the buyer already lives with.

**Push once, then push again.** The first answer is the polished version. The real answer arrives on the second or third push. Comfort means the question has not gone deep enough.

**Be direct to the point of discomfort.** Diagnosis, not encouragement. Take a position on every answer and say what evidence would change it. The banned-phrase table in [[Maps & Manuals/Me|Me]] applies with full force here.

**Do not build anything.** The output is a written diagnosis. No code, no prototype, no scaffolding, not even a sketch of one.

---

## Step 1: Establish goal and stage

Ask both before anything else. Together they decide which questions get asked.

**Goal:** a startup, a consulting or services business, a side project, or learning. The first two get the hard questions. The others get a lighter, generative session.

**Stage:** pre-product (no users), has users but nobody paying, or has paying customers. A prototype nobody has used is pre-product.

---

## Step 2: The six forcing questions

One at a time. Stop after each and wait for the answer. Push until the answer is specific, evidence-based and uncomfortable. Skip a question only if an earlier answer already covered it.

**Routing by stage.** Pre-product: Q1, Q2, Q3. Has users: Q2, Q4, Q5. Has paying customers: Q4, Q5, Q6.

### Q1: Demand reality

**Ask:** "What is the strongest evidence you have that someone actually wants this, not 'is interested', not 'signed up for a waitlist', but would be genuinely upset if it disappeared tomorrow?"

**Push until you hear:** specific behaviour. Someone paying. Someone expanding usage. Someone building their workflow around it. Someone who would have to scramble if it vanished.

**Red flags:** "People say it's interesting." "We got 500 waitlist signups." "Investors are excited about the space." None of these are demand.

After the first answer, check three things before continuing. Are the key terms defined well enough to measure? What does the framing take for granted, and has that assumption been verified? Is the evidence actual pain or a thought experiment? "I think teams would want this" is hypothetical. "Three analysts spent ten hours a week on this" is real.

### Q2: Status quo

**Ask:** "What are your users doing right now to solve this problem, even badly? What does that workaround cost them?"

**Push until you hear:** a specific workflow. Hours spent. Money wasted. Tools duct-taped together. People hired to do it manually. Internal tools maintained by engineers who would rather be building product.

**Red flag:** "Nothing, there is no solution, that is why the opportunity is so big." If truly nothing exists and nobody is doing anything, the problem is probably not painful enough to act on.

### Q3: Desperate specificity

**Ask:** "Name the actual human who needs this most. What is their title? What gets them promoted? What gets them fired? What keeps them up at night?"

**Push until you hear:** a name, a role, and a specific consequence that person faces if the problem goes unsolved. Ideally something heard directly from that person.

**Red flags:** category-level answers. Industries, company sizes, job families. These are filters, not people, and you cannot email a category.

Do not collapse the stack into one ask. The pressure comes from asking all of it: whose career, whose day, what they are actually avoiding. Never let the answer stay at "users".

### Q4: Narrowest wedge

**Ask:** "What is the smallest possible version of this that someone would pay real money for this week, not after you build the platform?"

**Push until you hear:** one feature, one workflow. Possibly as small as a weekly email or a single automation, shippable in days rather than months.

**Red flags:** "We need to build the full platform before anyone can really use it." "We could strip it down but then it would not be differentiated." Both signal attachment to the architecture rather than the value.

**Bonus push:** "What if the user had to do nothing at all to get value? No login, no integration, no setup. What would that look like?"

### Q5: Observation and surprise

**Ask:** "Have you actually sat down and watched someone use this without helping them? What did they do that surprised you?"

**Push until you hear:** a specific surprise, something that contradicted an assumption. If nothing has surprised you, you are either not watching or not paying attention.

**Red flags:** "We sent out a survey." "We did some demo calls." "Nothing surprising, it is going as expected." Surveys lie, demos are theatre, and "as expected" means filtered through existing assumptions.

**The gold:** users doing something the product was not designed for. That is often the real product trying to emerge.

### Q6: Future-fit

**Ask:** "If the world looks meaningfully different in three years, and it will, does your product become more essential or less?"

**Push until you hear:** a specific claim about how the users' world changes and why that change makes the product more valuable. Not "AI keeps getting better so we keep getting better", which is a rising-tide argument every competitor can make.

**Red flag:** "The market is growing 20% per year." A growth rate is not a vision.

### If the user asks to skip the questions

Say once that the hard questions are the value, ask the two most critical for his stage, then move on. If he pushes back a second time, respect it and proceed. Do not ask a third time.

---

## Step 3: Name the failure pattern out loud

If one of these appears in an answer, say so directly rather than working around it: solution in search of a problem, hypothetical users, waiting to launch until it is perfect, assuming interest equals demand.

---

## Step 4: Challenge the premises

Before any solution is discussed, write the premises as numbered statements the user must agree or disagree with.

1. Is this the right problem? Would a different framing make it dramatically simpler or more valuable?
2. What happens if nothing is done? Real pain or hypothetical?
3. Is this the most direct path to the outcome, or is it solving a proxy for the real problem?

If he disagrees with a premise, revise and loop back. Never proceed on a premise he has rejected.

---

## Step 5: Map the dream state

From gstack's `plan-ceo-review`. One line, and it catches the trap where a fast-cash path quietly moves away from the thing actually wanted.

```
CURRENT STATE  --->  THIS CHOICE  --->  12-MONTH IDEAL
[describe]           [the delta]        [describe]
```

Does this choice move toward that ideal or away from it?

---

## Step 6: Force alternatives

Mandatory, never skipped, even when one option looks obviously right. Two approaches minimum, three preferred.

- One must be the **minimal viable** version: smallest thing that ships, fastest.
- One must be the **ideal** version: best long-term trajectory.
- One may be **lateral**: a different framing of the problem entirely.

**The first two carry equal weight.** Do not default to the smaller one because it is smaller.

For each: summary, effort labelled twice (by hand and with an agent), risk, two or three pros, two or three cons. Then a recommendation with a one-line reason. Then stop and let him choose, using the question format in [[System/Skills/Workflows/Decide|Decide]].

---

## Step 7: Write the diagnosis

Save to `Ideaverse/Outputs/YYYY-MM-DD - Office Hours - [Topic].md` using these headings:

```
Problem statement
Demand evidence
Status quo
Target user and narrowest wedge
Constraints
Premises (agreed / disagreed)
Approaches considered
Recommended approach
Open questions
Success criteria
Distribution path to the first 10 customers
The assignment
What showed up about how the founder thinks
```

Once a startup repository exists, design documents move there under rule 9 in [[Maps & Manuals/Me|Me]]. The method stays here; the records do not.

---

## Step 8: Give one assignment

Every session ends with exactly one concrete real-world action. An action, not a strategy, and not "go build it". Usually it is a conversation with a named human.

---

## What showed up about how the founder thinks

Note which of these appeared during the session and record them in the diagnosis. Across several sessions this becomes a record of founder behaviour that no single session can see.

Articulated a real problem someone actually has. Named specific humans rather than categories. Pushed back on a premise with reasoning rather than complying. Showed domain expertise from the inside. Showed taste, cared about getting the details right. Showed agency, was building rather than planning. Decided rather than deferring.

Record what was absent as well as what was present. An absent signal is the finding.

---

## Rules

- Never start building. The output is a written diagnosis.
- One question at a time. Never batch.
- The assignment is mandatory.
- If the user arrives with a fully formed plan, skip step 2 but still run steps 4 and 6. Premise challenge and forced alternatives are never skipped.
- End with a completion status per rule 6 in [[Maps & Manuals/Me|Me]]: done with the diagnosis written, partial with what is missing, or needs context with exactly what is unanswered.
- Any unanswered question goes into the diagnosis under open questions. Never default it silently.
- **Never run this workflow under `/goal`.** That command removes the per-turn stop: after each turn a separate model checks the condition and, if unmet, starts another turn without waiting. A turn ending in a question to the user reads as "condition not met", so the next turn answers the question on their behalf and the session produces a diagnosis about a founder who never spoke. Use `/goal` for the desk research a diagnosis feeds on, never for the diagnosis itself. Added 2026-08-02.

---

## Related

[[System/Skills/Workflows/Decide|Decide]] | [[System/Skills/Workflows/Roast|Roast]] | [[Maps & Manuals/Me|Me]] | [[Maps & Manuals/Skill Map|Skill Map]]
