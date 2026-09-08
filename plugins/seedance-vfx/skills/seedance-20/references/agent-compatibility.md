# Agent Compatibility

last_verified: 2026-05-30

Use this file when reviewing whether this repository is shaped correctly as an Agent Skill package. This is about packaging and agent behavior, not Seedance model capability.

## Current Agent-Skill Shape

Codex's current Agent Skills documentation describes a skill as a directory with a required `SKILL.md` file plus optional `scripts/`, `references/`, `assets/`, and `agents/` folders. It also describes progressive disclosure: the agent sees the name, description, and path first, then loads the full `SKILL.md` only when the skill matches the task.

This repository follows that pattern:

| Agent-skill expectation | Repository location | Status |
|---|---|---|
| Root skill metadata and routing | `SKILL.md` | Present |
| Task-specific sub-skills | `skills/*/SKILL.md` | Present |
| Dense reference material | `references/*.md` | Present |
| Validation and maintenance scripts | `scripts/*.py` | Present |
| README-facing visual resources | `assets/*` | Present |
| Codex UI metadata | `agents/openai.yaml` | Present |
| Behavioral evals | `evals/evals.json` | Present |
| CI validation | `.github/workflows/validate-skills.yml` | Present |
| Local Codex installer | `scripts/install_codex_skill.py` | Present |

## Compatibility Rules

- Keep every active `description` in third-person activation wording so tools can match it from a shortened skill list.
- Keep the root `SKILL.md` small. Route to sub-skills and references instead of copying long tables into the root.
- Keep volatile facts in dated references such as `api-status.md` and `source-registry.md`.
- Keep generated bitmap images inside `assets/` if they are referenced by README.
- Keep `agents/openai.yaml` aligned with the root skill name and make the default prompt invoke `$seedance-20`.
- Use `scripts/install_codex_skill.py --force` to install or refresh the local user-level Codex copy at `$CODEX_HOME/skills/seedance-20` or `~/.codex/skills/seedance-20`.
- Keep scripts deterministic and local. They should validate structure, schema, design, and source metadata without requiring private credentials.
- Do not store API keys, account cookies, or private prompt corpora in the skill package.

## Cross-Client Notes

Different agent clients scan different local paths. Codex documentation says Codex scans `.agents/skills` locations from the current directory upward, plus user/admin/system skill locations. A repository root with `SKILL.md` has the right skill-folder shape, but it is not automatically discovered as a repository skill unless installed under a scanned skill directory or packaged through the relevant plugin/distribution path. Other agent clients may use `.claude/skills`, `.gemini/skills`, `.github/skills`, `.cursor/skills`, or `.windsurf/skills`. Treat those as installation targets, not separate source trees.

Runway MCP is a separate agent connector surface. It can expose Seedance 2.0 through Runway inside MCP-compatible agents, but it does not make this repository a Runway plugin and does not change Codex skill installation rules.

## Source Signals

- OpenAI Codex Agent Skills docs: https://developers.openai.com/codex/skills
- OpenAI Codex Plugins docs: https://developers.openai.com/codex/plugins
- OpenAI Academy plugins and skills explainer: https://openai.com/academy/codex-plugins-and-skills/
- OpenAI skills catalog: https://github.com/openai/skills
- Agent Skills open standard overview: https://agentskills.io/
- Runway MCP announcement: https://runwayml.com/news/mcp

## Do Not Claim

- Do not claim every agent client can install directly from this repository URL.
- Do not claim every client honors the same metadata fields beyond `name` and `description`.
- Do not claim this repository provides a live Seedance API wrapper. It is an agent-skill workflow and reference package.
