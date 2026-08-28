---
id: workflow-start-tracker
type: workflow
status: stable
domain: ai_os
updated: 2026-08-04
summary: "Set up a running register of things that change over time: clients and invoices, applications, subscriptions, contacts, deadlines. Fixed columns, one row per thing, a closed status vocabulary."
triggers: "track my clients, keep track of, a list of, who owes me, register, log of, spreadsheet, invoices, applications, subscriptions, deadlines, tracker"
expose: true
---

# Workflow: Start a Tracker

Use when the user wants to keep track of a set of things that change over time, rather than run a project. Clients and what they owe. Job applications. Subscriptions. Contacts at a company. Deadlines. Anything where the natural question is "what is the current state of all of them".

**Triggers:** track my clients, who owes me money, keep a list of, a register of, log of, invoices, applications, subscriptions, deadlines, renewals.

---

## Why this is its own workflow

[[System/Skills/Workflows/Start New Effort|Start New Effort]] sets up a project: a goal, a scope, next actions, a finish line. A tracker has none of those. It has rows, and it is never finished.

Handled as an effort, a tracker ends up with an invented structure that the next person changes, so two months of entries stop being comparable. The point of this note is that the shape is decided once, before the first row.

---

## Decide these five things before writing anything

Ask where you can. Each one is cheap to answer now and expensive to change after fifty rows.

**When you cannot ask**, because the request arrived by message, or they asked for it and left, or they plainly do not want five questions before anything exists: use the defaults in the next section, build it, and say in one line what you assumed. Do not stall waiting for answers. An empty tracker with a stated guess in it is easy to correct; nothing at all is not, and "I need five decisions from you first" is how a good idea dies on a Tuesday evening.

1. **What is one row?** One client, or one invoice? One application, or one company? Pick the smaller thing: rows can always be grouped, but a row that means two things cannot be split later.
2. **What are the columns?** The fewest that answer the real question. Every column is something a person has to fill in forever.
3. **What is the status vocabulary?** A closed list of words, decided now. `draft, sent, overdue, paid, written off` is a good one because every row is in exactly one, and "still owed" is a rule over that list rather than another column.
4. **What is the one question this answers?** "How much am I owed and by whom." "Which applications need chasing this week." Write it at the top of the note. A tracker that does not answer a question stops getting updated.
5. **Dates: which ones matter?** Usually two, when it started and when it is due. A third is usually somebody being thorough rather than useful.

If the user does not know yet, say so in the note as an open question and leave the column out. An empty column invites invented data.

---

## Defaults, for when nobody is there to ask

Use these rather than stopping. They are the answers most people give, and every one of them is easy to change while the table is still empty.

| Decision | Default | Why this one |
|---|---|---|
| What is one row | The smaller thing: one invoice, not one client | Rows group upward, they never split downward |
| Columns | What it is, who it involves, one amount or quantity, one date, status, notes | Six is what fits on a phone screen |
| Status vocabulary | `open, waiting, done, dropped` | Fits almost anything, and every row is in exactly one |
| The question it answers | Take it from the words they used asking for it | "Track my invoices" answers "who owes me what" |
| Dates | Two: when it started, when it is due | A third is thoroughness, not usefulness |

Write the assumptions into the note under a heading called **Assumed, change freely**, in plain language, so the first thing they see is what to correct. Delete that heading once they have looked at it.

The one thing no default covers is real data. Rows still come from them, always.

---

## Then build it

- One note, in `Ideaverse/Efforts/[Name]/`, with the usual frontmatter. A tracker is an effort with `status: active`; its `next:` is whatever is due soonest.
- The table goes in the note itself. Markdown tables are fine well past a hundred rows and stay readable in Obsidian and on a phone.
- **Write the status vocabulary into the note**, next to the table, not just in the agent's head. The person filling in rows next month needs to see the allowed words.
- **Add a "How to use this" section in plain language**: how to add a row, what each status means, what happens when something is paid or closed. Written for the user, not for an agent.
- Leave the table empty rather than inventing sample rows. A fake client that looks real is worse than a blank table.
- Add a routing row to [[Maps & Manuals/Active Context|Active Context]] so the questions this answers jump straight here.
- Run `python3 System/scripts/build_views.py` so it appears in the index.

---

## When a table stops being enough

Move to structured data only when one of these is true, and not before:

- It needs to be sorted or filtered in ways a person cannot do by eye.
- It feeds something else: an invoice document, a report, a chart.
- It has grown past a few hundred rows.

Then see [[System/Skills/Workflows/Convert Note to Structured Data|Convert Note to Structured Data]]. Until then a table in a note beats a spreadsheet, because it lives next to the context that explains it.

---

## What not to do

**Do not invent rows.** If the user has not given real clients, amounts or dates, the table stays empty and the first next action is to fill it in together. Every other rule in [[Maps & Manuals/Me|Me]] about not inventing facts applies hardest here, because a tracker looks authoritative.

**Do not add a column because it might be useful.** Ask what question it answers. If there is no answer, leave it out.

**Do not let two trackers cover the same thing.** Check [[Ideaverse/Efforts/Efforts Index|Efforts Index]] first. Merging two half-kept registers is worse than either.

---

## Related

[[System/Skills/Workflows/Start New Effort|Start New Effort]] | [[System/Skills/Workflows/Convert Note to Structured Data|Convert Note to Structured Data]] | [[System/Skills/Data Models/YAML Metadata Standard|YAML Metadata Standard]] | [[Maps & Manuals/Me|Me]]
