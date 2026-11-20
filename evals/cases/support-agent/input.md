# HelpBot — design doc (fictional test document)

HelpBot is an LLM-powered customer-support agent for an online store.

## Guarantees

- **G1.** HelpBot never issues a refund over $100 without human approval.
- **G2.** HelpBot never reveals another customer's personal data.
- **G3.** HelpBot always hands off to a human when a customer asks for one.
- **G4.** HelpBot's answers are grounded in our help-center articles.
- **G5.** Conversations are not retained by our model provider.

## Implementation

- **Refunds.** HelpBot calls the `issue_refund(order_id, amount)` tool. The payments service enforces the cap: any amount over $100 is rejected unless the request carries a signed approval token, which only the human-agent console can mint.
- **Customer data.** The `lookup_orders` tool takes no customer-ID argument. The backend reads the customer ID from the authenticated chat session, so the model can only fetch the current customer's orders.
- **Human handoff.** The system prompt says: "If the customer asks for a human, call `escalate()` immediately." Each week a QA lead samples 50 transcripts and checks handoffs.
- **Grounding.** Every prompt or model change runs a 200-question eval suite in CI. A change ships only if at least 92% of answers cite a help-center article that supports them.
- **Provider retention.** We have a zero-data-retention agreement with our LLM provider.
