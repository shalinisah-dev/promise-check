# The enforcement ladder

A promise is only as strong as the rung that enforces it. Place each promise on the **strongest rung that the material shows evidence for**.

| Rung | Name | What enforces the promise | Evidence to look for | Typical weakness |
|---|---|---|---|---|
| 6 | Cryptography or hardware | Math or silicon: no one, including the operator, can break it, and clients can often verify that | End-to-end encryption with keys only users hold; trusted execution environments with remote attestation the client checks; transparency logs; secure enclaves | Metadata outside the encrypted payload; trusting the attestation chain |
| 5 | Architecture | The system is built so the forbidden action can't happen: no code path, permission or data exists for it | Server-side checks the caller can't bypass; identity taken from the session, not from input; data never collected or stored; capability removed (no admin read path); automatic hard deletion | Copies the design forgot (backups, logs, exports); later changes reintroducing the path |
| 4 | Monitoring | The live system is watched continuously, so a break is detected fast | Alerts, audits of access logs, anomaly detection, canaries, data-flow scanners on production | Detects after the fact; only as good as what's instrumented |
| 3 | Test | A check fails before a break ships | Unit or integration tests, eval suites with thresholds in CI, static analysis, policy-as-code gates | Covers only the cases someone thought of at build time |
| 2 | Process | People are meant to catch it | Reviews, approvals, launch checklists, manual sampling, training | Depends on attention under deadline pressure |
| 1 | Policy | A sentence in a doc, a prompt or a contract; nothing technical enforces it | "We never…", terms of service, system-prompt instructions, vendor agreements | Holds only while everyone remembers and agrees |

## Why monitoring sits above test

Tests check the code paths someone anticipated, at build time. Monitoring checks the running system continuously, including configuration drift and paths no test covered. Both are weaker than architecture, because they detect a problem rather than make it impossible.

## Verdicts

- **Enforced:** rung 5 or 6 with evidence, and no contradiction.
- **Partial:** rung 2–4, or rung 5–6 with a documented gap.
- **Policy-only:** rung 1.
- **Contradicted:** the material shows the system does, or can do, what the promise rules out. This outranks any mechanism.
- **Unknown:** there isn't enough material to judge.

## Moving a promise up a rung (common moves)

- Policy → test: turn the rule into an eval or test that runs in CI with a pass threshold.
- Test → monitoring: run the same check against production traffic or logs, and alert on failure.
- Process → architecture: remove the capability, so there's no admin read path and nothing for a reviewer to approve.
- Architecture → cryptography: move the keys to users, or move processing into attested hardware the client verifies.
- For deletion: track every copy (backups, logs, exports, caches, devices) and give each one a deadline or cryptographic erasure.
