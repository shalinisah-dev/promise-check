# Blind eval results

**Run:** 2026-11-20 · Claude Opus 5.5 · skill as committed, no edits during the run

**How it was kept blind:** a fresh session with no memory of writing the answer keys. It wrote every ledger before it opened any `expected.json` or the scorer. It read the public sources through a fetch step that returned an extraction of each page, not the raw HTML.

## Scores

| Case | Recall | Verdict | Rung |
|---|---|---|---|
| support-agent (synthetic) | 5/5 | 5/5 | 5/5 |
| notes-app-privacy (synthetic) | 5/5 | 4/5 | 4/5 |
| apple-private-cloud-compute | 5/5 | 5/5 | 5/5 |
| signal-sealed-sender | 3/3 | 1/3 | 2/3 |
| **Total** | **18/18 (100%)** | **15/18 (83%)** | **16/18 (89%)** |

Extra promises found beyond the keys aren't penalised: 3 for Apple, 3 for Signal. Some of them are good finds.

## The misses

| Case | Promise | The audit said | The key says |
|---|---|---|---|
| notes-app-privacy | no AI training | policy-only, rung 1: a policy plus a yearly acknowledgment is still a statement | partial, rung 2: the acknowledgment counts as process |
| signal-sealed-sender | server can't see the sender | partial, rung 6: it folded the IP and timing gap Signal admits into this promise | enforced, rung 6: judged against the envelope alone |
| signal-sealed-sender | hiding who talks to whom | the scorer matched it to a different promise (Signal doesn't store your social graph), rated policy-only | partial, rung 6 |

## What I'm changing

1. **Split a promise from the gap it admits.** This is the real miss. Sealed sender does exactly what it says. The metadata gap Signal names is a separate, bigger goal. The skill should record it as its own row, not downgrade the promise that holds.
2. **Say whether an acknowledgment is process or policy.** The ladder is ambiguous here, so either answer is defensible. I'll pick one and write it down.
3. **Fix the scorer's matching.** It pairs each key with the first audit row whose text matches a keyword. "Social graph" appears in two Signal promises, so the pairing went wrong. Matching on the best fit instead of the first one fixes that.
