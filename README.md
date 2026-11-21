# ai-config

Personal skills for Claude Code (both accounts) and Augment, kept in one place under source control.

```
skills/<name>/SKILL.md      # one directory per skill; SKILL.md is the entry point
skills/<name>/*.md          # optional supporting files the skill links to
skills/<name>/*.local.yaml  # names/recipients: gitignored, copy from *.example
```

Skills:
- `weekly-update`: status email to my manager.
- `team-update`: the weekly "DevOps Team - Weekly Update" email to my team, with a thank-you per person.
- `meeting-plan`, `meeting-recap`: recap each meeting from its transcript into Confluence.
- `maint-email`: draft a lab maintenance, outage or all-clear notice as an Outlook-ready HTML card (draft only, never sends).
- `pro-ticket`: create or flesh out a procurement ticket: host facts, OEM vs third-party prices with sources, every field (including the edit-screen-only ones), a price comparison comment.
- `color-by-number`: printable color-by-number page + answer key; the image model draws, `cbn.py` numbers.

`./install.sh` links each skill into `~/.claude/skills`, `~/.claude-work/skills` and `~/.augment/skills`.
It is idempotent and never overwrites a real file.

Never link or commit credentials, history, sessions, projects or settings.json.
