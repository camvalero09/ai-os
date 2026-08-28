---
id: use-subagents
type: workflow
status: stable
domain: ai_os
updated: 2026-06-18
summary: "Protocol for deciding when and how to spawn subagents: decision criteria, briefing template, and patterns for parallel and sequential work."
triggers: "large input, many files, parallel subtasks, verify my own output, fresh eyes, review this work"
expose: true
---

# Use Subagents

A subagent is a separate Claude instance spawned to handle a specific subtask. It starts with no context from the parent session, it only knows what you explicitly tell it in its prompt.

---

## Decision criteria

Spawn a subagent when any of these are true:

### Volume
The input is too large to process accurately in one pass. Rough thresholds:
- More than ~50 pages of text to read and synthesize
- More than ~30 files to process
- A batch where holding all the content plus the task degrades output quality

When this is true: split the input into batches, assign one batch per subagent, run in parallel.

### Parallelism
The task has 2 or more independent subtasks where no subtask needs another's output before starting.

Examples from this vault:
- Processing 35 ChatGPT conversations into Atlas notes → each batch of 8-10 conversations is independent
- Creating 4 different vault skill notes → each note is independent
- Running QA checks on 20 Atlas notes simultaneously

When this is true: identify which subtasks are truly independent, spawn them all at once.

### Fresh eyes
You just produced something, a document, a set of vault notes, a script, and need it verified. You will miss your own errors. A subagent with no knowledge of your work finds more issues.

Use cases:
- Visual QA on a presentation you just built
- Fact-checking an Atlas note you just wrote
- Reviewing a SQL query or script for logic errors
- Verifying wikilinks in a batch of files you just edited

### Isolation
A subtask is complex enough that a clean context (no noise from the surrounding session) produces better output. Use this when a subtask is large and coherent enough to stand alone.

---

## When NOT to use a subagent

- Subtasks are sequential, B depends on A's output. Complete A first, then B.
- The task is small, a subagent briefing takes more effort than just doing the task.
- The subtask requires real-time context from the current session that cannot be captured in a written prompt.

---

## How to write a subagent prompt

The most important rule: **a subagent starts cold.** It has no memory of this session. Its prompt must be entirely self-contained. Do not say "based on what we discussed" or "continue from where we left off."

### Briefing template

```
CONTEXT
[2-4 sentences: what the vault is, what the user is working on,
why this specific task matters. Enough for a cold start.]

TASK
[One clear sentence: what this subagent must produce.]

INPUT
[Exact file paths, content to process, or data to work with.
If processing files: list them explicitly.]

OUTPUT
[What should exist when the subagent is done. Be specific:
file paths, format, what to write back to the parent session.]

CONSTRAINTS
[Any rules that apply: no bare wikilinks, YAML required,
summary field mandatory, no em-dashes, etc.]
```

### Example, batch synthesis

```
CONTEXT
This is the user's personal AI OS vault (Obsidian). I am processing
ChatGPT conversation history into Atlas notes. Atlas notes are
permanent, stable reference notes written in the user's own words.

TASK
Read the 8 conversations in the batch below and synthesize them
into one Atlas note covering startup validation frameworks.

INPUT
[paste batch content here, or reference exact file path]

OUTPUT
Write the Atlas note to:
Ideaverse/Atlas/Startup Validation Framework.md

Include YAML frontmatter with: id, type: atlas, status: draft,
domain: startup, updated: today's date, summary: one sentence.
Use full vault-relative wikilinks: [[Folder/Note|Display Name]].

CONSTRAINTS
- No bare [[Note Name]] wikilinks
- No em-dashes
- Write in plain, direct language, not corporate or AI-sounding
- If something is unclear from the source, note it explicitly
  rather than inventing content
```

---

## Parallel vs sequential patterns

### Parallel (run all at once)

Use when all subtasks are independent:

```
Spawn subagent A → batch 1 of conversations
Spawn subagent B → batch 2 of conversations   ← simultaneously
Spawn subagent C → batch 3 of conversations

Wait for all three to complete.
Merge outputs, verify consistency.
```

### Sequential (wait for each result)

Use when a later task depends on an earlier one:

```
Step 1: Spawn subagent to extract raw data from source files.
Wait for result.

Step 2: Using that result, spawn subagent to synthesize into Atlas note.
Wait for result.

Step 3: Spawn subagent to verify the Atlas note against source.
```

### Fan-out + verify pattern

Best for large synthesis tasks (this is what was used for the ChatGPT processing):

```
1. Parent: split input into N batches
2. Parent: spawn N subagents in parallel (one per batch)
3. Subagents: each processes its batch independently
4. Parent: collects all outputs
5. Parent: spawns one more subagent for QA / consistency check
```

---

## After subagents complete

- Review all outputs before accepting them into the vault
- Run lint script to verify no bare wikilinks or missing YAML were introduced
- Commit to git after a successful batch: `git add -A && git commit -m "..."`

---

## Related

[[Maps & Manuals/Me|Me]] (When to use subagents) | [[System/Skills/Tools/Vault Lint|Vault Lint]] | [[System/Skills/Workflows/Vault Maintenance|Vault Maintenance]]
