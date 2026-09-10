"""stop_check.py -- decide whether a loop-gauntlet run should continue or stop.

Reads every compare/<tag>_review.json whose tag matches iter\\d+ (sorted by
the number in the tag). Each review file has the shape:

    {"tag": "iter03", "scores": {"<view>": [ints, one per rubric entry]},
     "gaps": ["..."], "next": "...", "notes": "..."}

Validates every view in the spec is present and every score list has
exactly len(rubric) integers in 1..5 -- on failure this exits 2 naming the
file and the field that failed, rather than silently skipping a bad record.

Decision order (first match wins):
  (a) TARGET MET     -- the last `consecutive_passes` iterations each have
                         every score (every view, every criterion) >= pass_score.
  (b) MAX ITERATIONS -- iteration count >= max_iterations.
  (c) STALLED        -- for the last `no_improvement_streak` iterations,
                         NEITHER the global minimum score NOR the total score
                         improved over the best seen before them. Improvement
                         on EITHER measure resets the streak -- this dual
                         rule exists because a global-minimum-only rule froze
                         a real run while four of six views were still
                         improving on total. A stall is only allowed once
                         `min_iterations` (optional, default 0) have run, so
                         the later fix tiers get iterations of their own.
  otherwise CONTINUE.

Usage:
    python stop_check.py --spec gauntlet_spec.json [--json]

Flags:
    --spec PATH   path to the gauntlet spec JSON (required)
    --json        print the decision as a JSON object instead of a human table
"""
import argparse
import json
import re
import sys
from pathlib import Path

TAG_RE = re.compile(r"^(iter(\d+))_review\.json$")


def load_spec(spec_path):
    if not spec_path.exists():
        print("ERROR: spec file not found: {0}".format(spec_path), file=sys.stderr)
        sys.exit(2)
    try:
        with open(spec_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        print("ERROR: spec file is not valid JSON: {0} ({1})".format(spec_path, exc), file=sys.stderr)
        sys.exit(2)


def _fail(review_path, field, detail):
    print(
        "ERROR: malformed review file {0}: field '{1}' {2}".format(review_path, field, detail),
        file=sys.stderr,
    )
    sys.exit(2)


def collect_reviews(compare_dir, views, rubric):
    """Load, validate and score every iterNN_review.json under compare_dir.

    Returns a list of iteration records sorted by iteration number, each:
    {"tag", "num", "scores", "global_min", "total", "per_view_sum", "lowest"}.
    """
    view_names = [v["name"] for v in views]
    rubric_len = len(rubric)
    rubric_names = [r["name"] for r in rubric]

    found = []
    if compare_dir.exists():
        for path in compare_dir.iterdir():
            m = TAG_RE.match(path.name)
            if m:
                found.append((int(m.group(2)), m.group(1), path))
    found.sort(key=lambda x: x[0])

    iterations = []
    for num, tag, path in found:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                review = json.load(fh)
        except json.JSONDecodeError as exc:
            _fail(path, "<file>", "is not valid JSON ({0})".format(exc))

        if "scores" not in review or not isinstance(review["scores"], dict):
            _fail(path, "scores", "is missing or is not an object")
        scores = review["scores"]

        for vname in view_names:
            if vname not in scores:
                _fail(path, "scores.{0}".format(vname), "is missing (every spec view must be scored)")
            row = scores[vname]
            if not isinstance(row, list) or len(row) != rubric_len:
                _fail(
                    path,
                    "scores.{0}".format(vname),
                    "must be a list of exactly {0} ints (one per rubric entry), got {1}".format(
                        rubric_len, row
                    ),
                )
            for i, s in enumerate(row):
                if not isinstance(s, int) or isinstance(s, bool) or not (1 <= s <= 5):
                    _fail(
                        path,
                        "scores.{0}[{1}]".format(vname, i),
                        "must be an int in 1..5, got {0!r}".format(s),
                    )

        all_scores = [s for vname in view_names for s in scores[vname]]
        global_min = min(all_scores)
        total = sum(all_scores)
        per_view_sum = {vname: sum(scores[vname]) for vname in view_names}

        lowest_view, lowest_criterion, lowest_val = None, None, None
        for vname in view_names:
            for i, s in enumerate(scores[vname]):
                if lowest_val is None or s < lowest_val:
                    lowest_val = s
                    lowest_view = vname
                    lowest_criterion = rubric_names[i]

        iterations.append(
            {
                "tag": tag,
                "num": num,
                "scores": scores,
                "global_min": global_min,
                "total": total,
                "per_view_sum": per_view_sum,
                "lowest": {"view": lowest_view, "criterion": lowest_criterion},
            }
        )
    return iterations


def compute_streak(iterations):
    """Current no-improvement streak plus the best min/total seen before it."""
    if not iterations:
        return 0, None, None
    best_min = iterations[0]["global_min"]
    best_total = iterations[0]["total"]
    streak = 0
    for it in iterations[1:]:
        improved = it["global_min"] > best_min or it["total"] > best_total
        if improved:
            streak = 0
            best_min = max(best_min, it["global_min"])
            best_total = max(best_total, it["total"])
        else:
            streak += 1
    return streak, best_min, best_total


def decide(iterations, stop_cfg):
    pass_score = stop_cfg["pass_score"]
    consecutive_passes = stop_cfg["consecutive_passes"]
    max_iterations = stop_cfg["max_iterations"]
    no_improvement_streak = stop_cfg["no_improvement_streak"]

    n = len(iterations)
    streak, best_min, best_total = compute_streak(iterations)
    decision, reason = "continue", "CONTINUE"

    if n >= consecutive_passes and n > 0:
        last_k = iterations[-consecutive_passes:]

        def all_pass(it):
            return all(s >= pass_score for row in it["scores"].values() for s in row)

        if all(all_pass(it) for it in last_k):
            decision, reason = "stop", "TARGET_MET"

    if decision == "continue" and n >= max_iterations and n > 0:
        decision, reason = "stop", "MAX_ITERATIONS"

    # v1.2.0: a stall cannot fire before `min_iterations` (default 0 = off).
    # A builder that follows the fix priority (composition first) plateaus on
    # structure early; without a floor the stall rule fired at iteration 5 on
    # a real run before the materials tier had a single iteration of its own.
    min_iterations = int(stop_cfg.get("min_iterations", 0) or 0)
    if decision == "continue" and streak >= no_improvement_streak and n >= min_iterations:
        decision, reason = "stop", "STALLED"

    return decision, reason, streak, best_min, best_total


def compute(spec):
    working_folder = Path(spec["working_folder"])
    compare_dir = working_folder / "compare"
    views = spec["views"]
    rubric = spec["rubric"]
    stop_cfg = spec["stop"]

    iterations = collect_reviews(compare_dir, views, rubric)
    decision, reason, streak, best_min, best_total = decide(iterations, stop_cfg)

    if iterations:
        last = iterations[-1]
        global_min, total = last["global_min"], last["total"]
        per_view_total, lowest = last["per_view_sum"], last["lowest"]
    else:
        global_min, total, per_view_total, lowest = None, None, {}, None

    return {
        "decision": decision,
        "reason": reason,
        "count": len(iterations),
        "iterations": iterations,
        "global_min": global_min,
        "total": total,
        "best_min": best_min,
        "best_total": best_total,
        "streak": streak,
        "lowest": lowest,
        "per_view_total": per_view_total,
    }


def print_human(spec, result):
    print("iteration table:")
    print("{0:<10}{1:>6}{2:>8}  lowest".format("tag", "min", "total"))
    for it in result["iterations"]:
        low = "{0}/{1}".format(it["lowest"]["view"], it["lowest"]["criterion"])
        print("{0:<10}{1:>6}{2:>8}  {3}".format(it["tag"], it["global_min"], it["total"], low))
    print("")
    print(
        "streak={0} best_min={1} best_total={2}".format(
            result["streak"], result["best_min"], result["best_total"]
        )
    )
    print("DECISION: {0} -- {1}".format(result["decision"].upper(), result["reason"]))


def main():
    parser = argparse.ArgumentParser(
        description="Decide continue/stop for a loop-gauntlet run from its compare/<tag>_review.json files."
    )
    parser.add_argument("--spec", required=True, help="path to the gauntlet spec JSON")
    parser.add_argument("--json", action="store_true", help="print the decision as a JSON object")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    spec = load_spec(spec_path)
    working_folder = Path(spec["working_folder"])
    print("working_folder: {0}".format(working_folder))
    print("compare_dir:    {0}".format(working_folder / "compare"))

    result = compute(spec)

    if args.json:
        out = {
            "decision": result["decision"],
            "reason": result["reason"],
            "iterations": result["count"],
            "global_min": result["global_min"],
            "total": result["total"],
            "best_min": result["best_min"],
            "best_total": result["best_total"],
            "streak": result["streak"],
            "lowest": result["lowest"],
            "per_view_total": result["per_view_total"],
        }
        print(json.dumps(out, indent=2))
    else:
        print_human(spec, result)

    sys.exit(0)


if __name__ == "__main__":
    main()
