#!/usr/bin/env python
"""task-observer SessionStart hook dispatcher - one command for every harness.

Why this exists: a hook line that starts with `bash` breaks outside Claude Code
on Windows (the PATH `bash` is the WSL stub in system32, not Git Bash), and
plugin-bundled hooks are ignored by Codex, which only reads user- or repo-level
hooks. This script is the single entry point both can call:

    python observe_hook.py [--ws <workspace>] [--helper-dir <dir>]

It runs the platform helper next to it (observe.ps1 on Windows, observe.sh
elsewhere) with the `status` subcommand and prints the hook response envelope
that Claude Code, Codex and Qwen Code all inject as session context:

    {"hookSpecificOutput": {"hookEventName": "SessionStart",
                            "additionalContext": "<status lines>"}}

Fail-soft: any failure becomes a one-line additionalContext explaining what
broke, and the exit code is always 0 - the observer must never block a session.
--ws sets TASK_OBSERVER_WS for the helper (the harness's own env is not always
inherited by hook processes). Stdin (the harness's hook JSON) is drained on a
timeout so a pipe left open can never hang the start of a session. ASCII only.
"""
import argparse
import json
import os
import platform
import subprocess
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))


def drain_stdin(timeout=2.0):
    """Read the hook JSON if the harness sent one; never wait on an open pipe."""
    box = {}

    def _read():
        try:
            box["data"] = sys.stdin.read()
        except Exception as e:  # noqa: BLE001
            box["err"] = repr(e)

    t = threading.Thread(target=_read, daemon=True)
    t.start()
    t.join(timeout)
    return box.get("data", "")


def envelope(text):
    return json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
                                              "additionalContext": text}})


def run_helper(helper_dir, env):
    if platform.system() == "Windows":
        ps1 = os.path.join(helper_dir, "observe.ps1")
        if not os.path.exists(ps1):
            return None, "observe.ps1 not found in " + helper_dir
        shell = "powershell"
        for cand in ("pwsh", "powershell"):
            try:
                subprocess.run([cand, "-NoProfile", "-Command", "exit 0"], capture_output=True, timeout=20, env=env)
                shell = cand
                break
            except Exception:  # noqa: BLE001
                continue
        cmd = [shell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps1, "status", "-Json"]
    else:
        sh = os.path.join(helper_dir, "observe.sh")
        if not os.path.exists(sh):
            return None, "observe.sh not found in " + helper_dir
        cmd = ["bash", sh, "status"]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=60, env=env)
    except Exception as e:  # noqa: BLE001
        return None, "helper failed to launch: %r" % (e,)
    out = (p.stdout or "").strip()
    if p.returncode != 0 and not out:
        return None, "helper exit %d: %s" % (p.returncode, (p.stderr or "").strip()[:300])
    return out, None


def main():
    ap = argparse.ArgumentParser(description="task-observer SessionStart hook")
    ap.add_argument("--ws", default=None, help="observation workspace (sets TASK_OBSERVER_WS)")
    ap.add_argument("--helper-dir", default=HERE, help="directory holding observe.ps1 / observe.sh")
    args = ap.parse_args()
    drain_stdin()
    env = dict(os.environ)
    if args.ws:
        env["TASK_OBSERVER_WS"] = args.ws
    out, err = run_helper(args.helper_dir, env)
    if err:
        print(envelope("task-observer: hook could not run the helper - " + err))
        return 0
    # observe.ps1 -Json already returns the envelope; observe.sh returns plain lines.
    try:
        doc = json.loads(out)
        if isinstance(doc, dict) and "hookSpecificOutput" in doc:
            print(out)
            return 0
    except ValueError:
        pass
    print(envelope(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
