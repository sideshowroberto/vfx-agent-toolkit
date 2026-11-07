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

For "does app X support / ship Y" questions, ask the installed app first: query
its own help (for example an MCP help-search tool) and grep its install tree
before reporting "no such feature". The running install is the version-exact
source. An unversioned vendor docs URL can serve the NEXT release, so cite
versioned URLs only (for example `/docs/<app><version>/`).

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

When fanning research out to sub-agents, paste the phase's hard limits (no
downloads, no scene changes, write only to <path>) verbatim into EVERY brief: a
limit missing from a brief does not exist for that agent. Check each agent's
scratch output for files it should not have made before relying on its report.

Keep queries free of credentials and confidential shot or client material.
Respect actual service errors and rate limits rather than hard-coded plan
assumptions. If a connector fails, state that and use an available search or
documentation tool when it can answer the question.

Return the useful finding, supporting links, applicable versions, and remaining
uncertainty. Save durable discoveries in the relevant project notes; avoid
dumping entire search responses into the conversation or prescribing an
interview, delegation, or approval gate for every research task.

### Verify sourced URLs and images

A URL or image returned by a search is a lead until something has looked at it.
Mark the links you opened in the deliverable (e.g. `[checked]`).

- HTTP status is only a 404 filter: bot-protected marketplaces answer 200/202/403
  for ANY path. Open decision-critical listings in a browser and judge the
  variant or era from the image itself, not the seller's title.
- A tool's TEXT description of a photo (WebFetch, any summarizer) is a lead, not
  a verdict - one session got "straight-on" and "oblique" both wrong. Open the
  pixels before any keep/reject or view label.
- A blocked fetch (e.g. 406) means a browser DOM read of each `img` `src`/`srcset`;
  copy signed CDN URLs (Getty) byte for byte. An article's hero image is
  unverified until opened - it can be a generic site-wide graphic.
- A CDN that returns 403 to scripts but serves the browser: fetch the image inside
  the page (fetch -> blob -> base64) instead of varying request headers.
- A bulk image list from one listing page can include an adjacent item or a
  document scan; check each kept image against details of the specific target.
- Image CDNs such as Wikimedia's throttle after about 5-8 downloads (HTTP 429), per
  CDN: front-load the file list and stop on the first 429.
- A vendor doc that is a PDF: a fetch tool may return raw compressed bytes, which
  is a gap in the instrument, not proof the document is silent. If the binary was
  auto-saved locally, extract it with PyMuPDF (`fitz.open(path)`, `page.get_text()`)
  in a `python -I` script, and put `sys.stdout.reconfigure(encoding='utf-8')`
  inside it (`-I` drops `PYTHONIOENCODING`). Do not report a PDF-only fact as
  "not stated" until the text has been extracted.
- The same photograph is often mirrored at different resolutions. Before settling
  for a capped, watermarked stock-agency comp of a historic moment, check the
  rights holder's own video or press archive page (the URL is often guessable
  from the article slug). Do not hunt a second camera angle by probing agency
  photo ids near a known-good one: ids are not clustered by event.
- Shared Browser pane: another session can drive the default tab (origins you
  never visited show up in `tabs_context`). Create a dedicated tab with
  `tabs_create` before any multi-step task and pass its `tabId` on every call;
  screenshots and coordinate clicks on a tab you did not just navigate are not
  trustworthy.
- To find reference images use the `brave-search` skill's
  `brave-search/scripts/brave_image_search.py` (full-size URL, WxH and caption per hit; zero
  results means rephrase), then open each candidate.
