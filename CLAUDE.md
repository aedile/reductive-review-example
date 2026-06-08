# CLAUDE.md — how to work in this repo

This repository demonstrates **reductive review**. The protocol of record is
[`docs/reviews/README.md`](docs/reviews/README.md); read it before doing review work.

- The document under review lives in `docs/design/`. It is fictional and
  intentionally flawed — a teaching artifact, never to be presented as sound.
- Improve documents only through the reductive loop: panel → graded findings →
  arbiter → versioned revision → repeat to convergence. Never hand-edit the target
  doc outside a round's recorded decisions.
- Freeze the panel for the duration of a descent. Changing the panel starts a new
  run; it resets the convergence signal.
- Apply the anti-rubber-stamp guards in the protocol every round: fresh full read,
  perturbed prompts, and suspicion (not celebration) when findings suddenly collapse
  to zero. Re-grading a finding to advisory must be recorded and decided, never used
  as a quiet way to ignore it.
- When committing, sequence commits so the git history shows the descent:
  doc v0.1 → round-001 → doc v0.2 → round-002 → … → doc v0.6 → round-006.
- Keep everything fictional. Do not add real or proprietary content.
