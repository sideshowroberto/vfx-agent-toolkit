# CLAUDE.md

Instructions for Claude Code sessions working inside this repo (contributors
and maintainers). This is a public open-source repo published to
github.com/sideshowroberto/vfx-agent-toolkit under the MIT license.

## What this repo is

A Claude Code plugin marketplace plus MCP connector toolkit for VFX artists.
Users add it with `/plugin marketplace add sideshowroberto/vfx-agent-toolkit`
and install plugins from it. Everything in this repo ships to end users.

## Repo layout

```
.claude-plugin\marketplace.json   Marketplace manifest - plugin list, versions
plugins\<plugin>\                 One directory per plugin
  .claude-plugin\plugin.json      Plugin manifest
  skills\<skill-name>\SKILL.md    Skills (markdown with YAML frontmatter)
  agents\<agent-name>.md          Agents (markdown with YAML frontmatter)
  install.ps1                     Optional setup script (vfx-core has one)
connectors\<app>\                 MCP bridge installers per application
  install.ps1 / register.ps1      Setup scripts
  bridge\                         Bundled bridge code (nuke, houdini, unreal, maya)
docs\                             GETTING-STARTED.md, ARCHITECTURE.md
```

## Generated artifacts - do not hand-edit manifests

`plugin.json` and `marketplace.json` are GENERATED in the upstream development
workspace and synced into this repo. If a skill or agent needs changing, edit
the SKILL.md or agent markdown file. Do not hand-edit the manifests to add or
remove plugins; manifest changes happen upstream and land here via sync. If a
manifest looks wrong, flag it rather than patching it in place.

## Rules for anything that ships

- **ASCII only.** No em dashes, curly quotes, arrows, box-drawing characters,
  or emoji in any file that ships (markdown, scripts, skill files). This repo
  is used on Windows where non-ASCII characters corrupt in some tools and
  terminals. Use `-`, `->` spelled as text, and straight quotes.
- **No secrets.** Never commit API keys, tokens, credentials, or anything
  that looks like one. Setup scripts prompt for keys or read env vars.
- **Generic examples only.** No personal paths (`C:\Users\<someone>`), no
  studio or client names, no network drive paths. Use placeholders like
  `C:\path\to\project` or `%USERPROFILE%`.
- **Windows-first scripts, portable content.** Installers are PowerShell.
  Skills and agents must not assume any OS beyond what the target app
  requires. In script examples use `python`, not `python3` (python3 does not
  exist on Windows).

## Skill and agent format

Skills: `plugins\<plugin>\skills\<skill-name>\SKILL.md` with frontmatter:

```yaml
name: skill-name          # lowercase, hyphens, matches directory name
description: What + When + Triggers (max 1024 chars)
```

Agents: `plugins\<plugin>\agents\<agent-name>.md` with `name`, `description`,
`tools` frontmatter. No `model` field in skill frontmatter.

## Testing changes locally

Add the local clone as a marketplace to test before pushing:

```
/plugin marketplace add C:\path\to\vfx-agent-toolkit
/plugin install <plugin>@vfx-agent-toolkit
```

Restart Claude Code after MCP or plugin changes - both load at startup.
