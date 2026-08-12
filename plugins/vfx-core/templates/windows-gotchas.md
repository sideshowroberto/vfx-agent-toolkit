# Windows Gotchas

Hard-won rules for working on this Windows machine (and any teammate's). Each of these has caused a real failure — follow them without re-deriving.

## Encoding — the #1 hazard

- **ASCII only in generated code.** Never write em dashes (`—`), arrows (`→`), curly quotes, or any non-ASCII character into Python, `.nk`, `.ps1`, or config files. Windows cp1252 encodes an em dash as `\x97`, which breaks Python with `SyntaxError: Non-UTF-8 code` — this shipped to a teammate's Nuke `menu.py` once. Print statements crash too (`UnicodeEncodeError` on `→` after an otherwise successful run).
- Quick scan before distributing any Python file: `python -c "open(r'FILE', encoding='ascii').read()"` — a clean exit means pure ASCII.
- PowerShell 5.1 `Out-File`/`Set-Content` default to UTF-16 LE. Pass `-Encoding utf8` when other tools will read the file.
- **PS 5.1 `Set-Content -Encoding utf8` writes a BOM** — JSON parsers reject BOM'd files with "Unexpected token", and some apps respond by regenerating their config with defaults (wiping your settings). Write JSON with `[System.IO.File]::WriteAllText($path, $text, (New-Object System.Text.UTF8Encoding($false)))`. Back up before editing.
- **Console encoding:** set `PYTHONIOENCODING=utf-8` (or `.encode("ascii","replace")` before printing) in scripts that print text sourced from JSON/READMEs — an emoji or em dash in the data crashes cp1252 stdout mid-script (`UnicodeEncodeError`) after the real work succeeded.

## Python

- **`python3` does not exist on Windows.** It resolves to a Microsoft Store stub that prints an install prompt and exits 49. Always use `python`.
- **Backslash paths in docstrings/f-strings:** `"C:\Users\..."` inside a docstring raises `SyntaxError: unicodeescape` (`\U` starts a unicode escape). Use raw strings `r"C:\Users\..."` everywhere a Windows path appears in Python source.
- **Embedded interpreters:** apps like portable ComfyUI use their own Python (`python_embeded\python.exe`). Validating imports with system Python gives false `ModuleNotFoundError`s — always use the app's interpreter.
- **Windows Python cannot resolve Git-Bash paths.** `/tmp/x.json` and `/d/PROJECTS/...` are MSYS-only; `open(r'/tmp/...')` throws `FileNotFoundError` and ffmpeg rejects `/d/...` inputs. Pass native `D:\...` (or `D:/...`) paths to anything not running under bash.

## PATH and shells

- **Git-Bash PATH ≠ Windows PATH.** Tools on `~/.local/bin` (uv tool installs) are visible in Git Bash but NOT to apps spawned from Windows (Explorer, desktop apps, other agents). Use full paths or add to the Windows user PATH.
- **`ffprobe`/`ffmpeg` may not be on PATH** in Git Bash even when installed. Check with `where ffprobe.exe` (PowerShell) and use the full path.
- **Bash on Windows chokes on spaced filenames in arrays/loops.** Prefer Python for batch file operations; if bash, quote everything and prefer `find -print0 | xargs -0`.
- `cp` into a directory that doesn't exist fails and cascades cancellations in parallel calls — `mkdir -p` first, always.

## Downloads and archives

- **GitHub zip downloads nest a double directory** (`repo-name-main/repo-name-main/`). Check depth before copying — this has caused wrong-path copies three times.

## Claude Code / MCP config

- MCP transport type is `"http"`, NOT `"streamable-http"` — the schema rejects the latter and the error costs two app restarts.
- MCP servers load at startup: after editing `.mcp.json`, restart Claude Code before testing tools.
- Apps that own their config (desktop apps that rewrite settings files on a timer) will silently revert your file edits — use the app's CLI/UI to change settings, or stop the app first.
- **A session's MCP tool inventory is snapshotted at conversation start.** If a server needed OAuth when the conversation began, authenticating later — even from a separate terminal, even after relaunching and resuming — will NOT surface its tools in that conversation. The auth itself lands fine; only a NEW conversation picks it up. Don't debug the config — start a fresh conversation.
- Duplicate MCP configs shadow each other: user-scope `~/.claude.json` and desktop-app config files can carry stale keys that override a valid project `.mcp.json`. When an MCP auth error survives a key fix + restart, grep ALL config locations for the old key.
- **Agent-shell writes to AppData can be sandbox-virtualized** — a pip install or file copy into `%APPDATA%` from an agent's shell may succeed in-sandbox but never land on the real filesystem (other apps see nothing). For installs an app must see (e.g. Blender addon deps), run them from inside the app itself; verify with a read from the target app, not the shell.

## Long-running app processes

- A DLL/package can't be upgraded while its app is running (`WinError 5 Access is denied`) — stop the app (e.g. ComfyUI) before `pip install --upgrade`.
- Port conflicts: find the holder with `netstat -ano | findstr :PORT`, then `taskkill /PID <pid> /F`.
