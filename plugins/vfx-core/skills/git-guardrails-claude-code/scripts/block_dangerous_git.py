"""PreToolUse hook: block destructive git commands before Claude Code runs them.

Reads the hook JSON from stdin, checks tool_input.command against DANGEROUS,
and exits 2 (block, reason on stderr) or 0 (allow). No third-party tools and no
shell needed - plain Python 3, so it works the same on Windows, macOS and Linux.

FAILS CLOSED: if the input cannot be parsed, the command is blocked. A guard
that silently allows everything when something is missing is worse than none.

Test (both must hold):
    echo {"tool_input":{"command":"git push origin main"}} | python block_dangerous_git.py   -> exit 2
    echo {"tool_input":{"command":"git status"}} | python block_dangerous_git.py             -> exit 0
"""
import json
import re
import sys

# Optional global options between "git" and the subcommand, e.g. git -C repo push
_GIT = r"\bgit(?:\s+-(?:C|c)\s+\S+|\s+--\S+)*\s+"

DANGEROUS = [
    ("git push", _GIT + r"push\b"),
    ("git reset --hard", _GIT + r"reset\b[^\n;&|]*--hard\b"),
    ("git clean -f", _GIT + r"clean\b[^\n;&|]*\s-[a-zA-Z]*f"),
    ("git branch -D", _GIT + r"branch\b[^\n;&|]*\s(?:-D\b|--delete\s+--force\b|--force\s+--delete\b)"),
    ("git checkout .", _GIT + r"checkout\s+(?:--\s+)?\.(?:\s|$)"),
    ("git restore .", _GIT + r"restore\b[^\n;&|]*\s\.(?:\s|$)"),
]


def main():
    raw = sys.stdin.read()
    try:
        command = json.loads(raw).get("tool_input", {}).get("command", "")
        if not isinstance(command, str):
            raise ValueError("command is not a string")
    except Exception as exc:  # fail closed
        sys.stderr.write("BLOCKED: git guardrail could not read the hook input (%s).\n" % exc)
        return 2
    for label, pattern in DANGEROUS:
        if re.search(pattern, command):
            sys.stderr.write(
                "BLOCKED: '%s' matches the guarded pattern '%s'. "
                "The user has prevented you from doing this.\n" % (command, label))
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
