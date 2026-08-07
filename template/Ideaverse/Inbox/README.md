# Inbox

Drop files here. Tell me "process the inbox" and I will handle the rest.

---

## How it works

1. Drop any file into this folder: notes, articles, PDFs, transcripts, ideas, CVs, documents.
2. Open a Cowork session and say "process the inbox."
3. I read everything here, route each item to the right place, and summarize what I did.
4. Raw source files (exports, JSONs, binaries) that have been fully processed go to `Ideaverse/Archive/[YYYY-MM] - [Project Name]/`. This folder should be empty after each processing session.

## Best formats

- `.md` or `.txt`, read instantly, no conversion needed
- `.pdf`, works well
- `.docx`, works with conversion
- `.pages`, requires extra work, prefer exporting to PDF first

## What I will do with each item

I will infer the task type from the content and file name:
- Raw notes or ideas → [[System/Skills/Workflows/Capture|Capture]] into Sources, or directly into an Effort if the context is clear
- Articles or references → Sources, flagged for [[System/Skills/Workflows/Process Source into Atlas|Process Source into Atlas]]
- People (CVs, bios) → `Atlas/People/`
- Tasks or requests you wrote down → I will execute them

If a file has a note at the top like `TASK: [what you want me to do]`, I will follow that instruction instead of inferring.

## Tip

You can also add a simple text file with a task description, like:

```
TASK: Capture this article and link it to the Startup Ideas effort.
[article text below]
```
