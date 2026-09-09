---
name: vfx-research
description: Research VFX application APIs, errors, workflow integrations, and library examples using Brave Search and Context7. Use for Blender, Nuke, Houdini, Unreal, ComfyUI, and related development questions that need external evidence.
---

# VFX research

Harness-neutral companion to the `brave-search` skill, which documents the
Claude Code MCP tools in detail. Use the connected tools' current schemas; tool
names quoted in other skills are not an API contract for this harness.

## Pick the source for the question

- Brave Search: discover application documentation, release notes, exact error
  matches, and integration sources. Include the application, installed version,
  task, and relevant renderer or operating system in the query.
- Context7: retrieve library documentation and code examples. Resolve the
  library with `resolve-library-id` using `libraryName` and a specific `query`,
  then call `query-docs` with the returned `libraryId` and the actual question.
  Skip resolution when the user supplies the exact library ID or it was already
  resolved for the current task.
- For DCC APIs missing from Context7, read the vendor's versioned documentation
  directly. Relevant starting domains include docs.blender.org,
  learn.foundry.com, sidefx.com/docs, dev.epicgames.com, and docs.comfy.org.

Match documentation to the installed version. If the requested version is not
indexed, disclose that mismatch and check the vendor's docs or local API before
using an example. Do not silently substitute the newest release.

## Search and verify

Inspect the available Brave tool schema before choosing filters. Start with a
focused web query and a small result set. Use exact quoted error text where
helpful. Apply freshness filters to release/news questions, not automatically
to stable APIs or older software versions. Use dedicated video or image tools
when exposed rather than assuming the web tool accepts every result type.

Search snippets identify sources; open relevant pages before treating their
contents as verified. Ground technical conclusions in vendor docs, upstream
source, or maintainer examples. Treat community reports as leads to reproduce.
If Context7 returns an excerpt without sufficient provenance or version detail,
follow its source link before relying on it for a version-sensitive claim.

Keep queries free of credentials and confidential shot or client material.
Respect actual service errors and rate limits rather than hard-coded plan
assumptions. If a connector fails, state that and use an available search or
documentation tool when it can answer the question.

Return the useful finding, supporting links, applicable versions, and remaining
uncertainty. Save durable discoveries in the relevant project notes; avoid
dumping entire search responses into the conversation or prescribing an
interview, delegation, or approval gate for every research task.
