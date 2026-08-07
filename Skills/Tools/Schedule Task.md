---
id: schedule-task
type: tool
status: stable
domain: ai_os
updated: 2026-06-18
summary: "How to schedule recurring or one-time tasks on Mac using launchd (recommended) or cron, covering setup, common schedules, and management commands."
---

# Schedule Task

Use this when a task should run automatically on a schedule: daily briefings, weekly vault lint, recurring summaries, reminders, or any process that should happen without manual triggering.

**Triggers:** "every day", "each morning", "weekly", "schedule this", "run this automatically", "remind me", "set up a recurring task."

---

## Which tool to use

| Tool | Use when |
|---|---|
| **launchd** (recommended) | Recurring tasks on Mac, survives reboots, runs even after login, Mac-native |
| **cron** | Quick one-liners, Unix familiarity, simpler syntax |

---

## launchd (recommended for Mac)

launchd uses `.plist` XML files stored in `~/Library/LaunchAgents/`. Each file defines one job.

### Step 1, Create the plist file

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aios.vault-lint</string>         <!-- unique identifier -->

    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string><vault>/System/scripts/vault_lint.py</string>
    </array>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key><integer>1</integer>      <!-- 1=Monday, 0=Sunday -->
        <key>Hour</key><integer>9</integer>
        <key>Minute</key><integer>0</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>/tmp/vault-lint.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/vault-lint-error.log</string>

    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
```

Save to: `~/Library/LaunchAgents/com.aios.vault-lint.plist`

> **Trap: never point `StandardOutPath` or `StandardErrorPath` into a TCC-protected folder** (`~/Documents`, `~/Desktop`, `~/Downloads`, iCloud Drive). Keep them in `/tmp` or `~/Library/Logs/`, as the example above does.
>
> launchd opens those two files itself, before the program runs, and attributes the access to the job's program. If that program is not Apple-signed (any compiled wrapper, or a copied shell), macOS denies the open and the job dies with **exit 78 `EX_CONFIG`** having produced no output at all. The empty log files make it look like the job never fired.
>
> Diagnosed the hard way on 2026-07-29, when this pattern had silently killed the weekly maintenance job for 19 days. Note that probing with an Apple-signed binary like `/bin/echo` gives a false negative: it is allowed to write there, so the test passes while the real job still fails. Test with the actual program.
>
> Granting Full Disk Access to the program does **not** fix this. The denial is on launchd's redirect open, not on the program's own file access. A program that cannot get its stdout redirected may still write into `~/Documents` perfectly well once running.

### Step 2, Load and start

```bash
# Load the job (register it with launchd)
launchctl load ~/Library/LaunchAgents/com.aios.vault-lint.plist

# Run it immediately to test
launchctl start com.aios.vault-lint

# Check the output
cat /tmp/vault-lint.log
cat /tmp/vault-lint-error.log
```

### Step 3, Manage

```bash
# Stop the job
launchctl unload ~/Library/LaunchAgents/com.aios.vault-lint.plist

# Check if loaded
launchctl list | grep aios

# Remove permanently
launchctl unload ~/Library/LaunchAgents/com.aios.vault-lint.plist
rm ~/Library/LaunchAgents/com.aios.vault-lint.plist
```

---

## Common schedule patterns (launchd)

### Daily at a specific time

```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key><integer>8</integer>
    <key>Minute</key><integer>0</integer>
</dict>
```

### Weekly on Monday at 9am

```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Weekday</key><integer>1</integer>
    <key>Hour</key><integer>9</integer>
    <key>Minute</key><integer>0</integer>
</dict>
```

### Every N minutes

```xml
<key>StartInterval</key>
<integer>3600</integer>   <!-- seconds: 3600 = every hour -->
```

### Multiple times per day

```xml
<key>StartCalendarInterval</key>
<array>
    <dict><key>Hour</key><integer>8</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Hour</key><integer>20</integer><key>Minute</key><integer>0</integer></dict>
</array>
```

---

## cron (simpler syntax)

```bash
# Open crontab editor
crontab -e

# Format: minute hour day month weekday command
# Examples:
0 8 * * 1 python3 "<vault>/System/scripts/vault_lint.py"   # Every Monday 8am
0 9 * * * /usr/bin/python3 /path/to/script.py    # Every day at 9am
*/30 * * * * /path/to/script.py                  # Every 30 minutes

# View current crontab
crontab -l

# Remove all cron jobs
crontab -r
```

**Cron shorthand:**

| Expression | Meaning |
|---|---|
| `0 8 * * *` | Every day at 8:00am |
| `0 8 * * 1` | Every Monday at 8:00am |
| `0 9 * * 1-5` | Weekdays at 9:00am |
| `*/30 * * * *` | Every 30 minutes |
| `0 8,20 * * *` | 8am and 8pm daily |

---

## Recommended scheduled tasks for this vault

**Currently: none.** The vault deliberately schedules nothing on this machine.

The weekly maintenance launchd job was removed on 2026-07-29 after failing silently for 19 days. It is now a recurring Google Calendar event that reminds the user to run `/weekly-maintenance` by hand. See [[System/Skills/Workflows/Weekly Maintenance|Weekly Maintenance]].

**Prefer a calendar reminder over a scheduled job** when the task is a prompt a human should run anyway. A calendar event needs no permissions, cannot fail silently, is visible on the phone, and is trivial to hand to someone else. Reserve launchd for work that genuinely must happen unattended, and give it a health signal so its silence is not mistaken for success.

---

## Running a Python script as a scheduled task

The vault lint script can be run directly. First, make sure the VAULT path in the script points to the correct location:

```python
VAULT = Path("<vault>")
```

Then save it as a standalone `.py` file (copy the script from [[System/Skills/Tools/Vault Lint|Vault Lint]]) and reference that path in your plist or crontab.

---

## Related

[[Maps & Manuals/Me|Me]] (Proactive file creation) | [[Maps & Manuals/Skill Map|Skill Map]] | [[System/Skills/Tools/Vault Lint|Vault Lint]]
