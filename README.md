# Reductive Review — a worked example

A small, public, runnable example of **reductive review**: improving a document by
repeatedly subjecting it to a panel of adversarial AI critics and driving the count
of legitimate objections down to zero.

Companion to the article in [`docs/blog/reductive-descent.md`](docs/blog/reductive-descent.md).

The document under review — a passwordless "magic link" login spec — is
**fictional and deliberately imperfect**. It exists to be torn apart so you can
watch the technique work. Read the rounds in order and watch the objection count
fall — not smoothly: in five of the six rounds a fix introduced a *new* problem the
next round caught. That non-monotonic descent is the honest part, and the loop is
what kept catching the regressions until the panel genuinely had nothing left.

> The review history here was produced by **actually running the loop** — four
> independent critic subagents per round, six rounds, an arbiter between each — not by
> hand-authoring a tidy story. The findings are the agents' own; the counts are
> whatever they actually found. The whole process is meant to be inspected end to end:
> the critiques are in [`rounds/`](docs/reviews/rounds/) and the timing/cost of every
> agent run is in [`RUN-LOG.md`](docs/reviews/RUN-LOG.md).

## The idea in one paragraph

Most agent-assisted review is additive and one-shot: "review this, suggest
improvements," apply some, move on. There's no notion of *done*. Reductive review
inverts that. The goal isn't more suggestions — it's to shrink the set of
legitimate, material criticisms that remain, round over round, until a panel of
adversarial critics can't find anything material left. You aren't adding to the
document; you're subtracting from the pile of things still wrong with it.

## What's in here

- [`docs/design/magic-link-auth.md`](docs/design/magic-link-auth.md) — the target
  document, versioned (v0.1 → v0.6, changelog at the bottom).
- [`docs/reviews/README.md`](docs/reviews/README.md) — the protocol: panel, findings
  format, arbiter, termination. **This is the reusable part.**
- [`docs/reviews/prompts/`](docs/reviews/prompts/) — one standing brief per critic.
- [`docs/reviews/rounds/`](docs/reviews/rounds/) — the actual review history. Start
  at [`round-001.md`](docs/reviews/rounds/round-001.md).
- [`docs/reviews/RUN-LOG.md`](docs/reviews/RUN-LOG.md) — the meter: per-critic
  duration, tokens, and tool calls for all 24 agent runs. How long it took, what it cost.
- [`.claude/agents/`](.claude/agents/) + [`.claude/commands/`](.claude/commands/) —
  wiring to run a round in one command.

## How to run it

1. `/review-init docs/design/<your-doc>.md` — proposes the right panel for the
   document and drafts any missing critics from the examples. You approve/edit.
2. `/review-round docs/design/<your-doc>.md` — runs one round: every critic reviews
   in parallel and writes graded findings; an arbiter aggregates into a round file
   and lists required revisions. Revise, bump the version, repeat.
3. Stop when every critic reports nothing material left.

## The descent at a glance

| Round | Doc  | BLOCKER | FINDING | ADVISORY | What happened |
|-------|------|:-------:|:-------:|:--------:|---------------|
| 001   | v0.1 |    3    |   11    |    4     | the seeded flaws surface |
| 002   | v0.2 |    3    |    9    |    5     | original BLOCKERs closed — but the fixes opened **3 new** ones |
| 003   | v0.3 |    1    |    3    |    7     | those closed; the login-denial fix opened **1 new** BLOCKER |
| 004   | v0.4 |    0    |    1    |    6     | a redesign (drop the single-token invariant) clears BLOCKERs |
| 005   | v0.5 |    0    |    2    |    5     | the recovery-enumeration fix introduced **2 new** findings |
| 006   | v0.6 |    0    |    0    |    3     | **converged** — 4/4 critics, nothing material left |

The objection count is not a clean staircase down — it bulges in the middle because
real revisions introduce real regressions. The point of the loop is that it keeps
finding them until it can't.

## Make it yours

Swap the document, swap the panel — keep the protocol. Critics are domain-specific;
the loop is universal. Over time you accumulate a personal library of reviewer
agents in your own style that travels between projects. Generate critics from the
*domain*, not from the document's own claims (a critic spun up to agree will agree),
and prune lenses that never surface anything material.

## Disclaimer

Every document here is fictional. The login spec is intentionally insecure as a
teaching artifact — **do not ship it.** Even the converged v0.6 is a worked example,
not a production design.
