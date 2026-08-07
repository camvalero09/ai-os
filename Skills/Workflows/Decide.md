---
id: workflow-decide
type: workflow
status: stable
domain: ai_os
updated: 2026-08-02
summary: "Work through a decision: options, tradeoffs, reversibility, next step."
triggers: "work through a decision, compare options, tradeoffs, what should I do"
expose: claude_code
---

# Workflow: Decide

Use when the user needs help making a decision.

---

## Steps

1. Clarify the decision if it is not explicit.
2. Generate several genuinely distinct options before narrowing, not just the first one or two that come to mind. Include at least one option that isn't an obvious variant of another (e.g. "do nothing," "delay," or a structurally different approach). Then list them.
3. Identify what matters most (criteria).
4. Map tradeoffs, risks, and opportunity costs.
5. Separate reversible from irreversible choices. Flag irreversible ones explicitly.
6. Note what information is missing.
7. Give a clear recommendation with reasoning. Do not be overconfident.
8. Identify the smallest next step.

---

## Output format

```
## Decision: [What is being decided]

**Options:** [list]
**Criteria:** [what matters most]
**Tradeoffs:** [table or list]
**Key risks:** [what could go wrong]
**Reversibility:** [what is locked in vs adjustable]
**Missing information:** [what would change the recommendation]
**Recommendation:** [clear, not overconfident]
**Next step:** [one concrete action]
```

---

## Asking the user to choose

Whenever the decision comes back to the user, use this shape every time. Same order, same fields. Added 2026-08-02, adapted from gstack.

```
D1, [one-line question title]
Context: [one sentence grounding him in what this is about]
In plain words: [2 to 4 sentences a non-specialist could follow, naming the stakes]
If we pick wrong: [one sentence on what actually breaks]
Recommendation: [option] because [one-line reason]

A) [option] (recommended)
   + [concrete, observable upside]
   - [honest downside]
B) [option]
   + [upside]
   - [downside]

Net: [one line on what he is really trading off]
```

**Number the questions.** First is D1, then D2. He answers "D2: B" and there is no ambiguity about which question he means.

**Five supporting rules:**

- **Score coverage, never kind.** If options differ in how much they cover, score each out of 10. If they differ in kind, two genuinely different approaches, write "these differ in kind, not coverage, so no score" and give none. A filler score is worse than no score. This matters most on legal, property and financial decisions, where a fake number reads as rigour.
- **One issue, one question.** Never bundle separate decisions into a single ask.
- **Five or more options: split, never drop.** Ask one question per option using four buckets: Include, Defer, Cut, Hold. Never merge or silently drop an option to make the list shorter.
- **Label effort twice.** "by hand: about 2 days / with an agent: about 15 minutes." It makes cheapness visible at the moment of deciding, which changes what is worth doing at all.
- **Irreversible choices need a typed confirmation.** See rule 1 in [[Maps & Manuals/Me|Me]].

---

## For high-stakes decisions

If the decision involves money, career, legal matters, health, or migration, always separate:
- Facts (what is confirmed)
- Assumptions (what is being inferred)
- Risks (what could go wrong)
- Unknowns (what is genuinely not known)
- Recommended next step

Do not give fake certainty. Do not optimize only for money. Include stress, time, emotional cost, and optionality.

---

## Related

[[Maps & Manuals/Skill Map|Skill Map]] | [[Maps & Manuals/Me|Me]]
