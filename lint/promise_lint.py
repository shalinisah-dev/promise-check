#!/usr/bin/env python3
"""promise-lint: keep every promise in your docs and prompts tied to what enforces it.

Finds promise language ("never", "always", "guarantee", "within 30 days"...) in
design docs, READMEs and agent system prompts, and checks each one against a
ledger file (promises.json). It fails CI when:

  * a ledger entry claims rung 3+ (test, monitoring, architecture, crypto) but the
    file that enforces it no longer exists, or no longer contains its anchor
    (enforcement drift: the promise stayed, the guard was deleted);
  * a ledger entry's promise text is no longer found anywhere (stale ledger);
  * with --strict, a promise sentence has no ledger entry at all.

Stdlib only. Python 3.8+.
"""
import argparse
import fnmatch
import json
import os
import re
import sys

RUNGS = {1: "policy", 2: "process", 3: "test", 4: "monitoring", 5: "architecture", 6: "crypto/hardware"}

PROMISE_PATTERNS = [
    r"\bnever\b", r"\balways\b", r"\bguarantee[sd]?\b", r"\bwill not\b", r"\bwon't\b",
    r"\bmust not\b", r"\bcannot\b", r"\bcan't\b", r"\bat no point\b", r"\bunder no circumstances\b",
    r"\bonly (?:with|after|if|when)\b", r"\bwithin \d+ (?:seconds?|minutes?|hours?|days?)\b",
    r"\b(?:is|are) not (?:retained|stored|logged|shared|sold|used)\b",
    r"\bend-to-end encrypted\b", r"\bpermanently (?:deleted|erased)\b",
]
PROMISE_RE = re.compile("|".join(PROMISE_PATTERNS), re.IGNORECASE)
# Sentences that talk *about* promises rather than make one.
SKIP_RE = re.compile(r"promise-lint:\s*ignore", re.IGNORECASE)

DEFAULT_INCLUDE = ["**/*.md", "**/*prompt*.txt", "**/*prompt*.md", "**/*.prompt"]
DEFAULT_EXCLUDE = ["**/node_modules/**", "**/.git/**", "**/vendor/**", "CHANGELOG.md", "**/CHANGELOG.md"]


def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[*_`>#]", "", s)).strip().lower()


def split_sentences(text):
    """Yield (line_no, sentence) for prose and list items. Skips fenced code."""
    in_fence = False
    for i, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if line.startswith("```") or line.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence or not line or line.startswith("|---") or line.startswith("#"):
            continue
        for part in re.split(r"(?<=[.!?])\s+(?=[A-Z\"'*])", line):
            part = part.strip(" -*|")
            if len(part) > 12:
                yield i, part


def match_glob(path, patterns):
    p = path.replace(os.sep, "/")
    for pat in patterns:
        if fnmatch.fnmatch(p, pat) or fnmatch.fnmatch(p, pat.replace("**/", "")):
            return True
    return False


def find_files(root, include, exclude):
    out = []
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in (".git", "node_modules", "vendor", "__pycache__")]
        for f in files:
            rel = os.path.relpath(os.path.join(d, f), root)
            if match_glob(rel, include) and not match_glob(rel, exclude):
                out.append(rel)
    return sorted(out)


def scan(root, files):
    found = []
    for rel in files:
        try:
            with open(os.path.join(root, rel), encoding="utf-8") as fh:
                text = fh.read()
        except (UnicodeDecodeError, OSError):
            continue
        for line_no, sent in split_sentences(text):
            if PROMISE_RE.search(sent) and not SKIP_RE.search(sent):
                found.append({"file": rel, "line": line_no, "text": sent})
    return found


def load_ledger(path):
    if not path or not os.path.exists(path):
        return {"promises": []}
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    for i, p in enumerate(data.get("promises", [])):
        if "match" not in p or "rung" not in p:
            raise ValueError("ledger entry %d needs 'match' and 'rung'" % i)
        if not (isinstance(p["rung"], int) and 1 <= p["rung"] <= 6):
            raise ValueError("ledger entry %d: rung must be an int 1-6" % i)
    return data


def check_enforcement(root, entry):
    """Return an error string if a rung-3+ claim has lost its enforcer, else None."""
    if entry["rung"] < 3:
        return None
    enf = entry.get("enforced_by")
    if not enf:
        return "claims rung %d (%s) but names no enforced_by file" % (entry["rung"], RUNGS[entry["rung"]])
    path = enf.get("path") if isinstance(enf, dict) else enf
    anchor = enf.get("contains") if isinstance(enf, dict) else None
    full = os.path.join(root, path)
    if not os.path.exists(full):
        return "enforced_by %s no longer exists" % path
    if anchor:
        with open(full, encoding="utf-8", errors="replace") as fh:
            if anchor not in fh.read():
                return "enforced_by %s no longer contains %r" % (path, anchor)
    return None


def lint(root, ledger_path, include=None, exclude=None):
    include = include or DEFAULT_INCLUDE
    exclude = (exclude or []) + DEFAULT_EXCLUDE
    ledger = load_ledger(ledger_path)
    ledger_rel = os.path.relpath(ledger_path, root) if ledger_path else None
    files = [f for f in find_files(root, include, exclude) if f != ledger_rel]
    found = scan(root, files)
    entries = ledger.get("promises", [])

    for f in found:
        n = norm(f["text"])
        f["entry"] = next((e for e in entries if norm(e["match"]) in n), None)

    results = {"promises": found, "drift": [], "stale": [], "unledgered": []}
    for e in entries:
        if not any(f["entry"] is e for f in found):
            results["stale"].append(e)
        err = check_enforcement(root, e)
        if err:
            results["drift"].append(dict(e, error=err))
    results["unledgered"] = [f for f in found if f["entry"] is None]
    return results


def report_md(results):
    found = results["promises"]
    ledgered = [f for f in found if f["entry"]]
    hist = {}
    for f in ledgered:
        hist[f["entry"]["rung"]] = hist.get(f["entry"]["rung"], 0) + 1
    low = sum(v for k, v in hist.items() if k <= 2)
    lines = ["## promise-lint", ""]
    lines.append("%d promise sentences found; %d in the ledger, %d not." % (len(found), len(ledgered), len(results["unledgered"])))
    if ledgered:
        lines.append("Ledgered promises enforced only by policy or process (rungs 1–2): **%d of %d**." % (low, len(ledgered)))
    lines.append("")
    if results["drift"]:
        lines += ["### Enforcement drift (fails the check)", "", "| Promise | Claimed rung | Problem |", "|---|---|---|"]
        for e in results["drift"]:
            lines.append("| %s | %d · %s | %s |" % (e.get("id", e["match"]), e["rung"], RUNGS[e["rung"]], e["error"]))
        lines.append("")
    if results["stale"]:
        lines += ["### Stale ledger entries", "", "These ledger entries no longer match any text. Update `match` or remove them.", ""]
        lines += ["- `%s`" % e.get("id", e["match"]) for e in results["stale"]] + [""]
    if ledgered:
        lines += ["### Ledger", "", "| Promise | Where | Rung | Enforced by |", "|---|---|---|---|"]
        for f in ledgered:
            e = f["entry"]
            enf = e.get("enforced_by")
            enf = (enf.get("path") if isinstance(enf, dict) else enf) or "—"
            lines.append("| %s | `%s:%d` | %d · %s | %s |" % (e.get("id", e["match"]), f["file"], f["line"], e["rung"], RUNGS[e["rung"]], enf))
        lines.append("")
    if results["unledgered"]:
        lines += ["### Promises with no ledger entry", "",
                  "Each of these reads like a guarantee. Add it to `promises.json` with the rung that enforces it, "
                  "or mark the line `promise-lint: ignore`.", ""]
        for f in results["unledgered"][:50]:
            lines.append("- `%s:%d` %s" % (f["file"], f["line"], f["text"][:160]))
        if len(results["unledgered"]) > 50:
            lines.append("- …and %d more" % (len(results["unledgered"]) - 50))
        lines.append("")
    lines.append("<sub>Rungs: 1 policy · 2 process · 3 test · 4 monitoring · 5 architecture · 6 crypto/hardware. "
                 "Deeper audit: the promise-check skill.</sub>")
    return "\n".join(lines)


def init_ledger(results):
    return {"promises": [
        {"id": "P%d" % (i + 1), "match": f["text"][:80], "rung": 1,
         "note": "TODO: set the real rung; for 3+ add enforced_by {path, contains}",
         "source": "%s:%d" % (f["file"], f["line"])}
        for i, f in enumerate(results["promises"])]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--ledger", default=None, help="ledger path (default: <root>/promises.json)")
    ap.add_argument("--include", action="append", help="glob of files to scan (repeatable)")
    ap.add_argument("--exclude", action="append", help="glob of files to skip (repeatable)")
    ap.add_argument("--strict", action="store_true", help="fail on promises with no ledger entry")
    ap.add_argument("--init", action="store_true", help="print a starter ledger for every promise found")
    ap.add_argument("--format", choices=["md", "json"], default="md")
    a = ap.parse_args(argv)
    ledger = a.ledger or os.path.join(a.root, "promises.json")
    try:
        res = lint(a.root, ledger, a.include, a.exclude)
    except ValueError as e:
        print("promise-lint: bad ledger: %s" % e, file=sys.stderr)
        return 2
    if a.init:
        print(json.dumps(init_ledger(res), indent=2))
        return 0
    if a.format == "json":
        clean = {k: [{kk: vv for kk, vv in x.items() if kk != "entry"} for x in v] for k, v in res.items()}
        print(json.dumps(clean, indent=2))
    else:
        md = report_md(res)
        print(md)
        summ = os.environ.get("GITHUB_STEP_SUMMARY")
        if summ:
            with open(summ, "a", encoding="utf-8") as fh:
                fh.write(md + "\n")
    failed = bool(res["drift"]) or (a.strict and bool(res["unledgered"]))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
