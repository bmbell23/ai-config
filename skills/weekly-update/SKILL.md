---
name: weekly-update
description: Draft Brandon's weekly status email to his manager (EXA DevOps, SFA DevOps, AI Harness; 5 one-sentence bullets each) from the past week's mail, Teams, meetings, Jira and Confluence. Use when asked for "the weekly update", "status report for Scott", or on the Wednesday "Send Scott Status Report" reminder.
---

# Weekly update

Drafts the weekly update. **It never sends.** It returns a draft for Brandon to edit and send himself.

## Config

Read `weekly-update.local.yaml` next to this file. The file is gitignored, so names stay out of the repo. If it's missing, ask for it.

```yaml
to: [manager@example.com]          # who the email goes to
cc: []
subject: "Weekly Update - DevOps & AI Harness"
window_days: 7                     # how far back to look
sections:                          # in this order
  - name: EXA DevOps
    hint: current state, what's bad, what's good, what we're fixing
    jira: 'project in (ED, EDR, DDNDO) OR labels = exa-devops'
  - name: SFA DevOps
    hint: current state, migrations, Kubernetes, CI
    jira: 'project = SFAP AND component in (CI, Infrastructure) OR project = DDNDO'
  - name: AI Harness
    hint: current state, RCA skills progress, productizing for L3
    jira: 'project = MLAI'
reference_email_subject: "Weekly Update - DevOps & AI Harness"   # last sent copy = the format to match
```

## Steps

1. **Window.** Run from the last sent copy of `reference_email_subject` until now. If none is found, use `window_days`. Brandon's time zone is America/Denver.
2. **Format reference.** Read the last sent copy. Match its section headers, its bullet style (`**Bold lead phrase**: one sentence.`) and its length. Don't repeat a bullet from last week unless something changed, and if it did, say what changed.
3. **Gather.** Read only; never send or post anything.
   - *Sent mail* (`outlook_email_search`, sender = Brandon, window). Brandon's own words are the strongest signal of what mattered.
   - *Meetings* (`outlook_calendar_search`). For each meeting Brandon organized or that has a recap, read the Teams Facilitator recap (`chat_message_search` "that's a wrap" / "rundown") or the transcript. Keep decisions and outcomes. Skip attendance.
   - *Teams 1:1s with leadership*, such as the manager's manager. Look for asks and priorities, since those decide what leads each section.
   - *Jira*: tickets in each section's `jira` filter that were resolved or moved in the window. Use them for evidence and keys, not for bullets of their own.
   - *Confluence*: pages Brandon created or edited in the window.
4. **Pick five per section.** Rank them: decisions and asks from leadership, then shipped or switched-over work, then risks and blockers with an owner, then new efforts started, then numbers (speedups, queue depth, counts). One sentence per bullet, with a concrete noun and a number where one exists. Don't use names below manager level, ticket keys or internal hostnames in the email body. The audience is two levels up.
5. **Output.** Return:
   - the email ready to paste (To, Subject, three sections × 5 bullets, no sign-off; Outlook adds the signature);
   - under it, a **Sources** list: one line per bullet with the mail, meeting or ticket it came from, so Brandon can check each bullet;
   - **Gaps**: anything Brandon should add that the sources can't show (hiring, budget conversations held by phone).

## Don'ts
- Don't send, draft in Outlook, or post anything. The output goes back to Brandon only.
- Don't guess. If a section has fewer than 5 real items, write fewer and say so under Gaps.
- Don't include confidential HR items (promotions, reporting-line changes) unless Brandon adds them.
