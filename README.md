# Reductive Review — a worked example

A small, public, runnable example of **reductive review**: improving a document by
repeatedly subjecting it to a panel of adversarial AI critics and driving the count
of legitimate objections down to zero.

Companion to the article in [`docs/blog/reductive-descent.md`](docs/blog/reductive-descent.md).

The document under review — a passwordless "magic link" login spec — is
**fictional and deliberately imperfect**. It exists to be torn apart so you can
watch the technique work. Read the rounds in order; the objection count falls.

## The idea in one paragraph

Most agent-assisted review is additive and one-shot: "review this, suggest
improvements," apply some, move on. There's no notion of *done*. Reductive review
inverts that. The goal isn't more suggestions — it's to shrink the set of
legitimate, material criticisms that remain, round over round, until a panel of
adversarial critics can't find anything material left. You aren't adding to the
document; you're subtracting from the pile of things still wrong with it.

## What's in here

- [`docs/design/magic-link-auth.md`](docs/design/magic-link-auth.md) — the target
  document, versioned (v0.1 → v0.3, changelog at the bottom).
- [`docs/reviews/README.md`](docs/reviews/README.md) — the protocol: panel, findings
  format, arbiter, termination. **This is the reusable part.**
- [`docs/reviews/prompts/`](docs/reviews/prompts/) — one standing brief per critic.
- [`docs/reviews/rounds/`](docs/reviews/rounds/) — the actual review history. Start
  at [`round-001.md`](docs/reviews/rounds/round-001.md).
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

| Round | Doc version | BLOCKER | FINDING | ADVISORY | Verdict       |
|-------|-------------|:-------:|:-------:|:--------:|---------------|
| 001   | v0.1        |    3    |    7    |    5     | far from done |
| 002   | v0.2        |    0    |    2    |    4     | closing       |
| 003   | v0.3        |    0    |    0    |    1     | converged     |

## Make it yours

Swap the document, swap the panel — keep the protocol. Critics are domain-specific;
the loop is universal. Over time you accumulate a personal library of reviewer
agents in your own style that travels between projects. Generate critics from the
*domain*, not from the document's own claims (a critic spun up to agree will agree),
and prune lenses that never surface anything material.

## Disclaimer

Every document here is fictional. The login spec is intentionally insecure as a
teaching artifact — **do not ship it.** Even the hardened v0.3 is a worked example,
not a production design.
