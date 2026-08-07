---
id: workflow-roast
type: workflow
status: stable
domain: startup
updated: 2026-08-04
summary: "Convene a five-persona adversarial council on an idea, then deliver one GO, RESHAPE or KILL verdict with the cheapest test that de-risks it."
triggers: "roast, roast this idea, roast it, pressure-test this, stress-test this, convene the council, brutal second opinion, validate a business idea, tear this apart, before I build this"
expose: claude_code
---

# Roast

Convene a council of five independent persona agents who attack an idea from every angle, then deliver one honest verdict. Use it before sinking time and money into building the wrong thing.

**Triggers:** roast, roast this idea, pressure-test this, stress-test this, convene the council, brutal second opinion, validate a business idea, tear this apart.

Adopted 2026-08-04 from an outside skill, after a live test on a real thesis. The original text is preserved; the vault-specific mechanics are in "How this runs here".

---

## Which workflow runs when

Four notes overlap. Only one runs at a time.

| Situation | Use |
|---|---|
| An idea exists and needs attacking from every angle, fast, with a verdict at the end | This note |
| An idea exists and the founder needs to be questioned, not the idea | [[System/Skills/Workflows/Office Hours\|Office Hours]] |
| A choice between options that are already understood | [[System/Skills/Workflows/Decide\|Decide]] |

**The real distinction.** Office Hours interrogates the person: what evidence do you have, who is the actual human, what is the smallest wedge. Its output is a diagnosis and one assignment. Roast interrogates the idea and returns a verdict. Office Hours is better when the founder has been fooling himself. Roast is better when the idea is articulated and needs breaking.

**Roast cannot generate.** It only evaluates an idea already in hand. It will not find a problem worth solving, and running it on an idea that arrived without evidence produces five confident opinions about a guess.

---

## What this does

Claude's default is to agree with you. Roast is the opposite. Five independent persona agents tear an idea apart and build it up from every angle, then a Judge synthesises everything into one honest verdict.

The council is adversarial on purpose. No persona hedges or is polite. The point is to surface what the founder cannot see because he is too close to it.

---

## Step 1: Get the brief

If the request contains the idea, start there. Then ask a tight set of clarifying questions so the council has real context. Ask only what has not already been provided. Three or four questions maximum, in one batch:

1. **The idea** in one or two sentences: what it is, what it does.
2. **Who it is for** and **how it makes money**: the buyer, the price, the model.
3. **The edge**: relevant skills, audience, or assets already in hand.
4. **Constraints**: budget, timeline, how fast the first dollar is needed.

If the user says "just run it" or has already given enough, skip the questions and proceed. Do not over-interrogate. One round, then convene.

Write the brief into a single short paragraph, pasted into every council member's prompt so all five judge the same thing. **State in the brief what has not been validated**, in plain words: whether any buyer has been spoken to, and which numbers are public benchmarks applied to a hypothetical customer rather than real figures. Without that line the council treats borrowed numbers as facts and the verdict inherits the error.

---

## Step 2: Convene the council

Spin up **all five agents in parallel in a single message**, one call each, `subagent_type: general-purpose`, running synchronously so the Judge has every answer before writing. Paste the same brief into each, then give each its persona mandate.

Each council member returns: a one-line stance, their 3 to 5 sharpest points, the single most important thing the user must hear, and a 1 to 10 score on their own dimension, where 1 is walk away and 10 is a no-brainer.

**1. The Contrarian (Red Team)**
> You are the Contrarian on an idea council. Assume this idea fails. Your job is to find the fatal flaws, the fastest way it dies, and the load-bearing assumptions that are probably wrong. Be ruthless and specific. No hedging, no "but it could work." Attack the weakest points. THE BRIEF: [brief]

**2. The Expansionist (Bull)**
> You are the Expansionist on an idea council. Make the strongest possible case FOR this idea. Find the biggest upside, the 10x version, the adjacent opportunities and unlock points the founder isn't seeing. Fight for the potential. Be specific about where the real money and leverage could be. THE BRIEF: [brief]

**3. The Logician (First principles)**
> You are the Logician on an idea council. Use NO outside research and NO web. Reason purely from first principles: does the core mechanism make sense, do the incentives line up, is the underlying logic sound, does the math even work in theory? Strip it to fundamentals and tell us if it holds together. THE BRIEF: [brief]

**4. The Researcher (Evidence)**
> You are the Researcher on an idea council. Use web search. Bring real-world evidence: who the existing competitors are, market size or demand signals, what comparable products charge, whether this is validated by what's already out there or contradicted by it. Cite what you find. Is the real world saying yes or no? THE BRIEF: [brief]

**5. The Buyer (Voice of customer)**
> You are the Buyer on an idea council. Role-play the exact target customer described in the brief. React as them, in first person. Would you actually pay for this? What's your real objection? What would make you choose a competitor or just do nothing instead? What price feels right, and what would make you say yes today? Be the honest, slightly skeptical customer, not a cheerleader. THE BRIEF: [brief]

---

## Step 3: The Judge delivers the verdict

Once all five return, act as the Judge. Read every council member's findings, weigh them, and synthesise one decisive verdict. Do not average the scores. Name the real tension between the personas and resolve it.

Fold in the **economics lens**: rough pricing, realistic time to first dollar, and whether this can actually be shipped fast given the edge described.

Output the verdict in this exact shape:

```
## THE VERDICT: GO / RESHAPE / KILL
Confidence: [low / medium / high]

**The call in one line:** [the decision, plainly]

**Why:** [2-3 sentences resolving the council's tension]

**Biggest risk:** [the single thing most likely to kill it]
**Biggest upside:** [the strongest reason to do it]

**Money read:** [rough price, time-to-first-dollar, can they ship fast]

**The cheapest 48-hour test:** [the smallest, fastest thing they can do
to validate the riskiest assumption BEFORE building anything]

**If RESHAPE:** [the specific pivot that fixes the fatal flaw while keeping the upside]
```

Then list the five council scores in one line: `Contrarian X/10 · Expansionist X/10 · Logician X/10 · Researcher X/10 · Buyer X/10`.

**Where a council member contradicts something already written in the vault, say so explicitly in the verdict and name the note.** A roast that quietly leaves a wrong number standing in a committed file has cost more than it produced.

---

## Rules

- Every persona stays in character. None hedges or softens. The value is in the friction.
- The Judge must make an actual call. "It depends" is not a verdict. Pick GO, RESHAPE or KILL and own it.
- The cheapest 48-hour test is the most important output. It is how you find out if you are right without building the whole thing.
- Keep the final verdict skimmable. The council does the depth, the Judge does the decision.
- **Never run this under `/goal`,** for the same reason as [[System/Skills/Workflows/Office Hours\|Office Hours]]: a turn ending in a clarifying question reads as "condition not met" and the next turn answers on the user's behalf.

---

## How this runs here

Vault mechanics only. The council text above is unchanged.

**Outbound search consent.** The Researcher uses the web, so rule 2 in [[Maps & Manuals/Me\|Me]] applies: say what will be looked up and get a yes **before convening**, not after. Instruct the Researcher in its prompt to keep every query generic and industry-level, and to name no person, no employer tied to an individual, and no identifying detail from the brief.

**Evidence floor for the Researcher.** Its mandate asks "is the real world saying yes or no", which is a question that always returns an answer. Add to its prompt: say "nothing found" out loud rather than filling a gap with a plausible estimate, and mark each claim as sourced with a URL or as unverified. This is the confidence floor in [[Maps & Manuals/Me\|Me]] applied to a subagent, and in the first run it was the difference between a useful Researcher and a confident one.

**The scores are noise.** Five personas each scoring their own dimension produce numbers that do not combine. Report them because the format asks for them, and do not let them anchor the verdict.

**Output.** If the verdict is worth keeping, save it to `Ideaverse/Outputs/` as `YYYY-MM-DD - Roast - [Idea].md`. A verdict that only exists in chat dies with the session. Not every roast needs a file; one run on a passing thought does not.

---

## What the first run showed

Run on 2026-08-04 against a real thesis. Recorded so later runs are calibrated rather than trusting the format.

**The Buyer was the strongest persona and produced the finding that changed the verdict**, which was that the buyer's objection was system access and relationship risk with their largest customer, not price. This was the persona most likely to be cut on the argument that a simulated customer is the founder's own words in a costume. That argument still holds for demand validation: a role-played buyer cannot tell you anyone will pay. It is wrong about objections, where the persona is very good at surfacing the one nobody thought of.

**The Researcher earned its place** by finding two load-bearing facts that twenty manual searches the day before had missed: a competitor acquisition price that proved willingness to pay, and a funding history that undercut one of the three candidate markets.

**The Contrarian was the weakest.** It scored 3 out of 10 on assertion rather than evidence and treated "no buyer conversations yet" as a character defect rather than a stage. Read it for the failure modes it names, not for its score.

**Three of five converged independently on the same objection.** That convergence, not any single voice, was the actual signal. Watch for it in the Judge step.

---

## Related

[[System/Skills/Workflows/Office Hours\|Office Hours]] | [[System/Skills/Workflows/Decide\|Decide]] | [[System/Skills/Workflows/Use Subagents\|Use Subagents]] | [[Maps & Manuals/Me\|Me]] | [[Maps & Manuals/Skill Map\|Skill Map]]
