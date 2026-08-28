---
id: create-vault-skill-note
type: tool
status: stable
domain: ai_os
updated: 2026-06-18
summary: "Write a new skill note so it triggers correctly and stays within the startup budget."
triggers: "add a skill, create a skill note, document how to use a tool, teach agents how to do X"
expose: true
---

# Create Vault Skill Note

Use this when adding a new capability to the vault, a new tool, library, workflow pattern, or repeatable process that agents should know how to use proactively.

**Triggers:** "add a skill for X", "document how to use Y", "create a skill note", "teach agents how to do Z."

---

## When to create a skill note

Create one when:
- A tool or library will be used more than once (docx, a database client, a new API)
- A process has more than 3 steps and needs to be done consistently
- An agent keeps making the same mistake on a task, encode the fix
- A new capability should be triggered automatically without the user having to explain it

Do not create one when:
- The task is one-off and unlikely to repeat
- The content is already covered by an existing skill note
- It belongs in Atlas (stable knowledge) or an Effort (active project context) instead

### The second-time rule

The list above says when a skill note is warranted. This says when to raise it, because the usual failure is not disagreeing about the rule, it is nobody noticing the moment has arrived.

**The second time you handle something ad hoc, offer to save it as a workflow.** Not the first, because one occurrence is not a pattern and the vault fills with notes nobody reads. Not the fifth, because by then the method has been reinvented four times, each slightly differently, and the version written down is whichever one happened last.

The trigger is noticing you have done this before. The offer is one sentence at the end of the task, never an interruption in the middle:

> "That is the second time we have done X this way. Want me to save it as a workflow so the next session starts from it?"

Then wait. No is a normal answer, and asking again about the same thing is nagging. Record the refusal so the next session does not re-ask.

**If the answer is yes,** write the note from what actually happened, not from what should have happened. The value sits in the specifics that were surprising, the dead ends, and the checks that caught something. A workflow that reads like a tidy summary of an idealised process teaches nothing a reader could not have guessed.

**Where it goes decides who gets it.** A workflow about this person's own work goes in the vault's own `Skills/`. One that would help anyone goes upstream, where every installation receives it. If it names an employer, a client, a property or a family member, it is not general yet. See [[System/Skills/Tools/Update System|Update System]].

This convention exists because the vault already grew this way, handling something ad hoc and formalising it later, but with nothing naming the moment. It was left to whether an agent happened to remember.

---

## Standard structure

Every skill note follows this structure:

```markdown
---
id: skill-id-in-kebab-case
type: tool               # or: workflow, data_model, template
status: stable           # or: draft, active
domain: ai_os            # or: fraud, career, personal_finance, etc.
updated: YYYY-MM-DD
summary: "One sentence: what this note enables an agent to do."
triggers: "words or phrases that should make an agent reach for this skill"
---

# Skill Name

One sentence describing what this skill does and when to use it.

**Triggers:** comma-separated list of words or phrases that should cause an agent
to read this note before starting the task.

---

## Install (if needed)

bash/npm install commands.

---

## [Main sections]

Core instructions. Code snippets. Critical rules and pitfalls.
Use headers to separate distinct sub-tasks.

---

## Output location (if the skill produces files)

Where to save output. Naming convention.
```

The date lives in `updated:` at the top and nowhere else. A second copy at the
foot of the note is one more thing to keep in step, and it does not stay in step.

---

## What makes a good trigger list

The `triggers:` field in the skill note's frontmatter is what makes a skill proactive: it feeds the generated Skill Map table and, together with `expose: claude_code`, the generated Claude Code loader in `.claude/skills/`. A good trigger list:

- Uses the words the user actually says, not technical terms they would not use
- Covers both explicit requests ("create a Word doc") and implicit ones ("write a letter to my landlord")
- Is specific enough not to fire on unrelated tasks
- Includes the file extension as a trigger (`.docx`, `.xlsx`, `.pdf`)

After writing the skill note, run `python3 System/scripts/build_views.py`: the Skill Map tables regenerate and, if the note has `expose: claude_code`, its loader is created automatically.

---

## Checklist before saving

- [ ] YAML frontmatter complete with `summary:`
- [ ] Trigger line clearly states when to use this skill
- [ ] Install commands included (if any dependencies)
- [ ] Critical rules and common pitfalls documented
- [ ] Output location specified (if the skill creates files)
- [ ] Related section added with wikilinks to Me.md, Skill Map, and any cross-referenced skills
- [ ] Any plain-text references to other vault notes inside the file converted to wikilinks
- [ ] `triggers:` set in frontmatter; `expose: claude_code` added if it should auto-load in Claude Code; `python3 System/scripts/build_views.py` run
- [ ] Lint script passes after saving ([[System/Skills/Tools/Vault Lint|Vault Lint]])

---

## Where to save

- `Skills/Tools/`, for tools, libraries, integrations, utilities
- `Skills/Workflows/`, for multi-step processes that coordinate across tools or vault notes
- `Skills/Data Models/`, for data standards, schemas, field definitions

---

## Related

[[Maps & Manuals/Me|Me]] (Proactive file creation) | [[Maps & Manuals/Skill Map|Skill Map]] | [[System/Skills/Data Models/YAML Metadata Standard|YAML Metadata Standard]] | [[System/Skills/Tools/Vault Lint|Vault Lint]]

---

## Write it short

State what to do, not how or why. Reasoning belongs in the Agent Log, not in the skill.

Add only what an agent could not work out from the files. Cut any sentence explaining something the model already knows.

Keep the body well under 500 lines. Split into files in the same folder when it grows, and link them one level deep from the skill note.

**`summary:` and `triggers:` are the expensive fields.** They are injected into every session for every exposed skill, and the combined listing is capped at 2% of the context window or 8,000 characters. Past the cap some skills are never offered and nothing says which. Write them in third person, name what the skill does and when it applies, and stop.

**Set `expose: true` only if the skill should trigger on its own.** An unexposed skill costs nothing at startup and is still reachable through Skill Map.

Source: [Anthropic skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices).
