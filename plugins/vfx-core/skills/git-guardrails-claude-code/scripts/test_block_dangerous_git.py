"""Self-test for block_dangerous_git.py - feeds real hook JSON through the hook as a
subprocess (the way Claude Code calls it) and checks BOTH directions: every guarded
command is blocked (exit 2) and every ordinary command is allowed (exit 0).

    python test_block_dangerous_git.py        -> prints PASS n/n, exit 0 on success
"""
import json
import os
import subprocess
import sys

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "block_dangerous_git.py")

BLOCK = [
    "git push origin main",
    "git push --force",
    "git -C repo push",
    "cd x && git push",
    "git reset --hard HEAD~1",
    "git reset HEAD~1 --hard",
    "git clean -fd",
    "git clean -f",
    "git clean -xfd",
    "git branch -D feature",
    "git checkout .",
    "git checkout -- .",
    "git restore .",
    "git restore --staged .",
]
ALLOW = [
    "git status",
    "git pull",
    "git fetch origin",
    "git log --oneline -5",
    "git reset --soft HEAD~1",
    "git clean -n",
    "git branch -d merged-feature",
    "git checkout main",
    "git checkout .gitignore",
    "git restore file.txt",
    "ls -la",
    "echo pushing to the review queue",
]


def run(stdin_text):
    p = subprocess.run([sys.executable, HOOK], input=stdin_text, capture_output=True, text=True)
    return p.returncode


def main():
    fails = []
    for c in BLOCK:
        if run(json.dumps({"tool_input": {"command": c}})) != 2:
            fails.append("not blocked: " + c)
    for c in ALLOW:
        if run(json.dumps({"tool_input": {"command": c}})) != 0:
            fails.append("wrongly blocked: " + c)
    if run("this is not json") != 2:
        fails.append("bad input did not fail closed")
    total = len(BLOCK) + len(ALLOW) + 1
    if fails:
        print("FAIL %d/%d" % (total - len(fails), total))
        for f in fails:
            print("  " + f)
        return 1
    print("PASS %d/%d" % (total, total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
