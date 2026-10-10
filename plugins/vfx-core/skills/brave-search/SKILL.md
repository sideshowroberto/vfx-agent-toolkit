---
name: brave-search
description: "Researches VFX topics with Brave Search - MCP web search for filtered URL lists, an LLM Context script for deep research with extracted page content, and image search for references. Use when searching for tutorials, docs, errors, plugins or software updates."
allowed-tools: Read,Bash
---

# Brave Search Skill - VFX Research Intelligence

**Version:** 2.2.2 | **Updated:** 2026-10-10

---

## Three Tools, Three Jobs

| Tool | When to use | What you get |
|------|------------|--------------|
| `mcp__brave-search__brave_web_search` | Quick lookups, filtered results, URL lists, pagination | URLs + snippets |
| `brave_llm_context.py` (via Bash) | Deep research, grounding, actual page content | Extracted text, tables, code blocks |
| `brave_image_search.py` (via Bash) | Finding reference photos / stills | Full-size image URL + WxH + caption per hit |

**Decision rule:** If you need to read the content of pages (not just find them), use LLM Context. If you need URL lists, type-filtering, or pagination, use web_search. If you need the images themselves, use image search (Tool 3) - not a page search followed by scraping.

---

## Tool 1 - MCP Web Search

```
mcp__brave-search__brave_web_search(query, count, result_filter, freshness, extra_snippets)
```

### Parameters

| Param | Values | Default | Notes |
|-------|--------|---------|-------|
| `query` | string | - | Required. Max 400 chars / 50 words |
| `count` | 1-20 | 10 | 20 for comprehensive research |
| `result_filter` | `web` `news` `videos` `discussions` `images` | web | For reference photos with full-size URLs use Tool 3 |
| `freshness` | `pd` `pw` `pm` `py` or date range | - | pm = past 31 days |
| `extra_snippets` | boolean | false | Up to 5 extra excerpts per result |
| `spellcheck` | boolean | true | Set false for exact error messages |
| `offset` | 0-9 | 0 | Pagination |

### VFX Query Formula
```
[Software] [Version] [Task] [Context]

"Houdini 20.5 VEX wrangle point cloud tutorial"
"Unreal Engine 5.5 PCG graph landscape scatter"
"Blender 4.5 geometry nodes array instances procedural"
```

### Goggles - Domain Filtering
Pin results to authoritative VFX sources. Pass as `goggles` parameter string:

```
# SideFX only
$site=sidefx.com,boost=10\n$discard

# Foundry docs only
$site=learn.foundry.com,boost=10\n$discard

# Multiple trusted VFX domains
$site=sidefx.com,boost=10\n$site=odforce.net,boost=8\n$site=cgwiki.com,boost=6\n$discard
```

---

## Tool 2 - LLM Context (Deep Research)

Calls `/llm/context` directly via Python. Returns actual extracted page content - no scraping needed.

**Script:** bundled with this skill at `scripts/brave_llm_context.py` - resolve the path against this skill's own directory. Output is forced to UTF-8, so extracted web content prints safely on Windows (cp1252) consoles.

**Requires:** `BRAVE_API_KEY` environment variable (same key the brave-search MCP server uses).

### Basic usage
```bash
python <skill-dir>/scripts/brave_llm_context.py "Houdini VEX point attributes tutorial"
```

### With options
```bash
python <skill-dir>/scripts/brave_llm_context.py "USD Solaris render settings" \
  --tokens 16384 \
  --freshness pm \
  --threshold strict
```

### Parameters

| Flag | Default | Range | Notes |
|------|---------|-------|-------|
| `--tokens` | 8192 | 1024-32768 | Increase for complex research |
| `--count` | 20 | 1-50 | Search results to evaluate |
| `--urls` | 20 | 1-50 | Max pages to extract from |
| `--freshness` | none | pd/pw/pm/py | Filter by age |
| `--threshold` | balanced | strict/balanced/lenient/disabled | strict = authoritative only |
| `--json` | false | - | Raw JSON output |

### Token budget guidance
- Quick answer: `--tokens 4096`
- Standard research: `--tokens 8192` (default)
- Deep research: `--tokens 16384`
- Comprehensive: `--tokens 32768`

---

## Tool 3 - Image Search (Reference Sourcing)

Calls `/images/search` directly via Python. For every hit it returns the full-size image URL, the source page, the caption and the pixel size, largest first. One command replaces the search-pages-then-scrape loop. Search for images, not for pages about images.

**Script:** bundled with this skill at `scripts/brave_image_search.py` - resolve the path against this skill's own directory.

**Requires:** `BRAVE_API_KEY` environment variable (same key as Tool 2). The script reads it from the environment and never prints it.

### Usage
```bash
python <skill-dir>/scripts/brave_image_search.py "1980s arcade cabinet front view" 40
python <skill-dir>/scripts/brave_image_search.py "1980s arcade cabinet front view" --count 40 --safesearch strict
```

| Arg | Default | Notes |
|-----|---------|-------|
| `query` | - | Required |
| `count` (positional or `--count`) | 40 | 1-200 |
| `--safesearch` | strict | `off` or `strict` |

### Output
One line per hit, largest pixel area first, then a `RESULTS <n>` line:
```
<width>x<height> | <full image url> | <source page url> | <title/caption>
```
- `0x0` means Brave did not report a size: unknown, not small.
- The caption often carries the event and date, and the size is the first resolution filter - read both before downloading.
- `RESULTS <n>` proves the call ran. A failed call prints `FAIL ...` and exits 1.

### Rules
- **Zero results means rephrase.** `RESULTS 0` is returned for valid queries. Re-run with other wording (add or drop the year, name the event or the exact object); never conclude "no images exist".
- **Hits are leads, not verdicts.** Sidebar images of other people or items get attached to the right page, and many CDNs serve AVIF/WEBP under a `.jpg` URL. Download, confirm the file opens, then open every candidate and look before keeping or naming it (see vfx-research, "Verify sourced URLs and images").

---

## Search Protocols

### 1. Tutorial Discovery
```python
# Web search - find video tutorials
mcp__brave-search__brave_web_search(
    query="Houdini 20.5 procedural terrain VEX tutorial",
    count=20, result_filter="videos", freshness="py"
)
```

### 2. Error Debugging
```python
# Discussions with exact error, no spellcheck
mcp__brave-search__brave_web_search(
    query='"Blueprint compile failed" Unreal 5.5 fix',
    count=15, result_filter="discussions", spellcheck=False
)
```

### 3. Documentation Deep Dive
```bash
# LLM Context - get actual doc content
python <skill-dir>/scripts/brave_llm_context.py \
  "Unreal Engine 5.5 PCG API documentation" \
  --tokens 16384 --threshold strict
```

### 4. Plugin Research
```python
mcp__brave-search__brave_web_search(
    query="Blender 4.5 geometry nodes scatter plugin free",
    count=20, extra_snippets=True
)
```

### 5. Software Updates
```python
mcp__brave-search__brave_web_search(
    query="Houdini 21 release notes new features",
    result_filter="news", freshness="pm"
)
```

### 6. Community Intelligence
```python
mcp__brave-search__brave_web_search(
    query="Unreal PCG vs Houdini procedural comparison reddit",
    count=15, result_filter="discussions", freshness="pw"
)
```

---

## Multi-Search Stacks

### Deep Research (LLM Context + Web Search)
1. LLM Context -> extract actual docs/tutorials content
2. Web Search (discussions) -> community experience
3. Context7 -> structured API reference if library-based

### Quick Debugging
1. Web Search (discussions, exact error, spellcheck=false)
2. Web Search (web, official docs)

### Plugin Evaluation
1. Web Search (web, discovery, count=20)
2. Web Search (discussions, reviews)
3. LLM Context -> extract full docs for top candidate

---

## Context7 Integration

After finding a Python/library-based tool via search:
```python
# 1. Resolve
lib = mcp__context7__resolve-library-id(libraryName="FastMCP", query="how to create server tools")

# 2. Get docs
docs = mcp__context7__query-docs(
    libraryId="/jlowin/fastmcp",
    query="how to create server tools"
)
```
Use Context7 for Python packages and frameworks. Use LLM Context for general web research.

---

## Large Output Handling

LLM Context can return large responses (8K-32K tokens). Use the file-redirect pattern to keep context clean:

```
1. Run brave_llm_context.py - output prints to stdout, captured by desktop-commander
2. Write full result to tmp/brave_context_output.md
3. Grep for the specific terms, functions, or patterns needed
4. Work from grep results - don't re-quote the full output in your response
5. Delete tmp/brave_context_output.md when done
```

Higher token budgets (`--tokens 16384` or `--tokens 32768`) are now practical since output goes to file rather than flooding context.

---

## Rate Limits

Brave Search is a paid API ($5/month credit, pay-as-you-go beyond).
- Web Search: no hard per-second limit on paid plans, but space requests ~1 second apart as good practice
- LLM Context: allow 30-second timeout (page extraction takes time)
- Image Search: same key and plan as web search; run sequentially. When downloading hits, stop on the first HTTP 429 from an image CDN
- No parallel execution - run searches sequentially
