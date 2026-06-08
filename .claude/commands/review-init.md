---
description: Propose and freeze an adversarial review panel for a document.
argument-hint: docs/design/<your-doc>.md
---

Analyze the document at $ARGUMENTS.

1. Read the document and the protocol in `docs/reviews/README.md`.
2. Propose a panel of **3-6 adversarial critics appropriate to the document's
   DOMAIN, not its specific claims** (a critic spun up to agree with the document
   will agree). For each lens, give a one-line mandate.
3. For each proposed critic **not already present in `.claude/agents/`**, draft an
   agent file using the template and protocol in `docs/reviews/` (a standing brief in
   `docs/reviews/prompts/` plus a matching subagent in `.claude/agents/`).
4. **Present the proposed panel for human approval BEFORE writing any files.**
5. Once approved, **freeze the panel for the run.** Changing the panel later starts a
   new run and resets the convergence signal.

Do not start a review round here, `review-init` only proposes and freezes the panel.
