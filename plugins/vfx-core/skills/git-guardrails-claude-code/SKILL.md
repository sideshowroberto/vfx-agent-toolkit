---
name: git-guardrails-claude-code
description: Sets up a Claude Code PreToolUse hook that blocks destructive git commands (push, reset --hard, clean -f, branch -D, checkout/restore .) before they run, with a Python hook that fails closed. Use when the user wants git safety hooks or to block git push/reset in Claude Code.
---

# Setup Git Guardrails

Installs a PreToolUse hook that intercepts destructive git commands before Claude runs them.

## Traps (read first)

- **The hook must FAIL CLOSED.** The previous version read the hook JSON with `jq`; on a machine
  without jq (Git for Windows does not ship it) it printed "jq: command not found", exited 0 and
  blocked NOTHING. The bundled hook is plain Python and blocks when it cannot read its input.
- **Start the settings command with `python`, never `bash`.** On Windows the `bash` on PATH is the
  WSL stub, so a `bash "..."` hook dies silently outside Claude Code's own shell.
- **Verify by feeding it a command it must block AND one it must allow.** "It ran" or "exit 0"
  proves nothing about a guard - a hook that allows everything passes that check.
- Exit code 2 blocks the call and shows stderr to Claude; any other non-zero exit does NOT block.

## What Gets Blocked

- `git push` (all variants, including `git -C <dir> push` and after `&&`)
- `git reset --hard`
- `git clean` with `-f` in its flags (`-f`, `-fd`, `-xfd`; `-n` dry runs are allowed)
- `git branch -D` (lower-case `-d` on a merged branch is allowed)
- `git checkout .` / `git checkout -- .` / `git restore .`

Claude sees "BLOCKED: ... The user has prevented you from doing this."

## Steps

### 1. Ask scope

Install for **this project only** (`.claude/settings.json`) or **all projects**
(`~/.claude/settings.json`)?

### 2. Copy the hook

The bundled hook is [scripts/block_dangerous_git.py](scripts/block_dangerous_git.py). Copy it to:

- **Project**: `.claude/hooks/block_dangerous_git.py`
- **Global**: `~/.claude/hooks/block_dangerous_git.py`

### 3. Add the hook to settings

Merge into the existing `hooks.PreToolUse` array - never overwrite other settings or hooks.

**Project** (`.claude/settings.json`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "python \"$CLAUDE_PROJECT_DIR/.claude/hooks/block_dangerous_git.py\"" }
        ]
      }
    ]
  }
}
```

**Global** (`~/.claude/settings.json`): same block with
`"command": "python ~/.claude/hooks/block_dangerous_git.py"`.

Use `python` on Windows (`python3` is a Microsoft Store stub there); `python3` on macOS/Linux if
`python` is absent. Check the interpreter with `python -c "print(1)"` first: if the interpreter is
missing the hook exits with a non-2 error, which Claude Code does NOT treat as a block - the guard
would be off. The step 5 check catches this.

### 4. Ask about customization

Ask whether to add or remove patterns; edit the `DANGEROUS` list in the copied hook.

### 5. Verify (both directions)

Run the bundled self-test against the copied hook (copy
[scripts/test_block_dangerous_git.py](scripts/test_block_dangerous_git.py) next to it):

```bash
python .claude/hooks/test_block_dangerous_git.py
```

It must print `PASS n/n`: every guarded command blocked, every ordinary command (git status,
git pull, git checkout main, ...) allowed, and unparsable input blocked. Then start a NEW Claude
Code session (hooks load at start) and ask it to run `git push --dry-run`: the call must be refused.
