# ai-config

Personal skills for Claude Code (both accounts) and Augment, kept in one place under source control.

```
skills/<name>/SKILL.md      # one directory per skill; SKILL.md is the entry point
skills/<name>/*.md          # optional supporting files the skill links to
skills/<name>/*.local.yaml  # names/recipients: gitignored, copy from *.example
```

`./install.sh` links each skill into `~/.claude/skills`, `~/.claude-work/skills` and `~/.augment/skills`.
It is idempotent and never overwrites a real file.

Never link or commit credentials, history, sessions, projects or settings.json.
