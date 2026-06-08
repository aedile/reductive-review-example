# Run Log — the descent, with the meter running

This is the audit trail for *how* the review history in `rounds/` was produced — not
just the findings, but the time and tokens each critic spent. The point of reductive
review is that the whole process is inspectable; that includes the cost.

**Methodology.** Each round spawned the four critics in **parallel** as independent
subagents. Each got its standing brief (`prompts/`), the protocol (`README.md`), the
document at its current version, and round-specific instructions (fresh read, output
path) — but **no target counts** and no sight of the other critics' output. From round 2
on, each critic's checklist order was **perturbed** (round 1 is the un-perturbed
baseline) to defeat pattern-matching. Between rounds, an arbiter (the orchestrating
session) de-duplicated and adjudicated the findings, then revised the document. The
critics did a fresh full read each round and were required to *prove* prior closures
against the text rather than trust the changelog.

**What the numbers are.** Duration and token figures below are what the harness
reported per **critic subagent** — its wall-clock, and the token count the harness
attributes to that subagent (reported as `subagent_tokens`; treat it as the subagent's
own token usage, not the round's total). They do **not** include the arbiter's
de-duplication, adjudication, and document-revision work between rounds, which is
additional. "Round wall-clock" is the parallel critic phase (≈ the slowest of the four
critics that round), not the sum.

> Why this lives in a file and not in `git log`: the commit timestamps cluster, because
> the history was committed in one batch after the run. These durations are the real
> timing of the review work. Sunlight, not a stopwatch on the `git push`.

## Per-round summary

| Round | Doc  | Critic wall-clock (parallel) | Σ critic tokens | Arbitrated B / F / A | Verdict |
|-------|------|:----------------------------:|:----------------------:|:--------------------:|---------|
| 001   | v0.1 | ~65 s  | ~58.1k | 3 / 11 / 4 | far from done |
| 002   | v0.2 | ~91 s  | ~82.7k | 3 / 9 / 5  | 3 new BLOCKERs from the v0.2 fixes |
| 003   | v0.3 | ~126 s | ~99.5k | 1 / 3 / 7  | 1 new BLOCKER from the v0.3 fix |
| 004   | v0.4 | ~109 s | ~90.1k | 0 / 1 / 6  | BLOCKERs cleared |
| 005   | v0.5 | ~79 s  | ~83.3k | 0 / 2 / 5  | 2 new findings from the v0.5 fixes |
| 006   | v0.6 | ~77 s  | ~83.7k | 0 / 0 / 3  | **converged** |

**Totals:** 6 rounds · 24 critic runs · **~497k** critic tokens ·
**~28.5 min** cumulative critic compute · **~9.1 min** summed parallel critic
wall-clock (arbiter/revision time additional) · 127 critic tool calls.

## Per-critic detail

Raw B/F/A is what each critic reported *before* the arbiter de-duplicated across the
panel (which is why the raw column sums higher than the arbitrated counts above).

| Round | Critic | Duration | Tokens | Tool calls | Raw B / F / A |
|-------|--------|:--------:|:-------------:|:----------:|:-------------:|
| 001 | Security Adversary  | 55.5 s | 14,222 | 4 | 3 / 3 / 3 |
| 001 | Systems Engineer    | 52.0 s | 14,217 | 4 | 2 / 5 / 2 |
| 001 | Product / UX        | 62.5 s | 14,758 | 4 | 3 / 3 / 2 |
| 001 | Skeptical Generalist| 65.2 s | 14,900 | 4 | 2 / 4 / 3 |
| 002 | Security Adversary  | 86.0 s | 22,053 | 6 | 1 / 2 / 2 |
| 002 | Systems Engineer    | 90.8 s | 21,745 | 6 | 1 / 3 / 2 |
| 002 | Product / UX        | 79.7 s | 17,624 | 4 | 2 / 4 / 2 |
| 002 | Skeptical Generalist| 75.1 s | 21,280 | 6 | 1 / 3 / 2 |
| 003 | Security Adversary  | 65.1 s | 19,247 | 4 | 0 / 0 / 2 |
| 003 | Systems Engineer    | 125.9 s| 28,280 | 7 | 1 / 2 / 2 |
| 003 | Product / UX        | 64.3 s | 24,802 | 6 | 0 / 0 / 2 |
| 003 | Skeptical Generalist| 120.1 s| 27,193 | 6 | 0 / 2 / 2 |
| 004 | Security Adversary  | 79.5 s | 20,177 | 6 | 0 / 0 / 2 |
| 004 | Systems Engineer    | 108.9 s| 27,675 | 8 | 0 / 1 / 2 |
| 004 | Product / UX        | 57.3 s | 22,736 | 6 | 0 / 0 / 1 |
| 004 | Skeptical Generalist| 70.9 s | 19,488 | 5 | 0 / 0 / 2 |
| 005 | Security Adversary  | 45.0 s | 19,059 | 4 | 0 / 0 / 2 |
| 005 | Systems Engineer    | 79.0 s | 21,978 | 6 | 0 / 1 / 3 |
| 005 | Product / UX        | 58.8 s | 19,204 | 5 | 0 / 1 / 1 |
| 005 | Skeptical Generalist| 60.7 s | 23,049 | 6 | 0 / 0 / 0 |
| 006 | Security Adversary  | 77.0 s | 25,780 | 7 | 0 / 0 / 2 |
| 006 | Systems Engineer    | 46.2 s | 19,866 | 5 | 0 / 0 / 0 |
| 006 | Product / UX        | 37.1 s | 19,026 | 4 | 0 / 0 / 0 |
| 006 | Skeptical Generalist| 45.0 s | 19,038 | 4 | 0 / 0 / 1 |

## Reading the run

- **Round 3 is the standout** — the most expensive of all six (~376 s of cumulative
  critic compute, ~99.5k tokens), with rounds 2 and 4 close behind. That's the descent
  working: those are the rounds where Systems and the Skeptic re-derived the deepest
  concurrency and recovery arguments (the 126 s / 28k-token Systems run in round 3 is the
  supersession-vs-invariant contradiction being worked out). The hardest rounds are the
  most valuable, not the cheapest.
- **Round 6 used the least cumulative compute** (~205 s across the four critics; round 1
  is close behind, and is actually the shortest by parallel wall-clock) — not because the
  panel coasted, but because there was genuinely little left to refute. Each critic still
  re-derived its prior closures (see the round files) before signing off.
- The raw-vs-arbitrated gap (e.g. round 1's raw 10/15/10 → arbitrated 3/11/4) is the
  arbiter's de-duplication and severity adjudication, recorded in each `round-NNN.md`.
