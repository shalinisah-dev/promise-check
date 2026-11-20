# Evals

Each case in `cases/` has an `input.md` (the material to audit) and an `expected.json` (the promises a good audit should find, with verdict and rung).

| Case | Type | Ground truth |
|---|---|---|
| `notes-app-privacy` | Synthetic trap | Exact: contradictions hidden in an admin console, provider-held keys and 90-day backups |
| `support-agent` | Synthetic trap | Exact: architecture vs. system-prompt vs. CI-eval enforcement for an LLM agent |
| `apple-private-cloud-compute` | Public | Verified against the source (2026-11-19) |
| `signal-sealed-sender` | Public | Verified against the source (2026-11-19) |

## Run

1. Have an agent with the skill installed audit each case and write JSON. With Claude Code:

   ```bash
   claude -p "Use the promise-check skill on evals/cases/support-agent/input.md. Write the JSON ledger to out/support-agent.json."
   ```

2. Score:

   ```bash
   python3 evals/score.py --all out/
   ```

The score reports recall (did it find each promise?), verdict accuracy and rung accuracy (within the case's tolerance). Extra promises aren't penalized, so read them yourself: a good audit often finds more than the key.
