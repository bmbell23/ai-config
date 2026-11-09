---
name: meeting-plan
description: Plan today's meeting recaps. Reads Brandon's calendar for today and queues one `meeting-recap` run per real meeting at its end + 30 min, as agent-bus `[[at:]]` lines. Use on the weekday 06:30 "meeting-plan" schedule (Haiku), or when asked to "plan today's recaps".
---

# Meeting plan

Cheap and short: this runs on Haiku every weekday morning. It reads the calendar and writes `[[at:]]` lines. It doesn't read transcripts or write anywhere.

## Config

Read `../meeting-recap/meeting-recap.local.yaml` (gitignored; copy it from the `.example` next to it). This skill only uses `tz`, `include` and `exclude`. If the file is missing, use America/Denver and no filters.

## Steps

1. **Window.** Today in `tz`, from 00:00 to 24:00 local time. Calendar times come back in UTC, so convert them. For America/Denver that's 06:00Z to 06:00Z (07:00Z in winter).
2. **Read.** Use `outlook_calendar_search` for that window. Don't `read_resource` each event: big series carry hundreds of attendees, and the search fields are enough.
3. **Keep** an event only if all of these hold:
   - it isn't all-day;
   - Brandon hasn't declined it, and it isn't cancelled;
   - it isn't a focus/busy block: no other attendees, or show-as "free"/"workingElsewhere", or a title like Focus, Focus time, Lunch, Hold, Block, OOO, Commute;
   - it has at least one attendee besides Brandon;
   - its end + 30 min is still in the future (on a late `!meeting-plan` run, skip meetings already recapped);
   - it passes the config: if `include` is non-empty, the title must contain one of its entries; it must not contain any `exclude` entry (case-insensitive substring match).
4. **Queue.** For each kept event, write one line on its own:
   ```
   [[at: <end + 30 min, ISO 8601 with offset> meeting-recap <title> | <start, ISO 8601 with offset>]]
   ```
   - Times are in `tz` with the offset written out, e.g. `2026-11-09T09:30:00-07:00`.
   - `<title>` is the event subject exactly as the calendar has it, on one line, without `|` or `]]` (put a `-` in their place).
   - Two events with the same title on the same day get different `<start>` values, so each one is its own run.
   - The router caps this at 30 queued runs per agent and 24h ahead. If there are more than 30 meetings, keep the first 30 and say so.

## Reply

At most one line per meeting before the `[[at:]]` block, and a count:

```
3 recaps queued for Mon 2026-11-09 (skipped: 2 focus, 1 declined).
- 08:30–08:45 Daily Sync-up - Exa DevOps → 09:15
- ...
[[at: 2026-11-09T09:15:00-07:00 meeting-recap Daily Sync-up - Exa DevOps | 2026-11-09T08:30:00-07:00]]
...
```

The `[[at:]]` lines go last, each alone on its line. If no meetings qualify, write "No meetings to recap today." and no `[[at:]]` lines.

## Don'ts
- Don't read transcripts or write to Confluence or Jira. That's `meeting-recap`'s job.
- Don't queue anything except `meeting-recap`.
- If the calendar tools aren't in this turn, say so in one line and stop. Don't guess the schedule.
