---
name: promise-check
description: Audit the promises a system makes (privacy, deletion, access, reliability, safety, AI agent behavior) and show which rung of the enforcement ladder actually enforces each one, from policy-only up to cryptography or hardware. Use it on design docs, PRDs, RFCs, PR descriptions, privacy whitepapers, READMEs, agent system prompts or architecture diagrams whenever someone asks "is this promise real?", "what does this system guarantee?", "review this for privacy or safety claims", or "where are we only promising by policy?", even if they never say "promise".
---

# promise-check

A promise is only as strong as the rung that enforces it. This skill finds every promise in the material you're given, places each one on the **enforcement ladder**, and reports where promises are real, partial, policy-only or contradicted.

Read `references/ladder.md` before the first audit in a session. It defines the six rungs and the evidence each one needs.

## Why this matters

Teams write "we never read your messages" or "the agent never issues refunds over $100" and then rely on people remembering the rule. Good systems turn promises into constraints the architecture enforces. The useful question isn't "is there a policy?" but "what stops this from happening, and how would we know?"

## Process

1. **Collect the material.** Read everything provided: docs, code paths, prompts, diagrams. If a URL is given and you can fetch it, read the source rather than relying on memory.
2. **Extract promises.** A promise is any statement that rules something out or guarantees something, explicit ("we never…", "only you can…", "always…", "within 30 days") or implied by a feature's name ("disappearing messages", "private mode"). Record where each one appears.
3. **Find the mechanism.** For each promise, look for what enforces it. Pick the **strongest rung that the material actually shows evidence for**, not the strongest one that sounds plausible. A rung without evidence doesn't count.
4. **Look for contradictions.** Check whether anything in the material shows the system can do what the promise rules out: an admin "view" tool, backups that outlive a deletion promise, a model choosing the customer ID. A contradiction outweighs any mechanism.
5. **Give a verdict:**
   - **Enforced:** rung 5 or 6 with evidence, and no contradiction.
   - **Partial:** rung 2–4, or rung 5–6 with a documented gap.
   - **Policy-only:** rung 1, meaning there's no mechanism beyond a statement or contract.
   - **Contradicted:** the material shows the system does, or can do, what the promise rules out.
   - **Unknown:** the material doesn't say enough to judge. Say what you'd need to see.
6. **Name the next rung.** For every promise that isn't Enforced, give one concrete change that would move it up a rung.

## Output

Lead with a one-line summary, e.g. "7 promises: 2 enforced, 2 partial, 2 policy-only, 1 contradicted."

Then the ledger:

| # | Promise | Kind | Rung | Mechanism and evidence | Verdict | Next rung |
|---|---|---|---|---|---|---|

- **Promise:** the promise in a few words, with where it came from (section, file or line).
- **Kind:** privacy · deletion/retention · access · reliability · integrity · safety · agent-behavior · compliance.
- **Rung:** 1–6, using the names in the ladder reference.

Close with **the three riskiest promises** (contradicted first, then policy-only promises users would care most about) and **questions to ask the team** when the material is silent.

### JSON (for evals or when asked)

When asked for machine-readable output, or when running an eval, also write the ledger as JSON in this shape:

```json
{
  "system": "name of the system audited",
  "promises": [
    {
      "id": "P1",
      "promise": "Only the user can read their notes",
      "source": "Privacy section, para 2",
      "kind": "access",
      "rung": 1,
      "rung_name": "policy",
      "mechanism": "what enforces it, or 'none found'",
      "evidence": "the specific line, component or doc section",
      "verdict": "policy-only",
      "next_rung": "one concrete change"
    }
  ],
  "summary": {"enforced": 0, "partial": 0, "policy_only": 1, "contradicted": 0, "unknown": 0}
}
```

`verdict` is one of `enforced`, `partial`, `policy-only`, `contradicted` or `unknown`. `rung` is an integer from 1 to 6, or `null` when the verdict is `unknown`.

## Judgment calls

- **A system prompt is policy, not architecture.** "The system prompt tells the agent never to…" is rung 1. A tool that refuses the action server-side is rung 5.
- **A contract is policy.** A vendor's zero-retention agreement is rung 1 for your system, however good the vendor is.
- **Rate each promise against the threat it names.** "Encrypted in transit" is about network eavesdroppers, so TLS 1.3 with certificate pinning is rung 6 for that promise, even though TLS ends at the operator's servers. "We can't read your data" is about the operator, so encryption only counts as rung 6 if the operator can't decrypt. Encryption at rest with keys the operator holds protects against stolen disks, not against the operator: rung 5 at best for operator promises.
- **A contradicted promise still gets a rung.** Record the strongest mechanism the material does show, so readers can see how far the system got before the contradiction.
- **Deletion promises include copies.** Backups, logs, analytics exports, caches, search indexes, replicas and linked devices are part of the promise.
- **Be fair to good systems.** When a mechanism is strong, say so plainly. The aim is accuracy, not a list of findings.
- **Stick to the material.** Don't invent mechanisms or weaknesses the material doesn't show. Mark them `unknown` and ask.
