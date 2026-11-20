#!/usr/bin/env python3
"""Score promise-check ledgers against expected answers.

Usage:
    python3 evals/score.py evals/cases/<case>/expected.json out/<case>.json
    python3 evals/score.py --all out/        # scores every case that has out/<case>.json

For each expected promise, the script finds the first unused ledger promise whose
"promise" text matches every keyword (case-insensitive regex). It reports:
  - recall:   expected promises the ledger found
  - verdict:  matched promises with the right verdict ("verdict" may be a list of
              acceptable verdicts when the source leaves a defensible choice)
  - rung:     matched promises whose rung is within the case's tolerance
Extra promises in the ledger aren't penalized; read them by hand.
No third-party dependencies.
"""
import json
import re
import sys
from pathlib import Path

CASES = Path(__file__).parent / "cases"


def load(path):
    with open(path) as f:
        return json.load(f)


def norm_verdict(v):
    return (v or "").strip().lower().replace("_", "-").replace(" ", "-")


def score(expected, ledger):
    tol = expected.get("rung_tolerance", 0)
    found = ledger.get("promises", [])
    used = set()
    rows = []
    for exp in expected["promises"]:
        match = None
        for i, got in enumerate(found):
            if i in used:
                continue
            text = got.get("promise", "")
            if all(re.search(k, text, re.I) for k in exp["keywords"]):
                match = i
                break
        if match is None:
            rows.append((exp["id"], "MISSING", "", ""))
            continue
        used.add(match)
        got = found[match]
        want = exp["verdict"] if isinstance(exp["verdict"], list) else [exp["verdict"]]
        v_ok = norm_verdict(got.get("verdict")) in {norm_verdict(w) for w in want}
        if exp.get("rung") is None:
            r_ok = True  # contradicted or unknown: rung isn't scored
        else:
            r = got.get("rung")
            r_ok = isinstance(r, int) and abs(r - exp["rung"]) <= tol
        rows.append((exp["id"], "found", "ok" if v_ok else f"got {got.get('verdict')} want {exp['verdict']}",
                     "ok" if r_ok else f"got {got.get('rung')} want {exp['rung']}"))
    n = len(expected["promises"])
    hits = [r for r in rows if r[1] == "found"]
    return {
        "case": expected.get("case"),
        "recall": len(hits) / n if n else 0,
        "verdict_acc": sum(r[2] == "ok" for r in hits) / len(hits) if hits else 0,
        "rung_acc": sum(r[3] == "ok" for r in hits) / len(hits) if hits else 0,
        "rows": rows,
        "extra": len(found) - len(used),
    }


def report(res):
    print(f"\n## {res['case']}")
    print(f"recall {res['recall']:.0%} · verdict {res['verdict_acc']:.0%} · rung {res['rung_acc']:.0%} · extra promises {res['extra']}")
    for pid, status, verdict, rung in res["rows"]:
        print(f"  - {pid}: {status}" + (f" | verdict {verdict} | rung {rung}" if status == "found" else ""))


def main(argv):
    if len(argv) == 3 and argv[1] == "--all":
        out_dir = Path(argv[2])
        results = []
        for case_dir in sorted(CASES.iterdir()):
            out = out_dir / f"{case_dir.name}.json"
            if out.exists():
                results.append(score(load(case_dir / "expected.json"), load(out)))
        for r in results:
            report(r)
        if not results:
            print(f"No ledgers found in {out_dir}")
        return 0
    if len(argv) == 3:
        report(score(load(argv[1]), load(argv[2])))
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
