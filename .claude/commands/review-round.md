---
description: Run one reductive-review round against a document using the frozen panel.
argument-hint: docs/design/<your-doc>.md
---

Run one reductive-review round against $ARGUMENTS using the frozen panel in
`.claude/agents/`.

1. Determine the next round number NNN (one past the highest `round-NNN.md`).
2. **Spawn every critic in parallel.** Each does a **fresh full read** of the current
   document version and writes graded findings (format in `docs/reviews/README.md`)
   to `docs/reviews/rounds/round-NNN/<role>.md`.
3. Apply the **anti-rubber-stamp guards**: force the fresh full read, **perturb each
   critic's prompt** from last round (reorder/reword the checklist), and treat any
   sudden collapse to zero findings with suspicion.
4. Then act as **ARBITER**:
   - Aggregate and de-duplicate into `docs/reviews/rounds/round-NNN.md` with
     per-critic counts and a BLOCKER/FINDING/ADVISORY table.
   - Decide what gets acted on and **record why**; resolve disagreements rather than
     averaging them. If any critic re-graded a finding down to advisory, scrutinize
     it and decide explicitly whether to fix or defer.
   - List the **exact document revisions required**.
   - State explicitly whether the panel has **converged** (0 BLOCKER, 0 FINDING, and
     every critic reports nothing material to add, a lone ADVISORY does not block
     convergence).
5. If not converged: revise the document per the round's decisions, **bump its
   version with a changelog entry**, and run another round.

Never hand-edit the target doc outside a round's recorded decisions.
