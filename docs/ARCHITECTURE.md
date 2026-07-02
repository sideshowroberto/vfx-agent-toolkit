# Architecture

How the pieces of vfx-agent-toolkit fit together, and how to add to it.

## The big picture

```
marketplace.json  ->  plugins  ->  skills + agents     (what Claude knows)
connectors        ->  MCP servers -> running DCC apps  (what Claude can touch)
```

Two layers, deliberately separate:

- **Plugins teach Claude.** A plugin is a bundle of skills and agents -
  plain markdown that Claude Code loads on demand. Skills carry
  production-tested knowledge ("how to set up a Cattery inference chain in
  Nuke"); agents are specialized handlers Claude can delegate to. Plugins
  install through the Claude Code plugin system and involve no application
  setup.
- **Connectors wire Claude to the running application.** A connector
  registers an MCP (Model Context Protocol) server that exposes live tools:
  create a node in Nuke, query the Houdini scene, drive Unreal. Some also
  install bridge code inside the application (a Python listener in `.nuke`,
  for example). Connectors install through PowerShell scripts, outside the
  plugin system.

A plugin is useful without its connector (Claude still knows the techniques
and can write scripts for you to run), but the combination is the point:
skills tell Claude how, the connector gives it hands.

## The marketplace manifest

`.claude-plugin\marketplace.json` is what Claude Code reads when you run
`/plugin marketplace add sideshowroberto/vfx-agent-toolkit`. It declares the
marketplace name, owner, and the plugin list - each entry has a `name`,
`version`, `description`, and a `source` path pointing into `plugins\`.

When you run `/plugin install nuke-vfx@vfx-agent-toolkit`, Claude Code
resolves `nuke-vfx` through this manifest to `plugins\nuke-vfx` and installs
that directory's contents.

## Plugin format

Each plugin is a self-contained directory:

```
plugins\<plugin-name>\
+-- .claude-plugin\
|   +-- plugin.json            Plugin manifest (name, version, description)
+-- skills\
|   +-- <skill-name>\
|       +-- SKILL.md           Required: the skill itself
|       +-- <support files>    Optional: scripts, references, templates
+-- agents\
|   +-- <agent-name>.md        Optional: specialized agents
+-- install.ps1                Optional: extra setup (vfx-core registers MCPs)
```

### SKILL.md format

A skill is a directory containing a `SKILL.md` with YAML frontmatter:

```yaml
---
name: nuke-tiling-tool
description: Automated image tiling for ML processing in Nuke with seamless
  gradient blending. Use for large plates (4K+) through ML nodes. Triggers on
  "tile this plate", "tiling tool", "ViTMatte tiles".
---

# Skill content in markdown...
```

Rules:

- `name` is lowercase with hyphens, max 64 chars, and matches the directory
  name.
- `description` covers What + When + Triggers, max 1024 chars. This is what
  Claude reads when deciding whether to load the skill, so the trigger
  phrases matter more than anything else in the file.
- No `model` field in skill frontmatter.
- Keep the SKILL.md body focused; push long references into support files in
  the same directory (progressive disclosure - Claude reads them only when
  needed).

### Agent format

Agents live at `agents\<agent-name>.md` with frontmatter:

```yaml
---
name: nuke-specialist
description: What it does + when to delegate + trigger phrases
tools: Read,Write,Bash
---
```

The `name` must match the filename.

## Connector format

Each connector is a directory under `connectors\<app>\`:

- `register.ps1` - registers the MCP server with Claude Code (all
  connectors have this step, either standalone or inside install.ps1).
- `install.ps1` - full setup: installs dependencies, copies bridge files
  into the application, then registers.
- `bridge\` - bundled bridge code, where the app needs code installed
  (nuke, houdini, unreal, maya). Blender and Magnific need no bridge:
  Blender's MCP add-on is official and ships with Blender 4.5+, and
  Magnific's MCP is hosted.

Plugin `install.ps1` files that need an app bridge delegate to the matching
connector script rather than duplicating the logic.

## Generated manifests

`plugin.json` and `marketplace.json` are generated in the upstream
development workspace and synced into this repo. Contributions should edit
skills and agents, not the manifests - see CLAUDE.md at the repo root.

## Adding a new skill to an existing plugin

1. Create `plugins\<plugin>\skills\<skill-name>\SKILL.md` with valid
   frontmatter (see format above).
2. Keep it ASCII-only, no personal or studio paths, no secrets.
3. Test locally: `/plugin marketplace add C:\path\to\vfx-agent-toolkit`,
   install the plugin, restart Claude Code, and confirm the skill triggers
   on its phrases.
4. Open a PR.

## Adding a new plugin

1. Create `plugins\<new-plugin>\` with at least one skill under `skills\`.
2. Note in the PR that the plugin needs a `plugin.json` and a
   `marketplace.json` entry - maintainers generate these upstream.
3. If the plugin drives an application, add a matching
   `connectors\<app>\` directory with `install.ps1` / `register.ps1` and any
   bridge code.
4. Update the plugin table in README.md.

## PR checklist

- [ ] SKILL.md frontmatter: `name` matches directory, `description` has
      What + When + Triggers, under 1024 chars
- [ ] ASCII-only in every shipped file (no em dashes, curly quotes, arrows,
      emoji)
- [ ] No secrets, API keys, or credentials
- [ ] No personal paths, studio names, or network drives - generic
      placeholders only
- [ ] Scripts use `python`, never `python3`
- [ ] Tested via a local marketplace add and a Claude Code restart
- [ ] README tables updated if a plugin or connector was added
