---
name: deploy-skills
description: Deploy this project's skills/ folder to global skill locations; use when the user asks to deploy, publish, sync, or push skills to Claude or Openclaw
---

# Deploy Skills

Copy skills from this project's `skills/` folder into the global skill locations so they are available in all sessions.

## Target Locations

| Agent | Global Skills Path |
|-------|-------------------|
| Claude Code | `~/.claude/skills/` |
| Openclaw | `~/.openclaw/workspace/skills/` |

## Workflow

### 1. Identify skills to deploy

List the project's skills:

```bash
ls skills/
```

Each subdirectory is a skill to deploy.

### 2. Diff each skill against both targets

For each skill directory, check whether it differs from the installed versions:

```bash
diff -r skills/<name> ~/.claude/skills/<name>
diff -r skills/<name> ~/.openclaw/workspace/skills/<name>
```

### 3. Copy changed skills

For any skill that differs (or doesn't exist at the target), copy it:

```bash
cp -r skills/<name> ~/.claude/skills/
cp -r skills/<name> ~/.openclaw/workspace/skills/
```

### 4. Report results

Tell the user which skills were updated and which were already up to date.

## Rules

- **Only copy from `skills/` → global locations.** Never copy in the reverse direction.
- **Never touch skills in the global locations that don't exist in this project's `skills/` folder.** Other projects own those.
- **Do not create skills at the target if the source skill directory is empty or malformed** (missing `SKILL.md`).
- Copying is non-destructive: `cp -r` overwrites but does not delete unrelated skills at the target.
