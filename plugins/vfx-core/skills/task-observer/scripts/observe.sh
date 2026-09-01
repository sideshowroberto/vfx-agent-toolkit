#!/usr/bin/env bash
# task-observer helper - the mechanical half of the skill.
#
#   observe.sh status    one-screen state of the observation log (SessionStart hook + manual)
#   observe.sh init      create the workspace layout (only when status reports MISSING)
#   observe.sh scan      print the frontmatter header of every active observation
#   observe.sh next-id   allocate the next observation id (updates archive/.id-floor)
#   observe.sh archive   move resolved observations (resolved before today) to archive/
#
# Portable POSIX tools only (ls, grep, sort, awk, printf, mv, date). Runs under
# Git Bash on Windows (Claude Code requires it there), macOS and Linux. ASCII only.
#
# Workspace resolution, in order:
#   1. TASK_OBSERVER_WS environment variable. The token {user} is replaced by the
#      current username, so a team can share ONE value such as
#      <team share>/skill-observations/{user} and each person gets a private folder.
#   2. Default: $HOME/.claude/skill-observations
# Never the current working directory - a cwd inside a temporary checkout is torn
# down and takes the observations with it.
#
# Fail-soft rule: if the PARENT of the workspace does not exist (a team share that
# is not mounted, a drive that is offline) the helper reports UNREACHABLE and exits 0
# without creating anything. Logging is skipped for that session; a second log is
# never created somewhere else.

set -u

me="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
user="${USERNAME:-${USER:-$(id -un 2>/dev/null || echo user)}}"
WS="${TASK_OBSERVER_WS:-$HOME/.claude/skill-observations}"
WS="${WS//\{user\}/$user}"
WS="${WS%/}"
LOG="$WS/observation-log"
ARCH="$LOG/archive"

cmd="${1:-status}"

# Print the frontmatter block (between the first two --- lines) of one file.
header_of() {
  awk 'NR==1 && /^---[[:space:]]*$/ {fm=1; next}
       fm && /^---[[:space:]]*$/ {exit}
       fm' "$1"
}

# Value of a scalar frontmatter field, brackets and trailing comments stripped.
field() {  # $1 = header text, $2 = field name
  printf '%s\n' "$1" | awk -v k="$2" -F': *' '$1==k {sub(/^[^:]*: */,""); print; exit}' \
    | sed -e 's/^\[//' -e 's/\]$//' -e 's/#.*$//' -e 's/[[:space:]]*$//'
}

# Best-effort: does a skill directory with this name exist anywhere the harness
# would load it from? Searches the project, the user skills dir and the plugin cache.
skill_exists() {  # $1 = skill name
  local n="$1"
  [ -d ".claude/skills/$n" ] && return 0
  [ -d "$HOME/.claude/skills/$n" ] && return 0
  [ -d "$HOME/.claude/plugins" ] && \
    find "$HOME/.claude/plugins" -maxdepth 7 -type d -name "$n" -path "*skills*" 2>/dev/null | grep -q . && return 0
  return 1
}

reachable() { [ -d "$(dirname "$WS")" ]; }

case "$cmd" in
  status)
    echo "task-observer: helper $me"
    if ! reachable; then
      echo "task-observer: workspace UNREACHABLE - parent of $WS does not exist (share not mounted?). Skip logging this session; do NOT create a log elsewhere."
      exit 0
    fi
    if [ ! -d "$LOG" ]; then
      echo "task-observer: workspace MISSING at $WS - run '$me init' once, then re-run status."
      exit 0
    fi
    n=$(ls "$LOG"/*.md 2>/dev/null | wc -l | tr -d ' ')
    parsed=0; open=0; parked=0; nosib=0; targets=""
    for f in "$LOG"/*.md; do
      [ -e "$f" ] || continue
      hdr=$(header_of "$f")
      [ -n "$hdr" ] || continue
      parsed=$((parsed + 1))
      st=$(field "$hdr" status); [ -z "$st" ] && st=open
      case "$st" in
        open)   open=$((open + 1))
                sib=$(field "$hdr" siblings_checked); [ -z "$sib" ] && nosib=$((nosib + 1))
                targets="$targets,$(field "$hdr" skill)" ;;
        parked) parked=$((parked + 1)) ;;
      esac
    done
    if [ "$n" -gt 0 ] && [ "$parsed" -eq 0 ]; then
      echo "task-observer: SCAN BROKEN - $n files present, 0 headers parsed. Fix before logging."
      exit 1
    fi
    last=$(cat "$WS/last-review-date.txt" 2>/dev/null || echo missing)
    age_days=""
    if [ "$last" != "never" ] && [ "$last" != "missing" ]; then
      now=$(date +%s); then_s=$(date -d "$last" +%s 2>/dev/null || echo "")
      [ -n "$then_s" ] && age_days=$(( (now - then_s) / 86400 ))
    fi
    staged=$(ls -d "$WS"/skill-updates/*/ 2>/dev/null | wc -l | tr -d ' ')
    missing=""
    for s in $(printf '%s' "$targets" | tr ',' '\n' | sed 's/^ *//;s/ *$//' | grep -v '^$' | sort -u); do
      skill_exists "$s" || missing="$missing $s"
    done
    agetxt=""; [ -n "$age_days" ] && agetxt=" (${age_days}d ago)"
    echo "task-observer: workspace $WS"
    echo "task-observer: $open open, $parked parked, $n active files; last review: $last$agetxt; staged update dirs: $staged"
    [ "$nosib" -gt 0 ] && echo "task-observer: $nosib open observation(s) logged WITHOUT a sibling check"
    [ -n "$missing" ] && echo "task-observer: open observations target skills that do not resolve here:$missing"
    if [ "$open" -gt 0 ]; then
      if [ "$last" = "never" ] || [ "$last" = "missing" ]; then
        echo "task-observer: backlog has NEVER been reviewed - offer the review in one line, do not gate the task on it"
      elif [ -n "$age_days" ] && [ "$age_days" -ge 7 ]; then
        echo "task-observer: last review is 7+ days old with open observations - offer the review in one line"
      fi
    fi
    exit 0 ;;

  init)
    if ! reachable; then
      echo "task-observer: cannot init - parent of $WS does not exist. Mount the share or fix TASK_OBSERVER_WS."; exit 1
    fi
    if [ -d "$LOG" ]; then echo "task-observer: workspace already exists at $WS"; exit 0; fi
    mkdir -p "$ARCH" "$WS/skill-updates" || { echo "task-observer: mkdir failed under $WS"; exit 1; }
    [ -e "$ARCH/.id-floor" ] || echo 0 > "$ARCH/.id-floor"
    [ -e "$WS/last-review-date.txt" ] || echo never > "$WS/last-review-date.txt"
    [ -e "$WS/checkpoints.log" ] || : > "$WS/checkpoints.log"
    if [ ! -e "$WS/cross-cutting-principles.md" ]; then
      cat > "$WS/cross-cutting-principles.md" <<'EOT'
# Cross-Cutting Principles

Principles that apply to all skills. Read as a mandatory checklist during any
skill creation, regeneration or staged update. Added by reviews.

---

## Active Principles

(none yet - a review adds entries in the form below)

### N. Principle title
**Added:** YYYY-MM-DD (source)
**Applies to:** all skills | all public skills | skills that ...
**Requirement:** what it requires
**Propagation:** immediate | opportunistic
**Status:** active
EOT
    fi
    if [ ! -e "$WS/skill-families.md" ]; then
      cat > "$WS/skill-families.md" <<'EOT'
# Skill families

Families of sibling skills (same methodology for different tools, same
structure for different subjects). The sibling check resolves every
observation target against this file. Add a family the first time an
observation would apply to more than one member.

## family-name
**Members:** skill-a, skill-b
**Coherence model:** synced-duplicates | shared-core
**Shared:** what every member should carry
**Member-specific:** what legitimately differs, and why
EOT
    fi
    # Verify the layout landed (a network share can accept mkdir and drop the files).
    for p in "$ARCH/.id-floor" "$WS/last-review-date.txt" "$WS/cross-cutting-principles.md" "$WS/skill-families.md"; do
      [ -s "$p" ] || { echo "task-observer: init INCOMPLETE - $p missing or empty"; exit 1; }
    done
    echo "task-observer: workspace created at $WS"
    exit 0 ;;

  scan)
    reachable && [ -d "$LOG" ] || { echo "task-observer: workspace unavailable at $WS"; exit 1; }
    n=$(ls "$LOG"/*.md 2>/dev/null | wc -l | tr -d ' ')
    parsed=0
    for f in "$LOG"/*.md; do
      [ -e "$f" ] || continue
      hdr=$(header_of "$f")
      [ -n "$hdr" ] && parsed=$((parsed + 1))
      printf '%s\n%s\n---\n' "$(basename "$f")" "$hdr"
    done
    [ "$n" -gt 0 ] && [ "$parsed" -eq 0 ] && { echo "SCAN COMMAND BROKEN - $n files present, 0 headers parsed"; exit 1; }
    echo "scanned $parsed of $n files"
    exit 0 ;;

  next-id)
    reachable && [ -d "$ARCH" ] || { echo "ID COMMAND BROKEN - workspace unavailable at $WS (run init, or the share is unreachable)"; exit 1; }
    hi=$( { ls "$LOG" "$ARCH" 2>/dev/null | grep -oE '^[0-9]+'; cat "$ARCH/.id-floor" 2>/dev/null; } \
         | sort -n | tail -1); : "${hi:=0}"
    if [ "$hi" -eq 0 ] && [ -n "$(ls "$LOG"/*.md 2>/dev/null)" ]; then
      echo "ID COMMAND BROKEN - log is non-empty but no ids extracted"; exit 1
    fi
    next=$((hi + 1))
    echo "$next" > "$ARCH/.id-floor"
    printf '%04d\n' "$next"
    exit 0 ;;

  archive)
    reachable && [ -d "$LOG" ] || { echo "task-observer: workspace unavailable at $WS"; exit 1; }
    mkdir -p "$ARCH"
    today=$(date +%F); moved=0
    for f in "$LOG"/*.md; do
      [ -e "$f" ] || continue
      hdr=$(header_of "$f")
      st=$(field "$hdr" status)
      case "$st" in actioned|declined|superseded) ;; *) continue ;; esac
      rd=$(field "$hdr" resolved)
      if [ -z "$rd" ]; then
        echo "no resolved: date on $(basename "$f") - set it to today ($today) and archive tomorrow"; continue
      fi
      # ISO dates sort lexically; archive only if strictly before today.
      if [ "$(printf '%s\n%s\n' "$rd" "$today" | sort | head -1)" = "$rd" ] && [ "$rd" != "$today" ]; then
        mv "$f" "$ARCH/" && moved=$((moved + 1)) && echo "archived $(basename "$f")"
      fi
    done
    echo "archived $moved file(s)"
    exit 0 ;;

  *)
    echo "usage: observe.sh {status|init|scan|next-id|archive}"; exit 2 ;;
esac
