# Acme Notes — Privacy overview (fictional test document)

Acme Notes is the privacy-first notes app. Your thoughts belong to you.

## Our promises

1. **We never read your notes.** Your notes are yours alone.
2. **Only you can access your notes.**
3. **Deleted notes are permanently erased within 30 days.**
4. **Your notes are encrypted in transit.**
5. **We don't use your notes to train AI models.**

## How it works

- Notes are stored in our Postgres cluster, encrypted at rest with AWS KMS keys that Acme manages.
- Notes sync between devices over TLS 1.3. Our apps pin our server certificate.
- To help with support tickets, our support team has an admin console with a "View note" button. Using it requires approval from the agent's manager, recorded in the ticket.
- When you delete a note, we set a `deleted_at` flag. A nightly job hard-deletes rows whose `deleted_at` is older than 30 days.
- Database backups are taken daily and kept for 90 days.
- Our analytics pipeline exports note titles and word counts to our data warehouse to improve search ranking.
- Our AI policy prohibits training models on customer content. All employees acknowledge this policy yearly.
