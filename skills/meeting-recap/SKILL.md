---
name: meeting-recap
description: Recap one meeting from its Teams transcript. Posts a short summary to Brandon (with a "For you" list of every time Brandon was named or addressed) and writes Confluence notes (Meetings › ‹title› rolling summary › ‹title› › ‹date›), and finds, links or proposes the Jira tickets and Confluence pages asked for out loud. Args are `<title> | <start ISO>`. Use when agent-bus runs `meeting-recap` (queued by `meeting-plan`), or when asked to "recap <meeting>".
---

# Meeting recap

Runs on Sonnet, about 30 min after a meeting ends. Args: `<title> | <start ISO>`, as written by `meeting-plan`. With no `| <start>`, use today's most recent occurrence of `<title>` that has already ended.

## Config

Read `meeting-recap.local.yaml` next to this file. It's gitignored; copy it from `meeting-recap.local.yaml.example`. If it's missing, say so and stop: the space key is personal.

```yaml
tz: America/Denver
confluence:
  space: "~<accountId>"      # Brandon's personal space key (not ~bbell)
  parent: Meetings           # page under the space home; created on first run
include: []                  # title substrings to recap; empty = all (meeting-plan applies these)
exclude: []                  # title substrings never to recap
owner_names: [Brandon, BB]   # every name/nickname the owner answers to; drives "For you"
```

If `owner_names` is missing or empty, still write the recap, but leave out **For you** and add the line "For you skipped: set `owner_names` in meeting-recap.local.yaml" to the reply.

## 1. Transcript

1. Use `outlook_calendar_search` for a window of `<start>` ± 5 min to find the event whose subject is `<title>`, then `read_resource` the event to get `meetingTranscriptUrl`.
2. Use `read_resource` on that URL with `start`/`end` set to the occurrence: `<start>` up to now. Recurring meetings can share one recording, so keep only the cues inside this occurrence.
3. **Not ready** (empty, or "may still be processing"): end the reply with exactly this line and stop. It's the one retry the router allows per meeting per day.
   ```
   [[at: <now + 30 min, ISO with offset> meeting-recap <same args, unchanged>]]
   ```
   If this run already is the retry (it started ≥ 50 min after the meeting's end), don't queue another. Reply "No transcript for ‹title› yet; run `!meeting-recap <args>` later." and stop.
4. **No access** (403 "does not have access", or no transcript URL because recording was off): reply one line saying so and stop. No retry, no pages.
5. Large transcripts get saved to a tool-results file. Parse that file with `python3 -I`. The VTT cues look like `<v Name>text</v>`:
   `re.findall(r"(\d\d:\d\d):\d\d\.\d+ --> [^\n]+\n<v ([^>]+)>(.*?)</v>", content, re.S)`.

## 2. Squash

Turn the transcript into notes of who said what. Merge each speaker's consecutive cues into one line, `HH:MM Name: gist`, and drop filler, greetings and crosstalk. Keep exact wording only for decisions, commitments and asks. Then pull out:

- **Decisions**: what was agreed, and by whom.
- **Action items**: owner, the action, and a due date if one was said. Mark it `(inferred)` if the owner isn't explicit.
- **Spoken asks** for Jira or Confluence: "make/file/open a ticket", "is there a ticket for", "find/write/make a page/doc". Note who asked and the timestamp.
- **Open questions** left unanswered.
- **For you**: every time the owner was named or addressed. A cue counts when it contains any of `owner_names` (whole word, case-insensitive), or when a speaker says "you" *to the owner*. Decide that from context: the owner spoke just before or answers right after, or the line follows one of their names. A generic "you" said to the room doesn't count, and neither do the owner's own lines. For each hit keep: `HH:MM`, who said it, a short exact quote, and the ask if there was one (`ask: <what they want, by when>`), else `mention`. Merge hits from the same speaker on the same topic within a minute into one.

A conference-room mic (one speaker name for many people, e.g. "Colorado Springs - Phantom Canyon"): attribute from context and add "(room mic; attribution inferred)".

## 3. Spoken asks

- **Find a ticket**: use JQL `text ~ "<2–3 key words>" ORDER BY updated DESC` across the projects named in the meeting, or else `project in ("SFAP", "MLAI", "DO", "DCO", "DDNDO", "DOR", "EXR")`. Quote every key, since bare DO fails. Link the best match. If nothing clearly matches, list the top 3 as "maybe".
- **Make a ticket**: search first, as above. If it exists, link it. Otherwise **propose** it; don't file it. Ticket drafts reach Jira only when Brandon replies `go`, because the router refuses them in a scheduled turn. List each proposal under **Proposed tickets** as `title · type · which teammate's repo` (the meeting-tickets flow, BBELL-12). When Brandon later replies `go` in this thread, emit one block per ticket in that reply:
  ```
  [[ticket-draft: @<agent>]]
  <title>
  Type: Story            (Bug only with build/kit, controller IP and where it was found)
  Branch: <release>      (only if the meeting named one)
  <problem, the ask, people, timestamped quotes, open questions>
  [[/ticket-draft]]
  ```
  The agent is the teammate who owns the repo. Use the Jira desk when there's no repo. Allow at most 20 per reply.
- **Find a Confluence page**: CQL `title ~ "<words>" OR text ~ "<words>"`, then link it.
- **Make a Confluence page**: create it under the meeting's ‹title› page, titled as asked, with the context from the transcript. Link it.

## 4. Confluence

Every page goes in `confluence.space`. Write the bodies in storage format (HTML). Before each write, find the page by exact title in that space (CQL `space = "<space>" AND title = "<title>"`).

1. **`Meetings`** (`confluence.parent`): create it under the space home page if it doesn't exist. The body is one line: "Meeting notes, written by Penny ~30 min after each meeting (DO-1412)."
2. **`‹title›`** under Meetings. Confluence titles are unique per space, so if the title is taken elsewhere in the space, use `‹title› (meeting)`. Create it or update it, never by retyping it blindly: read it, then rewrite these sections.
   - **Summary**: a rolling 3–6 line picture of what this series is about and where things stand. Fold in today; don't just append to it.
   - **Open action items**: a table of Owner, Item, From (date link) and Status. Add today's items. Mark items done that the transcript says are done. Keep the rest.
   - **Meetings**: the newest date page first (the child pages macro `<ac:structured-macro ac:name="children"/>` is enough).
   A one-off meeting gets the same layout with a single date.
3. **`‹title› › ‹YYYY-MM-DD›`** under ‹title›, with the date in `tz` of `<start>`. If it exists (a re-run), update it. Sections: **For you** (first, before everything else; see §5 for the order of lines), Attendees (speakers heard), Summary, Decisions, Action items, Asks (with links), Open questions, Notes (the squashed `HH:MM Name: gist` lines), Source (the event subject and start, and "transcript via M365").

If a Confluence write fails, put the exact error in the reply. Still post the summary, add "Confluence not written: ‹error›", and stop there. Don't retry other ways, and don't pull in other agents.

## 5. Reply

Penny posts this to Brandon, so keep it tight:

```
**‹title›** · ‹date› ‹HH:MM›–‹HH:MM› · [notes](‹date page link›)
**For you:**
‹action items owned by the owner first: "Action: item (due) · from Name HH:MM"›
‹then each mention: "HH:MM Name: “quote” → ask: …" or "→ mention"; or "nothing addressed to you"›
‹5–8 lines: what happened, what changed, what's blocked›
**Decisions:** ‹one per line, or "none"›
**Action items:** ‹Owner: item (due)›, one per line
**Links:** ‹tickets / pages found or created, as links›
**Proposed tickets** (reply `go` to file): ‹title · type · teammate›   (only if any)
```

**For you** goes right under the header line, before the summary, and the date page uses the same lines. List the owner's action items first, then mentions in time order. If there are more than 8 mentions, show the 8 with asks (or the earliest ones) and add "+N more on the notes page". The date page lists them all. The 5–8 line limit is for the summary only; For you doesn't count toward it.

Name the teammate in Proposed tickets without an `@`. An `@` here would wake them.

## Don'ts
- Don't file Jira tickets from this run. Propose them, and they go out on Brandon's `go`.
- Don't post to Teams, mail, or anyone but Brandon.
- Don't invent owners, dates or decisions. If the transcript doesn't say, write "unclear".
- Don't paste the raw transcript anywhere.
