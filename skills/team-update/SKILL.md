---
name: team-update
description: Draft Brandon's weekly "DevOps Team - Weekly Update" email to his team (opener, a key message he supplies, wins, what to focus on next, one thank-you per person for the biggest thing they did this week, updates, close) from the week's mail, Teams, meetings, Jira and Gerrit. Use when asked for "the team update", "the team email", "kudos email", or "DevOps weekly update". Not the status email to his manager (that's weekly-update).
---

# Team update

Drafts the weekly email Brandon sends his team. **It never sends**: it returns a draft for Brandon to edit and send himself.

## Input

Brandon's **key message** for the week, usually a rough brain dump. Turn it into the key-message section in his voice. Keep his ideas and their order, and don't add claims he didn't make. Anything else he mentions (a holiday, an update, someone to thank) goes in the section it belongs to.

No key message given: draft everything else, put `[KEY MESSAGE]` where it goes, and suggest 2–3 topics from the week under **Gaps**.

## Config

Read `team-update.local.yaml` next to this file. It's gitignored (names and addresses), so copy it from `team-update.local.yaml.example`. If it's missing, say so and stop.

```yaml
tz: America/Denver
thread_subject: "DevOps Team - Weekly Update"   # each week is a reply-all in this thread
to: [team-dl@example.com]
cc: [boss@example.com]
window_days: 7                 # fallback when no previous send is found
jira_projects: ["DO", "DOR", "DDNDO", "SFAP"]
team:                          # everyone here gets a kudos line, in this order
  - name: Pat                  # as Brandon writes it in the email
    email: pat@example.com
    jira: "<accountId>"        # assignee in JQL
    gerrit: pat@example.com    # owner: in Gerrit queries; omit if they don't use Gerrit
    works_on: Gerrit, CI       # helps find the right evidence
```

## Steps

1. **Window.** From Brandon's last send in `thread_subject` (search sent mail, newest first) until now, in `tz`. If there isn't one, use `window_days`.
2. **Read the last send.** It's the format reference, and it's what not to repeat: don't thank someone for the same thing two weeks running unless it reached a new milestone (then say what's new). Note its **Updates** bullets, since the ones still open get carried forward.
3. **Gather.** Read only.
   - *Brandon's own words first*: sent mail and Teams messages in the window (`outlook_email_search` sender = Brandon; `chat_message_search` sender = Brandon, words like thank/great/awesome/nice). Praise he already gave someone is the strongest kudos signal. In a 1:1 chat, the other member is who he's thanking.
   - *Jira*, per person: `assignee = "<jira>" AND (resolved >= "<start>" OR status CHANGED AFTER "<start>")`, within `jira_projects` plus any project the person's tickets turn up. Results are large: keep only key, summary, status and resolution date (save to a file and parse with `python3 -I`). A batch of old tickets all moved the same day is cleanup, not this week's work.
   - *Gerrit*, per person with `gerrit` set: `query_gerrit_changes` `owner:<gerrit> status:merged after:<start>`.
   - *Meetings*: demos, retros and incident reviews in the window (calendar, then the Teams recap or transcript). Presenting a demo counts.
   - *Incidents*: DOR incidents opened, mitigated or closed in the window, and who moved them.
4. **Pick one thing per person.** For each person on `team`, choose the single most notable thing in the window, ranked:
   1. something Brandon already thanked them for this week;
   2. an incident handled, or the prevent and monitor steps for one (alerts, health checks), since incidents are the team's #1 priority;
   3. off-hours or weekend work (an upgrade, an outage);
   4. something shipped or switched over that other teams will feel;
   5. helping another person or team, a demo, docs;
   6. otherwise their most meaningful closed or merged work.
   When two people did the same thing together, give them one shared line ("Charlie and Jin: …"). No evidence for someone: write `Name: [?]` and list them under **Gaps**. Never invent one, and never leave anyone off.
5. **Write the email** in this order, in Brandon's voice: plain, warm, direct, first person, short sentences, "you guys" is fine. Avoid corporate filler and hype words.
   1. **Opener**, 1–3 sentences: a holiday the team celebrates in the past few days or the coming week (the team is in the US and India), otherwise "Hello, Team!" and a line on the week. Holiday dates only from the calendar or a source you checked.
   2. **Key message** under a short bold heading, then short paragraphs. Use a numbered list for steps and a bulleted list for a ladder or a set of points. Usually 120–300 words.
   3. **Wins this week**: 2–4 bullets of team-level milestones. Names and ticket keys are fine (the audience is the team); link a key when there's follow-up on it.
   4. **What to focus on next**: 2–4 bullets: open incidents still needing prevent or monitor steps, deadlines, asks from the key message.
   5. **Kudos & Shoutouts**: one bullet per person, in `team` order: `Name: thank you for <the one thing>.` plus at most one short sentence on why it mattered. Vary the wording ("a HUGE thank you for", "great work on", "thank you for") but keep the shape.
   6. **Updates**: `Topic: one or two sentences.` Carry forward last send's open items only with news, or mark them `[still open, any news?]` for Brandon to fill or drop. Add new ones from the week.
   7. **Close**, verbatim: "As always, please reach out to me with any questions, comments, or concerns and feel free to schedule 1:1 time with me any time." then "Thanks, everyone. Great week!" No signature: Outlook adds it.
6. **Output.** Return:
   - **To / Cc / Subject**: reply-all to the last send (`Re: <thread_subject>`), with the recipients from that send, else from the config;
   - the email body in Markdown (bold headings, lists). It pastes into Outlook with formatting when copied from rendered Markdown;
   - **Sources**: one line per win and kudos bullet with the ticket, change, mail or chat it came from, plus the runner-up pick for each person so Brandon can swap;
   - **Gaps**: people with no evidence, carried-forward updates with no news, anything to confirm.

## Don'ts
- Don't send, create an Outlook draft, or post anything. The draft goes back to Brandon only.
- Don't name individuals' review status, pay, performance concerns, or who's leaving or joining unless Brandon wrote it in his input.
- Don't thank anyone for ticket counts alone ("closed 12 tickets"). Name the work.
- Don't reuse last week's kudos line for the same person.
