---
name: maint-email
description: Draft a lab maintenance or outage announcement email (scheduled, unplanned, incident, or the all-clear) in Brandon's house format, an Outlook-safe HTML card plus subject and recipients. Use when asked for "a maintenance email", "a maint notice", "an outage email", "an all-clear", or for `!maint-email <what> [when]`.
---

# Maintenance email

Drafts the notice. **It never sends.** Brandon pastes it into Outlook and sends it himself.

## Inputs

- **What**: the host or service and the work, e.g. "fs-01 reboot", "build-02 RAM swap".
- **When**: a start time, or "tonight" / "now". If no time is given, use the last notice's time for the same host and mark it `[confirm time]` in the reply.
- **Status**: `Scheduled` (announced ahead), `Unplanned` (same day), `Incident` (already broken), `Completed` (the all-clear). Infer it from the words ("tonight" means Unplanned; "is down" means Incident; "all clear" or "done" means Completed). Otherwise use Scheduled.

## Config

Read `maint-email.local.yaml` next to this file. It's gitignored so distribution lists, hosts and ticket projects stay out of the repo. If it's missing, ask for it. Its shape is `maint-email.local.yaml.example`: `team`, `sender`, `support`, `zones`, `jira_projects`, `lists` and `hosts`. Without `zones`, use MT, then ET and IST. Without `jira_projects`, ask which projects to search.

## Gather (read-only)

1. **The last notice for the same host**: Outlook search `"<host>" maintenance OR reboot OR outage`. Reuse its recipients, its facts (what the host serves, past downtime) and its tickets. Read the latest one in full.
2. **The trigger**: the Teams chat or mail that asked for the work (who, why, proposed time). Quote it in the reply, not in the email.
3. **Tickets**: JQL `text ~ "<host>" AND project in (<jira_projects, each key quoted>) ORDER BY created DESC`. Quote every key: `DO` is a reserved word and the bare form fails. Put the current ticket in Tracking. If there's none, write `[TICKET]` and say so in the reply. Never create one.
4. **Follow-up work**: an open migration or root-cause ticket, or an upcoming meeting about it, goes in "What's next".

## Write

Fill `template.html` (every `{{FIELD}}`; `example.html` is a finished one). Rules:

- **Times**: in the first `zones` entry first, then the others on the second line (by default MT, then ET and IST: the audience is Colorado, the East Coast and Pune). Compute each with `TZ=<tz> date -d 'TZ="<first tz>" 2026-11-17 17:30' '+%a %b %-d %-I:%M %p'`, never by hand (the inner `TZ="..."` says which zone the input is in), and watch the DST change dates and the date rolling over.
- **Status colour**: Scheduled `#0E7AB8`, Unplanned `#C77700`, Incident `#C0352B`, Completed `#2E7D32`.
- **Affected / Not affected**: only what you can show from the last notice, the config's `hosts:` notes, or the trigger. Don't guess at dependencies. Leave a row out rather than invent it.
- **What you need to do**: one sentence each for Before, During and After. For a Completed notice, replace the block with "What changed" and "If something's still wrong".
- **Why**: plain words for a developer audience: what broke, why this fixes it. 3 to 4 sentences, no jargon without a gloss.
- **What's next**: only commitments already made (a ticket, a meeting). Drop the block for routine work.
- **Subject**: `[Maintenance] <host> <work>: <Day M/D> at <time> <first zone label> (~<duration>)`. Incidents use `[Incident]`, the all-clear `[Resolved]`.
- **Importance**: High for Unplanned and Incident.

## Output

1. Write the filled HTML to a scratch file and hand it over (in agent-bus: your scratch dir, attached with `[[attach: <path>]]`).
2. In the reply: To/Cc, subject, importance, then a plain-text preview of the card. Then every `[placeholder]` or `[confirm ...]` left in the email, and the evidence for each fact (mail, chat, ticket).
3. How to send: open the HTML in a browser, select all, copy, and paste into a new Outlook message. Tables and colours survive the paste.

When Brandon asks for it, the all-clear is the same template with Status `Completed`, sent as a reply to the original thread.
