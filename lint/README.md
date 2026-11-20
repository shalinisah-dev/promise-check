# promise-lint

**Your README says "never." Does your code still agree?**

promise-check audits a system once. promise-lint keeps it honest on every PR. It finds promise language in docs and agent prompts ("never", "always", "within 30 days", "not retained"), ties each promise to a rung on the enforcement ladder in `promises.json`, and fails CI when the thing that enforces a promise disappears.

The failure it catches: someone refactors away the refund gate, the eval suite, or the alert, and the README still says "never." The promise stays; the guard is gone. That's **enforcement drift**.

## Use it

```yaml
# .github/workflows/promises.yml
on: [pull_request]
jobs:
  promises:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: shalinisah-dev/promise-check@v0
        with:
          strict: "false"   # true = also fail on promises with no ledger entry
```

Or locally, no install, stdlib Python:

```bash
python3 lint/promise_lint.py .            # report
python3 lint/promise_lint.py . --init > promises.json   # starter ledger, every promise at rung 1
```

## The ledger

```json
{"promises": [
  {"id": "refund-cap", "match": "never issues a refund over $100", "rung": 5,
   "enforced_by": {"path": "payments/refund_gate.py", "contains": "verify_signed_approval"}},
  {"id": "handoff", "match": "always hands off to a human", "rung": 2,
   "note": "System prompt + weekly QA sample"}
]}
```

- `match`: a phrase from the promise sentence (case and markdown are ignored).
- `rung`: 1 policy · 2 process · 3 test · 4 monitoring · 5 architecture · 6 crypto/hardware.
- `enforced_by`: required for rung 3 and up. The check fails if the file is gone or no longer contains `contains`.

## What fails the check

| Problem | Fails? |
|---|---|
| A rung 3+ promise's `enforced_by` file is deleted, or loses its anchor | Yes |
| A rung 3+ promise names no `enforced_by` | Yes |
| A promise sentence has no ledger entry | Only with `strict` |
| A ledger entry matches no text anymore | Reported, not failed |

The report also says how many of your promises are enforced only by policy or process. It's written to the job summary on GitHub.

Silence a sentence that isn't a promise with `promise-lint: ignore` on the same line.

See `examples/helpbot` for a complete repo.
